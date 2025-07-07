from __future__ import annotations

import asyncio
import logging
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
    """非同期ファイル I/O でメモと埋め込みを永続化するリポジトリ"""

    HEADER_BREAK = "---\n"
    _SEM_LIMIT = 10  # 同時並列読み込み数

    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Initialized FileSystemMemoRepository at {self.root}")

    async def add(self, memo: Memo) -> None:
        """新規メモを保存し、embedding があれば .npy にも保存"""
        path = self._build_path(memo)
        path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(path, "w", encoding="utf-8") as fp:
            await fp.write(self._serialize(memo))

        if memo.embedding is not None:
            # NumPy I/O をスレッドプールで実行
            await asyncio.to_thread(self._save_embedding, memo)

    async def list_all(self) -> list[Memo]:
        """全テキストをパス→並列ロード→Memoリスト返却"""
        paths = list(self.root.rglob("*.txt"))
        sem = asyncio.Semaphore(self._SEM_LIMIT)
        tasks = [self._with_semaphore(sem, self._load_memo, p) for p in paths]
        results = await asyncio.gather(*tasks)
        return [m for m in results if m is not None]

    async def get_by_uuid(self, uuid: str) -> Memo:
        """UUIDで検索・取得。なければ例外"""
        pattern = f"{uuid}.txt"
        for path in self.root.rglob(pattern):
            memo = await self._load_memo(path)
            if memo:
                return memo
        raise MemoNotFoundError(f"Memo with UUID {uuid} not found")

    async def update(self, uuid: str, title: str, body: str) -> Memo:
        """ロック付き上書き＋埋め込み再保存"""
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

        await asyncio.to_thread(_sync_replace)

        if updated.embedding is not None:
            await asyncio.to_thread(self._save_embedding, updated)

        return updated

    async def delete(self, uuid: str) -> bool:
        """メモと .npy を削除"""
        try:
            memo = await self.get_by_uuid(uuid)
        except MemoNotFoundError:
            return False

        path = self._build_path(memo)
        await asyncio.to_thread(path.unlink)

        embed_path = path.with_suffix(".npy")
        if embed_path.exists():
            await asyncio.to_thread(embed_path.unlink)

        return True

    # ── Internal ──

    async def _with_semaphore(self, sem: asyncio.Semaphore, fn, arg):
        async with sem:
            return await fn(arg)

    async def _load_memo(self, path: Path) -> Optional[Memo]:
        """非同期にファイル読み込み→パース→埋め込みロード"""
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                raw = await f.read()

            if self.HEADER_BREAK not in raw:
                raise ValueError("Header separator not found")

            header, body = raw.split(self.HEADER_BREAK, 1)
            meta = self._parse_header(header)

            # CREATED_AT の正規化
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
                memo.embedding = await asyncio.to_thread(np.load, str(embed_path))

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
