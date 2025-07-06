from abc import ABC, abstractmethod
from typing import List, Tuple

from domain.memo import Memo


class SearchRepository(ABC):
    """
    Elasticsearch などの全文検索エンジン向け
    メモ検索および取得機能のインタフェース
    """

    @abstractmethod
    async def search(self, query: str, top_k: int) -> List[Tuple[Memo, float]]:
        """
        クエリ文字列を全文検索し、(Memo, score) のリストを返す
        """
        ...

    @abstractmethod
    async def mget(self, uuids: List[str]) -> List[Memo]:
        """
        複数 UUID からまとめて Memo を取得する。
        存在しない場合は None ではなく空リストや例外で制御してください。
        """
        ...
