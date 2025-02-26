# src/bot/client.py
"""Discord Botのメインクライアントモジュール。"""

import logging
from typing import override

import discord
from discord.ext import commands

from .announcement import AnnouncementService, AnnouncementType
from .config import ConfigManager
from .constants import ConfigKeys, ReactionEmoji
from .scheduler import TaskScheduler


class AnnounceBotClient(commands.Bot):
    """告知Bot用のDiscordクライアント。

    イベント処理、スケジュールタスク、コマンド登録などを担当する。
    """

    def __init__(self):
        """Botクライアントを初期化する。"""
        # インテントを構成
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.reactions = True

        # Botを初期化
        super().__init__(
            command_prefix="!",  # メッセージコマンド用のフォールバックプレフィックス
            intents=intents,
            help_command=None,  # デフォルトのヘルプコマンドを無効化
        )

        # ロガーを設定
        self.logger = logging.getLogger("announce-bot.client")

        # コンポーネントを初期化
        self.config = ConfigManager()
        self.announcement_service = AnnouncementService(self.config)
        self.scheduler = TaskScheduler()

        # 次回の告知タイプ（デフォルトは通常開催）
        self.next_announcement_type = AnnouncementType.REGULAR

        self.logger.info("Botクライアントを初期化しました")

    @override
    async def setup_hook(self) -> None:
        """Botの起動前に呼び出されるセットアップフック。

        コグとエクステンションを読み込み、スケジュールタスクを設定する。
        """
        await self._load_extensions()
        await self._setup_scheduled_tasks()

        await self.tree.sync()

        self.logger.info("Botのセットアップが完了しました")

    async def _load_extensions(self) -> None:
        """コマンドコグを読み込む。"""
        from .commands import ConfigCog, LtCog, ManualCog, UtilityCog

        # コグを追加
        await self.add_cog(LtCog(self))
        await self.add_cog(ConfigCog(self))
        await self.add_cog(UtilityCog(self))
        await self.add_cog(ManualCog(self))

        self.logger.info("コマンド拡張を読み込みました")

    async def _setup_scheduled_tasks(self) -> None:
        """確認と告知のスケジュールタスクを設定する。"""
        # 確認タスクをスケジュール
        confirm_time = self.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_CONFIRM_TIME, "21:30"
        )
        confirm_weekday = self.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_CONFIRM_WEEKDAY, "Thu"
        )

        self.scheduler.schedule_daily_task(
            "confirmation", confirm_time, confirm_weekday, self.confirmation_task
        )

        # 告知タスクをスケジュール
        announce_time = self.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_TIME, "21:30"
        )
        announce_weekday = self.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_WEEKDAY, "Sun"
        )

        self.scheduler.schedule_daily_task(
            "announcement", announce_time, announce_weekday, self.announcement_task
        )

        self.logger.info("スケジュールタスクを設定しました")

    async def confirmation_task(self) -> None:
        """確認メッセージを送信するスケジュールタスク。"""
        # アクションチャンネルを取得
        action_channel_id = self.config.get(
            ConfigKeys.SECTION_CHANNELS, ConfigKeys.KEY_ACTION_CHANNEL_ID, ""
        )
        if not action_channel_id:
            self.logger.error(
                "確認メッセージを送信できません: アクションチャンネルが設定されていません"
            )
            return

        action_channel = self.get_channel(int(action_channel_id))
        if not action_channel:
            self.logger.error(
                f"確認メッセージを送信できません: チャンネル {action_channel_id} が見つかりません"
            )
            return
        if not isinstance(action_channel, discord.TextChannel):
            self.logger.error(
                f"確認メッセージを送信できません: チャンネル {action_channel_id} はテキストチャネルではありません。"
            )
            return

        # アクションロールを取得
        action_role_name = self.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ACTION_ROLE, ""
        )
        action_role = None

        if action_role_name:
            # @が含まれている場合は削除
            clean_role_name = action_role_name.lstrip("@")

            guild = action_channel.guild
            action_role = discord.utils.get(guild.roles, name=clean_role_name)

            if not action_role:
                self.logger.warning(
                    f"ロール {clean_role_name} がギルドに見つかりません"
                )

        # 確認メッセージを送信
        await self.announcement_service.send_confirmation(action_channel, action_role)

    async def announcement_task(self) -> None:
        """告知メッセージを送信するスケジュールタスク。"""
        # 告知チャンネルを取得
        announce_channel_id = self.config.get(
            ConfigKeys.SECTION_CHANNELS, ConfigKeys.KEY_ANNOUNCE_CHANNEL_ID, ""
        )
        if not announce_channel_id:
            self.logger.error(
                "告知を送信できません: 告知チャンネルが設定されていません"
            )
            return

        announce_channel = self.get_channel(int(announce_channel_id))
        if not announce_channel:
            self.logger.error(
                f"告知を送信できません: チャンネル {announce_channel_id} が見つかりません"
            )
            return
        if not isinstance(announce_channel, discord.TextChannel):
            self.logger.error(
                f"告知を送信できません: チャンネル {announce_channel_id} はテキストチャネルではありません。"
            )
            return

        # 告知メッセージを送信
        await self.announcement_service.send_announcement(
            announce_channel, self.next_announcement_type
        )

        # 次回のデフォルトを通常開催にリセット
        self.next_announcement_type = AnnouncementType.REGULAR

    async def on_ready(self) -> None:
        """Botの準備完了時に呼び出されるイベントハンドラ。"""
        self.logger.info(f"Botの準備が完了しました! ログイン: {self.user}")

        # 接続先ギルドを記録
        guild_names = [guild.name for guild in self.guilds]
        self.logger.info(
            f"{len(guild_names)}個のギルドに接続しています: {', '.join(guild_names)}"
        )

    async def on_reaction_add(
        self, reaction: discord.Reaction, user: discord.User | discord.Member
    ) -> None:
        """リアクション追加時に呼び出されるイベントハンドラ。

        Args:
            reaction: 追加されたリアクション
            user: リアクションを追加したユーザー
        """
        # Botの自身のリアクションは無視
        if self.user is None:
            return
        if user.id == self.user.id:
            return

        # Botからの確認メッセージへのリアクションかチェック
        if (
            reaction.message.author.id == self.user.id
            and "の予定を確認します。" in reaction.message.content
        ):
            # リアクションの種類をチェック
            if str(reaction.emoji) == ReactionEmoji.REGULAR:
                self.next_announcement_type = AnnouncementType.REGULAR
                self.logger.info(f"ユーザー {user} が通常開催を選択しました")

            elif str(reaction.emoji) == ReactionEmoji.LIGHTNING_TALK:
                self.next_announcement_type = AnnouncementType.LIGHTNING_TALK
                self.logger.info(f"ユーザー {user} がLT開催を選択しました")

                # LT情報が完全かチェック
                if not self.announcement_service.lt_info.is_complete:
                    self.logger.warning("LTが選択されましたが、情報が不完全です")

                    # 同じチャンネルで通知を試みる
                    try:
                        await reaction.message.channel.send(
                            f"{user.mention} LTが選択されましたが、情報が不完全です。"
                            "/announce-bot lt コマンドで発表者、タイトル、URLを設定してください。",
                            delete_after=60,
                        )
                    except discord.DiscordException:
                        self.logger.error("LT情報不足の警告送信に失敗しました")

            elif str(reaction.emoji) == ReactionEmoji.REST:
                self.next_announcement_type = AnnouncementType.REST
                self.logger.info(f"ユーザー {user} がおやすみを選択しました")
