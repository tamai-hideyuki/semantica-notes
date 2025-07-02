from fastapi import APIRouter, Depends, Request, HTTPException, status
from interfaces.dtos.create_memo_dto import CreateMemoDTO
from interfaces.dtos.memo_dto import MemoDTO
from interfaces.controllers.utils import log_request
from interfaces.controllers.dependencies import get_create_uc, get_datetime_provider

router = APIRouter()

@router.post("", response_model=MemoDTO, status_code=status.HTTP_201_CREATED)
async def create_memo(
    request: Request,
    dto: CreateMemoDTO,
    uc = Depends(get_create_uc),
    dt_provider = Depends(get_datetime_provider),
) -> MemoDTO:
    log_request(request, dto)
    created_at = dto.created_at or dt_provider.now()
    try:
        memo = await uc.execute(
            title=dto.title,
            body=dto.body,
            tags=dto.tags,
            category=dto.category,
            created_at=created_at,
        )
        return MemoDTO.from_domain(memo)
    except Exception:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="メモ保存失敗です")
