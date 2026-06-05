# Discord 告知Bot

定期イベント (ML集会) の告知を Discord に投稿するボット。

## 運用フロー

ML集会は **水曜 21:30** 開催。ボットは次のサイクルで動く:

1. **日曜 12:00（自動）** — 告知チャンネルへ「今週の予定（初回告知）」を投稿。
   `👍 通常 / ⚡ LT / 🛠️ 作業部屋 / 💤 おやすみ` のリアクションが付く。
2. **日曜〜水曜** — モデレーターがリアクション、または `/plan set <種別>` で今週の種別を変更。
   LT 開催なら `/lt set <タイトル> <発表者> [URL]` で内容を設定。
3. **水曜の開催時（手動）** — インスタンスを開けたら `/open` を実行し、開催告知を投稿。
   種別ごとに文面が変わる（LT は発表者・タイトル入り）。おやすみの週は送信されない。

初回告知の曜日・時刻、開催の曜日・時刻はすべて `/config` で変更できる。

## コマンド

| コマンド                               | 説明                                                      |
| -------------------------------------- | --------------------------------------------------------- |
| `/plan show` / `/plan set <種別>`      | 今週の種別を表示 / 変更 (regular, lt, workspace, rest)    |
| `/open`                                | 開催告知を送信 (おやすみの週は送信しない)                 |
| `/lt set <title> <speaker> [url]`      | LT情報を一括設定 (個別は `/lt speaker` / `title` / `url`) |
| `/lt info` / `/lt clear`               | LT情報の表示 / クリア                                     |
| `/config announce <day> <time>`        | 初回告知の曜日・時刻                                      |
| `/config event <day> <time>`           | 開催の曜日・時刻                                          |
| `/config role [role]`                  | アクションロール                                          |
| `/config channel announce [channel]`   | 告知チャンネル                                            |
| `/config show` / `/config reset`       | 全設定の表示 / リセット                                   |
| `/status`                              | 次回予定と今週の種別を表示                                |
| `/manual announce`                     | 初回告知を手動送信                                        |
| `/test announce` / `/test open [type]` | メッセージのプレビュー                                    |
| `/help`                                | ヘルプ                                                    |

権限はロール名ベース（`config.toml` の `[permissions]`）。`/config`・`/open`・`/plan set`・`/manual` は admin/moderator、`/lt` の編集は admin/moderator/lt_admin。

## ローカル開発

ツーリングは [uv](https://docs.astral.sh/uv/)。

```bash
# セットアップ
uv venv --clear && uv run pre-commit install

# 開発チェック (format → test → type[pyright strict])
make run

# ボット起動 (.env に DISCORD_TOKEN が必要)
uv run python src/main.py
```

`.env` は `.env.example` をコピーして作成する。

## Docker デプロイ

```bash
# 起動 (ビルド込み)
docker compose up -d --build

# ログ確認
docker compose logs -f

# 停止
docker compose down
```

### 再起動

```bash
docker compose restart
```

設定変更（`/config` など）と実行時状態（今週の種別・LT情報）は、コンテナ内
`/app/data`（`config-overrides.toml` と `state.json`）に保存される。これは
`docker-compose.yaml` の named volume `bot-data` に永続化されるため、
**再起動・再ビルドをまたいで保持される**。中身を確認するには:

```bash
docker compose exec discord-bot cat /app/data/state.json
```

（ローカル実行時は同じ内容がリポジトリ直下の `./data/` に保存される。）

### 自動起動

`docker-compose.yaml` は `restart: unless-stopped` を指定済み。Docker デーモンが
起動していれば、ホスト再起動後やクラッシュ後もコンテナが自動復帰する。
ホスト起動時に Docker を自動起動するには:

```bash
sudo systemctl enable docker
```

`docker compose` 自体を systemd で管理したい場合の unit 例:

```ini
# /etc/systemd/system/discord-announcement-bot.service
[Unit]
Description=Discord Announcement Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/discord-announcement-bot
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now discord-announcement-bot
```

## ドキュメント

詳細な仕様は [docs/specification.md](docs/specification.md) を参照。
