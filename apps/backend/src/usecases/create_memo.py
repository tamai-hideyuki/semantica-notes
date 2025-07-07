import logging
from uuid import uuid4
from typing import Optional, List, Protocol

from domain.memo import Memo
from interfaces.repositories.memo_repo import MemoRepository
from interfaces.utils.datetime import DateTimeProvider

logger = logging.getLogger(__name__)


class IndexRepository(Protocol):
    """検索インデックス更新用インターフェース"""
    async def add_to_index(self, uuid: str, memo: Memo) -> None:
        ...


class CreateMemoUseCase:
    """
    メモを永続化し、任意で検索インデックスを更新するユースケース
    """
    def __init__(
        self,
        memo_repo: MemoRepository,
        datetime_provider: DateTimeProvider,
        index_repo: Optional[IndexRepository] = None,
    ):
        self._memo_repo = memo_repo
        self._dt_provider = datetime_provider
        self._index_repo = index_repo

    async def execute(
        self,
        title: str,
        body: str,
        tags: List[str],
        category: str,
        created_at: Optional[str] = None,
    ) -> Memo:
        # 1) Memo オブジェクト生成
        timestamp = created_at or self._dt_provider.now()
        memo = Memo(
            uuid=uuid4().hex,
            title=title,
            body=body,
            tags=tags,
            category=category,
            created_at=timestamp,
        )

        # 2) 永続化
        try:
            await self._memo_repo.add(memo)
            logger.info("Memo persisted (uuid=%s)", memo.uuid)
        except Exception as e:
            logger.error("Failed to persist memo (uuid=%s): %s", memo.uuid, e)
            raise

        # 3) インデックス更新（オプション）
        if self._index_repo is not None:
            try:
                await self._index_repo.add_to_index(memo.uuid, memo)
                logger.info("Memo indexed (uuid=%s)", memo.uuid)
            except AttributeError:
                logger.debug("Index repository does not support add_to_index; skipping")
            except Exception as e:
                logger.error("Failed to index memo (uuid=%s): %s", memo.uuid, e)

        return memo
