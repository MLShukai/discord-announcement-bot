# src/main.py
"""Botのメインエントリポイント。"""

import asyncio
import logging
import os
import signal

from dotenv import load_dotenv

from bot.client import AnnounceBotClient
from bot.constants import EnvKeys
from bot.utils.logger import BotLogger

# Botインスタンス
bot = None

# シャットダウンフラグ
shutdown_flag = False


async def shutdown(signal: signal.Signals | None = None):
    """Botをグレースフルシャットダウンする。

    Args:
        signal: 受信したシグナル（オプション）
    """
    global shutdown_flag

    if shutdown_flag:
        return

    shutdown_flag = True
    logger = logging.getLogger("announce-bot")

    if signal:
        logger.info(f"シグナル {signal.name} を受信しました。シャットダウンします...")
    else:
        logger.info("シャットダウンします...")

    if bot is not None:
        # スケジュールタスクをキャンセル
        if hasattr(bot, "scheduler"):
            bot.scheduler.cancel_all_tasks()
            logger.info("スケジュールタスクをキャンセルしました")

        # Botをクローズ
        await bot.close()
        logger.info("Botを終了しました")

    # イベントループを停止
    loop = asyncio.get_event_loop()
    if not loop.is_closed():
        loop.stop()


async def main():
    """Botのメインエントリポイント。"""
    global bot

    # 環境変数を読み込み
    load_dotenv()

    # ロガーを設定
    logger = BotLogger.setup()
    logger.info("Discord アナウンスBotを起動しています...")

    # トークンチェック
    token = os.getenv(EnvKeys.DISCORD_TOKEN)
    if not token:
        logger.error(
            "DISCORD_TOKENが設定されていません。.envファイルを確認してください。"
        )
        return

    # ハンドラを設定
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(s)))

    try:
        # Botを初期化して起動
        bot = AnnounceBotClient()
        await bot.start(token)
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        await shutdown()
    finally:
        if not shutdown_flag:
            await shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass  # シグナルハンドラが処理するため、ここでは何もしない
