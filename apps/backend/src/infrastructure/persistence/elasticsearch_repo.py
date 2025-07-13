import logging
import asyncio
from typing import List, Tuple, Optional, Union
from pathlib import Path

from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import TransportError, ApiError
from elasticsearch.helpers import async_bulk
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential

from domain.memo import Memo
from interfaces.repositories.search_repo import SearchRepository

logger = logging.getLogger(__name__)


class OptimizedElasticsearchMemoRepository(SearchRepository):
    """
    Elasticsearch 非同期全文検索リポジトリ（最適化版）
    - async_bulk で高速バルク投入＋リトライ
    - background_index の失敗検知
    - search/mget は TransportError/APIError をキャッチ
    """

    def __init__(
        self,
        hosts: Union[str, List[str]],
        index_name: str,
        *,
        request_timeout: int = 10,
        max_retries: int = 3,
        retry_on_timeout: bool = True,
        bulk_batch_size: int = 500,
    ):
        if isinstance(hosts, str):
            hosts = [hosts]
        self._es = AsyncElasticsearch(
            hosts=hosts,
            request_timeout=request_timeout,
            max_retries=max_retries,
            retry_on_timeout=retry_on_timeout,
            sniff_on_start=True,
            sniff_on_connection_fail=True,
            sniff_timeout=request_timeout,
            headers={
                "Accept": "application/vnd.elasticsearch+json;compatible-with=8",
                "Content-Type": "application/vnd.elasticsearch+json;compatible-with=8",
            },
        )
        self._index = index_name
        self._bulk_size = bulk_batch_size
        self._bg_task: Optional[asyncio.Task] = None

    async def close(self) -> None:
        if self._bg_task and not self._bg_task.done():
            await self._bg_task
        await self._es.close()

    async def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Tuple[Memo, float]]:
        try:
            resp = await self._es.search(
                index=self._index,
                size=top_k,
                query={
                    "multi_match": {
                        "query": query,
                        "fields": ["title^2", "body"],
                        "fuzziness": "AUTO",
                    }
                },
            )
        except (TransportError, ApiError) as e:
            logger.error("Elasticsearch search error: %s", e, exc_info=True)
            return []

        hits = resp.get("hits", {}).get("hits", [])
        return [
            (self._to_memo(hit["_source"]), float(hit.get("_score", 0.0)))
            for hit in hits
        ]

    async def mget(
        self,
        uuids: List[str],
    ) -> List[Optional[Memo]]:
        if not uuids:
            return []
        try:
            resp = await self._es.mget(index=self._index, body={"ids": uuids})
        except (TransportError, ApiError) as e:
            logger.error("Elasticsearch mget error: %s", e, exc_info=True)
            return [None] * len(uuids)

        return [
            self._to_memo(doc["_source"]) if doc.get("found", False) else None
            for doc in resp.get("docs", [])
        ]

    async def get_by_uuid(self, uuid: str) -> Optional[Memo]:
        result = await self.mget([uuid])
        return result[0] if result else None

    async def bulk_index(self, memos: List[Memo]) -> None:
        """
        async_bulk + tenacity でリトライ付き高速一括登録
        """
        async def _actions():
            for m in memos:
                yield {
                    "_op_type": "index",
                    "_index": self._index,
                    "_id": m.uuid,
                    "_source": {
                        "uuid": m.uuid,
                        "title": m.title,
                        "body": m.body,
                        "tags": m.tags,
                        "category": m.category,
                        "created_at": m.created_at.isoformat(),
                    },
                }

        # tenacity で指数バックオフリトライ
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True,
        ):
            with attempt:
                success, failed = await async_bulk(
                    client=self._es,
                    actions=_actions(),
                    chunk_size=self._bulk_size,
                    request_timeout=self._es.transport.request_timeout,
                )
                logger.info("Bulk indexed: success=%d, failed=%d", success, len(failed))
                if failed:
                    logger.warning("Failed bulk items: %s", failed)

    def background_index(self, memos: List[Memo]) -> None:
        """
        バルク登録をバックグラウンドで実行し、例外をログ出力
        """
        if self._bg_task and not self._bg_task.done():
            logger.debug("Previous bulk task still running")
            return

        async def _bg():
            try:
                await self.bulk_index(memos)
            except Exception as e:
                logger.error("Background bulk_index failed: %s", e, exc_info=True)

        self._bg_task = asyncio.create_task(_bg())

    def _to_memo(self, source: dict) -> Memo:
        return Memo(
            uuid=source.get("uuid", ""),
            title=source.get("title", ""),
            body=source.get("body", ""),
            tags=source.get("tags", []),
            category=source.get("category", ""),
            created_at=source.get("created_at"),
        )

ElasticsearchMemoRepository = OptimizedElasticsearchMemoRepository
