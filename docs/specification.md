# Discord 告知Bot 仕様書

## 概要

定期イベント (ML集会) の告知を Discord に投稿するボット。ML集会は **水曜 21:30** 開催。
ボットは日曜に「今週の予定（初回告知）」を自動投稿し、開催日までにモデレーターが種別を
決定・変更、開催時に手動 `/open` で開催告知を投稿する。

コードベース・コメント・docstring・Discord 向け文字列はすべて日本語。

## 機能要件

### 開催種別 (`AnnouncementType`)

| 種別         | 列挙子           | リアクション | 説明                         |
| ------------ | ---------------- | ------------ | ---------------------------- |
| 通常開催     | `REGULAR`        | 👍           | まったり雑談会               |
| LT開催       | `LIGHTNING_TALK` | ⚡           | 発表者・タイトル・URL を伴う |
| 作業部屋開催 | `WORKSPACE`      | 🛠️           | もくもく作業会（固定文面）   |
| おやすみ     | `REST`           | 💤           | 休会（開催告知なし）         |

リアクションが付かない場合は通常開催として扱う。

### スケジュールとフロー

1. **初回告知（日曜 12:00・自動）** — 告知チャンネルへ「今週の予定」を投稿する。
   - 種別ごとのテンプレートで本文を生成し、末尾にリアクション凡例を付与する。
   - 👍 ⚡ 🛠️ 💤 の 4 リアクションを付与する。
   - 投稿メッセージIDを状態に保存する（再起動後もリアクション追従するため）。
   - **新しい開催週**に入った場合は、投稿前に種別を通常開催へリセットし LT情報をクリアする。
2. **種別の変更（日曜〜開催日）** — 次のいずれかで今週の種別を変更できる。
   - 初回告知メッセージへの**リアクション**（admin/moderator ロールのみ有効、それ以外は無視）。
   - スラッシュコマンド `/plan set <種別>`。
3. **開催告知（開催時・手動 `/open`）** — 告知チャンネルへ開催告知を投稿する。
   - 種別ごとのテンプレートで本文を生成（LT は発表者・タイトルを埋め込む）。
   - おやすみ（REST）の週は送信せず、ephemeral で警告する。
   - LT で情報が不完全な場合は送信せず警告する。

初回告知の曜日・時刻（`announce_weekday`/`announce_time`）と開催の曜日・時刻
（`event_weekday`/`event_time`）はすべて設定で変更可能。

### コマンド

すべてトップレベルの `app_commands.Group` または単独コマンド。権限エラー・実行エラーは
`ephemeral=True` で応答する。

- **`/plan`** — 今週の予定の管理
  - `/plan show`: 今週の種別と LT情報を表示（誰でも）
  - `/plan set <type>`: 種別を設定（admin/moderator、autocomplete: regular/lt/workspace/rest）
- **`/open`** — 開催告知を手動送信（admin/moderator、REST は警告のみ）
- **`/manual announce`** — 初回告知を手動送信（admin/moderator、スケジュールと同一処理）
- **`/lt`** — LT情報管理（get 系は誰でも、set 系は admin/moderator/lt_admin）
  - `/lt speaker|title|url [値]`、`/lt set <title> <speaker> [url]`、`/lt info`、`/lt clear`
- **`/config`** — 設定管理（admin/moderator）
  - `/config announce <day> <time>`、`/config event <day> <time>`
  - `/config role [role]`、`/config channel announce [channel]`
  - `/config show`、`/config reset`
- **`/status`** — 次回初回告知・次回開催日・今週の種別・LT情報を表示（誰でも）
- **`/help`** — コマンドヘルプを表示（誰でも）
- **`/test`** — プレビュー（admin/moderator、実際には投稿しない）
  - `/test announce [type]`、`/test open [type]`

値を指定しない `/lt`・`/config` の取得系は getter として動作する。

### 権限管理

ロール名ベースで config の `[permissions]` セクション（`admin_roles` / `moderator_roles` /
`lt_admin_roles`）から解決する。

- `/config`・`/open`・`/plan set`・`/manual`・`/test`: admin または moderator
- `/lt` の編集系: admin / moderator / lt_admin
- `/plan show`・`/status`・`/help`・`/lt` の取得系: 誰でも
- 初回告知へのリアクションによる種別変更: admin または moderator（他は無視）

## 技術要件

### 開発要件

- Python 3.12 以上、`src/` は pyright **strict**
- 型注釈はビルトイン generics（`list`/`tuple`）。public なクラス/メソッドに Google-style docstring（英語、型情報なし）
- override メソッドは `@typing.override`
- スタイル: `ruff`（line-length 88, double quotes, isort combine-as-imports）
- ツーリングは `astral-uv`（`uv run` 前置）

### テスト要件

- pytest / pytest-asyncio / pytest-mock。Discord API はモック化、E2E は無い
- **時刻ソースは `Clock` を注入して決定化**（`datetime` の直接 patch に依存しない）
- `tests/` は `src/bot/` を 1:1 ミラー。`--doctest-modules` 有効

### エラー処理

- 不正入力は ephemeral でエラー応答。Discord 送信失敗はログ出力し None を返す
- すべてのエラーをログ出力。スラッシュコマンドのエラーは ephemeral 応答

### データ永続化

- **設定**: `config.toml`（読み取り専用デフォルト）＋ `config-overrides.toml`（差分のみ）。
  読み込みは override→default の順。デフォルトに戻した項目は override から削除。
- **実行時状態** (`state.json`): 今週の種別・LT情報・初回告知メッセージID・対象開催日を
  JSON で永続化。`StateStore` が変更のたびに保存。再起動で復元。
- **集約と永続化**: `config-overrides.toml` と `state.json` は `data/` 配下に置き、
  docker-compose で `./data:/app/data` を bind-mount して再起動・再ビルドをまたいで保持する。
- **Discord Token**: `.env`（環境変数）で管理。

### デプロイメント

- Docker (`python:3.12-slim`、`TZ=Asia/Tokyo`、非 root `botuser`、`pgrep` healthcheck)
- `restart: unless-stopped` でホスト/デーモン再起動後に自動復帰
- ログは `LOG_DIR` 配下の rotating file handler（バインドマウント）
- 開発は `.devcontainer/`

### 環境変数

- `DISCORD_TOKEN`（必須）
- `LOG_DIR`（既定 `./logs`）
- `CONFIG_PATH`（既定 `./config.toml`）
- `CONFIG_OVERRIDES_PATH`（既定 `./config-overrides.toml`、Docker では `/app/data/...`）
- `STATE_PATH`（既定 `./data/state.json`）

## アーキテクチャ

- **エントリポイント** (`src/main.py`): `.env` ロード、ロガー設定、SIGTERM/SIGINT による
  graceful shutdown、`AnnounceBotClient` 起動。
- **`AnnounceBotClient`** (`src/bot/client.py`): composition root。`Clock` / `ConfigManager` /
  `StateStore` / `AnnouncementService` / `TaskScheduler` を保持。`setup_hook` で 4 cog をロードし
  初回告知タスクを 1 本登録、コマンドツリーを sync。`on_raw_reaction_add` で初回告知メッセージ
  （保存済みID一致）へのリアクションを判定し、権限ガード後に種別を更新・永続化する。
- **`Clock`** (`src/bot/clock.py`): `now()`/`today()` を提供するプロトコルと `SystemClock`。
  scheduler / service に注入し、テストで時刻を決定化する。
- **`ConfigManager`** (`src/bot/config/`): 二層 TOML config。`get` は override→default、
  `set` はデフォルト一致時に override キーを削除して最小化。
- **`StateStore`** (`src/bot/state/`): `SessionState`（種別・`LTInfo`・メッセージID・対象開催日）
  を JSON で load/save。
- **`AnnouncementService`** (`src/bot/announcement/`): `Clock`・config・state を注入。
  `next_event_date()` / `build_announce(type)` / `build_open(type)->str|None`（REST は None）/
  `send_announce(channel)` / `send_open(channel)`。`string.Template` で文面を展開する。
- **`TaskScheduler`** (`src/bot/scheduler/`): pure-asyncio。次回実行時刻の計算は純粋関数
  `compute_next_run(now, weekday, hour, minute)` に分離（ユニットテスト可能）。`Clock` 注入。
- **Cog** (`src/bot/commands/`): `SessionCog`（/plan, /open, /manual）/ `LtCog`（/lt）/
  `ConfigCog`（/config）/ `UtilityCog`（/status, /help, /test）。権限判定は
  `commands/permissions.py` の `is_admin` / `is_lt_admin` に集約。

### 定数 (`src/bot/constants.py`)

config キー・環境変数・曜日変換・リアクション絵文字・開催種別を集約する。

- `ReactionEmoji`: `REGULAR`(👍) / `LIGHTNING_TALK`(⚡) / `WORKSPACE`(🛠️) / `REST`(💤)
- `AnnouncementType`: `REGULAR` / `LIGHTNING_TALK` / `WORKSPACE` / `REST`（`__str__` で日本語）
- `REACTION_TO_TYPE`（絵文字→種別）、`TYPE_BY_SLUG` / `SLUG_BY_TYPE`（スラッグ↔種別）
- `Weekday`、`EnvKeys`、`ConfigKeys`（テンプレートキーは `ANNOUNCE_TEMPLATE_KEYS` /
  `OPEN_TEMPLATE_KEYS` の 2 系統）

### 設定ファイル構造

`config.toml`（デフォルト値、抜粋）:

```toml
[settings]
announce_weekday = "Sun"   # 初回告知の曜日
announce_time = "12:00"    # 初回告知の時刻
event_weekday = "Wed"      # 開催曜日 (日付計算・文面表示)
event_time = "21:30"       # 開催時刻 (文面表示)
action_role = "告知管理者"
default_url = "https://x.com/VRC_ML_hangout/status/1779863235988242925"

[channels]
announce_channel_id = ""

[permissions]
admin_roles = ["Administrator", "告知管理者"]
moderator_roles = ["Moderator", "告知管理者"]
lt_admin_roles = ["LT管理者", "告知管理者"]

[templates]
# 変数: $month $day $weekday $time $url (LTは加えて $speaker_name $title)
announce_regular = "今週のML集会は $month/$day($weekday) $time から、まったり雑談会です！\n$url"
announce_lightning_talk = "今週のML集会は $month/$day($weekday) $time からLT会！\n$speaker_name さんより「$title」を行います。ぜひお越しください！\n$url"
announce_workspace = "今週のML集会は $month/$day($weekday) $time から作業会です！みなさんぜひご自由にご参加ください〜\n$url"
announce_rest = "今週のML集会はおやすみです。"
open_regular = "ML集会のインスタンスを開けました！まったりやっていきましょう〜\n$url"
open_lightning_talk = "ML集会(LT会)を開始します！\n$speaker_name さんより「$title」\nぜひお越しください！\n$url"
open_workspace = "作業会のインスタンスを開けました！ご自由にご参加ください〜\n$url"
```

`state.json`（実行時状態、例）:

```json
{
  "session_type": "LIGHTNING_TALK",
  "lt": {"speaker_name": "山田", "title": "強化学習入門", "url": "https://..."},
  "announce_message_id": 1234567890123456789,
  "target_event_date": "2026-06-10"
}
```
