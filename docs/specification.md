# Discord 告知Bot 仕様書

## 概要

Discordの特定のチャンネルに定期的に告知メッセージを投稿するボットを実装する。

## 機能要件

### 告知の種類

1. **通常開催**

   - テンプレート:
     ```
     今週のmm/ddのML集会も21時半より開催致します。今週はまったり雑談会です
     <URL>
     ```

2. **LT (Lightning Talk)**

   - テンプレート:
     ```
     今週のML集会はLT会! mm/ddの21時半より開催致します。
     <name>さんより「<title>」を行いますので、ぜひみなさんお越しください！
     <URL>
     ```

3. **おやすみ告知**

   - テンプレート:
     ```
     今週のML集会はおやすみです。
     ```

### 主要機能

1. **スケジュール実行**

   - 指定された曜日に:
     - アクションチャンネルで特定のユーザー/ロールにメンション
     - リアクションで次回イベントの種類を確認
     - リアクション選択肢:
       - 👍: 通常開催
       - ⚡: LT開催
       - 💤: おやすみ
     - リアクションがない場合は通常開催として扱う

2. **告知投稿**

   - 告知チャンネル（アクションチャンネルとは別）に告知を投稿
   - 指定された曜日
   - 指定された日時
   - 指定されたチャネル

3. **LT情報管理**

   - サブコマンドグループ: `/announce-bot lt`
     - `/announce-bot lt speaker [name:string]`: 発表者名を設定/取得
     - `/announce-bot lt title [title:string]`: 発表タイトルを設定/取得
     - `/announce-bot lt url [url:string]`: イベントURLを設定/取得
     - `/announce-bot lt info`: 現在設定されているLT情報をすべて表示
     - `/announce-bot lt clear`: LT情報をクリア
   - 値が指定されない場合はgetterとして動作
   - 情報は告知実行まで保持
   - 告知後に情報を自動的にクリア

4. **設定管理**

   - サブコマンドグループ: `/announce-bot config`
     - 時間設定 `/announce-bot config time`
       - `/announce-bot config time confirm [time:string]`: 確認時刻を設定/取得 (HH:MM形式)
       - `/announce-bot config time announce [time:string]`: 告知時刻を設定/取得 (HH:MM形式)
     - 曜日設定 `/announce-bot config weekday`
       - `/announce-bot config weekday confirm [day:string]`: 確認曜日を設定/取得
       - `/announce-bot config weekday announce [day:string]`: 告知曜日を設定/取得
     - `/announce-bot config role [role:role]`: アクションロールを設定/取得
     - チャンネル設定 `/announce-bot config channel`
       - `/announce-bot config channel action [channel:channel]`: アクションチャンネルを設定/取得
       - `/announce-bot config channel announce [channel:channel]`: 告知チャンネルを設定/取得
     - `/announce-bot config show`: 現在の全設定を表示
     - `/announce-bot config reset`: 設定をデフォルト値にリセット
   - 値が指定されない場合はgetterとして動作
   - 設定変更時は `config-overrides.toml` に差分のみを保存

5. **便利な追加機能**

   - `/announce-bot status`: 次回の確認イベントと告知イベントの日時、および現在のLT情報を表示
   - `/announce-bot help [command:string]`: コマンドヘルプを表示
   - `/announce-bot test`: テスト用サブコマンドグループ
     - `/announce-bot test announce`: 告知メッセージのプレビューを表示（実際には投稿しない）
     - `/announce-bot test confirm`: 確認メッセージのプレビューを表示（実際には投稿しない）
   - `/announce-bot manual`: 手動トリガーサブコマンドグループ
     - `/announce-bot manual confirm`: 手動で確認メッセージを送信
     - `/announce-bot manual announce`: 手動で告知メッセージを送信

### 権限管理

- コマンド実行権限:
  - `/announce-bot config` サブコマンドは「管理者」または「モデレーター」ロールを持つユーザーのみ実行可能
  - `/announce-bot lt` サブコマンドは「LT管理者」または「モデレーター」ロールを持つユーザーのみ実行可能
  - `/announce-bot manual` は「管理者」または「モデレーター」ロールを持つユーザーのみ実行可能
  - 権限エラーは一貫したメッセージで通知

## 技術要件

### 開発要件

- Python 3.12以上
- 型アノテーション必須（typing.List/Tupleではなくビルトインのlist/tupleを使用）
- 公開クラス・メソッドにはdocstring必須
- ドキュメントはGoogle Style、英語で記述
- docstringには型情報不要
- コンストラクタのdocstringはメソッドの後に記述
- 可読性とシンプルさを重視
- 構造化されたプログラム設計
- プロジェクトマネージャに `astral-uv`を使用

### テスト要件

- pytest、pytest-mockを使用
- コア機能のテストを実装
- Discord APIはモック化
- E2Eテストは不要
- コマンドパースとバリデーションのテストを実装

### エラー処理

- 不正な入力に対してはエラーメッセージを返す
- Discord API通信エラーは3回リトライ後に終了
- 全てのエラーを適切にログ出力
- スラッシュコマンドのエラーは ephemeral（一時的）メッセージで応答

### デプロイメント

- 環境: Dockerコンテナ（Ubuntu 24.04）, 開発時は devcontainerを用いる。deploy時はdocker composeでセットアップ
- リソース使用は最小限に
- ログ:
  - ディレクトリをバインドマウント
  - rotating file handlerを使用
- Dockerヘルスチェック必須

### データ永続化

- **設定管理**:

  - `config.toml` - デフォルトの設定値を含む読み取り専用ファイル
  - `config-overrides.toml` - ユーザーが変更した設定値のみを保存するファイル
  - 設定読み込み時は両方のファイルを読み込み、overridesで上書き
  - デフォルト値に戻した設定項目はoverridesファイルから削除

- **実行時データ**:

  - LT情報などの一時的なデータはメモリ内で管理
  - 再起動時にはリセット

- **Discord Token**:

  - 環境変数またはファイルで管理
  - `.env` ファイルを使用

### セキュリティ

- ボットコマンドは特定のチャンネルに制限
- 設定コマンドは制限されたチャンネルで実行
- Discord Tokenは.envファイルで管理
- 全ての設定変更は権限チェック後に実行

## 実装詳細

### 必要な依存関係

- discord.py
- pytest（テスト用）
- pytest-mock（テスト用）
- tomllib（Python 3.11以上はビルトイン）
- tomli-w (toml書き込み用)

### コマンド実装パターン

```python
from discord import app_commands
from discord.ext import commands

class AnnounceBotCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # LTグループ
    lt_group = app_commands.Group(name="lt", description="LT関連の設定")

    @lt_group.command(name="speaker")
    @app_commands.describe(name="発表者の名前")
    async def lt_speaker(self, interaction, name: str | None = None):
        """発表者名を設定または取得します"""
        # 実装

    # エラーハンドリング例
    @lt_speaker.error
    async def lt_speaker_error(self, interaction: discord.Interaction, error: DiscordException):
        """LT speaker コマンドのエラーハンドラー"""
        if isinstance(error, app_commands.errors.MissingRole):
            await interaction.response.send_message("このコマンドを実行する権限がありません。", ephemeral=True)
        # その他のエラーハンドリング
```

### 自動補完機能

曜日選択などのパラメータに自動補完機能を実装：

```python
@config_weekday_confirm.autocomplete("day")
async def weekday_autocomplete(self, interaction: Discord.Interaction, current: str):
    weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return [app_commands.Choice(name=day, value=day)
            for day in weekdays if current.lower() in day.lower()]
```

### ログ出力

- rotating file handlerを使用
- ログレベル:
  - ERROR: 全てのエラーと例外
  - INFO: 設定変更、告知投稿
  - DEBUG: 詳細な動作ログ

```python
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logger():
    log_dir = os.getenv("LOG_DIR", "./logs")
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger("announce-bot")
    logger.setLevel(logging.DEBUG)

    # ファイルハンドラー
    file_handler = RotatingFileHandler(
        f"{log_dir}/announce-bot.log",
        maxBytes=5*1024*1024,  # 5MB
        backupCount=5
    )
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)

    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
```

### 環境変数

- DISCORD_TOKEN: ボット認証トークン
- LOG_DIR: ログファイルディレクトリ（Dockerバインドマウント用）
- ADMIN_ROLE: 管理者ロール名（省略可、デフォルトは `Administrator`）
- MODERATOR_ROLE: モデレーターロール名（省略可、デフォルトは `Moderator`）
- LT_ADMIN_ROLE: LT管理者ロール名（省略可、デフォルトは `LT管理者`）
- CONFIG_PATH: 設定ファイルのパス（省略可、デフォルトは `./config.toml`）
- CONFIG_OVERRIDES_PATH: 設定上書きファイルのパス（省略可、デフォルトは `./config-overrides.toml`）

### 設定ファイル構造

`config.toml` (デフォルト値):

```toml
# 基本設定
[settings]
announce_time = "21:30"
confirm_time = "21:30"
action_role = "@GesonAnko"
confirm_weekday = "Thu"
announce_weekday = "Sun"
default_url = "https://x.com/VRC_ML_hangout/status/1779863235988242925"

# チャンネル設定
[channels]
action_channel_id = ""
announce_channel_id = ""

# 権限設定
[permissions]
admin_roles = ["Administrator"]
moderator_roles = ["Moderator"]
lt_admin_roles = ["LT管理者"]

# メッセージテンプレート
[templates]
# 通常開催テンプレート
regular = "今週の$mm/$ddのML集会も21時半より開催致します。今週はまったり雑談会です\n$url"

# LT開催テンプレート
lightning_talk = "今週のML集会はLT会! $mm/$ddの21時半より開催致します。\n$speaker_nameさんより「$title」を行いますので、ぜひみなさんお越しください！\n$url"

# おやすみテンプレート
rest = "今週のML集会はおやすみです。"

# 確認メッセージテンプレート
confirmation = "$role 今度の日曜 ($month/$day) の予定を確認します。\n👍: 通常開催\n⚡: LT開催\n💤: おやすみ\nリアクションがない場合は通常開催として扱います。"
```

`config-overrides.toml` (例):

```toml
# ユーザーがカスタマイズした設定のみを含む
[channels]
action_channel_id = "1234567890123456789"
announce_channel_id = "9876543210987654321"

[settings]
announce_time = "20:00"
```
