import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Union
from concurrent.futures import ThreadPoolExecutor

import faiss
import numpy as np
from domain.memo import Memo
from interfaces.repositories.index_repo import IndexRepository

logger = logging.getLogger(__name__)


class AsyncFaissIndexRepository(IndexRepository):
    """
    非同期 I/O＋バックグラウンド永続化＋IVF Flatインデックス対応のFAISSリポジトリ
    """

    def __init__(
        self,
        index_dir: Union[str, Path],
        memo_repo,
        dim: int = 768,
        nlist: int = 100,              # IVF セル数
        use_gpu: bool = False,         # GPU有効化フラグ
        persist_workers: int = 2,      # 永続化スレッド数
    ):
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.index_dir / "faiss.index"
        self.map_path = self.index_dir / "id_to_uuid.json"
        self.dim = dim
        self.memo_repo = memo_repo

        # ThreadPoolExecutor for disk I/O
        self._io_executor = ThreadPoolExecutor(max_workers=persist_workers)

        # --- インデックスの読み込み／新規作成 ---
        if self.index_path.exists() and self.map_path.exists():
            self.index: faiss.Index = faiss.read_index(str(self.index_path))
            self.id_to_uuid = self._load_id_map()
            logger.debug("Loaded FAISS index (%d entries)", self.index.ntotal)
        else:
            # IVF Flat Index: 検索速度向上（nlistはデータ量に応じて調整）
            quantizer = faiss.IndexFlatL2(self.dim)
            ivf_index = faiss.IndexIVFFlat(quantizer, self.dim, nlist, faiss.METRIC_L2)
            ivf_index.train(np.zeros((1, self.dim), dtype="float32"))  # 空でも train 必須
            self.index = ivf_index
            self.id_to_uuid: Dict[int, str] = {}
            logger.debug("Created new IVF Flat index (dim=%d, nlist=%d)", self.dim, nlist)

        if self.index.ntotal != len(self.id_to_uuid):
            logger.warning(
                "Index-map mismatch: ntotal=%d, mapped=%d",
                self.index.ntotal,
                len(self.id_to_uuid),
            )

    def _load_id_map(self) -> Dict[int, str]:
        data = json.loads(self.map_path.read_text(encoding="utf-8"))
        return {int(k): v for k, v in data.items()}

    def _save_id_map(self) -> None:
        payload = {str(k): v for k, v in self.id_to_uuid.items()}
        self.map_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    async def _persist(self) -> None:
        """バックグラウンドでディスクに書き出す"""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self._io_executor, self._sync_persist)

    def _sync_persist(self) -> None:
        faiss.write_index(self.index, str(self.index_path))
        self._save_id_map()
        logger.debug("Persisted FAISS index & ID map")

    async def incremental_update(self, memos: List[Memo]) -> None:
        """
        未登録メモのみを追加登録し、非同期で永続化
        """
        # まだ未登録のもの
        new = [m for m in memos if m.uuid not in self.id_to_uuid.values()]
        if not new:
            logger.debug("No new memos to index")
            return

        # ベクトルをまとめて用意
        vecs = np.stack([m.embedding for m in new]).astype("float32")

        # IndexIVF は add の前に train が必要だが、Flat や既存であればそのまま
        self.index.add(vecs)

        base = self.index.ntotal - len(new)
        for i, m in enumerate(new):
            self.id_to_uuid[base + i] = m.uuid

        # ディスクへの書き出しを非同期で
        await self._persist()

    async def rebuild(self, memos: List[Memo]) -> None:
        """
        全件クリアして再構築。非同期で永続化
        """
        # 新規インデックス
        quantizer = faiss.IndexFlatL2(self.dim)
        ivf = faiss.IndexIVFFlat(quantizer, self.dim, self.index.nlist, faiss.METRIC_L2)
        ivf.train(np.stack([m.embedding for m in memos]).astype("float32"))
        ivf.add(np.stack([m.embedding for m in memos]).astype("float32"))

        self.index = ivf
        self.id_to_uuid = {i: m.uuid for i, m in enumerate(memos)}

        await self._persist()

    async def search(
        self, query_vec: np.ndarray, top_k: int = 10
    ) -> Tuple[List[str], np.ndarray]:
        """
        同期的な search を非同期ラッパーで呼び出し、
        (UUIDリスト, 距離配列) を返却
        """
        loop = asyncio.get_running_loop()
        uuids, dists = await loop.run_in_executor(
            None, self._sync_search, query_vec, top_k
        )
        return uuids, dists

    def _sync_search(
        self, query_vec: np.ndarray, top_k: int
    ) -> Tuple[List[str], np.ndarray]:
        q = query_vec.reshape(1, -1).astype("float32")
        # IVF は nprobe で検索精度⇔速度調整可能
        if isinstance(self.index, faiss.IndexIVFFlat):
            self.index.nprobe = min(10, self.index.nlist // 10)
        dists, ids = self.index.search(q, top_k)
        uuids = [self.id_to_uuid.get(int(i)) for i in ids[0]]
        return uuids, dists[0]

FaissIndexRepository = AsyncFaissIndexRepository
