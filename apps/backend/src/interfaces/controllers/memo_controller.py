import logging
from typing import List
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.interfaces.dtos.search_dto import SearchRequestDTO, SearchResultDTO
from src.interfaces.dtos.create_memo_dto import CreateMemoDTO
from src.interfaces.dtos.memo_dto import MemoDTO

from src.interfaces.controllers.common import get_search_uc, get_create_uc
from src.infrastructure.utils.datetime_jst import now_jst

from src.interfaces.repositories.memo_repo import MemoRepository
from src.infrastructure.persistence.fs_memo_repo import FileSystemMemoRepository
from src.usecases.list_categories import list_categories
from src.usecases.list_tags       import list_tags

HERE     = Path(__file__).resolve()
BACKEND  = HERE.parents[3]
MEMO_DIR = BACKEND / "memos"

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["memo"])


def _log_request(request: Request, dto: object) -> None:
    logger.debug(f"📥 {request.method} {request.url} payload={dto!r}")


@router.post(
    "/search",
    response_model=List[SearchResultDTO],
    status_code=status.HTTP_200_OK,
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="検索処理中にエラーが発生しました",
        )


@router.post(
    "/memo",
    response_model=MemoDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_memo(
    request: Request,
    dto: CreateMemoDTO,
    uc=Depends(get_create_uc),
) -> MemoDTO:
    _log_request(request, dto)

    try:
        memo = await uc.execute(
            title=dto.title,
            body=dto.body,
            tags=dto.tags,
            category=dto.category,
            created_at=dto.created_at or now_jst(),
        )
        logger.debug(f"📤 Created memo uuid={memo.uuid}")
        return MemoDTO.from_domain(memo)
    except Exception:
        logger.exception("💥 メモ保存中に例外発生")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="メモの保存に失敗しました",
        )


@router.get(
    "/tags",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="既存のタグ一覧を取得",
)
async def get_tags() -> List[str]:
    repo: MemoRepository = FileSystemMemoRepository(root=MEMO_DIR)
    return await list_tags(repo)


@router.get(
    "/categories",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="既存のカテゴリ一覧を取得",
)
async def get_categories() -> List[str]:
    repo: MemoRepository = FileSystemMemoRepository(root=MEMO_DIR)
    return await list_categories(repo)