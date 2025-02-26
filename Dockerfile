FROM python:3.12-slim

# 環境変数設定
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Tokyo
ENV LOG_DIR=/var/log/discord-bot

# 必要なパッケージをインストール
RUN apt-get update && apt-get install -y \
    tzdata \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 作業ディレクトリ作成
WORKDIR /app

# プロジェクトファイルをコピー
COPY src/ ./src/
COPY pyproject.toml README.md config.toml ./

# 依存関係をインストール
RUN pip install --upgrade pip && pip install -e .

# ログディレクトリ作成
RUN mkdir -p /var/log/discord-bot

# 実行ユーザー作成と権限設定
RUN useradd -m botuser && chown -R botuser:botuser /app /var/log/discord-bot
USER botuser

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD pgrep -f "python.*src/main.py" || exit 1

# 実行コマンド
CMD ["python", "src/main.py"]
