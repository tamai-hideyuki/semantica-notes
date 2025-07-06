import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List

from interfaces.dtos.search_dto import SearchRequestDTO, SearchResultDTO
from interfaces.controllers.dependencies import get_hybrid_uc
from usecases.hybrid_search import HybridSearchUseCase

logger = logging.getLogger(__name__)
router = APIRouter(tags=["memo"])

@router.post(
    "",
    response_model=List[SearchResultDTO],
    status_code=status.HTTP_200_OK,
    summary="ハイブリッド検索（semantic＋elastic）",
)
async def search_hybrid(
    request: Request,
    dto: SearchRequestDTO,
    uc: HybridSearchUseCase = Depends(get_hybrid_uc),
) -> List[SearchResultDTO]:
    # ログ出力
    logger.debug(f"Hybrid search query: {dto.query!r}")

    query = dto.query.strip()
    if not query:
        return []

    try:
        memos = await uc.execute(query, top_k=dto.top_k if hasattr(dto, "top_k") else 10)
        # ドメインモデル → DTO 変換
        return [SearchResultDTO.from_domain(m) for m in memos]

    except Exception as e:
        logger.error("ハイブリッド検索エラー: %s", e, exc_info=True)
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ハイブリッド検索中にエラーが発生しました",
        )
