from typing import List
from src.interfaces.repositories.memo_repo import MemoRepository

async def list_categories(repo: MemoRepository) -> List[str]:
    """
    MemoRepository の list_categories() を呼び出すユースケース。
    """
    return await repo.list_categories()
