import asyncio
from pathlib import Path
import time
import logging

from fastapi import FastAPI, Request, Depends, Response
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from interfaces.controllers import router as api_router
from interfaces.controllers.dependencies import (
    get_memo_repo,
    get_index_repo,
    get_datetime_provider,
    get_faiss_index_repo,
    get_embedder_service,
)
from infrastructure.persistence.fs_memo_repo import FileSystemMemoRepository
from infrastructure.persistence.faiss_index_repo import FaissIndexRepository
from infrastructure.services.embedder import EmbedderService
from interfaces.utils.datetime import DateTimeProvider

# ─── Logging setup ─────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger("uvicorn.access")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.title,
        version=settings.version,
        description=settings.description,
    )

    # ─── Middleware ─────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.time()
        body = await request.body()
        logger.debug(
            "Request: method=%s path=%s headers=%s body=%r",
            request.method,
            request.url.path,
            dict(request.headers),
            body,
        )
        response: Response = await call_next(request)
        elapsed = (time.time() - start) * 1000
        logger.debug(
            "Response: status=%d method=%s path=%s elapsed=%.1fms",
            response.status_code,
            request.method,
            request.url.path,
            elapsed,
        )
        return response

    # ─── Dependency Providers ─────────────────────────────────────────────────
    def provide_memo_repo() -> FileSystemMemoRepository:
        return FileSystemMemoRepository(Path(settings.memos_root))

    def provide_index_repo(
        memo_repo: FileSystemMemoRepository = Depends(provide_memo_repo),
    ) -> FaissIndexRepository:
        return FaissIndexRepository(
            index_dir=Path(settings.index_data_root),
            memo_repo=memo_repo,
            dim=settings.embedding_dim,
        )

    def provide_datetime_provider() -> DateTimeProvider:
        return get_datetime_provider()

    def provide_embedder() -> EmbedderService:
        return get_embedder_service()

    app.dependency_overrides = {
        get_memo_repo: provide_memo_repo,
        get_index_repo: provide_index_repo,
        get_datetime_provider: provide_datetime_provider,
        get_faiss_index_repo: provide_index_repo,
        get_embedder_service: provide_embedder,
    }

    # ─── Startup Events ───────────────────────────────────────────────────────
    @app.on_event("startup")
    async def initialize_faiss():
        """
        起動時にFAISSインデックスの初期化を行う。
        初回のみ全メモのベクトル化とインデックス構築を実施し、以降はスキップ。
        """
        memo_repo = provide_memo_repo()
        faiss_repo = provide_index_repo(memo_repo)
        embedder = provide_embedder()

        if not faiss_repo.id_to_uuid:
            all_memos = await memo_repo.list_all()
            for memo in all_memos:
                if getattr(memo, "embedding", None) is None:
                    vec = embedder.encode(memo.body or memo.title or "")
                    memo.embedding = vec
                    await asyncio.to_thread(memo_repo._save_embedding, memo)
            faiss_repo.rebuild(all_memos)
            logger.debug("FAISS initial rebuild done: %d memos indexed", len(all_memos))
        else:
            logger.debug("FAISS initialization skipped: %d entries already indexed", len(faiss_repo.id_to_uuid))

    # ─── Routers ─────────────────────────────────────────────────────────────
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()
