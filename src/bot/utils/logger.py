# src/bot/utils/logger.py
"""Botのロギング設定を提供するモジュール。"""

import logging
import os
from logging.handlers import RotatingFileHandler


class BotLogger:
    """ロガー設定を提供するクラス。

    ファイルログとコンソールログを設定し、適切なフォーマットとレベルで出力する。
    """

    @staticmethod
    def setup() -> logging.Logger:
        """Botのロガーを設定して返す。

        Returns:
            設定されたロガーインスタンス
        """
        # ログディレクトリを環境変数から取得または既定値を使用
        log_dir = os.getenv("LOG_DIR", "./logs")
        os.makedirs(log_dir, exist_ok=True)

        # ロガーを取得
        logger = logging.getLogger("announce-bot")
        logger.setLevel(logging.DEBUG)

        # 既存のハンドラをクリア
        if logger.handlers:
            logger.handlers.clear()

        # ファイルハンドラ（ローテーション付き）
        file_handler = RotatingFileHandler(
            f"{log_dir}/announce-bot.log",
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,
        )
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)

        # コンソールハンドラ
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.INFO)

        # ハンドラをロガーに追加
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger
