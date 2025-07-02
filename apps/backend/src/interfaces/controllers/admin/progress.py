from fastapi import APIRouter, Depends, HTTPException, status
from interfaces.controllers.dependencies import get_progress_uc

router = APIRouter()

@router.get("", status_code=status.HTTP_200_OK)
async def progress(
    uc = Depends(get_progress_uc),
):
    try:
        processed, total = await uc.execute()
        return {"": processed, "total": total}
    except Exception:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="進捗取得失敗です")
