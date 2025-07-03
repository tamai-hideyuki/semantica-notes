from pathlib import Path
import time
import logging

from fastapi import FastAPI, Request, Depends
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware

from config import settings

# ルートルーター
from interfaces.controllers import router as api_router
# DI 用シグネチャ
from interfaces.controllers.dependencies import (
    get_memo_repo,
    get_index_repo,
    get_datetime_provider,
)

from interfaces.utils.datetime import DateTimeProvider
from infrastructure.utils.datetime_jst import DateTimeJST
from infrastructure.persistence.fs_memo_repo import FileSystemMemoRepository
from infrastructure.persistence.faiss_index_repo import FaissIndexRepository

# ─── ロギング設定 ───────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger("uvicorn.access")  # アクセスログと同じチャネルに出す


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.title,
        version=settings.version,
        description=settings.description,
    )

    # ─── リクエスト／レスポンス毎に日本語ログを出力 ────────────────────────────
    @app.middleware("http")
    async def log_request_jp(request: Request, call_next):
        start = time.time()
        body = await request.body()
        logger.debug(
            f"受信リクエスト: メソッド={request.method} パス={request.url.path} "
            f"ヘッダ={dict(request.headers)} ボディ={body!r}"
        )
        response: Response = await call_next(request)
        elapsed_ms = (time.time() - start) * 1000
        logger.debug(
            f"レスポンス: ステータスコード={response.status_code} "
            f"メソッド={request.method} パス={request.url.path} 所要時間={elapsed_ms:.1f}ms"
        )
        return response

    # ─── CORS 設定 ────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    # ─── アプリ状態 ────────────────────────────────────────────────────────────
    app.state.vectorize_progress = {"processed": 0, "total": 0}

    # ─── DI バインディング ─────────────────────────────────────────────────────
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
        return DateTimeJST()

    # FastAPI の Depends でインターフェース→具象注入
    app.dependency_overrides = {
        get_memo_repo: _provide_memo_repo,
        get_index_repo: _provide_index_repo,
        get_datetime_provider: _provide_datetime_provider,
    }

    # ─── ルーター登録 ────────────────────────────────────────────────────────────
    app.include_router(api_router, prefix="/api", tags=["memo"])

    # ─── 起動時ルート一覧ログ ────────────────────────────────────────────────────
    @app.on_event("startup")
    async def _log_routes() -> None:
        logger.debug("🚀 Registered routes:")
        for route in app.routes:
            if hasattr(route, "methods"):
                methods = ",".join(route.methods)
                logger.debug(f"   {methods:10s} → {route.path}")

    return app


app = create_app()
