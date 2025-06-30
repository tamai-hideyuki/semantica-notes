import logging
from functools import lru_cache
from fastapi import Depends, Request

from config import settings

# 抽象インターフェイスだけをインポート
from interfaces.repositories.memo_repo import MemoRepository
from interfaces.repositories.index_repo import IndexRepository

# ユースケース抽象インターフェース
from usecases.create_memo import CreateMemoUseCase
from usecases.search_memos import SearchMemosUseCase
from usecases.incremental_vectorize import IncrementalVectorizeUseCase
from usecases.get_progress import GetVectorizeProgressUseCase

# 日時プロバイダ
from interfaces.utils.datetime import DateTimeProvider

logger = logging.getLogger(__name__)

@lru_cache()
def get_memo_repo() -> MemoRepository:
    """
    抽象リポジトリプロバイダ（DIで具体実装とバインド）
    """
    ...  # main.py でオーバーライド

@lru_cache()
def get_index_repo(
    memo_repo: MemoRepository = Depends(get_memo_repo),
) -> IndexRepository:
    """
    抽象インデックスリポジトリプロバイダ
    """
    ...

@lru_cache()
def get_datetime_provider() -> DateTimeProvider:
    """
    抽象日時プロバイダ
    """
    ...

@lru_cache()
def get_create_uc(
    memo_repo: MemoRepository = Depends(get_memo_repo),
    dt_provider: DateTimeProvider = Depends(get_datetime_provider),
) -> CreateMemoUseCase:
    return CreateMemoUseCase(memo_repo, dt_provider)

@lru_cache()
def get_search_uc(
    index_repo: IndexRepository = Depends(get_index_repo),
    memo_repo: MemoRepository = Depends(get_memo_repo),
) -> SearchMemosUseCase:
    """
    メモ検索用ユースケースを返す
    """
    # SearchMemosUseCase は (index_repo, memo_repo) の順で受け取る
    return SearchMemosUseCase(index_repo, memo_repo)

@lru_cache
def get_incremental_uc(
    request: Request,
    index_repo: IndexRepository = Depends(get_index_repo),
    memo_repo: MemoRepository = Depends(get_memo_repo),
) -> IncrementalVectorizeUseCase:
    return IncrementalVectorizeUseCase(index_repo, memo_repo, request.app)

@lru_cache
def get_progress_uc(
    request: Request,
) -> GetVectorizeProgressUseCase:
    return GetVectorizeProgressUseCase(request.app)
