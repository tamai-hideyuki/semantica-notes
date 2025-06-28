from datetime import datetime, timezone
import pytz

JST = pytz.timezone('Asia/Tokyo')

def now_jst() -> datetime:
    # 現在UTC時刻をJSTに変換して返す
    return datetime.now(timezone.utc).astimezone(JST)

def to_jst(dt: datetime) -> datetime:
    # 既存の日時をJSTに変換して返す
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(JST)
