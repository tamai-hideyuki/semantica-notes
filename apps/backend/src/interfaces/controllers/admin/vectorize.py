from fastapi import APIRouter, Depends, BackgroundTasks, status
from interfaces.controllers.dependencies import get_incremental_uc

router = APIRouter()

@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def incremental_vectorize(
    background_tasks: BackgroundTasks,
    uc = Depends(get_incremental_uc),
):
    background_tasks.add_task(uc.execute)
    return {"status": "started"}
