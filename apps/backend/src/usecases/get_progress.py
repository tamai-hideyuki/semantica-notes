from typing import Tuple
from fastapi import FastAPI

class GetVectorizeProgressUseCase:
    def __init__(self, app: FastAPI):
        self.app = app

    async def execute(self) -> Tuple[int, int]:
        # アプリケーション state から進捗を取得
        progress = getattr(self.app.state, 'vectorize_progress', None)
        if not progress:
            # 初期化されていない場合は 0/0
            return 0, 0
        processed = getattr(progress, 'processed', 0)
        total = getattr(progress, 'total', 0)
        return processed, total
