

from pydantic import BaseModel
from typing import List
from src.domain.memo import Memo

class MemoDTO(BaseModel):
    uuid:       str
    title:      str
    body:       str
    snippet:    str
    category:   str
    tags:       List[str]
    created_at: str
    score:      float

    @classmethod
    def from_domain(cls, m: Memo) -> "MemoDTO":
        return cls(
            uuid       = m.uuid,
            title      = m.title,
            body       = m.body,
            snippet    = m.snippet,
            category   = m.category,
            tags       = m.tags if isinstance(m.tags, list) else m.tags.split(","),
            created_at = m.created_at.isoformat(),
            score      = m.score,
        )
