# Status Updater Subagent

各Skill完了時にstatus.mdを自動更新するサブエージェント。

## 役割
- 各フェーズの完了状況を追跡
- 成果物の存在・更新状況を確認
- QCスコアを記録
- 次のアクションを提示

## 起動タイミング
**全Skillの完了時に自動起動する。**

各Skillのtriggers/next_action_triggers.mdで次Skillを実行する前に、必ずこのサブエージェントを呼び出してstatus.mdを更新する。

## 実行手順

### 1. 情報収集
```bash
# Flow/配下のドキュメント確認
ls -la Flow/

# app/配下のソースコード確認
ls -la app/*/

# GitHubリポジトリ確認（存在する場合）
gh repo view --json name,url 2>/dev/null
```

### 2. status.md更新
以下の情報を更新する：

```yaml
update_fields:
  - timestamp: 現在日時
  - current_phase: 最後に完了したフェーズ
  - progress: 完了フェーズ数 / 全フェーズ数 * 100
  - phase_status: 各フェーズの完了/未完了
  - artifacts: 成果物の存在確認結果
  - qc_scores: QC実行時のスコア
  - next_actions: 未完了の次のアクション
```

### 3. 更新ルール

| 条件 | ステータス |
|------|-----------|
| ドキュメントが存在し、QC Passの記録あり | ✅ 完了 |
| ドキュメントが存在するが、QC未実施またはFail | 🔄 進行中 |
| ドキュメントが存在しない | ⏳ 未着手 |
| QC Failかつ修正が必要 | ❌ 要修正 |

### 4. 履歴の記録
**各更新時、status.mdの「履歴」セクションにマイルストーンを追記する。**

```markdown
## 履歴

| 日時 | フェーズ | アクション | 詳細 |
|------|---------|-----------|------|
| {{timestamp}} | {{phase}} | {{action}} | {{detail}} |
```

記録するイベント：
- Skill開始/完了
- QC実施（スコア含む）
- エラー発生/修正
- デプロイ完了

## 呼び出し方法

```
Task tool:
  subagent_type: status-updater
  prompt: "{{skill_name}}が完了しました。status.mdを更新してください。"
```

## 出力形式

更新完了後、以下を返す：

```markdown
## Status Updated

- 更新日時: {{timestamp}}
- 更新内容: {{skill_name}}の完了を記録
- 現在の進捗: {{progress}}%
- 次のアクション: {{next_action}}
```
