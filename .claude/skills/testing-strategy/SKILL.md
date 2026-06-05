---
name: testing-strategy
description: この Discord bot のテスト戦略。Discord (discord.py) API はモックするが「他人の表面」だけに留め、自分のロジック (config 解決 / 日付計算 / テンプレート展開 / 権限判定 / scheduler の sleep 計算 / リアクション→種別の写像) は実物で検証する。tests を src/bot にミラーするレイアウト、pytest-asyncio / pytest-mock の使い分け、tmp_path での実 config I/O、時刻依存ロジックの決定化、書いてはいけないトートロジーテスト、--doctest-modules、E2E が無い前提。テストコードを書く／pytest 周りを設定する前に読む
---

# テスト方針リファレンス

手元で書き始める前にざっと読む「実行可能なまとめ」。背景となる学びの蓄積は [memory/](../../../memory/) 配下に集約する。

## 哲学

このプロジェクトは **Discord (`discord.py`) という外部 API との結合**が支配的だが、本質的な価値は **自分が書いたロジック** (config 解決、日付/曜日計算、テンプレート展開、権限判定、スケジューラの sleep 計算、リアクション→`AnnouncementType` の写像) にある。

方針はシンプル: **Discord の表面はモックする。自分のロジックは実物で検証する**。「他人の表面」をモックするのは結合を切るためであり、「自分の所有物」までモックすると、リファクタで壊れるだけで何も保証しないテストになる (GOOS / Freeman & Pryce: "Don't mock what you don't own")。

### 検証対象の優先順位

1. **自分のロジックを実物で検証** — `ConfigManager` の TOML 解決、`get_next_weekday` の曜日計算、`string.Template` のテンプレート展開、ロール名マッチによる権限判定、`TaskScheduler` の次回時刻計算、`constants.py` の変換。これが第一の検証対象
2. **実 file I/O は `tmp_path` で** — config テストは `tmp_path` に実 TOML (`config.toml` / `config-overrides.toml`) を書いて `ConfigManager` を通す。config ファイル読み書き自体をモックしない
3. **Discord 表面はモック** — `discord.Interaction` / `Client` / `Message` / `TextChannel` / `Member` / `Reaction` と送信系メソッド (`channel.send` / `interaction.response.send_message` / `message.add_reaction`) は `pytest-mock` の `mocker` で組む。呼ばれた引数 (送信先チャンネル・本文・絵文字) を assert することでロジックを検証する
4. **時刻依存は決定化** — 次回曜日・sleep 秒数は `datetime` を引数注入するか固定値を渡して決定的にする。`asyncio.sleep` の実行そのものをテストせず、**計算結果** (何秒待つべきか) を検証する

## やってはいけないモック

- 自分のサービス/マネージャの内部メソッドを `mocker.patch` で潰す (リファクタで壊れるだけ)
- `ConfigManager` をモックして「config を読んだこと」だけを確認する (実物を `tmp_path` で動かせる)
- `datetime.now` 全体を雑に patch して計算ロジックまで覆い隠す (計算対象の日付を引数で渡す設計を優先)

## 基本原則

- 必要十分なテストのみ。過剰なテストは避ける
- 内部実装の詳細はテストしない。公開インターフェースと振る舞いをテストする
- Python のテスト関数に戻り値の型アノテーションは不要
- **コードカバレッジは診断であり目標ではない** (Fowler: "high coverage numbers are too easy to reach with low quality testing")。100% は赤信号

## テストレイアウト — `tests/` を `src/bot/` に 1 対 1 でミラー

- `src/bot/announcement/service.py` ↔ `tests/announcement/test_service.py`
- `src/bot/announcement/models.py` ↔ `tests/announcement/test_models.py`
- `src/bot/config/config_manager.py` ↔ `tests/config/test_config_manager.py`
- `src/bot/scheduler/scheduler.py` ↔ `tests/scheduler/test_scheduler.py`
- `src/bot/commands/<name>_cog.py` ↔ `tests/commands/test_<name>_cog.py`
- `src/bot/constants.py` ↔ `tests/test_constants.py`
- 各テストディレクトリに `__init__.py` を置く。1 モジュール 1 テストファイルを原則とする

## async のテスト

- コマンド (cog) とサービスの async メソッドは `pytest-asyncio` でテストする。既存テスト (`tests/commands/`) のスタイル (デコレータ・fixture の組み方) を踏襲する
- `interaction.response.send_message` 等は `AsyncMock` で組み、`await` 可能にする
- 権限拒否のテストは「`ephemeral=True` で拒否メッセージが送られる / 本処理が呼ばれない」を assert する

## 書いてはいけないテスト (削除対象 — marginal value ゼロ)

- 継承の追試 (`assert issubclass(...)`)、import 可能性の追試 (`assert X is not None`)
- 定数 literal の追試 (`assert TIMEOUT == 5`。意味的不変条件ならOK)
- getter/setter ラウンドトリップ、`__init__` のフィールド設定確認だけ
- stdlib / framework の動作追試 (`assert json.loads("{}") == {}`)
- 例外メッセージの完全一致 (`"keyword" in str(err)` 程度に留める)
- モックの戻り値をそのまま検証するだけ (モックの動作確認になっている)

## 公開 API / 文言契約ピン (原則の例外)

スラッシュコマンド名・引数、リアクション絵文字の意味、テンプレートが生む文言の骨子のような「契約として固定する価値があるもの」はテストしてよい。コメントで「これは契約ピンであり振る舞いテストではない」と明示する。

## doctest

`pytest --doctest-modules` が有効 (`pyproject.toml`)。`src/` の docstring 内の `>>>` はすべて実行される。doctest を書くなら **必ず通す**こと。怪しいときは `>>>` を避け散文の例にする。

## E2E は無い

実 Discord に接続する E2E テストは持たない。`make run` (`format` → `test` → `type`) が green であることがマージの品質ゲート。実機での動作確認は手動 (ボットを起動して Discord 上で確認) で、テストスイートには含めない。
