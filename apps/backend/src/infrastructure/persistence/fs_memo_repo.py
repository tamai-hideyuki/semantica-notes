from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
import aiofiles

from domain.memo import Memo
from interfaces.repositories.memo_repo import MemoNotFoundError, MemoRepository
from infrastructure.utils.datetime_jst import now_jst
from interfaces.utils.file_lock import FileLock

logger = logging.getLogger(__name__)

class FileSystemMemoRepository(MemoRepository):
    """ローカル FS にメモを保存・取得・更新する軽量リポジトリ（非同期対応）"""

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

    async def list_all(self) -> list[Memo]:
        paths = list(self.root.rglob("*.txt"))
        sem = asyncio.Semaphore(self._SEM_LIMIT)
        coros = [self._with_semaphore(sem, self._parse_file, path) for path in paths]
        results = await asyncio.gather(*coros)
        return [m for m in results if m]

    async def get_by_uuid(self, uuid: str) -> Memo:
        pattern = f"{uuid}.txt"
        for path in self.root.rglob(pattern):
            memo = await self._parse_file(path)
            if memo:
                return memo
        raise MemoNotFoundError(f"Memo with UUID {uuid} not found")

    async def update(self, uuid: str, title: str, body: str) -> Memo:
        """
        UUID指定で既存メモを更新し、新しい Memo を返す。
        """
        # 既存メモを取得
        old = await self.get_by_uuid(uuid)
        file_path = self._build_path(old)

        # 新しい Memo オブジェクトを生成（更新フィールドのみ差し替え）
        new_memo = Memo(
            uuid=old.uuid,
            title=title,
            body=body,
            category=old.category,
            tags=old.tags,
            created_at=old.created_at,
            score=old.score,
        )

        # 排他ロックしてファイルを原子更新
        def _sync_write():
            with FileLock(str(file_path)):
                tmp = file_path.with_suffix('.tmp')
                data = self._serialize(new_memo)
                tmp.write_text(data, encoding='utf-8')
                tmp.replace(file_path)

        # ブロッキング処理をスレッドプール実行
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _sync_write)

        return new_memo

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

    async def _parse_file(self, file_path: Path) -> Memo | None:
        try:
            raw = await self._read_file(file_path)
            header_str, body = self._split_header_body(raw)
            meta = self._parse_header(header_str)

            if not meta.get("UUID"):
                raise ValueError("Missing UUID in header")

            created_at = (
                datetime.fromisoformat(meta["CREATED_AT"]) if meta.get("CREATED_AT") else now_jst()
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
        return raw.split(self.HEADER_BREAK, 1)

    def _parse_header(self, header: str) -> dict[str, str]:
        meta: dict[str, str] = {}
        for line in header.splitlines():
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            meta[key.strip()] = val.strip()
        return meta
