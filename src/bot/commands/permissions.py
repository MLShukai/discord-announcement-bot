# src/bot/commands/permissions.py
"""コマンドの権限判定を共通化するモジュール。"""

import discord

from ..config import ConfigManager
from ..constants import ConfigKeys


def _has_any_role(
    interaction: discord.Interaction, config: ConfigManager, *role_keys: str
) -> bool:
    """インタラクションのユーザーが指定キーのいずれかのロールを持つか判定する。

    Args:
        interaction: コマンドインタラクション
        config: 設定マネージャー
        role_keys: `[permissions]` セクションのロールキー（可変長）

    Returns:
        いずれかの許可ロールを持つ場合は True
    """
    if not isinstance(interaction.user, discord.Member):
        return False

    allowed: set[str] = set()
    for key in role_keys:
        allowed.update(config.get(ConfigKeys.SECTION_PERMISSIONS, key, []))
    return any(role.name in allowed for role in interaction.user.roles)


def is_admin(interaction: discord.Interaction, config: ConfigManager) -> bool:
    """設定・手動操作を行える権限 (admin / moderator) を持つか判定する。

    Args:
        interaction: コマンドインタラクション
        config: 設定マネージャー

    Returns:
        権限がある場合は True
    """
    return _has_any_role(
        interaction,
        config,
        ConfigKeys.KEY_ADMIN_ROLES,
        ConfigKeys.KEY_MODERATOR_ROLES,
    )


def is_lt_admin(interaction: discord.Interaction, config: ConfigManager) -> bool:
    """LT情報を編集できる権限 (admin / moderator / lt_admin) を持つか判定する。

    Args:
        interaction: コマンドインタラクション
        config: 設定マネージャー

    Returns:
        権限がある場合は True
    """
    return _has_any_role(
        interaction,
        config,
        ConfigKeys.KEY_ADMIN_ROLES,
        ConfigKeys.KEY_MODERATOR_ROLES,
        ConfigKeys.KEY_LT_ADMIN_ROLES,
    )
