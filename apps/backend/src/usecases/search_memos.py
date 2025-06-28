from sentence_transformers import SentenceTransformer
import numpy as np
import asyncio
from typing import List
from src.domain.memo import Memo

class SearchMemosUseCase:
    _embedder = SentenceTransformer("sentence-transformers/LaBSE")

    def __init__(self, index_repo, memo_repo):
        self.index_repo = index_repo
        self.memo_repo = memo_repo

    async def execute(self, query: str, top_k: int = 10) -> List[Memo]:
        # ① クエリをベクトル化
        qvec = self._embedder.encode(query, convert_to_numpy=True).reshape(1, -1).astype("float32")

        # ② 類似検索
        distances, indices = self.index_repo.search(qvec, top_k)

        # ③ UUID解決
        uuids = [self.index_repo.id_to_uuid.get(int(idx)) for idx in indices.flatten()]
        uuids = [u for u in uuids if u]

        # ④ メモ取得（並列）
        coros = [self.memo_repo.get_by_uuid(u) for u in uuids]
        memos: List[Memo] = await asyncio.gather(*coros)

        # ⑤ スコア注入（距離を類似度に変換してもよい）
        for memo, dist in zip(memos, distances.flatten()):
            memo.score = float(dist)  # そのままでも類似度1.0からの距離としてOK

        return memos
