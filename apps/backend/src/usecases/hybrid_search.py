import asyncio
import logging
from typing import Dict, List, Optional

from domain.memo import Memo
from interfaces.repositories.index_repo import IndexRepository
from interfaces.repositories.search_repo import SearchRepository
from infrastructure.services.embedder import EmbedderService

logger = logging.getLogger(__name__)


class HybridSearchUseCase:
    """
    チャンク単位 FAISS + Elasticsearch を融合したハイブリッド検索ユースケース。
    FAISSの距離を類似度に変換し、両者スコアをMin-Max正規化してから合成する。
    top_k=None のときは「無制限取得」を行う。
    """

    def __init__(
        self,
        chunk_repo: IndexRepository,
        elastic_repo: SearchRepository,
        embedder: EmbedderService,
        semantic_weight: float = 0.2,
        elastic_weight: float = 0.8,
    ) -> None:
        self.chunk_repo = chunk_repo
        self.elastic_repo = elastic_repo
        self.embedder = embedder
        self.semantic_weight = semantic_weight
        self.elastic_weight = elastic_weight

    async def execute(self, query: str, top_k: Optional[int] = None) -> List[Memo]:
        # ──── ショートサーキット：全文検索のみ ────
        if self.semantic_weight <= 0:
            es_hits = (
                await self.elastic_repo.search_all(query)
                if top_k is None
                else await self.elastic_repo.search(query, top_k)
            )
            results = []
            for memo, score in es_hits:
                setattr(memo, "hybrid_score", score)
                results.append(memo)
            return results if top_k is None else results[:top_k]

        # ──── ショートサーキット：セマンティック検索のみ ────
        if self.elastic_weight <= 0:
            q_vec = await asyncio.to_thread(self.embedder.encode, query)
            uuids_chunks, dists = await asyncio.to_thread(
                self.chunk_repo.search, q_vec, top_k
            )

            results = []
            for chunk_uuid, dist in zip(uuids_chunks, dists):
                if not chunk_uuid:
                    continue
                base_uuid = chunk_uuid.split("_", 1)[0]
                try:
                    memo = await self.chunk_repo.memo_repo.get_by_uuid(base_uuid)
                    # 距離→類似度
                    similarity = 1.0 - float(dist)
                    setattr(memo, "hybrid_score", similarity)
                    results.append(memo)
                except Exception as e:
                    logger.warning(
                        "Semantic fallback failed for uuid=%s: %s", base_uuid, e
                    )

            return results if top_k is None else results[:top_k]

        # ──── 通常のハイブリッド検索 ────

        # 1. クエリ埋め込みをスレッドで計算
        q_vec = await asyncio.to_thread(self.embedder.encode, query)

        # 2. 並列検索: FAISS と Elasticsearch
        faiss_task = asyncio.to_thread(self.chunk_repo.search, q_vec, top_k)
        es_task = (
            self.elastic_repo.search_all(query)
            if top_k is None
            else self.elastic_repo.search(query, top_k)
        )
        (uuids_chunks, dists), es_hits = await asyncio.gather(faiss_task, es_task)

        # 3. FAISS結果をベースUUIDごとに「最大類似度」で集計
        sem_raw: Dict[str, float] = {}
        for chunk_uuid, dist in zip(uuids_chunks, dists):
            if not chunk_uuid:
                continue
            base_uuid = chunk_uuid.split("_", 1)[0]
            similarity = 1.0 - float(dist)
            sem_raw[base_uuid] = max(sem_raw.get(base_uuid, 0.0), similarity)

        # 4. Elasticsearch結果をマップ化
        es_raw: Dict[str, float] = {}
        es_map: Dict[str, Memo] = {}
        for memo, score in es_hits:
            es_raw[memo.uuid] = float(score)
            es_map[memo.uuid] = memo

        # 5. スコアをMin-Max正規化
        sem_scores = self._normalize_scores(sem_raw)
        es_scores = self._normalize_scores(es_raw)

        # 6. 全候補UUIDを収集し、重み付き合成
        all_ids = set(sem_scores) | set(es_scores)
        combined_scores: Dict[str, float] = {
            uid: sem_scores.get(uid, 0.0) * self.semantic_weight
                 + es_scores.get(uid, 0.0) * self.elastic_weight
            for uid in all_ids
        }
        logger.debug("Combined hybrid scores: %s", combined_scores)

        # 7. Elasticsearch未取得分のフォールバック取得
        missing = [uid for uid in all_ids if uid not in es_map]
        fetched_map: Dict[str, Memo] = {}
        if missing:
            fetched = await self.elastic_repo.mget(missing)
            for uid, memo in zip(missing, fetched):
                if memo:
                    fetched_map[uid] = memo
                else:
                    try:
                        fallback = await self.chunk_repo.memo_repo.get_by_uuid(uid)
                        fetched_map[uid] = fallback
                    except Exception as e:
                        logger.warning(
                            "Fallback get_by_uuid failed for uuid=%s: %s", uid, e
                        )

        # 8. 結果組立 & ソート
        results: List[Memo] = []
        for uid, score in sorted(
            combined_scores.items(), key=lambda x: x[1], reverse=True
        ):
            memo = es_map.get(uid) or fetched_map.get(uid)
            if memo is None:
                logger.warning("Memo not found for uuid=%s", uid)
                continue
            setattr(memo, "hybrid_score", score)
            results.append(memo)

        return results if top_k is None else results[:top_k]

    @staticmethod
    def _normalize_scores(score_map: Dict[str, float]) -> Dict[str, float]:
        """
        Min-Max正規化を行う。全要素が同一値なら1.0を返す。
        """
        if not score_map:
            return {}
        vals = list(score_map.values())
        min_v, max_v = min(vals), max(vals)
        if max_v == min_v:
            return {k: 1.0 for k in score_map}
        return {k: (v - min_v) / (max_v - min_v) for k, v in score_map.items()}
