from fastapi import APIRouter, Depends, status
from typing import List
from interfaces.controllers.dependencies import get_memo_repo
from usecases.list_tags import list_tags

router = APIRouter()

@router.get("",  response_model=List[str], status_code=status.HTTP_200_OK)
async def get_tags(
    repo = Depends(get_memo_repo),
) -> List[str]:
    return await list_tags(repo)
