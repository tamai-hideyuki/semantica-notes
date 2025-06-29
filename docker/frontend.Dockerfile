# ─── 1. ベースイメージ ─────────────────────────
FROM node:18-alpine

# ─── 2. 作業ディレクトリ ───────────────────────
WORKDIR /app/apps/frontend

# ─── 3. 依存インストール ───────────────────────
# package.json と lockfile（npm: package-lock.json）をまとめてコピー
COPY apps/frontend/package.json apps/frontend/package-lock.json ./
RUN npm install

# ─── 4. ソースをマウントで反映 ─────────────────
# （ローカルの変更がホットリロードに反映される）
VOLUME [ "/app/apps/frontend" ]

# ─── 5. 開発サーバー起動 ───────────────────────
CMD ["npm", "run", "dev", "--", "-p", "3000"]
