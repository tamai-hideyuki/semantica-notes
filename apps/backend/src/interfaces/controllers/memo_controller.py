import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status

from interfaces.controllers.common import (
    get_search_uc,
    get_create_uc,
    get_datetime_provider,
)
from interfaces.dtos.create_memo_dto import CreateMemoDTO
from interfaces.dtos.memo_dto import MemoDTO
from interfaces.dtos.memo_update_dto import MemoUpdateDTO
from interfaces.dtos.search_dto import SearchRequestDTO, SearchResultDTO
from interfaces.repositories.memo_repo import MemoRepository, MemoNotFoundError
from interfaces.utils.datetime import DateTimeProvider
from infrastructure.persistence.fs_memo_repo import FileSystemMemoRepository
from usecases.list_categories import list_categories
from usecases.list_tags import list_tags

# logger の取得
logger = logging.getLogger(__name__)
# ルーターの作成：全エンドポイントの共通 prefix は /api
router = APIRouter(prefix="/api", tags=["memo"])

# ファイルシステム上のメモ保存ディレクトリパスを構築
HERE = Path(__file__).resolve()
BACKEND = HERE.parents[3]
MEMO_DIR = BACKEND / "memos"


def _log_request(request: Request, dto: object) -> None:
    """
    リクエスト情報をログ出力（メソッド、URL、ペイロード）
    """
    logger.debug(f"📥 {request.method} {request.url} payload={dto!r}")


def _get_repo() -> MemoRepository:
    """
    DI 用ヘルパー：FileSystemMemoRepository を返却
    """
    return FileSystemMemoRepository(root=MEMO_DIR)


@router.post(
    "/search",
    response_model=List[SearchResultDTO],
    status_code=status.HTTP_200_OK,
    summary="メモ検索",
)
async def search_memos(
    request: Request,
    dto: SearchRequestDTO,
    uc=Depends(get_search_uc),
) -> List[SearchResultDTO]:
    """
    検索クエリを受け取り、全文検索用 UseCase を実行して結果を返す
    """
    _log_request(request, dto)
    query = dto.query.strip()
    if not query:
        return []
    try:
        domain_results = await uc.execute(query)
        return [SearchResultDTO.from_domain(m) for m in domain_results]
    except Exception:
        logger.exception("💥 メモ検索中に例外発生")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="検索処理中にエラーが発生しました",
        )


@router.post(
    "/memo",
    response_model=MemoDTO,
    status_code=status.HTTP_201_CREATED,
    summary="メモ作成",
)
async def create_memo(
    request: Request,
    dto: CreateMemoDTO,
    uc=Depends(get_create_uc),
    dt_provider: DateTimeProvider = Depends(get_datetime_provider),
) -> MemoDTO:
    """
    新しいメモを作成し、作成済みの DTO を返却
    """
    _log_request(request, dto)
    try:
        created_at = dto.created_at or dt_provider.now()
        memo = await uc.execute(
            title=dto.title,
            body=dto.body,
            tags=dto.tags,
            category=dto.category,
            created_at=created_at,
        )
        logger.debug(f"📤 Created memo uuid={memo.uuid}")
        return MemoDTO.from_domain(memo)
    except Exception:
        logger.exception("💥 メモ保存中に例外発生")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="メモの保存に失敗しました",
        )


@router.get(
    "/memo/{uuid}",
    response_model=MemoDTO,
    status_code=status.HTTP_200_OK,
    summary="メモ取得",
)
async def get_memo(
    uuid: str,
    repo: MemoRepository = Depends(_get_repo),
) -> MemoDTO:
    """
    UUID をキーにメモを取得。存在しない場合は 404 を返却
    """
    try:
        memo = await repo.get_by_uuid(uuid)
        return MemoDTO.from_domain(memo)
    except MemoNotFoundError as e:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put(
    "/memo/{uuid}",
    response_model=MemoDTO,
    status_code=status.HTTP_200_OK,
    summary="メモ更新",
)
async def update_memo(
    request: Request,
    uuid: str,
    dto: MemoUpdateDTO,
    repo: MemoRepository = Depends(_get_repo),
) -> MemoDTO:
    """
    指定 UUID のメモを更新し、更新後の DTO を返却
    """
    _log_request(request, dto)
    try:
        updated = await repo.update(uuid=uuid, title=dto.title, body=dto.body)
        return MemoDTO.from_domain(updated)
    except MemoNotFoundError as e:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception:
        logger.exception("💥 メモ更新中に例外発生")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="メモの更新に失敗しました",
        )


@router.get(
    "/tags",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="タグ一覧取得",
)
async def get_tags(
    repo: MemoRepository = Depends(_get_repo),
) -> List[str]:
    """
    既存のタグ一覧を返却
    """
    return await list_tags(repo)


@router.get(
    "/categories",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="カテゴリ一覧取得",
)
async def get_categories(
    repo: MemoRepository = Depends(_get_repo),
) -> List[str]:
    """
    既存のカテゴリ一覧を返却
    """
    return await list_categories(repo)


@router.delete(
    "/memo/{uuid}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="メモ削除",
)
async def delete_memo(
    uuid: str,
    repo: MemoRepository = Depends(_get_repo),
) -> None:
    """
    指定 UUID のメモを削除。存在しなければ 404 を返却
    """
    deleted = await repo.delete(uuid)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Memo not found")
    return
