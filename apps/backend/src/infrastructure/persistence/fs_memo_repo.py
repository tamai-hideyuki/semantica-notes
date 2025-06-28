from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import aiofiles  # pip install aiofiles

from src.domain.memo import Memo
from src.interfaces.repositories.memo_repo import MemoNotFoundError, MemoRepository
from src.infrastructure.utils.datetime_jst import now_jst


class FileSystemMemoRepository(MemoRepository):
    """ローカル FS にメモを保存・取得する軽量リポジトリ（非同期対応）"""

    HEADER_BREAK = "---\n"

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    # ────────────────── Public API ────────────────── #

    async def add(self, memo: Memo) -> None:
        """メモをファイルへ保存（カテゴリごとにサブディレクトリを作成）"""
        file_path = self._build_path(memo)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, "w", encoding="utf-8") as fp:
            await fp.write(self._serialize(memo))

    async def list_all(self) -> List[Memo]:
        """ディレクトリ配下の *.txt を並列読み込みで一括取得"""
        txt_paths = list(self.root.rglob("*.txt"))
        coros = [self._parse_file(path) for path in txt_paths]
        return [m for m in await asyncio.gather(*coros) if m]

    async def get_by_uuid(self, uuid: str) -> Memo:
        """UUID → Memo 取得。見つからねば例外。"""
        pattern = f"{uuid}.txt"
        for path in self.root.rglob(pattern):
            memo = await self._parse_file(path)
            if memo:
                return memo
        raise MemoNotFoundError(f"Memo with UUID {uuid} not found")

    # ────────────────── Internal ────────────────── #

    def _build_path(self, memo: Memo) -> Path:
        return self.root / memo.category / f"{memo.uuid}.txt"

    def _serialize(self, memo: Memo) -> str:
        """Memo → ファイル文字列へ変換"""
        meta = {
            "UUID":        memo.uuid,
            "CREATED_AT":  memo.created_at.isoformat(),
            "TITLE":       memo.title,
            "TAGS":        ",".join(memo.tags),
            "CATEGORY":    memo.category,
            "SCORE":       memo.score,
        }
        header = "\n".join(f"{k}: {v}" for k, v in meta.items())
        return f"{header}\n{self.HEADER_BREAK}{memo.body.strip()}\n"

    async def _parse_file(self, file_path: Path) -> Optional[Memo]:
        """ファイル → Memo（失敗時 None）"""
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as fp:
                raw = await fp.read()
            header, body = raw.split(self.HEADER_BREAK, 1)
        except Exception:
            return None  # 壊れたファイルは黙殺

        meta = {
            k.strip(): v.strip()
            for k, v in (
                line.split(":", 1) for line in header.splitlines() if ":" in line
            )
        }

        # 安全パース
        created_at = (
            datetime.fromisoformat(meta["CREATED_AT"])
            if meta.get("CREATED_AT")
            else now_jst()
        )
        tags = [t.strip() for t in meta.get("TAGS", "").split(",") if t.strip()]
        score = float(meta.get("SCORE", 0.0) or 0.0)

        return Memo(
            uuid=meta.get("UUID", ""),
            title=meta.get("TITLE", ""),
            body=body.strip(),
            category=meta.get("CATEGORY", ""),
            tags=tags,
            created_at=created_at,
            score=score,
        )
