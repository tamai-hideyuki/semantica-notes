from pathlib import Path
import logging

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from interfaces.controllers.memo_controller import router as memo_router
from interfaces.controllers.admin_controller import router as admin_router
import interfaces.controllers.common as common
from infrastructure.persistence.fs_memo_repo import FileSystemMemoRepository
from infrastructure.persistence.faiss_index_repo import FaissIndexRepository
from interfaces.utils.datetime import DateTimeProvider

# ロギング設定
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
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

    # 依存の具象バインディング (Composition Root)
    def _provide_memo_repo() -> FileSystemMemoRepository:
        return FileSystemMemoRepository(root=Path(settings.memos_root))

    def _provide_index_repo(
        memo_repo: FileSystemMemoRepository = Depends(_provide_memo_repo),
    ) -> FaissIndexRepository:
        return FaissIndexRepository(
            index_dir=Path(settings.index_data_root),
            memo_repo=memo_repo,
        )

    def _provide_datetime_provider() -> DateTimeProvider:
        # 具象実装はローカルのみでインポート
        from infrastructure.utils.datetime_jst import DateTimeJST
        return DateTimeJST()

    # DI オーバーライド登録
    app.dependency_overrides = {
        common.get_memo_repo: _provide_memo_repo,
        common.get_index_repo: _provide_index_repo,
        common.get_datetime_provider: _provide_datetime_provider,
    }

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
