---
name: edit-dot-claude
description: Use when creating or editing any file under the .claude/ directory (settings, skills, agents, commands, hooks, etc.). Edits inside .claude/ trigger a permission prompt on every write, so this skill stages the work in /tmp and moves it back in a single batch at the end.
---

# edit-dot-claude

`.claude/` 配下のファイルを作成・編集するためのスキル。

## なぜこのスキルが必要か

`.claude/` 内のファイルを直接 Read/Edit/Write すると、書き込みのたびに permission を求められる。
そこで「作業は `/tmp` のステージング領域で行い、完了後に一括で `.claude/` へ `mv` する」ことで、
permission プロンプトを最後の 1 回（mv）だけに抑える。

## 手順

1. **ステージング領域を用意する**

   - 作業用ディレクトリを 1 つ決める。例: `/tmp/dot-claude-edit`
   - `mkdir -p /tmp/dot-claude-edit`

2. **対象を `/tmp` にコピーする**

   - 既存ファイルを編集する場合は、`.claude/` 内のファイルを階層構造を保ったまま `/tmp` にコピーする。
     例: `cp .claude/skills/foo/SKILL.md /tmp/dot-claude-edit/SKILL.md`
   - 新規ファイルの場合はコピー不要。`/tmp` 側に直接作成する。

3. **`/tmp` 上で編集する**

   - Read / Edit / Write はすべて `/tmp/dot-claude-edit/...` に対して行う。
   - ここでの編集は permission を求められないので、自由に何度でも編集してよい。
   - 編集が完了したら内容を見直す。

4. **完了後に一括で `.claude/` へ反映する**

   - すべての編集が終わってから、まとめて 1 回の `mv`（または `cp`）で `.claude/` に戻す。
   - 反映先のディレクトリが存在しない場合は `mkdir -p` で先に作る。
     例:
     ```bash
     mkdir -p .claude/skills/foo
     mv /tmp/dot-claude-edit/SKILL.md .claude/skills/foo/SKILL.md
     ```
   - 複数ファイルを編集した場合も、できる限り 1 つの Bash 呼び出しにまとめて移動する。

5. **後片付け**

   - 反映が終わったら、ステージング領域を削除する: `rm -rf /tmp/dot-claude-edit`

## 注意

- `.claude/` への直接の Edit / Write は行わない。必ず `/tmp` 経由にする。
- 上書きで失う情報がないよう、既存ファイルは編集前に必ず一度 Read して内容を把握する。
- 最終的な `mv` は「すべての編集が完了してから」実行する。途中で何度も `.claude/` に書き戻さない。
