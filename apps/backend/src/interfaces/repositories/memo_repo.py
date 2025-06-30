from abc import ABC, abstractmethod
from typing import List, Set
from domain.memo import Memo

class MemoNotFoundError(Exception):
    """指定された UUID のメモが見つからなかったときに投げられる例外"""
    pass

class MemoRepository(ABC):
    @abstractmethod
    async def add(self, memo: Memo) -> None:
        """メモを永続化する"""
        ...

    @abstractmethod
    async def list_all(self) -> List[Memo]:
        """すべてのメモを取得する"""
        ...


    async def list_categories(self) -> List[str]:
        """
        list_all() で取ってきたメモからカテゴリだけ抜き出して返す
        """
        memos = await self.list_all()
        cats: Set[str] = {m.category for m in memos if m.category}
        return list(cats)

    async def list_tags(self) -> List[str]:
        """
        list_all() で取ってきたメモからタグだけ抜き出して返す
        """
        memos = await self.list_all()
        tags_set: Set[str] = set()
        for m in memos:
            for t in m.tags:
                t = t.strip()
                if t:
                    tags_set.add(t)
        return list(tags_set)
