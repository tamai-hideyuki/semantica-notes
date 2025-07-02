import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from app.container import dependency_overrides
from interfaces.controllers.memo_controller import router as memo_router
from interfaces.controllers.admin_controller import router as admin_router

# ロギング設定
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    FastAPI アプリケーションを生成し、ルーター登録と依存注入を行う
    """
    app = FastAPI(
        title=settings.title,
        version=settings.version,
        description=settings.description,
    )

    # CORS ミドルウェア
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    # 進捗初期化
    app.state.vectorize_progress = {"processed": 0, "total": 0}

    # DI オーバーライド設定
    app.dependency_overrides = dependency_overrides()

    # ルーター登録
    app.include_router(memo_router)
    app.include_router(admin_router)

    @app.on_event("startup")
    async def _log_routes() -> None:
        logger.debug("🚀 Registered routes:")
        for route in app.routes:
            if hasattr(route, "methods"):
                methods = ",".join(route.methods)
                logger.debug(f"   {methods:10s} → {route.path}")

    return app


# アプリケーションインスタンス
app = create_app()
