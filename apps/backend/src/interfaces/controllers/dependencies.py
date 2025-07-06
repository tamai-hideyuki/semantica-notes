import logging
from functools import lru_cache
from pathlib import Path
from fastapi import Depends, Request

from config import settings
from domain.memo import Memo
from interfaces.repositories.index_repo   import IndexRepository
from interfaces.repositories.memo_repo    import MemoRepository, MemoNotFoundError
from interfaces.repositories.search_repo  import SearchRepository
from infrastructure.persistence.fs_memo_repo      import FileSystemMemoRepository
from infrastructure.persistence.faiss_chunk_repo import FaissChunkRepository
from infrastructure.persistence.faiss_index_repo import FaissIndexRepository
from infrastructure.persistence.elasticsearch_repo import ElasticsearchMemoRepository
from infrastructure.services.embedder         import EmbedderService
from interfaces.utils.datetime import DateTimeProvider

from usecases.create_memo           import CreateMemoUseCase
from usecases.search_memos          import SearchMemosUseCase
from usecases.hybrid_search         import HybridSearchUseCase
from usecases.incremental_vectorize import IncrementalVectorizeUseCase
from usecases.get_progress          import GetVectorizeProgressUseCase

logger = logging.getLogger(__name__)

@lru_cache()
def get_memo_repo() -> MemoRepository:
    # FileSystemMemoRepository のコンストラクタはパスのみを受け取る
    return FileSystemMemoRepository(Path(settings.memos_root))

@lru_cache()
def get_faiss_chunk_repo() -> FaissChunkRepository:
    # チャンク検索用 FAISS ディレクトリ
    base_dir = Path(__file__).parents[4] / ".index_data"
    logger.debug(f"🔧 FaissChunkRepository をインスタンス化します (index_dir={base_dir})")
    return FaissChunkRepository(
        index_dir=base_dir,
        dimension=settings.embedding_dim,
    )

@lru_cache()
def get_faiss_index_repo() -> FaissIndexRepository:
    # セマンティック検索用 FAISS インデックスディレクトリ
    base_dir = Path(__file__).parents[4] / ".index_data"
    logger.debug(f"🔧 FaissIndexRepository をインスタンス化します (index_dir={base_dir})")
    return FaissIndexRepository(
        index_dir=base_dir,
        memo_repo=get_memo_repo(),
    )

@lru_cache()
def get_index_repo(
    chunk_repo: FaissChunkRepository = Depends(get_faiss_chunk_repo),
) -> IndexRepository:
    return chunk_repo

@lru_cache()
def get_elastic_repo() -> ElasticsearchMemoRepository:
    raw = settings.elasticsearch_hosts
    if isinstance(raw, str) and raw.startswith("["):
        hosts_list = __import__("json").loads(raw)
    elif isinstance(raw, str):
        hosts_list = [h.strip() for h in raw.split(",") if h.strip()]
    else:
        hosts_list = raw
    return ElasticsearchMemoRepository(
        hosts=hosts_list,
        index_name=settings.elasticsearch_index,
    )

@lru_cache()
def get_embedder_service() -> EmbedderService:
    return EmbedderService(model_name=settings.model_name)

@lru_cache()
def get_datetime_provider() -> DateTimeProvider:
    logger.debug("🔧 DateTimeProvider をインスタンス化します")
    return DateTimeProvider()

@lru_cache()
def get_create_uc(
    memo_repo: MemoRepository = Depends(get_memo_repo),
    datetime_provider: DateTimeProvider = Depends(get_datetime_provider),
    faiss_index_repo: FaissIndexRepository = Depends(get_faiss_index_repo),
    faiss_chunk_repo: FaissChunkRepository = Depends(get_faiss_chunk_repo),
    elastic_repo: ElasticsearchMemoRepository = Depends(get_elastic_repo),
) -> CreateMemoUseCase:
    logger.debug("🔧 CreateMemoUseCase をインスタンス化します")
    class CompositeIndexRepo:
        async def add_to_index(self, uuid: str, memo: Memo) -> None:
            # セマンティック検索用インデックスを更新
            faiss_index_repo.incremental_update([memo])
            # チャンク単位ベクトルインデックスを更新
            chunks = EmbedderService(model_name=settings.model_name).encode_chunks(
                memo.body or memo.title or ""
            )
            items = [(f"{memo.uuid}_{i}", vec) for i, (_, vec) in enumerate(chunks)]
            faiss_chunk_repo.add_chunks_batch(items)
            # 全文検索用 Elasticsearch を更新
            await elastic_repo.index(memo)
    return CreateMemoUseCase(
        memo_repo,
        datetime_provider,
        CompositeIndexRepo(),
    )

@lru_cache()
def get_search_uc(
    faiss_repo: FaissIndexRepository = Depends(get_faiss_index_repo),
    memo_repo: MemoRepository = Depends(get_memo_repo),
) -> SearchMemosUseCase:
    logger.debug("🔧 SearchMemosUseCase をインスタンス化します")
    return SearchMemosUseCase(
        index_repo=faiss_repo,
        memo_repo=memo_repo,
    )

@lru_cache()
def get_hybrid_uc(
    chunk_repo: IndexRepository    = Depends(get_index_repo),
    elastic_repo: SearchRepository = Depends(get_elastic_repo),
    embedder: EmbedderService     = Depends(get_embedder_service),
) -> HybridSearchUseCase:
    logger.debug("🔧 HybridSearchUseCase をインスタンス化します")
    return HybridSearchUseCase(
        chunk_repo=chunk_repo,
        elastic_repo=elastic_repo,
        embedder=embedder,
        semantic_weight=settings.hybrid_semantic_weight,
        elastic_weight=settings.hybrid_elastic_weight,
    )

@lru_cache()
def get_incremental_uc(
    request: Request,
    memo_repo: MemoRepository     = Depends(get_memo_repo),
    chunk_repo: FaissChunkRepository = Depends(get_faiss_chunk_repo),
    embedder: EmbedderService     = Depends(get_embedder_service),
) -> IncrementalVectorizeUseCase:
    logger.debug("🔧 IncrementalVectorizeUseCase をインスタンス化します")
    return IncrementalVectorizeUseCase(
        chunk_repo,
        memo_repo,
        request.app,
        embedder,
    )

@lru_cache()
def get_progress_uc(
    request: Request,
) -> GetVectorizeProgressUseCase:
    logger.debug("🔧 GetVectorizeProgressUseCase をインスタンス化します")
    return GetVectorizeProgressUseCase(request.app)
