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
        """
        :param query:   検索クエリ文字列
        :param top_k:   取得上限件数。None の場合は無制限取得
        """

        # ──── ショートサーキット：全文検索のみ ────
        if self.semantic_weight <= 0:
            # top_k=None のときは scroll API 等で全件取得する search_all を使う
            if top_k is None:
                es_hits = await self.elastic_repo.search_all(query)
            else:
                es_hits = await self.elastic_repo.search(query, top_k)

            results: List[Memo] = []
            for memo, score in es_hits:
                setattr(memo, "hybrid_score", score)
                results.append(memo)

            # full list already returned; no slicing if top_k is None
            return results if top_k is None else results[:top_k]

        # ──── ショートサーキット：セマンティック検索のみ ────
        if self.elastic_weight <= 0:
            # 埋め込みを計算し、FAISS全件取得（top_k=None なら全件）
            q_vec = await asyncio.to_thread(self.embedder.encode, query)
            uuids_chunks, dists = await asyncio.to_thread(
                self.chunk_repo.search, q_vec, top_k
            )

            results: List[Memo] = []
            for chunk_uuid, dist in zip(uuids_chunks, dists):
                if not chunk_uuid:
                    continue
                base_uuid = chunk_uuid.split("_", 1)[0]
                try:
                    memo = await self.chunk_repo.memo_repo.get_by_uuid(base_uuid)
                    setattr(memo, "hybrid_score", float(dist))
                    results.append(memo)
                except Exception as e:
                    logger.warning(
                        "Semantic fallback failed for uuid=%s: %s", base_uuid, e
                    )

            return results if top_k is None else results[:top_k]

        # ──── 通常のハイブリッド検索 ────

        # 1. テキスト埋め込みをスレッドで計算
        q_vec = await asyncio.to_thread(self.embedder.encode, query)

        # 2. 並列検索: FAISS と Elasticsearch
        faiss_task = asyncio.to_thread(self.chunk_repo.search, q_vec, top_k)
        if top_k is None:
            es_task = self.elastic_repo.search_all(query)
        else:
            es_task = self.elastic_repo.search(query, top_k)
        (uuids_chunks, dists), es_hits = await asyncio.gather(faiss_task, es_task)

        # 3. セマンティックスコアをベースUUIDごとに最大値取得
        sem_scores: Dict[str, float] = {}
        for chunk_uuid, dist in zip(uuids_chunks, dists):
            if not chunk_uuid:
                continue
            base_uuid = chunk_uuid.split("_", 1)[0]
            sem_scores[base_uuid] = max(
                sem_scores.get(base_uuid, 0.0), float(dist)
            )

        # 4. Elasticsearch結果をマップ化
        es_map: Dict[str, Memo] = {memo.uuid: memo for memo, _ in es_hits}
        es_scores: Dict[str, float] = {memo.uuid: score for memo, score in es_hits}

        # 5. 全候補UUIDを収集し、重み付き合成スコア計算
        all_ids = set(sem_scores) | set(es_scores)
        combined_scores: Dict[str, float] = {
            uid: sem_scores.get(uid, 0.0) * self.semantic_weight
                 + es_scores.get(uid, 0.0) * self.elastic_weight
            for uid in all_ids
        }
        logger.debug("Combined hybrid scores: %s", combined_scores)

        # 6. Elasticsearch未取得分をまとめて取得し、ファイルシステムからフォールバック
        missing = [uid for uid in all_ids if uid not in es_map]
        fetched_map: Dict[str, Memo] = {}
        if missing:
            # mget は件数制限なしで取得可能
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

        # 7. 最終リスト組立 & 降順ソート
        results: List[Memo] = []
        for uid, score in combined_scores.items():
            memo = es_map.get(uid) or fetched_map.get(uid)
            if memo is None:
                logger.warning("Memo not found for uuid=%s", uid)
                continue
            setattr(memo, "hybrid_score", score)
            results.append(memo)

        # 全件ソート済みリストをそのまま返す（top_k=None）か、スライスする
        return results if top_k is None else results[:top_k]
