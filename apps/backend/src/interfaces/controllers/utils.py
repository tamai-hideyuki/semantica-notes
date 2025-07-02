from fastapi import Request
import logging
import time

logger = logging.getLogger(__name__)

async def log_request(request: Request, dto: object) -> None:
    """
    リクエスト情報とペイロードを詳細ログに出力
    """
    start = time.time()
    body = None
    try:
        body = await request.json()
    except Exception:
        pass
    logger.debug(
        f"📥 [リクエスト] メソッド={request.method} URL={request.url} ペイロード={body} ヘッダー={dict(request.headers)}"
    )
    request.state._log_start = start

async def log_response(request: Request, response) -> None:
    """
    レスポンス情報を詳細ログに出力
    """
    start = getattr(request.state, '_log_start', time.time())
    duration = time.time() - start
    logger.debug(
        f"📤 [レスポンス] メソッド={request.method} URL={request.url} ステータス={response.status_code} 処理時間={duration:.3f}秒"
    )
