from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from functools import partial
from pathlib import Path

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
        logger.debug(f"Initialized FileSystemMemoRepository at {self.root!s}")

    async def add(self, memo: Memo) -> None:
        """新規メモを保存し、embedding があれば別ファイルにも書き出す"""
        path = self._build_path(memo)
        path.parent.mkdir(parents=True, exist_ok=True)

        content = self._serialize(memo)
        # メタデータ＋本文を書き込む
        async with aiofiles.open(path, "w", encoding="utf-8") as fp:
            await fp.write(content)

        # embedding は同期 NumPy API なので threadpool で実行
        if memo.embedding is not None:
            await asyncio.to_thread(self._write_embedding, memo)

    async def list_all(self) -> list[Memo]:
        """ルート以下の全テキストファイルを読み込み、Memo オブジェクトを返す"""
        paths = list(self.root.rglob("*.txt"))
        sem = asyncio.Semaphore(self._SEM_LIMIT)
        coros = [self._with_semaphore(sem, self._load_memo, p) for p in paths]
        results = await asyncio.gather(*coros)
        return [m for m in results if m is not None]

    async def get_by_uuid(self, uuid: str) -> Memo:
        """UUID でファイルを探し、存在しなければ例外を投げる"""
        pattern = f"{uuid}.txt"
        for path in self.root.rglob(pattern):
            memo = await self._load_memo(path)
            if memo:
                return memo
        raise MemoNotFoundError(f"Memo with UUID {uuid} not found")

    async def update(self, uuid: str, title: str, body: str) -> Memo:
        """既存ファイルをロックして上書き。embedding も再保存"""
        old = await self.get_by_uuid(uuid)
        new = Memo(
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
                tmp.write_text(self._serialize(new), encoding="utf-8")
                tmp.replace(path)

        await asyncio.to_thread(_sync_replace)

        if new.embedding is not None:
            await asyncio.to_thread(self._write_embedding, new)

        return new

    async def delete(self, uuid: str) -> bool:
        """ファイル＋対応する .npy 埋め込みを削除"""
        try:
            memo = await self.get_by_uuid(uuid)
        except MemoNotFoundError:
            return False

        path = self._build_path(memo)
        await asyncio.to_thread(path.unlink)
        embed = path.with_suffix(".npy")
        if embed.exists():
            await asyncio.to_thread(embed.unlink)
        return True

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    async def _with_semaphore(self, sem: asyncio.Semaphore, fn, arg):
        async with sem:
            return await fn(arg)

    async def _load_memo(self, path: Path) -> Memo | None:
        """ファイルを読み込み、ヘッダ＋本文をパースして Memo を復元"""
        try:
            raw = await aiofiles.open(path, "r", encoding="utf-8").read()
            header, body = self._split_header_body(raw)
            meta = self._parse_header(header)

            created = (
                datetime.fromisoformat(meta["CREATED_AT"])
                if meta.get("CREATED_AT")
                else now_jst()
            )
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
            # embedding ファイルがあれば同期ロード
            embed_path = path.with_suffix(".npy")
            if embed_path.exists():
                memo.embedding = np.load(str(embed_path))
            return memo

        except Exception as e:
            logger.warning(f"Failed to load memo from {path}: {e}")
            return None

    def _serialize(self, memo: Memo) -> str:
        """Memo → ファイル書き込み用文字列に変換"""
        header = "\n".join([
            f"UUID:{memo.uuid}",
            f"TITLE:{memo.title or ''}",
            f"CATEGORY:{memo.category or ''}",
            f"TAGS:{','.join(memo.tags)}",
            f"CREATED_AT:{memo.created_at.isoformat()}",
            f"SCORE:{memo.score}",
        ])
        return f"{header}\n{self.HEADER_BREAK}{memo.body or ''}"

    def _write_embedding(self, memo: Memo) -> None:
        """同期 NumPy を使って .npy ファイルに保存"""
        path = self._build_path(memo).with_suffix(".npy")
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(str(path), memo.embedding)

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

    def _build_path(self, memo: Memo) -> Path:
        return (self.root / memo.category / f"{memo.uuid}.txt").resolve()
