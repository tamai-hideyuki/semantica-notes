from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class Memo:
    uuid: str
    title: str
    body: str
    category: str
    tags: list[str]
    created_at: datetime
    score: float = 0.0

    @property
    def snippet(self) -> str:
        return (self.body[:100] + '...') if len(self.body) > 100 else self.body
