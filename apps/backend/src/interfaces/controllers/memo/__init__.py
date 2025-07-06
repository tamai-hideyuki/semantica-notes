from fastapi import APIRouter

# メモ関連ルーターのインポート
from .create import router as create_router
from .get import router as get_router
from .update import router as update_router
from .delete import router as delete_router
from .semantic_search import router as semantic_search_router
from .hybrid_search import router as hybrid_search_router
from .tags import router as tags_router
from .categories import router as categories_router

router = APIRouter()

# メモ CRUD（単数形・複数形両方サポート）
for rtr in [create_router, get_router, update_router, delete_router]:
    router.include_router(rtr, prefix="/memo",  tags=["memo"])
    router.include_router(rtr, prefix="/memos", tags=["memo"])

# 検索エンドポイント
router.include_router(semantic_search_router, prefix="/search/semantic", tags=["memo"])
router.include_router(hybrid_search_router,  prefix="/search/hybrid",  tags=["memo"])

# タグ・カテゴリ取得
router.include_router(tags_router,       prefix="/tags",       tags=["memo"])
router.include_router(categories_router, prefix="/categories", tags=["memo"])
