# CLAUDE.md

このファイルは Claude Code (claude.ai/code) がこのリポジトリを扱う際のガイダンスを提供する。

## プロジェクト概要

定期イベントの告知 (ML集会 / "ML meetup") を Discord に投稿するボット。スケジュールされた曜日に「アクション」チャンネルへ 3 つのリアクション付きの**確認 (confirmation)** メッセージを投稿し、モデレーターのリアクションで次回のイベント種別が決まる。後日のスケジュール曜日に、選ばれた**告知 (announcement)** を別の「告知 (announce)」チャンネルへ投稿する。リアクション: 👍 通常開催 / ⚡ LT開催 / 💤 おやすみ。リアクションが無ければ通常開催。

コードベース・コメント・docstring・Discord 向け文字列はすべて**日本語**。[docs/specification.md](docs/specification.md) が正規の仕様書 (日本語) — 振る舞いが不明なときはこれを参照する。

## メモリ・スキル参照

セッション開始時、または規約が関係しそうなタスクに着手する前に [memory/MEMORY.md](memory/MEMORY.md) のインデックスを確認すること。タスク発火型の手順 (テスト方針 / 並列化 / GitHub 操作 / `.claude` 編集) は [.claude/skills/](.claude/skills/) 配下に置き、Claude harness が trigger に応じて自動で読み込む。

新しい規約・フィードバックが判明したら `memory/feedback_*.md` 等を追加し `MEMORY.md` に 1 行リンクを張る。プロジェクト固有の規約は git 管理する `memory/` に集約する (チームで共有するため)。`.claude/` 配下のファイルを編集する際は [edit-dot-claude skill](.claude/skills/edit-dot-claude/SKILL.md) の手順 (`/tmp` でステージングしてから一括 `mv`) に従う。

## 開発原則

LLM コーディングで陥りがちなミスを減らすための行動指針。**慎重さを速度に優先する**バイアスを置いている。trivial なタスクでは判断で柔軟に運用してよい。

### 1. 実装前に考える

**仮定を勝手に置かない。混乱を隠さない。トレードオフを表に出す。**

実装に着手する前に:

- 仮定は明示的に述べる。不確かなら質問する
- 複数の解釈が成り立つなら全部提示する。黙って 1 つに決めない
- もっと単純な方法があるなら言う。正当な理由があれば押し返す
- 何かが不明瞭なら止まる。何が混乱の原因か名指しして質問する
- 仕様が曖昧なときは [docs/specification.md](docs/specification.md) を正規とする

### 2. シンプルさを優先

**問題を解く最小限のコード。投機的な実装はしない。**

- 頼まれていない機能は足さない
- 単発の用途しかないコードに抽象化は入れない
- 要求されていない「柔軟性」「設定可能性」は持ち込まない
- 起こり得ないシナリオに対するエラーハンドリングは書かない
- 200 行書いて 50 行で済むなら書き直す

自問する: 「これをシニアエンジニアが見たら過剰だと言うか?」Yes なら単純化する。

### 3. 外科的な変更

**触る必要があるものだけ触る。自分が散らかしたものだけ片付ける。**

既存コードを編集するとき:

- 周辺コード・コメント・整形を「ついでに改善」しない
- 壊れていないものをリファクタしない
- 自分なら違う書き方をするとしても既存スタイルに合わせる
- 無関係な dead code に気付いたら指摘する。勝手に消さない

自分の変更が orphan を生んだ場合:

- 自分の変更が原因で未使用になった import / 変数 / 関数は消す
- 元から dead だったコードは、頼まれない限り消さない

判定基準: diff の全行が、ユーザーの要求から直接トレースできるか?

### 4. ゴール駆動の実行

**成功条件を定義する。検証できるまでループする。**

タスクを検証可能なゴールに変換する:

- 「バリデーションを足す」→「不正な入力に対するテストを書いて通す」
- 「バグを直す」→「再現するテストを書いて通す」
- 「X をリファクタする」→「変更前後でテストが通ることを確認する」

複数ステップのタスクでは短い計画を先に提示する:

```text
1. [手順] → 検証: [チェック]
2. [手順] → 検証: [チェック]
```

強い成功条件があれば独立してループできる。弱い条件 (「動くようにする」) は確認を繰り返す羽目になる。

**この原則が効いている指標**: diff から不要な変更が減る、過剰実装による書き直しが減る、ミスの後ではなく着手前に確認質問が出る。

## コマンド

ツーリングは `uv` (astral-uv)。Python 実行は常に `uv run` を前置する。`make` レシピが主要な作業をラップする。

- `make test` — pytest を実行 (`uv run pytest -v`)
- `make type` — `src/` に対し pyright (strict mode) を実行
- `make format` — pre-commit hooks をすべて実行 (`uv run pre-commit run -a`)
- `make run` — `format` → `test` → `type` の全ワークフロー (**コミット前の必須 check**。ボットの起動方法ではない)
- 単一テスト実行: `uv run pytest tests/announcement/test_service.py::test_name -v`
- ボット起動: `uv run python src/main.py` (`.env` に `DISCORD_TOKEN` が必要)

CI (`.github/workflows/main.yaml`) は pre-commit / pytest / pyright を個別に実行する — 3 つすべてパスが必須。

注意: pytest は `--doctest-modules` 付きで走るため、`src/` 内の docstring もテストとして実行される。

## アーキテクチャ

エントリポイント [src/main.py](src/main.py) は `.env` をロードし、ロガーをセットアップし、graceful shutdown 用の SIGTERM/SIGINT ハンドラを設置して `AnnounceBotClient` を起動する。

`AnnounceBotClient` ([src/bot/client.py](src/bot/client.py)) は composition root。`setup_hook` で 4 つのコマンド cog をロードし、2 つのスケジュールタスクを登録し、スラッシュコマンドツリーを sync する。`ConfigManager` / `AnnouncementService` / `TaskScheduler` のシングルトンインスタンスを保持し、mutable な `next_announcement_type` 状態を持つ。リアクション→イベント種別の選択は `on_reaction_add` にあり、自身の確認メッセージを author + メッセージ部分文字列で識別する。

主要な協調オブジェクト:

- **`ConfigManager`** ([src/bot/config/](src/bot/config/)) — 二層 TOML config。`config.toml` は read-only のデフォルト、ユーザー変更は diff として `config-overrides.toml` に書かれる。`get()` は override→default の順で読む。`set()` は値がデフォルトと等しいとき override キーを削除する (overrides ファイルを最小に保つ)。パスは `CONFIG_PATH` / `CONFIG_OVERRIDES_PATH` 環境変数から取る。
- **`AnnouncementService`** ([src/bot/announcement/](src/bot/announcement/)) — `[templates]` config セクションの `string.Template` 文字列からメッセージを組み立て、`get_next_weekday` で対象日付を計算し、確認/告知メッセージを送信し、in-memory の `LTInfo` (speaker/title/url、再起動でリセット、LT 告知投稿後に自動クリア) を保持する。
- **`TaskScheduler`** ([src/bot/scheduler/](src/bot/scheduler/)) — pure-asyncio スケジューラ。`schedule_daily_task` が次の該当する曜日+時刻まで sleep して loop でコールバックする長寿命タスクを spawn する。外部スケジューリングライブラリは使わない。

Cog ([src/bot/commands/](src/bot/commands/))、各々がトップレベルの `app_commands.Group` を登録する:

- `LtCog` (`lt`), `ConfigCog` (`config`), `ManualCog` (`manual`), `UtilityCog` (status/help/test)。
- コマンドは getter (引数なし) または setter (引数あり) として振る舞う — LT / config コマンドで共通のパターン。
- 権限チェックはロール名ベースで `[permissions]` config セクション (admin / moderator / lt_admin ロール) から読む。権限失敗やその他のスラッシュコマンドエラーは `ephemeral=True` メッセージで応答する。

定数 — リアクション絵文字、曜日の string↔int↔日本語変換 (`Weekday`)、config セクション/キー名 (`ConfigKeys`)、環境変数名 (`EnvKeys`)、`AnnouncementType` — は [src/bot/constants.py](src/bot/constants.py) に集約。config キーや環境変数を参照するときは文字列リテラルでなくこれらの定数を使う。

## コーディング規約

- Python 3.12+、`src/` には pyright **strict**。public なクラス/メソッドには Google-style docstring (英語、型情報は docstring に書かない) が必要。型注釈は builtin generics (`list`/`tuple`、`typing.List` ではない) を使う。
- override メソッドは `@typing.override` で装飾する (`reportImplicitOverride` 有効)。
- スタイル: `ruff` (line-length 88, double quotes, isort combine-as-imports)。
- Discord 向けの文字列・ロジック説明コメントは日本語。Google-style docstring の構造 (Args/Returns/Raises) は英語慣習に従う。

### カプセル化

- クラスの内部実装の詳細や属性は、基本的にすべて private (`_` prefix) にする
- 外部から参照する必要がある属性のみ public にする
- `__init__` で設定される属性は原則として private とする

例:

```python
class Example:
    def __init__(self, dim: int):
        self._dim = dim  # private
        self._client = SomeClient(dim)  # private
```

## テスト方針

詳細は [testing-strategy skill](.claude/skills/testing-strategy/SKILL.md) を必ず参照する。要点:

- **Discord API はモックする** (`pytest-mock`)。E2E テストは無い。Discord (`discord.py`) の表面は自分の所有物ではないため、`mocker` で `Interaction` / `Client` / `Message` 等を mock し、**自分のロジック** (config 解決、日付計算、テンプレート展開、権限判定、スケジューラの sleep 計算、リアクション→種別の写像) を検証する。
- テストレイアウトは `src/bot/` を `tests/` に 1 対 1 でミラーする (`src/bot/announcement/service.py` ↔ `tests/announcement/test_service.py`)。
- 内部実装の詳細ではなく公開振る舞いをテストする。`--doctest-modules` で docstring 内の `>>>` も実行されるので、doctest を書くなら必ず通す。

## デプロイ

Docker (`Dockerfile` / `docker-compose.yaml`): `python:3.12-slim`、非 root の `botuser` で実行、メインプロセスへの `pgrep` で healthcheck。`logs/` ディレクトリは bind-mount、ロギングは `LOG_DIR` 配下の rotating file handler。開発は `.devcontainer/` の devcontainer を使う。`.env` に必須の環境変数: `DISCORD_TOKEN` (`.env.example` 参照)。

## Git 運用

### ブランチ

- `main`: 開発の主軸
- 作業用ブランチの命名規則: `<種別>/<日付>/<内容>` (例: `feat/20260605/lt-command`、`fix/20260605/scheduler-timezone`)
  - 種別: `feat`, `fix`, `refactor`, `docs`, `chore`
- 必ずブランチ上で commit する (`main` に直接 commit しない)。作業ブランチは `main` から分岐
- `main` へのマージはユーザーが判断・実行する

### コミットメッセージ

`<種別>(<スコープ>): <内容>` または `<種別>: <内容>` の形式に従う (既存履歴は両方混在。日本語/英語どちらでも可)。

- 種別: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
- スコープ (任意): `announcement`, `config`, `scheduler`, `commands`, `ci`, `docker` などのモジュール単位
- 例: `feat(commands): LT情報を一括設定するコマンドを追加` / `fix(scheduler): 次回曜日の計算を修正`

GitHub 操作 (PR / issue / push) は [github-ops skill](.claude/skills/github-ops/SKILL.md) を参照。

## エージェントチーム戦略

「エージェントチームで行う」という指示があり、具体的な手順が示されていない場合、以下のサイクルに従う。利用可能なエージェントは [.claude/agents/](.claude/agents/) のもの。各エージェントの責務は**厳密に分離**されており、互いの担当領域に踏み込まない:

| エージェント              | 書く対象                                               | 触ってはいけない対象                                       |
| ------------------------- | ------------------------------------------------------ | ---------------------------------------------------------- |
| `spec-planner`            | 仕様書 (コードなし、最終メッセージとして返す)          | コード全般                                                 |
| `spec-driven-implementer` | `src/bot/` のプロダクションコード                      | `tests/` (テストは絶対に編集しない)                        |
| `spec-test-author`        | `tests/` 配下のテストコード                            | `src/bot/` のプロダクションコード                          |
| `code-quality-reviewer`   | `src/bot/` の内部 (public/Discord 向け surface は不変) | `tests/`、スラッシュコマンドの名前/引数、config キー、定数 |
| `docstring-author`        | docstring / コメント                                   | ロジック                                                   |

### 「公開 surface」の定義 (リファクタで不変に保つもの)

- スラッシュコマンドの名前・サブコマンド・引数・`ephemeral` 応答の有無 (`/lt`, `/config`, `/manual`, status/help/test)
- Discord に投稿される文字列を生むテンプレート構造、リアクション絵文字 (👍/⚡/💤) の意味
- `config.toml` のセクション/キー名、`constants.py` の公開定数 (`ConfigKeys` / `EnvKeys` / `Weekday` / `AnnouncementType`)
- `_` prefix を持たないモジュール / クラス / 関数 / 属性

### 実装サイクル

1. **spec-planner**: 要件を分析し、振る舞い・エッジケース・受け入れ基準を含む実装計画と仕様を策定する (コードは書かない。仕様は最終メッセージとして返し、orchestrator が必要なら [docs/specification.md](docs/specification.md) に反映する)
2. **spec-driven-implementer + spec-test-author**: 仕様を共通の入力として**並列起動**。実装エンジニアは仕様に従って `src/bot/` を書き、テストエンジニアは仕様に従って `tests/` を書く。テストは仕様書として機能する (実装に引きずられない)
3. **実装修正ループ**: テストが揃ったら、`spec-driven-implementer` がテストを通すように `src/bot/` だけを修正する。**テストコードは絶対に触らない**。テストが間違っていると思われる場合は、orchestrator 経由で `spec-test-author` に質問を回す (テストの修正可否を判定するのは spec-test-author の責務)
4. **テストクリア**: すべてのテストが green になり、`make run` (format → test → type) がパスしたら次へ
5. **code-quality-reviewer**: 公開 surface (上記定義) を一切変えずにリファクタリングする (重複排除・簡素化・命名・型精緻化)。`tests/` は触らない。各ステップで `make test` を回し green を保つ
6. **docstring-author**: 最後にコメントや docstring の追加・更新が必要か確認する

### 並列化 (論理的に可能な最大数で並列実行する)

並列性の最大化はマルチエージェント運用の中心戦略。Agent tool 呼び出しを **1 メッセージに複数並べて発射する**ことで並列実行される。逐次にしてよいのは依存関係がある場合のみ。tool 呼び出しレベルの並列化指針は [maximize-parallels skill](.claude/skills/maximize-parallels/SKILL.md) を参照。

- **フェーズ 2 (実装 + テスト)**: 1 つの仕様に対して `spec-driven-implementer` と `spec-test-author` を常に並列で 2 つ走らせる。仕様が独立した N 個のモジュール (例: `announcement` と `config` と `scheduler`、あるいは別々の cog) に分割可能なら、各モジュール毎に `spec-driven-implementer × N` と `spec-test-author × N` の合計 **2N エージェント**を並列起動する
- **フェーズ 3 (実装修正ループ)**: 独立モジュールごとに `spec-driven-implementer` を並列。テストへの質問が必要なモジュールだけ `spec-test-author` を再起動する
- **フェーズ 5 (リファクタリング)**: 独立モジュールごとに `code-quality-reviewer` を並列起動

並列化の前提:

- 担当領域が disjoint (同じファイルを 2 つのエージェントが同時に編集しない)
- 並列起動した結果は orchestrator が統合する。コンフリクトが起きたら逐次に切り替える

### エージェント間通信のルール

エージェント同士は直接通信できない。すべての通信は orchestrator (親 Claude) が中継する:

- 実装エンジニアからテストエンジニアへの質問 → orchestrator が `spec-test-author` を起動して回答を取り、実装エンジニアに渡す
- 仕様の解釈が分かれる場合 → orchestrator がユーザーに明確化を依頼するか、`spec-planner` を再起動して仕様を更新する
- リファクタリングで公開 surface を変えたくなった場合 → `code-quality-reviewer` は実施せず、改善案として報告。実施判断は orchestrator / ユーザーに委ねる
