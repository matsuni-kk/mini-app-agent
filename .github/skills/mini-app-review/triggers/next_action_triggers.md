# Mini App Review Next Action Triggers

## 自動実行ルール
**以下の条件を満たす場合は、該当Skillを必ず実行すること（WF自動継続）。**
条件判定はSkill完了時に自動で行い、スキップ条件に該当しない限り次Skillへ進む。

## ステータス更新（必須）
**Skill完了時、次Skillへ進む前に必ずstatus-updaterサブエージェントを呼び出す。**

```
Task tool:
  subagent_type: status-updater
  prompt: "mini-app-reviewが完了しました。status.mdを更新してください。"
```

## 起動条件テーブル

| ID | 起動条件 | 実行Skill | 優先度 | 備考 |
|----|---------|-----------|--------|------|
| T0 | Skill完了時 | `status-updater`（サブエージェント） | 0 | ステータス更新 |
| T1 | レビュー完了かつHigh Priority改善項目がない | `mini-app-deploy` | 1 | デプロイへ進む |
| T2 | ユーザーがHigh Priority改善の実施を希望した | `mini-app-build` | 2 | 改善実装へ進む |
| T3 | ユーザーがMedium Priority改善の実施を希望した | `mini-app-build` | 3 | 改善実装へ進む |
| T4 | ユーザーが改善をスキップしてデプロイを希望した | `mini-app-deploy` | 4 | 現状のままデプロイ |

## スキップ条件
以下の場合のみ、起動条件を満たしても実行をスキップできる:
- ユーザーが明示的に「レビューのみ」と指定した場合
- ユーザーが別のSkillの実行を指示した場合

## 条件判定ロジック
1. Skill完了時、まずstatus-updaterを呼び出してステータス更新
2. 起動条件テーブルを上から順に評価する
3. 条件を満たす行があれば、スキップ条件を確認する
4. スキップ条件に該当しなければ、該当Skillを実行する

## フロー図

```
レビュー完了
    ↓
status-updater（ステータス更新）
    ↓
High Priority改善あり？
    ├─ Yes → ユーザーに改善実施を確認
    │         ├─ 改善する → mini-app-build → mini-app-test → mini-app-review
    │         └─ スキップ → mini-app-deploy
    └─ No  → mini-app-deploy
```

## レビュー完了時の報告

レビュー完了時、以下をユーザーに報告して確認する:

```markdown
## レビュー完了

### 改善提案サマリー
- High Priority: {{n}}件
- Medium Priority: {{n}}件
- Low Priority: {{n}}件

### 対応方針を選択してください
1. High Priority項目を改善してからデプロイ
2. 現状のままデプロイ（改善は後で対応）
3. レビュー結果のみ保存（デプロイしない）
```
