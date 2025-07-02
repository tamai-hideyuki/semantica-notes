from fastapi import APIRouter
from .create     import router as create_router
from .get        import router as get_router
from .update     import router as update_router
from .delete     import router as delete_router
from .search     import router as search_router
from .tags       import router as tags_router
from .categories import router as categories_router

router = APIRouter()

# メモ作成
router.include_router(create_router, prefix="/memos", tags=["memo"])
router.include_router(create_router, prefix="/memo",  tags=["memo"])

# メモ取得（一覧ではなく単一取得の get_router にも単数形を追加！）
router.include_router(get_router,    prefix="/memos", tags=["memo"])
router.include_router(get_router,    prefix="/memo",  tags=["memo"])

# メモ更新・削除（必要なら単数形も同様に）
router.include_router(update_router, prefix="/memos", tags=["memo"])
router.include_router(update_router, prefix="/memo",  tags=["memo"])
router.include_router(delete_router, prefix="/memos", tags=["memo"])
router.include_router(delete_router, prefix="/memo",  tags=["memo"])

# 検索・タグ・カテゴリ
router.include_router(search_router,     prefix="/search",     tags=["memo"])
router.include_router(tags_router,       prefix="/tags",       tags=["memo"])
router.include_router(categories_router, prefix="/categories", tags=["memo"])
