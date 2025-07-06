from typing import List, Optional, Union, Tuple
import logging

from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import TransportError, ApiError

from domain.memo import Memo
from interfaces.repositories.search_repo import SearchRepository

logger = logging.getLogger(__name__)

class ElasticsearchMemoRepository(SearchRepository):
    """
    Elasticsearch を用いて Memo を全文検索・取得するリポジトリ実装。
    """

    def __init__(
        self,
        hosts: Union[str, List[str]],
        index_name: str,
        *,
        request_timeout: int = 10,
    ) -> None:
        if isinstance(hosts, str):
            hosts = [hosts]
        version_header = "application/vnd.elasticsearch+json;compatible-with=8"
        self._es = AsyncElasticsearch(
            hosts=hosts,
            request_timeout=request_timeout,
            max_retries=3,
            retry_on_timeout=True,
            headers={
                "Accept": version_header,
                "Content-Type": version_header,
            },
        )
        self._index = index_name

    async def close(self) -> None:
        """Elasticsearch クライアントをクローズします。"""
        await self._es.close()

    async def search(
        self,
        query: str,
        top_k: int = 10,
    ) -> List[Tuple[Memo, float]]:
        """
        全文検索を実行し、(Memo, スコア) リストを返却。
        エラー時は空リストを返します。
        """
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
        except (TransportError, ApiError) as exc:
            logger.error("Elasticsearch search error: %s", exc, exc_info=True)
            return []

        hits = resp.get("hits", {}).get("hits", [])
        results: List[Tuple[Memo, float]] = []
        for hit in hits:
            src = hit.get("_source") or {}
            memo = self._to_memo(src)
            score = float(hit.get("_score", 0.0))
            results.append((memo, score))
        return results

    async def mget(
        self,
        uuids: List[str],
    ) -> List[Optional[Memo]]:
        """
        複数 UUID でまとめて取得。順序を保持し、見つからなければ None。
        エラー時も空リストを返します。
        """
        # 取得対象が空なら即座に空返却して ES の BadRequest を防ぐ
        if not uuids:
            return []
        try:
            resp = await self._es.mget(
                index=self._index,
                body={"ids": uuids},
            )
        except (TransportError, ApiError) as exc:
            logger.error("Elasticsearch mget error: %s", exc, exc_info=True)
            return [None] * len(uuids)

        docs = resp.get("docs", [])
        result: List[Optional[Memo]] = []
        for doc in docs:
            if doc.get("found", False):
                result.append(self._to_memo(doc.get("_source", {})))
            else:
                result.append(None)
        return result

    async def get_by_uuid(self, uuid: str) -> Optional[Memo]:
        """
        UUID で単一メモを取得。見つからなければ None。
        mget を活用して実装。
        """
        results = await self.mget([uuid])
        return results[0] if results else None

    def _to_memo(self, source: dict) -> Memo:
        return Memo(
            uuid=source.get("uuid", ""),
            title=source.get("title", ""),
            body=source.get("body", ""),
            tags=source.get("tags", []),
            category=source.get("category"),
            created_at=source.get("created_at"),
        )
