from typing import List
from interfaces.repositories.memo_repo import MemoRepository

async def list_tags(repo: MemoRepository) -> List[str]:
    """
    MemoRepository の list_tags() を呼び出すユースケース。
    """
    return await repo.list_tags()
