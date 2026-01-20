---
name: mini-app-deploy
description: "ミニアプリをVercelにデプロイする。「デプロイ」「公開」「リリース」を依頼されたときに使用する。"
---

# Mini App Deploy Workflow

ミニアプリをVercelにデプロイする。主成果物はデプロイ完了URL・deploy_log.md。

## Instructions

### 1. Preflight（事前確認）
- ドキュメント精査原則（Preflight必須）：テンプレート確認後、生成前に必ず以下を実施すること。
  - test_report.mdで全Must機能がPassであることを確認する。
  - Critical/High不具合が0件であることを確認する。
  - ソースコード一式（index.html, css/, js/）が揃っていることを確認する。
  - これらを完了するまでデプロイを開始しない。
- `./assets/deploy_checklist.md` を先に読み、デプロイ前の確認項目を把握する（テンプレートファースト）。
- `./assets/vercel_guide.md` でVercelのデプロイ手順を確認する。

### 2. 生成
- `./questions/deploy_questions.md` を使ってデプロイ設定を確認する。
- 以下を実行する:
  1. GitHubリポジトリ作成（`gh repo create {{app_name}} --private`）※プライベートリポジトリ
  2. ソースコードをコミット・プッシュ
  3. Vercel CLIでデプロイ（`vercel --prod`）
  4. デプロイ完了確認
  5. 公開URLの動作確認
- `./assets/deploy_template.md` に従いdeploy_log.mdを作成する。
- README.mdにデプロイ情報を追記する。

### 3. QC（必須）
- `recommended_subagents` のQC Subagent（`qa-mini-app-qc`）に評価・チェックを委譲する。
- Subagentは最初に `./evaluation/evaluation_criteria.md` をReadし、評価指標に基づいてQCを実施する。
- 公開URLにアクセスして動作確認を実施する。
- 指摘を最小差分で反映する。
- 再度SubagentでQCする。
- これを最大3回まで繰り返し、確定する。
- 指摘に対し「修正した/しない」と理由を成果物に残す。

### 4. バックログ反映
- deploy_log.mdを`app/{app_name}/docs/`配下に保存する。
- 公開URLをユーザーに報告する。
- deploy_done=true を記録。
- 次アクション（追加タスク、運用開始等）を抽出しバックログへ反映する。
- **status-updater**を呼び出してステータスを更新する。

subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - サブエージェントの指摘を反映し、反映結果（修正有無/理由）を成果物に残す

recommended_subagents:
  - qa-mini-app-qc: デプロイ成功確認、公開URL動作、セキュリティ設定を検査
  - deployer: GitHubリポジトリ作成、Vercelデプロイ実行、動作確認

## Resources
- questions: ./questions/deploy_questions.md
- assets: ./assets/deploy_checklist.md
- assets: ./assets/deploy_template.md
- assets: ./assets/vercel_guide.md
- evaluation: ./evaluation/evaluation_criteria.md
- triggers: ./triggers/next_action_triggers.md

## Next Action
- triggers: ./triggers/next_action_triggers.md

起動条件に従い、条件を満たすSkillを自動実行する。
