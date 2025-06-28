from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class CreateMemoDTO(BaseModel):
    title: str = Field(..., description="メモのタイトル")
    body: str = Field(..., description="メモ本文")
    tags: List[str] = Field(default_factory=list, description="タグ一覧")
    category: str = Field(..., description="カテゴリ名")
