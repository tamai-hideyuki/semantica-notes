from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import numpy as np

@dataclass
class Memo:
    uuid:       str
    title:      str
    body:       str
    category:   str
    tags:       List[str]
    created_at: datetime
    score:      float = 0.0

    # 埋め込みベクトル用フィールド（初期は None）
    embedding: Optional[np.ndarray] = None

    @property
    def snippet(self) -> str:
        if len(self.body) <= 100:
            return self.body
        return self.body[:100] + '...'
