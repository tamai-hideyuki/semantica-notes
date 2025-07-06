FROM python:3.11-slim

# 1. 環境変数
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 2. 作業ディレクトリ
WORKDIR /app/apps/backend

# 3. 依存インストール
COPY apps/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. アプリ全体をコピー
COPY apps/backend/ .

# 5. 起動パスを明示（FastAPI用）
ENV PYTHONPATH=/app/apps/backend/src

# 6. 起動コマンド（FastAPIとして）
CMD ["uvicorn", "src.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
