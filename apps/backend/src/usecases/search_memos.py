from dataclasses import replace
import asyncio
import logging

import numpy as np
from sentence_transformers import SentenceTransformer

from domain.memo import Memo
from interfaces.repositories.index_repo import IndexRepository
from interfaces.repositories.memo_repo import MemoRepository

logger = logging.getLogger(__name__)


class SearchMemosUseCase:
    """SentenceTransformers + FAISS によるセマンティック検索"""

    _embedder = SentenceTransformer("sentence-transformers/LaBSE")

    def __init__(
        self,
        index_repo: IndexRepository,
        memo_repo: MemoRepository
    ) -> None:
        self.index_repo = index_repo
        self.memo_repo = memo_repo

    async def execute(self, query: str, top_k: int = 100) -> list[Memo]:
        # 1. ベクトル化
        q_vec = self._embed(query)

        # 2. 類似検索
        uuids, dists = self.index_repo.search(q_vec, top_k)
        dists = np.asarray(dists).flatten()
        uuids = [u for u in uuids if u]
        if not uuids:
            return []

        # 3. メモ取得（並列）
        coros = [self.memo_repo.get_by_uuid(u) for u in uuids]
        results = await asyncio.gather(*coros, return_exceptions=True)

        # 4. スコア付与 & フィルタリング
        memos: list[Memo] = []
        for uuid, res, dist in zip(uuids, results, dists):
            if isinstance(res, Exception):
                logger.warning("memo uuid=%s fetch failed: %s", uuid, res)
                continue
            # dataclasses.replace を使ってスコアを更新したコピーを生成
            memos.append(replace(res, score=float(dist)))

        return memos

    @classmethod
    def _embed(cls, text: str) -> np.ndarray:
        return cls._embedder.encode(text, convert_to_numpy=True).astype("float32")
