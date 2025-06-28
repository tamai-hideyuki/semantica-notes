from uuid import uuid4
from src.domain.memo import Memo
from src.interfaces.repositories.memo_repo import MemoRepository

from src.infrastructure.utils.datetime_jst import now_jst

class AddMemoUseCase:
    def __init__(self, memo_repo: MemoRepository):
        self.memo_repo = memo_repo

    async def execute(self, title: str, tags: str, category: str, body: str) -> str:
        uid = uuid4().hex
        # 直接 JST の現在時刻
        created_at = now_jst()

        memo = Memo(
            uuid=uid,
            title=title,
            tags=tags,
            category=category,
            body=body,
            created_at=created_at,
        )
        await self.memo_repo.add(memo)
        return uid
