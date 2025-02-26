# src/bot/config/config_manager.py
"""Botの設定管理を担当するモジュール。"""

import logging
import os
import tomllib
from typing import Any, override

import tomli_w

from ..constants import EnvKeys


class ConfigManager:
    """設定管理クラス。

    デフォルト設定とユーザーオーバーライド設定を管理し、設定の読み書きを行う。
    """

    def __init__(
        self, config_path: str | None = None, overrides_path: str | None = None
    ):
        """設定管理クラスを初期化する。

        Args:
            config_path: デフォルト設定ファイルのパス
            overrides_path: 設定オーバーライドファイルのパス
        """
        self.logger = logging.getLogger("announce-bot.config")

        # 設定ファイルパスを引数、環境変数、またはデフォルト値から取得
        self.config_path = config_path or os.getenv(
            EnvKeys.CONFIG_PATH, "./config.toml"
        )
        self.overrides_path = overrides_path or os.getenv(
            EnvKeys.CONFIG_OVERRIDES_PATH, "./config-overrides.toml"
        )

        self.config: dict[str, Any] = {}
        self.overrides: dict[str, Any] = {}

        # 設定を読み込む
        self._load_config()

    def _load_config(self) -> None:
        """デフォルト設定とオーバーライド設定を読み込む。"""
        try:
            # デフォルト設定を読み込む
            with open(self.config_path, "rb") as f:
                self.config = tomllib.load(f)
            self.logger.info(f"デフォルト設定を読み込みました: {self.config_path}")

            # オーバーライド設定が存在する場合は読み込む
            if os.path.exists(self.overrides_path):
                with open(self.overrides_path, "rb") as f:
                    self.overrides = tomllib.load(f)
                self.logger.info(
                    f"オーバーライド設定を読み込みました: {self.overrides_path}"
                )
        except (FileNotFoundError, tomllib.TOMLDecodeError) as e:
            self.logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
            raise

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """設定値を取得する。オーバーライド設定を優先する。

        Args:
            section: 設定セクション
            key: 設定キー
            default: 設定が見つからない場合のデフォルト値

        Returns:
            設定値
        """
        # オーバーライド設定を優先
        if section in self.overrides and key in self.overrides[section]:
            return self.overrides[section][key]

        # デフォルト設定を次に確認
        if section in self.config and key in self.config[section]:
            return self.config[section][key]

        # 見つからない場合はデフォルト値を返す
        return default

    def set(self, section: str, key: str, value: Any) -> None:
        """設定値を設定する。オーバーライド設定に書き込む。

        Args:
            section: 設定セクション
            key: 設定キー
            value: 設定値
        """
        # セクションが存在しない場合は作成
        if section not in self.overrides:
            self.overrides[section] = {}

        # デフォルト値を確認
        default_value = None
        if section in self.config and key in self.config[section]:
            default_value = self.config[section][key]

        if value == default_value:
            # デフォルト値と同じ場合はオーバーライドを削除
            if key in self.overrides[section]:
                del self.overrides[section][key]
                # 空のセクションを削除
                if not self.overrides[section]:
                    del self.overrides[section]
        else:
            # オーバーライド値を設定
            self.overrides[section][key] = value

        # オーバーライドを保存
        self._save_overrides()
        self.logger.info(f"設定を更新しました: {section}.{key} = {value}")

    def _save_overrides(self) -> None:
        """オーバーライド設定をファイルに保存する。"""
        try:
            # ディレクトリが存在しない場合は作成
            parent_dir = os.path.dirname(self.overrides_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)

            # オーバーライドをファイルに書き込む
            with open(self.overrides_path, "wb") as f:
                tomli_w.dump(self.overrides, f)
            self.logger.debug(
                f"オーバーライド設定を保存しました: {self.overrides_path}"
            )
        except Exception as e:
            self.logger.error(f"オーバーライド設定の保存に失敗しました: {e}")
            raise

    def reset(self) -> None:
        """全ての設定をデフォルト値にリセットする。"""
        self.overrides = {}

        # オーバーライドファイルが存在する場合は削除
        if os.path.exists(self.overrides_path):
            try:
                os.remove(self.overrides_path)
                self.logger.info(
                    f"オーバーライド設定ファイルを削除しました: {self.overrides_path}"
                )
            except OSError as e:
                self.logger.error(
                    f"オーバーライド設定ファイルの削除に失敗しました: {e}"
                )
                raise

        self.logger.info("全ての設定をデフォルト値にリセットしました")

    @override
    def __str__(self) -> str:
        """現在の設定（オーバーライド適用済み）の文字列表現を返す。"""
        result: dict[str, Any] = {}
        for section in self.config:
            result[section] = {}
            for key, value in self.config[section].items():
                result[section][key] = value

        # オーバーライドを適用
        for section in self.overrides:
            if section not in result:
                result[section] = {}
            for key, value in self.overrides[section].items():
                result[section][key] = value

        return str(result)
