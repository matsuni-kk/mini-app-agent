# Mini App Requirements Next Action Triggers

## 自動実行ルール
**以下の条件を満たす場合は、該当Skillを必ず実行すること（WF自動継続）。**
条件判定はSkill完了時に自動で行い、スキップ条件に該当しない限り次Skillへ進む。

## ステータス更新（必須）
**Skill完了時、次Skillへ進む前に必ずstatus-updaterサブエージェントを呼び出す。**

```
Task tool:
  subagent_type: status-updater
  prompt: "mini-app-requirementsが完了しました。status.mdを更新してください。"
```

## 起動条件テーブル

| ID | 起動条件 | 実行Skill | 優先度 | 備考 |
|----|---------|-----------|--------|------|
| T0 | Skill完了時 | `status-updater`（サブエージェント） | 0 | ステータス更新 |
| T1 | requirements.mdが生成された | `mini-app-design` | 1 | UI/UX設計へ進む |
| T2 | requirements.mdに重大な変更があり、既存design.mdの更新日時より新しい | `mini-app-design` | 2 | 再設計が必要 |

## スキップ条件
以下の場合のみ、起動条件を満たしても実行をスキップできる:
- ユーザーが明示的に「要件定義のみ」と指定した場合
- ユーザーが別のSkillの実行を指示した場合

## 条件判定ロジック
1. Skill完了時、まずstatus-updaterを呼び出してステータス更新
2. 起動条件テーブルを上から順に評価する
3. 条件を満たす行があれば、スキップ条件を確認する
4. スキップ条件に該当しなければ、該当Skillを実行する
