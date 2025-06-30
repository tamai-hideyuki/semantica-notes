from typing import List
from dataclasses import replace
import asyncio
from sentence_transformers import SentenceTransformer
import numpy as np

from domain.memo import Memo
from interfaces.repositories.memo_repo import MemoRepository
from interfaces.repositories.index_repo import IndexRepository

class SearchMemosUseCase:
    _embedder = SentenceTransformer("sentence-transformers/LaBSE")

    def __init__(
        self,
        index_repo: IndexRepository,
        memo_repo: MemoRepository,
    ):
        self.index_repo = index_repo
        self.memo_repo = memo_repo

    async def execute(self, query: str, top_k: int = 10) -> List[Memo]:
        # ① クエリをベクトル化
        qvec = self._embed(query)

        # ② 類似検索
        distances, indices = self.index_repo.search(qvec, top_k)

        # ③ UUIDマッピング
        uuids = [self.index_repo.id_to_uuid.get(int(idx)) for idx in indices.flatten()]
        uuids = [u for u in uuids if u]

        # ④ メモ取得（並列実行）
        coros = [self.memo_repo.get_by_uuid(u) for u in uuids]
        memos: List[Memo] = await asyncio.gather(*coros)

        # ⑤ 不変オブジェクトにスコアを注入
        results: List[Memo] = []
        for memo, dist in zip(memos, distances.flatten()):
            scored = replace(memo, score=float(dist))
            results.append(scored)

        return results

    def _embed(self, text: str) -> np.ndarray:
        """
        テキストを埋め込みベクトルに変換して返す
        """
        vec = self._embedder.encode(
            text,
            convert_to_numpy=True,
        ).reshape(1, -1).astype('float32')
        return vec
