import logging
from uuid import uuid4
from typing import Optional, List, TYPE_CHECKING

from domain.memo import Memo
from interfaces.repositories.memo_repo import MemoRepository

from infrastructure.utils.datetime_jst import now_jst

if TYPE_CHECKING:
    from interfaces.repositories.index_repo import IndexRepository

logger = logging.getLogger(__name__)

class CreateMemoUseCase:
    """
    メモを永続化し、オプションで検索インデックスを更新するユースケース
    """
    def __init__(
        self,
        memo_repo: MemoRepository,
        index_repo: Optional['IndexRepository'] = None,
    ):
        self.memo_repo = memo_repo
        self.index_repo = index_repo

    async def execute(
        self,
        title: str,
        body: str,
        tags: List[str],
        category: str,
        created_at: Optional[str] = None,
    ) -> Memo:
        memo = Memo(
            uuid=uuid4().hex,
            title=title,
            body=body,
            tags=tags,
            category=category,
            created_at=created_at or now_jst(),
        )

        try:
            await self.memo_repo.add(memo)
            logger.info(f"Persisted memo: {memo.uuid}")
        except Exception as e:
            logger.error(f"Persistence failed [{memo.uuid}]: {e}")
            raise

        if self.index_repo:
            try:
                await self.index_repo.add_to_index(memo.uuid, memo)
                logger.info(f"Indexed memo: {memo.uuid}")
            except AttributeError:
                logger.debug("Index repo missing add_to_index; skip indexing.")
            except Exception as e:
                logger.error(f"Indexing failed [{memo.uuid}]: {e}")

        return memo
