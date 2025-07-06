from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
import aiofiles
import numpy as np

from domain.memo import Memo
from interfaces.repositories.memo_repo import MemoNotFoundError, MemoRepository
from infrastructure.utils.datetime_jst import now_jst
from interfaces.utils.file_lock import FileLock

logger = logging.getLogger(__name__)


class FileSystemMemoRepository(MemoRepository):
    """ローカル FS にメモと埋め込みを永続化する非同期リポジトリ"""

    HEADER_BREAK = "---\n"
    _SEM_LIMIT = 10  # 同時並列読み込み数

    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    async def add(self, memo: Memo) -> None:
        file_path = self._build_path(memo)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        content = self._serialize(memo)
        # メタファイル書き込み
        async with aiofiles.open(file_path, "w", encoding="utf-8") as fp:
            await fp.write(content)
        # 埋め込み永続化
        if memo.embedding is not None:
            await self._save_embedding(memo)

    async def list_all(self) -> list[Memo]:
        paths = list(self.root.rglob("*.txt"))
        sem = asyncio.Semaphore(self._SEM_LIMIT)
        coros = [self._with_semaphore(sem, self._load_memo, path) for path in paths]
        results = await asyncio.gather(*coros)
        return [m for m in results if m]

    async def get_by_uuid(self, uuid: str) -> Memo:
        pattern = f"{uuid}.txt"
        for path in self.root.rglob(pattern):
            memo = await self._load_memo(path)
            if memo:
                return memo
        raise MemoNotFoundError(f"Memo with UUID {uuid} not found")

    async def update(self, uuid: str, title: str, body: str) -> Memo:
        old = await self.get_by_uuid(uuid)
        new_memo = Memo(
            uuid=old.uuid,
            title=title,
            body=body,
            category=old.category,
            tags=old.tags,
            created_at=old.created_at,
            score=old.score,
            embedding=old.embedding,
        )
        file_path = self._build_path(old)

        def _sync_write():
            with FileLock(str(file_path)):
                tmp = file_path.with_suffix('.tmp')
                data = self._serialize(new_memo)
                tmp.write_text(data, encoding='utf-8')
                tmp.replace(file_path)
        await asyncio.to_thread(_sync_write)

        # 更新後も embedding を保持
        if new_memo.embedding is not None:
            await self._save_embedding(new_memo)
        return new_memo

    async def delete(self, uuid: str) -> bool:
        try:
            memo = await self.get_by_uuid(uuid)
        except MemoNotFoundError:
            return False
        file_path = self._build_path(memo)
        await asyncio.to_thread(file_path.unlink)
        # embedding ファイルも削除
        embed_path = file_path.with_suffix('.npy')
        if embed_path.exists():
            await asyncio.to_thread(embed_path.unlink)
        return True

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    async def _with_semaphore(self, sem: asyncio.Semaphore, fn, arg):
        async with sem:
            return await fn(arg)

    async def _load_memo(self, path: Path) -> Memo | None:
        try:
            raw = await self._read_file(path)
            header_str, body = self._split_header_body(raw)
            meta = self._parse_header(header_str)
            uuid = meta.get("UUID")
            if not uuid:
                raise ValueError("Missing UUID in header")
            created_at = (
                datetime.fromisoformat(meta["CREATED_AT"]) if meta.get("CREATED_AT")
                else now_jst()
            )
            tags = [t.strip() for t in meta.get("TAGS", "").split(",") if t.strip()]
            score = float(meta.get("SCORE", 0) or 0)
            memo = Memo(
                uuid=uuid,
                title=meta.get("TITLE", ""),
                body=body.strip(),
                category=meta.get("CATEGORY", ""),
                tags=tags,
                created_at=created_at,
                score=score,
                embedding=None,
            )
            # 埋め込み復元
            embed_path = path.with_suffix('.npy')
            if embed_path.exists():
                memo.embedding = np.load(str(embed_path))
            return memo
        except Exception as e:
            logger.warning(f"Failed to load memo {path}: {e}")
            return None

    async def _read_file(self, path: Path) -> str:
        async with aiofiles.open(path, "r", encoding="utf-8") as fp:
            return await fp.read()

    def _save_embedding(self, memo: Memo) -> None:
        embed_path = self.root / memo.category / f"{memo.uuid}.npy"
        embed_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(str(embed_path), memo.embedding)

    def _build_path(self, memo: Memo) -> Path:
        return self.root / memo.category / f"{memo.uuid}.txt"

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
