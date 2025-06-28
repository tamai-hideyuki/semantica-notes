import logging
from functools import lru_cache
from fastapi import Depends, Request

from src.config import settings

# 抽象インターフェイスだけをインポート
from src.interfaces.repositories.memo_repo import MemoRepository
from src.interfaces.repositories.index_repo import IndexRepository

from src.usecases.search_memos import SearchMemosUseCase
from src.usecases.create_memo import CreateMemoUseCase
from src.usecases.incremental_vectorize import IncrementalVectorizeUseCase
from src.usecases.get_progress import GetVectorizeProgressUseCase

logger = logging.getLogger(__name__)

# 依存先の型は抽象インターフェイス
@lru_cache()
def get_memo_repo() -> MemoRepository:
    raise RuntimeError("ここは main.py でオーバーライドした方がいいですな")

@lru_cache()
def get_index_repo(
    memo_repo: MemoRepository = Depends(get_memo_repo),
) -> IndexRepository:
    raise RuntimeError("ここは main.py でオーバーライドした方がいいですな")

@lru_cache()
def get_search_uc(
    index_repo: IndexRepository = Depends(get_index_repo),
    memo_repo: MemoRepository = Depends(get_memo_repo),
) -> SearchMemosUseCase:
    return SearchMemosUseCase(index_repo, memo_repo)

@lru_cache()
def get_create_uc(
    memo_repo: MemoRepository = Depends(get_memo_repo),
    index_repo: IndexRepository = Depends(get_index_repo),
) -> CreateMemoUseCase:
    return CreateMemoUseCase(memo_repo, index_repo)

def get_incremental_uc(
    request: Request,
    index_repo: IndexRepository = Depends(get_index_repo),
    memo_repo: MemoRepository = Depends(get_memo_repo),
) -> IncrementalVectorizeUseCase:
    return IncrementalVectorizeUseCase(index_repo, memo_repo, request.app)

def get_progress_uc(
    request: Request,
) -> GetVectorizeProgressUseCase:
    return GetVectorizeProgressUseCase(request.app)
