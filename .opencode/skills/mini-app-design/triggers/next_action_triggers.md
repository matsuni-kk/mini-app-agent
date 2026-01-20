# Mini App Design Next Action Triggers

## 自動実行ルール
**以下の条件を満たす場合は、該当Skillを必ず実行すること（WF自動継続）。**
条件判定はSkill完了時に自動で行い、スキップ条件に該当しない限り次Skillへ進む。

## ステータス更新（必須）
**Skill完了時、次Skillへ進む前に必ずstatus-updaterサブエージェントを呼び出す。**

```
Task tool:
  subagent_type: status-updater
  prompt: "mini-app-designが完了しました。status.mdを更新してください。
           app_name: {{app_name}}"
```

**注意**: app_name は必須パラメータ。アプリごとにステータスを管理する。

## 起動条件テーブル

| ID | 起動条件 | 実行Skill | 優先度 | 備考 |
|----|---------|-----------|--------|------|
| T0 | Skill完了時 | `status-updater`（サブエージェント） | 0 | ステータス更新 |
| T1 | design.mdが生成された | `mini-app-build` | 1 | 実装へ進む |
| T2 | design.mdに重大な変更があり、既存ソースコードの更新日時より新しい | `mini-app-build` | 2 | 再実装が必要 |

## スキップ条件
以下の場合のみ、起動条件を満たしても実行をスキップできる:
- ユーザーが明示的に「設計のみ」と指定した場合
- ユーザーが別のSkillの実行を指示した場合

## 条件判定ロジック
1. Skill完了時、まずstatus-updaterを呼び出してステータス更新
2. 起動条件テーブルを上から順に評価する
3. 条件を満たす行があれば、スキップ条件を確認する
4. スキップ条件に該当しなければ、該当Skillを実行する
