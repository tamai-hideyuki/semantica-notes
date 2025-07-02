import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status

from interfaces.repositories.memo_repo import MemoRepository, MemoNotFoundError
from interfaces.dtos.memo_dto import MemoDTO
from interfaces.controllers.dependencies import get_memo_repo
from interfaces.controllers.utils import log_request  # リクエストログ用ユーティリティ

logger = logging.getLogger(__name__)
router = APIRouter(tags=["memo"])


@router.get(
    "/{uuid}",
    response_model=MemoDTO,
    status_code=status.HTTP_200_OK,
    summary="メモ取得",
)
async def get_memo(
    request: Request,
    uuid: str,
    repo: MemoRepository = Depends(get_memo_repo),
) -> MemoDTO:
    """
    UUID に紐づくメモを取得して返します。
    見つからない場合は 404 を返却します。
    """
    # リクエストをログに出力
    await log_request(request, {"uuid": uuid})

    try:
        # ドメインモデル取得
        memo = await repo.get_by_uuid(uuid)
        # DTO に変換して返却
        return MemoDTO.from_domain(memo)

    except MemoNotFoundError as e:
        logger.warning("メモが見つかりません: %s", uuid)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
