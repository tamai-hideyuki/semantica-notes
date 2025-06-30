from datetime import datetime
from interfaces.utils.datetime import DateTimeProvider
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

# JSTタイムゾーン
try:
    JST_ZONE = ZoneInfo("Asia/Tokyo")
except ZoneInfoNotFoundError:
    # fallback: UTC+9
    from datetime import timezone, timedelta

    JST_ZONE = timezone(timedelta(hours=9))

class DateTimeJST(DateTimeProvider):
    """
    日本標準時 (JST) で現在日時を返すプロバイダの実装
    """
    def now(self) -> datetime:
        # 現在のUTC時刻をJSTに変換して返す
        return datetime.now(JST_ZONE)

# 補助関数として従来の now_jst も提供

def now_jst() -> datetime:
    """
    現在時刻をJSTで返す関数
    """
    return DateTimeJST().now()


def to_jst(dt: datetime) -> datetime:
    """
    任意の datetime を JST に変換して返す関数
    tzinfo がない場合は JST_ZONE を tzinfo に設定
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=JST_ZONE)
    return dt.astimezone(JST_ZONE)
