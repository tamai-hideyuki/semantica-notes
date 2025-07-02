import logging
from fastapi import APIRouter, Depends, Request, HTTPException, status

from interfaces.dtos.memo_update_dto import MemoUpdateDTO
from interfaces.dtos.memo_dto        import MemoDTO
from interfaces.controllers.utils     import log_request
from interfaces.controllers.dependencies import get_memo_repo
from interfaces.repositories.memo_repo   import MemoNotFoundError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["memo"])


@router.put(
    "/{uuid}",
    response_model=MemoDTO,
    status_code=status.HTTP_200_OK,
    summary="メモ更新",
)
async def update_memo(
    request: Request,
    uuid: str,
    dto: MemoUpdateDTO,
    repo = Depends(get_memo_repo),
) -> MemoDTO:
    """
    指定した UUID のメモを更新して新しい状態を返却します。
    見つからない場合は 404、その他エラーは 500 を返します。
    """
    # リクエストを詳細ログに出力
    await log_request(request, dto)

    try:
        # 更新処理
        updated = await repo.update(
            uuid=uuid,
            title=dto.title,
            body=dto.body,
        )
        return MemoDTO.from_domain(updated)

    except MemoNotFoundError as e:
        logger.warning("更新対象のメモが見つかりません: %s", uuid)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    except Exception as e:
        logger.error("メモ更新中に予期せぬエラー: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="メモの更新に失敗しました",
        )
