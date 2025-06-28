import logging
from fastapi import APIRouter, Depends, BackgroundTasks, Request, status, HTTPException

from src.interfaces.controllers.common import get_memo_repo, get_index_repo, get_progress_uc
from src.usecases.incremental_vectorize import IncrementalVectorizeUseCase
from src.usecases.get_progress import GetVectorizeProgressUseCase

router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger(__name__)

@router.post("/incremental-vectorize", status_code=status.HTTP_202_ACCEPTED)
async def incremental_vectorize(
    background_tasks: BackgroundTasks,
    request: Request,
    memo_repo = Depends(get_memo_repo),
    index_repo = Depends(get_index_repo),
):
    """
    バックグラウンドでインクリメンタルにベクトル化を走らせます。
    """
    uc = IncrementalVectorizeUseCase(index_repo, memo_repo, request.app)
    background_tasks.add_task(uc.execute)
    logger.debug("📌 Background task registered for vectorization")
    return {"status": "started"}

@router.get("/progress", status_code=status.HTTP_200_OK)
async def progress(
    uc: GetVectorizeProgressUseCase = Depends(get_progress_uc),
):
    """
    ベクトル化の進捗を返します。
    """
    try:
        processed, total = await uc.execute()
        logger.debug(f"📊 Progress {processed}/{total}")
        return {"processed": processed, "total": total}
    except Exception:
        logger.exception("💥 進捗取得中に例外発生")
        raise HTTPException(status_code=500, detail="進捗取得に失敗しました")
