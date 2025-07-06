import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List

from interfaces.dtos.search_dto import SearchRequestDTO, SearchResultDTO
from interfaces.controllers.dependencies import get_search_uc
from interfaces.controllers.utils  import log_request
from usecases.search_memos import SearchMemosUseCase

logger = logging.getLogger(__name__)

# FastAPI ルーター: メモ検索エンドポイント
router = APIRouter(tags=["memo"])

@router.post("", response_model=List[SearchResultDTO], status_code=status.HTTP_200_OK, summary="メモ検索")
async def search_memos(
    request: Request,
    dto: SearchRequestDTO,
    uc: SearchMemosUseCase = Depends(get_search_uc),
) -> List[SearchResultDTO]:
    """セマンティック + FAISS によるメモ検索"""
    log_request(request, dto)
    query = dto.query.strip()
    if not query:
        return []

    try:
        results = await uc.execute(query)
        return [SearchResultDTO.from_domain(m) for m in results]
    except Exception as exc:
        logger.error("Search failed: %s", exc, exc_info=True)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="検索処理中にエラーが発生しました")
