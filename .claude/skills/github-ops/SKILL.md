---
name: github-ops
description: "GitHub 操作 — PR の作成/レビュー (`gh pr create`, `gh pr view`, `gh pr checks`)、issue 管理、ブランチの push、gh CLI 認証を行うときに使う。トリガー: 'gh pr create', 'gh pr', 'gh issue', 'gh auth', 'PR を作成', 'PR を送る', 'pull request を作る', 'git push', 'PR レビュー', 'issue を立てる'。"
---

# GitHub Operations (gh CLI)

このリポジトリでの GitHub 連携 (PR / issue / push) のための skill。[CLAUDE.md](../../../CLAUDE.md) の「Git 運用」節を `gh` 操作に落とし込む手順書。

______________________________________________________________________

## 1. 認証 (gh auth)

```bash
gh auth status                # 認証状態と scope を表示
gh api user --jq .login       # 自分の username を返せれば OK
```

未認証なら `gh auth login --hostname github.com --git-protocol https --web` を実行 (ブラウザ device flow)。CI / headless では `GH_TOKEN` 環境変数 (PAT、scope: `repo` / 必要なら `workflow`) を最優先で参照する。`.env` に token を置く場合は gitignore 済みを確認 (`git check-ignore -v .env`)。

______________________________________________________________________

## 2. ブランチと commit (CLAUDE.md 規約)

- `main` に直接 commit しない。作業は `main` から分岐したブランチ上で行う
- ブランチ名: `<種別>/<日付>/<内容>` (例: `feat/20260605/stats-command`)。種別は `feat` / `fix` / `refactor` / `docs` / `chore`
- commit メッセージ: `<種別>(<スコープ>): <内容>` または `<種別>: <内容>` (日本語/英語可)

```bash
git switch -c feat/20260605/stats-command   # main から分岐
# ... 実装・make run が green ...
git add -A && git commit -m "feat(commands): 集計コマンド /stats を追加"
git push -u origin HEAD
```

______________________________________________________________________

## 3. PR 作成

**push 前に `make run` (format → test → type) が green であることを必須確認**。CI (`.github/workflows/main.yaml`) は pre-commit / pytest / pyright を個別に走らせるため、3 つすべてパスする必要がある。

```bash
gh pr create --base main --title "feat: /stats コマンドを追加" --body "$(cat <<'EOF'
## 概要
<このPRが解決すること>

## 変更点
- ...

## 検証
- [ ] make run が green (format / test / type)
EOF
)"
```

- PR タイトルは commit メッセージ規約に揃える
- `main` へのマージは**ユーザーが判断・実行する** (勝手にマージしない)

______________________________________________________________________

## 4. PR の確認・レビュー

```bash
gh pr view --web              # ブラウザで開く
gh pr checks                  # CI の状態を確認
gh pr diff                    # 差分を確認
```

CI が落ちていたら、`gh pr checks` でどのジョブ (pre-commit / pytest / pyright) が落ちたかを特定し、ローカルで該当の `make` ターゲット (`make format` / `make test` / `make type`) を再現してから直す。

______________________________________________________________________

## 5. issue

```bash
gh issue create --title "<タイトル>" --body "<本文>"
gh issue list --state open
```

______________________________________________________________________

## 注意

- push / PR 作成 / マージのような外向きの操作は、durable に許可されていない限り着手前にユーザーへ確認する
- secret (`DISCORD_TOKEN` 等) を PR 本文・issue・commit に含めない
