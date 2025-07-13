from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
import numpy as np
from domain.memo import Memo
from interfaces.repositories.memo_repo import MemoNotFoundError, MemoRepository
from infrastructure.utils.datetime_jst import now_jst
from interfaces.utils.file_lock import FileLock

logger = logging.getLogger(__name__)


class FileSystemMemoRepository(MemoRepository):
    """非同期ファイル I/O と並列Executorで高速化したメモリポジトリ"""

    HEADER_BREAK = "---\n"
    _SEM_LIMIT = 20
    _IO_WORKERS = 20
    _EMBED_WORKERS = 4

    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

        self._io_executor = ThreadPoolExecutor(max_workers=self._IO_WORKERS)
        self._embed_executor = ProcessPoolExecutor(max_workers=self._EMBED_WORKERS)
        logger.debug(f"Initialized FileSystemMemoRepository at {self.root}")

    async def add(self, memo: Memo) -> None:
        path = self._build_path(memo)
        path.parent.mkdir(parents=True, exist_ok=True)


        async with aiofiles.open(path, "w", encoding="utf-8") as fp:
            await fp.write(self._serialize(memo))

        if memo.embedding is not None:
            loop = asyncio.get_running_loop()

            await loop.run_in_executor(self._embed_executor, self._save_embedding, memo)

    async def list_all(self) -> list[Memo]:
        """チャンク＆Semaphore でメモを並列ロード"""
        paths = list(self.root.rglob("*.txt"))
        sem = asyncio.Semaphore(self._SEM_LIMIT)

        async def load_with_sem(p: Path) -> Optional[Memo]:
            async with sem:
                return await self._load_memo(p)

        tasks = [load_with_sem(p) for p in paths]
        results = await asyncio.gather(*tasks)
        return [m for m in results if m is not None]

    async def get_by_uuid(self, uuid: str) -> Memo:
        pattern = f"{uuid}.txt"
        for path in self.root.rglob(pattern):
            memo = await self._load_memo(path)
            if memo:
                return memo
        raise MemoNotFoundError(f"Memo with UUID {uuid} not found")

    async def update(self, uuid: str, title: str, body: str) -> Memo:
        old = await self.get_by_uuid(uuid)
        updated = Memo(
            uuid=old.uuid,
            title=title,
            body=body,
            category=old.category,
            tags=old.tags,
            created_at=old.created_at,
            score=old.score,
            embedding=old.embedding,
        )
        path = self._build_path(old)

        def _sync_replace():
            with FileLock(str(path)):
                tmp = path.with_suffix(".tmp")
                tmp.write_text(self._serialize(updated), encoding="utf-8")
                tmp.replace(path)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self._io_executor, _sync_replace)

        if updated.embedding is not None:
            await loop.run_in_executor(self._embed_executor, self._save_embedding, updated)

        return updated

    async def delete(self, uuid: str) -> bool:
        try:
            memo = await self.get_by_uuid(uuid)
        except MemoNotFoundError:
            return False

        path = self._build_path(memo)
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self._io_executor, path.unlink)

        embed_path = path.with_suffix(".npy")
        if embed_path.exists():
            await loop.run_in_executor(self._io_executor, embed_path.unlink)

        return True

    # ── Internal ──

    async def _load_memo(self, path: Path) -> Optional[Memo]:
        try:

            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                raw = await f.read()

            if self.HEADER_BREAK not in raw:
                raise ValueError("Header separator not found")

            header, body = raw.split(self.HEADER_BREAK, 1)
            meta = self._parse_header(header)


            created_str = meta.get("CREATED_AT", "").strip()
            if created_str.endswith("Z"):
                created_str = created_str[:-1] + "+00:00"
            try:
                created = datetime.fromisoformat(created_str)
            except ValueError:
                logger.warning(
                    f"Invalid CREATED_AT '{meta.get('CREATED_AT')}', fallback to now_jst()"
                )
                created = now_jst()

            tags = [t.strip() for t in meta.get("TAGS", "").split(",") if t.strip()]
            score = float(meta.get("SCORE", "0") or 0)

            memo = Memo(
                uuid=meta["UUID"],
                title=meta.get("TITLE", ""),
                body=body.strip(),
                category=meta.get("CATEGORY", ""),
                tags=tags,
                created_at=created,
                score=score,
                embedding=None,
            )


            embed_path = path.with_suffix(".npy")
            if embed_path.exists():
                loop = asyncio.get_running_loop()
                memo.embedding = await loop.run_in_executor(
                    self._embed_executor, np.load, str(embed_path)
                )

            return memo
        except Exception as e:
            logger.warning(f"Failed to load memo from {path}: {e!r}")
            return None

    def _serialize(self, memo: Memo) -> str:
        header = "\n".join([
            f"UUID:{memo.uuid}",
            f"TITLE:{memo.title}",
            f"CATEGORY:{memo.category}",
            f"TAGS:{','.join(memo.tags)}",
            f"CREATED_AT:{memo.created_at.isoformat()}",
            f"SCORE:{memo.score}",
        ])
        return f"{header}\n{self.HEADER_BREAK}{memo.body}"

    def _save_embedding(self, memo: Memo) -> None:
        """同期 NumPy で .npy 保存"""
        path = self._build_path(memo).with_suffix(".npy")
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(str(path), memo.embedding)

    def _parse_header(self, header: str) -> dict[str, str]:
        meta: dict[str, str] = {}
        for line in header.splitlines():
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            meta[key.strip()] = val.strip()
        return meta

    def _build_path(self, memo: Memo) -> Path:
        return (self.root / memo.category / f"{memo.uuid}.txt").resolve()
