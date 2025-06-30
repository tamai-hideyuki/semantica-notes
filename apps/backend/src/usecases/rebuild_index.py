from typing import List

from interfaces.repositories.index_repo import IndexRepository
from interfaces.repositories.memo_repo import MemoRepository
from domain.memo import Memo

class RebuildIndexUseCase:
    def __init__(self, index_repo: IndexRepository, memo_repo: MemoRepository):
        self.index_repo = index_repo
        self.memo_repo = memo_repo

    async def execute(self) -> None:
        memos: List[Memo] = await self.memo_repo.list_all()
        # 同期メソッドとして全件再構築
        self.index_repo.rebuild(memos)
