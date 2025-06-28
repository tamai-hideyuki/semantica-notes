from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import logging

from src.config import settings
from src.interfaces.controllers.memo_controller import router as memo_router
from src.interfaces.controllers.admin_controller import router as admin_router

# common の中で定義した抽象プロバイダ
import src.interfaces.controllers.common as common

# 具体実装
from src.infrastructure.persistence.fs_memo_repo import FileSystemMemoRepository
from src.infrastructure.persistence.faiss_index_repo import FaissIndexRepository

# ——————————————————————————————————————————————————————————
# ロギング設定（DEBUGレベルを有効化）
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    level=logging.DEBUG,
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.title,
    version=settings.version,
    description=settings.description,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# 進捗初期化
app.state.vectorize_progress = {"processed": 0, "total": 0}

# ——————————————————————————————————————————————————————————
# 依存の具象バインディング（Composition Root）
# common.get_memo_repo → FileSystemMemoRepository
def _provide_memo_repo() -> FileSystemMemoRepository:
    return FileSystemMemoRepository(root=Path(settings.memos_root))

# common.get_index_repo → FaissIndexRepository
def _provide_index_repo(
    memo_repo: FileSystemMemoRepository = Depends(_provide_memo_repo),
) -> FaissIndexRepository:
    return FaissIndexRepository(
        index_dir=Path(settings.index_data_root),
        memo_repo=memo_repo,
    )

# FastAPI にオーバーライドを登録
app.dependency_overrides[common.get_memo_repo] = _provide_memo_repo
app.dependency_overrides[common.get_index_repo] = _provide_index_repo

# ——————————————————————————————————————————————————————————
# ルーター登録
app.include_router(memo_router)
app.include_router(admin_router)

@app.on_event("startup")
async def dump_routes():
    logger.debug("🚀 Registered routes:")
    for route in app.routes:
        if hasattr(route, "methods"):
            methods = ",".join(route.methods)
            logger.debug(f"   {methods:10s} → {route.path}")
