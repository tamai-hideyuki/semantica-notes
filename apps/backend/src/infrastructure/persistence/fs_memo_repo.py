from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import aiofiles

from src.domain.memo import Memo
from src.interfaces.repositories.memo_repo import MemoNotFoundError, MemoRepository
from src.infrastructure.utils.datetime_jst import now_jst

logger = logging.getLogger(__name__)

class FileSystemMemoRepository(MemoRepository):
    """ローカル FS にメモを保存・取得する軽量リポジトリ（非同期対応）"""

    HEADER_BREAK = "---\n"
    _SEM_LIMIT = 10  # 同時並列読み込み数

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    async def add(self, memo: Memo) -> None:
        file_path = self._build_path(memo)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        content = self._serialize(memo)
        async with aiofiles.open(file_path, "w", encoding="utf-8") as fp:
            await fp.write(content)

    async def list_all(self) -> List[Memo]:
        """
        ディレクトリ配下の *.txt をバッファリング + 制限付き並列で読み込み → パース
        """
        paths: List[Path] = list(self.root.rglob("*.txt"))
        sem = asyncio.Semaphore(self._SEM_LIMIT)
        coros = [self._with_semaphore(sem, self._parse_file, path) for path in paths]
        results = await asyncio.gather(*coros)
        # None（パース失敗）は除外
        return [m for m in results if m]

    async def get_by_uuid(self, uuid: str) -> Memo:
        pattern = f"{uuid}.txt"
        for path in self.root.rglob(pattern):
            memo = await self._parse_file(path)
            if memo:
                return memo
        raise MemoNotFoundError(f"Memo with UUID {uuid} not found")

    # ────────────────── Internal ────────────────── #

    async def _with_semaphore(self, sem: asyncio.Semaphore, fn, arg):
        async with sem:
            return await fn(arg)

    def _build_path(self, memo: Memo) -> Path:
        return self.root / memo.category / f"{memo.uuid}.txt"

    def _serialize(self, memo: Memo) -> str:
        meta = {
            "UUID":       memo.uuid,
            "CREATED_AT": memo.created_at.isoformat(),
            "TITLE":      memo.title,
            "TAGS":       ",".join(memo.tags),
            "CATEGORY":   memo.category,
            "SCORE":      memo.score,
        }
        header = "\n".join(f"{k}: {v}" for k, v in meta.items())
        body   = memo.body.strip()
        return f"{header}\n{self.HEADER_BREAK}{body}\n"

    async def _parse_file(self, file_path: Path) -> Optional[Memo]:
        try:
            raw = await self._read_file(file_path)
            header_str, body = self._split_header_body(raw)
            meta = self._parse_header(header_str)

            # 必須フィールドチェック
            if not meta.get("UUID"):
                raise ValueError("Missing UUID in header")

            created_at = (
                datetime.fromisoformat(meta["CREATED_AT"])
                if meta.get("CREATED_AT")
                else now_jst()
            )
            tags = [t.strip() for t in meta.get("TAGS", "").split(",") if t.strip()]
            score = float(meta.get("SCORE", 0) or 0)

            return Memo(
                uuid=meta["UUID"],
                title=meta.get("TITLE", ""),
                body=body.strip(),
                category=meta.get("CATEGORY", ""),
                tags=tags,
                created_at=created_at,
                score=score,
            )
        except Exception as e:
            logger.warning(f"Failed to parse memo file {file_path}: {e}")
            return None

    async def _read_file(self, path: Path) -> str:
        async with aiofiles.open(path, "r", encoding="utf-8") as fp:
            return await fp.read()

    def _split_header_body(self, raw: str) -> tuple[str, str]:
        if self.HEADER_BREAK not in raw:
            raise ValueError("Header separator not found")
        header, body = raw.split(self.HEADER_BREAK, 1)
        return header, body

    def _parse_header(self, header: str) -> dict[str, str]:
        meta: dict[str, str] = {}
        for line in header.splitlines():
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            meta[key.strip()] = val.strip()
        return meta
