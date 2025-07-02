from pathlib import Path
from fastapi import Depends

from config import settings
from interfaces.controllers.dependencies import (
    get_memo_repo as abstract_memo_repo,
    get_index_repo as abstract_index_repo,
    get_datetime_provider as abstract_datetime_provider,
)
from infrastructure.persistence.fs_memo_repo import FileSystemMemoRepository
from infrastructure.persistence.faiss_index_repo import FaissIndexRepository

from interfaces.utils.datetime import DateTimeProvider
from infrastructure.utils.datetime_jst import DateTimeJST


def provide_memo_repo() -> FileSystemMemoRepository:
    """
    FileSystemMemoRepository の具象実装を提供
    """
    return FileSystemMemoRepository(root=Path(settings.memos_root))


def provide_index_repo(
    memo_repo: FileSystemMemoRepository = Depends(provide_memo_repo),
) -> FaissIndexRepository:
    """
    FaissIndexRepository の具象実装を提供
    """
    return FaissIndexRepository(
        index_dir=Path(settings.index_data_root),
        memo_repo=memo_repo,
    )


def provide_datetime_provider() -> DateTimeProvider:
    """
    DateTimeProvider の具象実装を提供
    """
    return DateTimeJST()


def dependency_overrides() -> dict:
    """
    FastAPI の dependency_overrides 用マッピングを返す
    """
    return {
        abstract_memo_repo: provide_memo_repo,
        abstract_index_repo: provide_index_repo,
        abstract_datetime_provider: provide_datetime_provider,
    }

