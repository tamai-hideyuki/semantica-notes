from functools import lru_cache
from fastapi import Depends, Request
import logging

from interfaces.repositories.memo_repo import MemoRepository
from interfaces.repositories.index_repo import IndexRepository
from interfaces.utils.datetime import DateTimeProvider
from usecases.create_memo import CreateMemoUseCase
from usecases.search_memos import SearchMemosUseCase
from usecases.incremental_vectorize import IncrementalVectorizeUseCase
from usecases.get_progress import GetVectorizeProgressUseCase

logger = logging.getLogger(__name__)

@lru_cache()
def get_memo_repo() -> MemoRepository:
    logger.debug("🔧 MemoRepository の実装を提供します")
    ...  # FastAPI 依存オーバーライドで具体実装をバインド

@lru_cache()
def get_index_repo(
    memo_repo: MemoRepository = Depends(get_memo_repo)
) -> IndexRepository:
    logger.debug("🔧 IndexRepository の実装を提供します")
    ...  # FastAPI 依存オーバーライドで具体実装をバインド

@lru_cache()
def get_datetime_provider() -> DateTimeProvider:
    logger.debug("🔧 DateTimeProvider の実装を提供します")
    ...  # FastAPI 依存オーバーライドで具体実装をバインド

@lru_cache()
def get_create_uc(
    memo_repo: MemoRepository = Depends(get_memo_repo),
    index_repo: IndexRepository = Depends(get_index_repo),
    datetime_provider: DateTimeProvider = Depends(get_datetime_provider),
) -> CreateMemoUseCase:
    logger.debug("🔧 CreateMemoUseCase をインスタンス化します")
    return CreateMemoUseCase(memo_repo, index_repo, datetime_provider)

@lru_cache()
def get_search_uc(
    index_repo: IndexRepository = Depends(get_index_repo),
    memo_repo: MemoRepository = Depends(get_memo_repo),
) -> SearchMemosUseCase:
    logger.debug("🔧 SearchMemosUseCase をインスタンス化します")
    return SearchMemosUseCase(index_repo, memo_repo)

@lru_cache()
def get_incremental_uc(
    request: Request,
    index_repo: IndexRepository = Depends(get_index_repo),
    memo_repo: MemoRepository = Depends(get_memo_repo),
) -> IncrementalVectorizeUseCase:
    logger.debug("🔧 IncrementalVectorizeUseCase をインスタンス化します")
    return IncrementalVectorizeUseCase(index_repo, memo_repo, request.app)

@lru_cache()
def get_progress_uc(
    request: Request,
) -> GetVectorizeProgressUseCase:
    logger.debug("🔧 GetVectorizeProgressUseCase をインスタンス化します")
    return GetVectorizeProgressUseCase(request.app)
