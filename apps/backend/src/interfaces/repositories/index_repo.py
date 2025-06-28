from abc import ABC, abstractmethod
from typing import List
from src.domain.memo import Memo

from typing import List, Tuple
import numpy as np

class IndexRepository:
    ...
    async def search(self, query_vec: np.ndarray, top_k: int) -> Tuple[List[float], List[int]]:
        """query_vec を FAISS に投げて (距離, インデックス) を返す"""
        raise NotImplementedError

    @abstractmethod
    async def incremental_update(self, memos: List[Memo]) -> None:
        """新規メモのみインデックスに追加する"""
        pass

    @abstractmethod
    async def search(self, query: str, top_k: int) -> List[Memo]:
        """クエリを検索し、上位K件のメモを返す"""
        pass
