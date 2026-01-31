# skill-distribution - Questions

## 必須入力項目

1. **skill_names**: 配布するSkill名（複数可、カンマ区切り or 空白区切り）
   - 例: `chatgpt-parallel-research`
   - 例: `chatgpt-parallel-research, x-automation, note-automation`
   - 例: `--all`（全Skill配布）

2. **mode**: 配布モード
   - `overwrite`（デフォルト）: 既存フォルダを上書き
   - `new_only`: 既存フォルダがない場合のみ配布
   - `all`: 上書き＋新規の両方

## 任意入力項目

3. **target_repos**: 配布先リポジトリ（指定しない場合は全リポジトリ）
   - 例: `fiction_craft_agent, o2p-agent`
   - デフォルト: デスクトップ配下の全エージェントリポジトリ

4. **dry_run**: ドライラン（実行せず確認のみ）
   - `yes` / `no`（デフォルト: no）

5. **exclude_repos**: 除外するリポジトリ
   - 例: `browser-controller-agent`（配布元は自動除外）

## 確認項目

6. **verification**: 配布後の検証方法
   - ファイル存在確認
   - Skill読み込み確認
   - 動作テスト

## 使用例

```yaml
# 単一Skill配布
skill_names: chatgpt-parallel-research
mode: overwrite
dry_run: no

# 複数Skill配布
skill_names: chatgpt-parallel-research, x-automation
mode: overwrite
target_repos: fiction_craft_agent, o2p-agent

# 全Skill配布（ドライラン）
skill_names: --all
mode: overwrite
dry_run: yes
```
