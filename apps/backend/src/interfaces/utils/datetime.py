from abc import ABC, abstractmethod
from datetime import datetime

class DateTimeProvider(ABC):
    """現在時刻を提供する抽象インターフェース"""

    @abstractmethod
    def now(self) -> datetime:
        """
        現在日時を返す。

        Returns:
            datetime: 現在の日時インスタンス
        """
        ...
