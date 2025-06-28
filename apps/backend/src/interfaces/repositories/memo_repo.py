class MemoNotFoundError(Exception):
    """指定された UUID のメモが見つからなかったときに投げられる例外"""
    pass

from abc import ABC, abstractmethod
from typing import List
from src.domain.memo import Memo

class MemoRepository(ABC):
    @abstractmethod
    async def add(self, memo: Memo) -> None:
        """メモを永続化する"""
        pass

    @abstractmethod
    async def list_all(self) -> List[Memo]:
        """すべてのメモを取得する"""
        pass
