---
name: mini-app-status
description: "アプリ開発の進捗状況を確認・更新する。「進捗」「ステータス」「状況確認」を依頼されたときに使用する。"
---

# Mini App Status Workflow

アプリ開発の進捗状況を一覧化し、status.mdを生成・更新する。主成果物はstatus.md（各フェーズの完了状況・成果物一覧・次のアクション）。

**重要**: このスキルは各Skill完了時にサブエージェント（status-updater）として自動実行される。

## Instructions

### 1. Preflight（事前確認）
- Flow/配下の全ドキュメントを確認する。
- app/配下のソースコードの存在を確認する。
- GitHubリポジトリの状態を確認する（存在する場合）。
- `./assets/status_template.md` を先に読み、ステータスレポートの構造を確認する。

### 2. 情報収集・更新
以下の情報を収集・整理する:

#### フェーズ進捗の判定ルール

| フェーズ | 完了条件 |
|----------|----------|
| 要件定義 | Flow/requirements.md が存在 |
| 設計 | Flow/design.md が存在 |
| 実装 | app/{app_name}/index.html が存在 |
| テスト | Flow/test_report.md が存在かつ判定Pass |
| レビュー | Flow/review_report.md が存在 |
| デプロイ | Flow/deploy_log.md が存在かつ公開URL記載 |

#### 進捗率の計算
```
進捗率 = 完了フェーズ数 / 6 * 100
```

### 3. status.md生成・更新
- Flow/status.mdを生成または更新する。
- 各フェーズのステータス、成果物一覧、次のアクションを記録する。

### 4. サブエージェント呼び出し時の動作
各Skill完了時に自動で以下を実行：
1. 完了したSkillのステータスを更新
2. QCスコアがあれば記録
3. 次のアクションを更新
4. 全体進捗率を再計算

## サブエージェント設定

```yaml
subagent:
  name: status-updater
  trigger: 各Skill完了時
  auto_run: true
  path: .claude/agents/status-updater.md
```

## 呼び出し方（メインエージェントから）

各Skill完了後、次Skillへ進む前に以下を実行：

```
Task tool:
  subagent_type: status-updater
  prompt: "{{skill_name}}が完了しました。status.mdを更新してください。
           完了Skill: {{skill_name}}
           QCスコア: {{score}}（あれば）
           次のアクション: {{next_action}}"
```

## Resources
- assets: ./assets/status_template.md
- agent: .claude/agents/status-updater.md
- triggers: ./triggers/next_action_triggers.md

## Next Action
- triggers: ./triggers/next_action_triggers.md

ステータス確認後、ユーザーの指示に応じて該当Skillを実行する。
