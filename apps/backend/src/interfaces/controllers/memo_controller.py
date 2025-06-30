import logging
from typing import List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status

from interfaces.dtos.search_dto import SearchRequestDTO, SearchResultDTO
from interfaces.dtos.create_memo_dto import CreateMemoDTO
from interfaces.dtos.memo_dto import MemoDTO
from interfaces.dtos.memo_update_dto import MemoUpdateDTO
from interfaces.repositories.memo_repo import MemoRepository, MemoNotFoundError

from interfaces.controllers.common import (
    get_search_uc,
    get_create_uc,
    get_datetime_provider,
)
from interfaces.utils.datetime import DateTimeProvider
from infrastructure.persistence.fs_memo_repo import FileSystemMemoRepository
from usecases.list_categories import list_categories
from usecases.list_tags import list_tags

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["memo"])

HERE = Path(__file__).resolve()
BACKEND = HERE.parents[3]
MEMO_DIR = BACKEND / "memos"


def _log_request(request: Request, dto: object) -> None:
    logger.debug(f"📥 {request.method} {request.url} payload={dto!r}")


def _get_repo() -> MemoRepository:
    """
    DI 用ユーティリティ：FileSystemMemoRepository を返す
    """
    return FileSystemMemoRepository(root=MEMO_DIR)


@router.post(
    "/search",
    response_model=List[SearchResultDTO],
    status_code=status.HTTP_200_OK,
    summary="メモ検索",
)
async def search_memos(
    request: Request,
    dto: SearchRequestDTO,
    uc=Depends(get_search_uc),
) -> List[SearchResultDTO]:
    _log_request(request, dto)
    query = dto.query.strip()
    if not query:
        return []
    try:
        domain_results = await uc.execute(query)
        return [SearchResultDTO.from_domain(m) for m in domain_results]
    except Exception:
        logger.exception("💥 メモ検索中に例外発生")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="検索処理中にエラーが発生しました",
        )


@router.post(
    "/memo",
    response_model=MemoDTO,
    status_code=status.HTTP_201_CREATED,
    summary="メモ作成",
)
async def create_memo(
    request: Request,
    dto: CreateMemoDTO,
    uc=Depends(get_create_uc),
    dt_provider: DateTimeProvider = Depends(get_datetime_provider),
) -> MemoDTO:
    _log_request(request, dto)
    try:
        created_at = dto.created_at or dt_provider.now()
        memo = await uc.execute(
            title=dto.title,
            body=dto.body,
            tags=dto.tags,
            category=dto.category,
            created_at=created_at,
        )
        logger.debug(f"📤 Created memo uuid={memo.uuid}")
        return MemoDTO.from_domain(memo)
    except Exception:
        logger.exception("💥 メモ保存中に例外発生")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="メモの保存に失敗しました",
        )


@router.get(
    "/memo/{uuid}",
    response_model=MemoDTO,
    status_code=status.HTTP_200_OK,
    summary="メモ取得",
)
async def get_memo(
    uuid: str,
    repo: MemoRepository = Depends(_get_repo),
) -> MemoDTO:
    try:
        memo = await repo.get_by_uuid(uuid)
        return MemoDTO.from_domain(memo)
    except MemoNotFoundError as e:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put(
    "/memo/{uuid}",
    response_model=MemoDTO,
    status_code=status.HTTP_200_OK,
    summary="メモ更新",
)
async def update_memo(
    request: Request,
    uuid: str,
    dto: MemoUpdateDTO,
    repo: MemoRepository = Depends(_get_repo),
) -> MemoDTO:
    _log_request(request, dto)
    try:
        updated = await repo.update(uuid=uuid, title=dto.title, body=dto.body)
        return MemoDTO.from_domain(updated)
    except MemoNotFoundError as e:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception:
        logger.exception("💥 メモ更新中に例外発生")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="メモの更新に失敗しました",
        )


@router.get(
    "/tags",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="既存のタグ一覧を取得",
)
async def get_tags(
    repo: MemoRepository = Depends(_get_repo),
) -> List[str]:
    return await list_tags(repo)


@router.get(
    "/categories",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="既存のカテゴリ一覧を取得",
)
async def get_categories(
    repo: MemoRepository = Depends(_get_repo),
) -> List[str]:
    return await list_categories(repo)
