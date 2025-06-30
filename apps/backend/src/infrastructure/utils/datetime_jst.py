from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from interfaces.utils.datetime import DateTimeProvider

# JSTタイムゾーン
try:
    JST_ZONE = ZoneInfo("Asia/Tokyo")
except ZoneInfoNotFoundError:
    from datetime import timezone, timedelta
    JST_ZONE = timezone(timedelta(hours=9))

class DateTimeJST(DateTimeProvider):
    """
    日本標準時 (JST) で現在日時を返すプロバイダの実装
    """
    def now(self) -> datetime:
        return datetime.now(JST_ZONE)

def now_jst() -> datetime:
    """
    現在時刻をJSTで返す関数
    """
    return DateTimeJST().now()
