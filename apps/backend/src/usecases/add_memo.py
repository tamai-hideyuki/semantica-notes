from uuid import uuid4
from domain.memo import Memo
from interfaces.repositories.memo_repo import MemoRepository
from interfaces.utils.datetime import DateTimeProvider

class AddMemoUseCase:
    def __init__(self, memo_repo: MemoRepository, dt_provider: DateTimeProvider):
        self.memo_repo = memo_repo
        self.dt_provider = dt_provider

    async def execute(self, title: str, tags: list[str], category: str, body: str) -> str:
        # 一意のUUIDを生成
        uid = uuid4().hex
        # 抽象インターフェース経由で現在時刻を取得
        created_at = self.dt_provider.now()

        memo = Memo(
            uuid=uid,
            title=title,
            tags=tags,
            category=category,
            body=body,
            created_at=created_at,
        )
        # リポジトリに保存
        await self.memo_repo.add(memo)
        return uid
