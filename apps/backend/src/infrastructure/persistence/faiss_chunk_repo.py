import json
import logging
import asyncio
from pathlib import Path
from typing import List, Tuple, Optional, Set, Union
from concurrent.futures import ThreadPoolExecutor

import faiss
import numpy as np
from domain.memo import Memo

logger = logging.getLogger(__name__)

class AsyncFaissChunkRepository:
    """
    チャンク単位の FAISS インデックス管理リポジトリ（非同期永続化対応）
    - チャンクIDリストでインデックス⇔ID逆引きをO(1)に
    - ThreadPoolExecutorでディスクI/Oをオフロード
    - 大規模向けIVF Flat IPインデックスに切り替え可能
    """
    def __init__(
        self,
        index_dir: Union[str, Path],
        dimension: int,
        use_ivf: bool = False,
        nlist: int = 128,
        io_workers: int = 2,
    ):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.dimension = dimension
        self.use_ivf = use_ivf
        self.nlist = nlist

        # 永続化用スレッドプール
        self._io_executor = ThreadPoolExecutor(max_workers=io_workers)
        # チャンクID の順序付きマッピング
        self._chunk_ids: List[str] = []

        # FAISS インデックスをロード or 作成
        self.index = self._load_or_create_index()

        # チャンクIDリストをロード
        self._load_chunk_ids()

    def _load_or_create_index(self) -> faiss.Index:
        idx_path = self.index_dir / "chunk.index"
        if idx_path.exists():
            idx = faiss.read_index(str(idx_path))
            logger.debug("Loaded FAISS index: %s (ntotal=%d)", idx_path, idx.ntotal)
        else:
            if self.use_ivf:
                quantizer = faiss.IndexFlatIP(self.dimension)
                idx = faiss.IndexIVFFlat(quantizer, self.dimension, self.nlist, faiss.METRIC_INNER_PRODUCT)
                idx.train(np.zeros((1, self.dimension), dtype="float32"))  # train 必須
                logger.debug("Created IVF FlatIP index (dim=%d, nlist=%d)", self.dimension, self.nlist)
            else:
                idx = faiss.IndexFlatIP(self.dimension)
                logger.debug("Created FlatIP index (dim=%d)", self.dimension)
        return idx

    def _load_chunk_ids(self) -> None:
        path = self.index_dir / "chunk_ids.json"
        if path.exists():
            try:
                raw = path.read_text(encoding="utf-8")
                self._chunk_ids = json.loads(raw)
                logger.debug("Loaded %d chunk IDs", len(self._chunk_ids))
            except Exception as e:
                logger.error("Failed to load chunk_ids.json: %s", e)
                self._chunk_ids = []
        else:
            self._chunk_ids = []

    async def _persist(self) -> None:
        """FAISSインデックスとチャンクIDリストを非同期で永続化"""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self._io_executor, self._sync_persist)

    def _sync_persist(self) -> None:
        try:
            # インデックス書き出し
            faiss.write_index(self.index, str(self.index_dir / "chunk.index"))
            # チャンクIDリスト書き出し
            (self.index_dir / "chunk_ids.json").write_text(
                json.dumps(self._chunk_ids, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.debug("Persisted index and %d chunk IDs", len(self._chunk_ids))
        except Exception as e:
            logger.error("Persistence error: %s", e)

    async def add_chunks_batch(self, items: List[Tuple[str, np.ndarray]]) -> None:
        """
        バッチ単位でチャンクを追加し、非同期で一度だけ永続化
        """
        # 新規チャンクのみフィルタ
        new = [(cid, vec) for cid, vec in items if cid not in self._chunk_ids]
        if not new:
            logger.debug("No new chunks to add")
            return

        vecs = np.stack([vec for _, vec in new]).astype("float32")
        self.index.add(vecs)

        # ID リストを伸張
        self._chunk_ids.extend([cid for cid, _ in new])

        # 非同期永続化
        await self._persist()

    async def add_chunks(self, items: List[Tuple[str, np.ndarray]]) -> None:
        """単体追加もバッチ関数に委譲"""
        await self.add_chunks_batch(items)

    def _sync_search(self, query: np.ndarray, top_k: int) -> List[Tuple[str, float]]:
        total = self.index.ntotal
        if total == 0:
            return []

        k = min(top_k, total)
        # IVF 時は nprobe を調整可能
        if self.use_ivf and isinstance(self.index, faiss.IndexIVFFlat):
            self.index.nprobe = min(10, self.nlist // 10)

        D, I = self.index.search(query.reshape(1, -1).astype("float32"), k)
        results: List[Tuple[str, float]] = []
        for idx, score in zip(I[0], D[0]):
            if idx < 0 or idx >= len(self._chunk_ids):
                continue
            results.append((self._chunk_ids[idx], float(score)))
        return results

    async def search(self, query_vec: np.ndarray, top_k: int) -> List[Tuple[str, float]]:
        """非同期ラッパー"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._sync_search, query_vec, top_k)

    async def filter_new(self, memos: List[Memo]) -> List[Memo]:
        """
        まだベクトル化されていないメモだけを返す
        """
        existing = {cid.split("_", 1)[0] for cid in self._chunk_ids}
        return [m for m in memos if m.uuid not in existing]

FaissChunkRepository = AsyncFaissChunkRepository
