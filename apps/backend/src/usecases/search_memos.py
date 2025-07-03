from typing import List, Optional
from dataclasses import replace
import asyncio
import logging
from sentence_transformers import SentenceTransformer
import numpy as np

from domain.memo import Memo
from interfaces.repositories.memo_repo import MemoRepository, MemoNotFoundError
from interfaces.repositories.index_repo import IndexRepository

logger = logging.getLogger(__name__)

class SearchMemosUseCase:
    _embedder = SentenceTransformer("sentence-transformers/LaBSE")

    def __init__(
        self,
        index_repo: IndexRepository,
        memo_repo: MemoRepository,
    ):
        self.index_repo = index_repo
        self.memo_repo = memo_repo

    async def execute(self, query: str, top_k: int = 100) -> List[Memo]:
        # ① クエリをベクトル化
        qvec = self._embed(query)

        # ② 類似検索
        distances, indices = self.index_repo.search(qvec, top_k)

        # ③ UUIDマッピング
        uuids = [self.index_repo.id_to_uuid.get(int(idx)) for idx in indices.flatten()]
        uuids = [u for u in uuids if u]

        # ④ メモ取得（並列実行・エラー捕捉あり）
        coros = [self.memo_repo.get_by_uuid(u) for u in uuids]
        results = await asyncio.gather(*coros, return_exceptions=True)

        # ⑤ スコア注入（取得失敗を除外）
        valid_results: List[Memo] = []
        for uuid, memo_or_exc, dist in zip(uuids, results, distances.flatten()):
            if isinstance(memo_or_exc, MemoNotFoundError):
                logger.warning(f"[検索] UUID={uuid} のメモが見つかりませんでした（スキップ）")
                continue
            elif isinstance(memo_or_exc, Exception):
                logger.error(f"[検索] UUID={uuid} のメモ取得中に未知の例外: {memo_or_exc}", exc_info=True)
                continue
            # スコアを注入して格納
            scored = replace(memo_or_exc, score=float(dist))
            valid_results.append(scored)

        return valid_results

    def _embed(self, text: str) -> np.ndarray:
        """
        テキストを埋め込みベクトルに変換して返す
        """
        vec = self._embedder.encode(
            text,
            convert_to_numpy=True,
        ).reshape(1, -1).astype('float32')
        return vec
