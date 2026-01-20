# Mini App Deploy Next Action Triggers

## 自動実行ルール
**以下の条件を満たす場合は、該当Skillを必ず実行すること（WF自動継続）。**
条件判定はSkill完了時に自動で行い、スキップ条件に該当しない限り次Skillへ進む。

## ステータス更新（必須）
**Skill完了時、必ずstatus-updaterサブエージェントを呼び出す。**

```
Task tool:
  subagent_type: status-updater
  prompt: "mini-app-deployが完了しました。status.mdを更新してください。
           app_name: {{app_name}}
           公開URL: {{public_url}}
           リポジトリ: {{repo_url}}"
```

**注意**: app_name は必須パラメータ。アプリごとにステータスを管理する。

## 起動条件テーブル

| ID | 起動条件 | 実行Skill | 優先度 | 備考 |
|----|---------|-----------|--------|------|
| T0 | Skill完了時 | `status-updater`（サブエージェント） | 0 | ステータス更新 |
| T1 | デプロイ完了かつ公開URLで動作確認Pass | なし（ワークフロー完了） | 1 | 成功終了 |
| T2 | デプロイ失敗または公開URLで動作確認Fail | `mini-app-build` | 2 | 修正→再テスト→再デプロイ |

## スキップ条件
以下の場合のみ、起動条件を満たしても実行をスキップできる:
- ユーザーが明示的にワークフロー終了を指示した場合
- ユーザーが別のSkillの実行を指示した場合

## 条件判定ロジック
1. Skill完了時、まずstatus-updaterを呼び出してステータス更新
2. 起動条件テーブルを上から順に評価する
3. 条件を満たす行があれば、スキップ条件を確認する
4. T1が満たされた場合はワークフロー完了として終了する

## ワークフロー完了時の報告

デプロイ成功時、以下をユーザーに報告する:

```markdown
## デプロイ完了

- **公開URL**: https://{{username}}.github.io/{{repo_name}}/
- **リポジトリ**: https://github.com/{{username}}/{{repo_name}}
- **ステータス**: 正常デプロイ完了

ミニアプリの開発が完了しました。

### 進捗サマリー
status.mdで全フェーズの履歴を確認できます。
```
