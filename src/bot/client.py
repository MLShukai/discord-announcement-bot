# src/bot/client.py
"""Discord Botのメインクライアントモジュール。"""

import logging
import os
from typing import override

import discord
from discord.ext import commands

from .announcement import AnnouncementService
from .clock import SystemClock
from .config import ConfigManager
from .constants import (
    REACTION_TO_TYPE,
    AnnouncementType,
    ConfigKeys,
    EnvKeys,
    Weekday,
)
from .scheduler import TaskScheduler
from .state import StateStore

ANNOUNCE_TASK_ID = "weekly-announce"


class AnnounceBotClient(commands.Bot):
    """告知Bot用のDiscordクライアント。

    イベント処理、スケジュールタスク、コマンド登録などを担当する composition root。
    """

    def __init__(self):
        """Botクライアントを初期化する。"""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.reactions = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )

        self.logger = logging.getLogger("announce-bot.client")

        # コンポーネントを初期化 (composition root)
        self.clock = SystemClock()
        self.config = ConfigManager()
        self.state = StateStore(os.getenv(EnvKeys.STATE_PATH, "./data/state.json"))
        self.announcement_service = AnnouncementService(
            self.config, self.state, self.clock
        )
        self.scheduler = TaskScheduler(self.clock)

        self.logger.info("Botクライアントを初期化しました")

    @override
    async def setup_hook(self) -> None:
        """Botの起動前に呼ばれるセットアップフック。"""
        from .commands import ConfigCog, LtCog, SessionCog, UtilityCog

        await self.add_cog(LtCog(self))
        await self.add_cog(ConfigCog(self))
        await self.add_cog(UtilityCog(self))
        await self.add_cog(SessionCog(self))
        self.logger.info("コマンド拡張を読み込みました")

        self.schedule_announce_task()
        await self.tree.sync()
        self.logger.info("Botのセットアップが完了しました")

    def schedule_announce_task(self) -> None:
        """初回告知の週次スケジュールタスクを (再)登録する。"""
        weekday = self.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_WEEKDAY, Weekday.SUNDAY
        )
        time_str = self.config.get(
            ConfigKeys.SECTION_SETTINGS, ConfigKeys.KEY_ANNOUNCE_TIME, "12:00"
        )
        self.scheduler.schedule_weekly_task(
            ANNOUNCE_TASK_ID, weekday, time_str, self.run_weekly_announce
        )

    def get_announce_channel(self) -> discord.TextChannel | None:
        """設定された告知チャンネルを取得する。

        Returns:
            告知チャンネル。未設定・不正な場合は None
        """
        channel_id = self.config.get(
            ConfigKeys.SECTION_CHANNELS, ConfigKeys.KEY_ANNOUNCE_CHANNEL_ID, ""
        )
        if not channel_id:
            return None
        channel = self.get_channel(int(channel_id))
        return channel if isinstance(channel, discord.TextChannel) else None

    async def run_weekly_announce(self) -> None:
        """初回告知を送信する（スケジュール／手動共通）。

        新しい開催週に入った場合は種別を通常開催へリセットし、LT情報をクリアする。
        """
        channel = self.get_announce_channel()
        if channel is None:
            self.logger.error("初回告知を送信できません: 告知チャンネルが未設定です")
            return

        # 新しい週なら今週の予定をリセット
        event_date = self.announcement_service.next_event_date()
        if self.state.state.target_event_date != event_date:
            self.state.state.session_type = AnnouncementType.REGULAR
            self.state.state.lt.clear()
            self.state.state.target_event_date = event_date
            self.state.save()
            self.logger.info(f"新しい開催週({event_date})の予定を初期化しました")

        await self.announcement_service.send_announce(channel)

    async def on_ready(self) -> None:
        """Botの準備完了時に呼ばれるイベントハンドラ。"""
        self.logger.info(f"Botの準備が完了しました! ログイン: {self.user}")
        guild_names = [guild.name for guild in self.guilds]
        self.logger.info(
            f"{len(guild_names)}個のギルドに接続しています: {', '.join(guild_names)}"
        )

    def _has_moderator_role(self, member: discord.Member) -> bool:
        """メンバーが種別変更権限 (admin/moderator) を持つか判定する。

        Args:
            member: 判定対象のメンバー

        Returns:
            権限がある場合は True
        """
        admin_roles = self.config.get(
            ConfigKeys.SECTION_PERMISSIONS, ConfigKeys.KEY_ADMIN_ROLES, []
        )
        moderator_roles = self.config.get(
            ConfigKeys.SECTION_PERMISSIONS, ConfigKeys.KEY_MODERATOR_ROLES, []
        )
        allowed = set(admin_roles) | set(moderator_roles)
        return any(role.name in allowed for role in member.roles)

    async def on_raw_reaction_add(
        self, payload: discord.RawReactionActionEvent
    ) -> None:
        """初回告知メッセージへのリアクションで今週の種別を更新する。

        メッセージIDを永続化しているため、再起動後のメッセージにも追従できる。

        Args:
            payload: 生のリアクション追加イベント
        """
        # 自身のリアクション・対象外メッセージは無視
        if self.user is not None and payload.user_id == self.user.id:
            return
        if payload.message_id != self.state.state.announce_message_id:
            return

        announcement_type = REACTION_TO_TYPE.get(str(payload.emoji))
        if announcement_type is None:
            return

        # 権限ガード (mod/admin のみ種別変更を許可)
        member = payload.member
        if not isinstance(member, discord.Member) or not self._has_moderator_role(
            member
        ):
            return

        self.state.state.session_type = announcement_type
        self.state.save()
        self.logger.info(
            f"ユーザー {member} が種別を {announcement_type} に変更しました"
        )

        # LT選択時に情報が不完全なら警告
        if (
            announcement_type == AnnouncementType.LIGHTNING_TALK
            and not self.state.state.lt.is_complete
        ):
            channel = self.get_channel(payload.channel_id)
            if isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(
                        f"{member.mention} LTが選択されましたが、情報が不完全です。"
                        "`/lt set` で発表者・タイトル・URLを設定してください。",
                        delete_after=60,
                    )
                except discord.DiscordException:
                    self.logger.error("LT情報不足の警告送信に失敗しました")
