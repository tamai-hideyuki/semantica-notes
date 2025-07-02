from fastapi import APIRouter
from .vectorize import router as vectorize_router
from .progress  import router as progress_router

router = APIRouter()
router.include_router(vectorize_router, prefix="/incremental-vectorize", tags=["admin"])
router.include_router(progress_router,    prefix="/progress",               tags=["admin"])
