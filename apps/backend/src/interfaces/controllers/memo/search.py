import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from typing import List

from interfaces.dtos.search_dto import SearchRequestDTO, SearchResultDTO
from interfaces.controllers.dependencies import get_search_uc
from interfaces.controllers.utils  import log_request
from usecases.search_memos import SearchMemosUseCase

logger = logging.getLogger(__name__)

router = APIRouter(tags=["memo"])

@router.post(
    "",
    response_model=List[SearchResultDTO],
    status_code=status.HTTP_200_OK,
    summary="メモ検索",
)
async def search_memos(
    request: Request,
    dto: SearchRequestDTO,
    uc: SearchMemosUseCase = Depends(get_search_uc),
) -> List[SearchResultDTO]:
    # リクエスト内容をログ出力
    log_request(request, dto)

    # クエリ前処理
    query = dto.query.strip()
    if not query:
        return []

    try:
        # ユースケース実行 → ドメインモデルのリストを取得
        domain_results = await uc.execute(query)
        # ドメインモデル → DTO 変換
        return [SearchResultDTO.from_domain(m) for m in domain_results]

    except Exception as e:
        # エラー詳細をログに残す
        logger.error("検索処理中にエラーが発生しました: %s", e, exc_info=True)
        # クライアントには汎用エラーメッセージを返却
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="検索処理中にエラーが発生しました",
        )
