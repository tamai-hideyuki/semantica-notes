from fastapi import APIRouter
from .memo  import router as memo_router
from .admin import router as admin_router

router = APIRouter()

# サブルーターを一括登録
router.include_router(memo_router)
router.include_router(admin_router, prefix="/admin", tags=["admin"])
