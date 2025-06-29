# ─── 1. ベースイメージ ─────────────────────────
FROM python:3.11-slim

# ─── 2. 動作環境整備 ───────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/apps/backend

# ─── 3. 依存インストール ───────────────────────
COPY apps/backend/requirements.txt ./
RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ─── 4. ソースをマウントで反映 ─────────────────
VOLUME [ "/app/apps/backend" ]

# ─── 5. アプリ起動 ───────────────────────────
# (python run.py は内部で uvicorn を立ち上げる)
CMD ["python", "run.py"]
