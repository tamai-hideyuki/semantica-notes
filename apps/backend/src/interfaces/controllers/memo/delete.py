import logging
from fastapi import APIRouter, Depends, Request, HTTPException, status

from interfaces.controllers.dependencies import get_memo_repo
from interfaces.controllers.utils import log_request

logger = logging.getLogger(__name__)
router = APIRouter(tags=["memo"])


@router.delete(
    "/{uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="メモ削除",
)
async def delete_memo(
    request: Request,
    uuid: str,
    repo = Depends(get_memo_repo),
) -> None:
    """
    UUID に紐づくメモを削除します。
    削除成功時は 204 No Content、存在しない場合は 404 を返します。
    """
    # リクエストをログに出力
    await log_request(request, {"uuid": uuid})

    deleted = await repo.delete(uuid)
    if not deleted:
        logger.warning("削除対象のメモが見つかりません: %s", uuid)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="メモが見つからないです",
        )

    # 成功時は何も返さず 204
    return
