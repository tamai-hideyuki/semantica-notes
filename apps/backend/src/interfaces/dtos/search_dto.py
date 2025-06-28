from pydantic import BaseModel
from typing import List
from src.domain.memo import Memo

class SearchRequestDTO(BaseModel):
    query: str

class SearchResultDTO(BaseModel):
    uuid:       str
    title:      str
    snippet:    str
    body:       str
    category:   str
    tags:       List[str]
    created_at: str
    score:      float

    @classmethod
    def from_domain(cls, m: Memo) -> "SearchResultDTO":
        return cls(
            uuid       = m.uuid,
            title      = m.title,
            snippet    = m.snippet,
            body       = m.body,
            category   = m.category,
            tags       = m.tags if isinstance(m.tags, list) else m.tags.split(","),
            created_at = m.created_at.isoformat(),
            score      = m.score,
        )
