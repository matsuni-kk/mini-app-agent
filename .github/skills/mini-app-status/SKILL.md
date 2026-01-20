---
name: mini-app-status
description: "アプリ開発の進捗状況を確認・更新する。「進捗」「ステータス」「状況確認」を依頼されたときに使用する。"
---

# Mini App Status Workflow

**アプリごと**の進捗状況を一覧化し、`app/{app_name}/status.md`を生成・更新する。
主成果物はstatus.md（各フェーズの完了状況・成果物一覧・次のアクション）。

**重要**: このスキルは各Skill完了時にサブエージェント（status-updater）として自動実行される。

## Instructions

### 0. app_name の確定
- ユーザーから app_name が指定されていない場合、`app/` 配下のディレクトリを確認する。
- 複数アプリが存在する場合は、対象アプリを確認する。
- app_name は以降のすべてのパスで `{app_name}` として使用する。

### 1. Preflight（事前確認）
- `app/{app_name}/docs/` 配下の全ドキュメントを確認する。
- `app/{app_name}/` 配下のソースコードの存在を確認する。
- GitHubリポジトリの状態を確認する（存在する場合）。
- `./assets/status_template.md` を先に読み、ステータスレポートの構造を確認する。

### 2. 情報収集・更新
以下の情報を収集・整理する:

#### フェーズ進捗の判定ルール

| フェーズ | 完了条件 |
|----------|----------|
| 要件定義 | `app/{app_name}/docs/requirements.md` が存在 |
| 設計 | `app/{app_name}/docs/design.md` が存在 |
| 実装 | `app/{app_name}/index.html` が存在 |
| テスト | `app/{app_name}/docs/test_report.md` が存在かつ判定Pass |
| レビュー | `app/{app_name}/docs/review_report.md` が存在 |
| デプロイ | `app/{app_name}/docs/deploy_log.md` が存在かつ公開URL記載 |

#### 進捗率の計算
```
進捗率 = 完了フェーズ数 / 6 * 100
```

### 3. status.md生成・更新
- `app/{app_name}/status.md` を生成または更新する。
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
           app_name: {{app_name}}
           完了Skill: {{skill_name}}
           QCスコア: {{score}}（あれば）
           次のアクション: {{next_action}}"
```

**注意**: app_name は必須パラメータ。これがないとどのアプリのステータスを更新すべきか判断できない。

## Resources
- assets: ./assets/status_template.md
- agent: .claude/agents/status-updater.md
- triggers: ./triggers/next_action_triggers.md

## Next Action
- triggers: ./triggers/next_action_triggers.md

ステータス確認後、ユーザーの指示に応じて該当Skillを実行する。
