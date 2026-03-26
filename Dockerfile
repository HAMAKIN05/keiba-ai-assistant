# ============================================
# 競馬予想 AI アシスタント - Dockerfile
# マルチステージビルド: Node.js(フロント) → Python(バックエンド)
# ============================================

# --- Stage 1: フロントエンドビルド ---
FROM node:20-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: 本番サーバー ---
FROM python:3.12-slim
WORKDIR /app

# システム依存
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python依存パッケージ
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# バックエンドコード
COPY backend/ ./

# フロントエンドビルド成果物
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# 環境変数
ENV FRONTEND_DIST_DIR=/app/frontend/dist

# ポート
EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# 起動
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
