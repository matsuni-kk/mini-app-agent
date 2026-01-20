---
name: mini-app-test
description: "ミニアプリのテストを実施する。「テスト」「動作確認」「検証」を依頼されたときに使用する。"
---

# Mini App Test Workflow

実装コードのテストを実施する。主成果物はtest_report.md（テストケース・結果・カバレッジ）。

## Instructions

### 1. Preflight（事前確認）
- ドキュメント精査原則（Preflight必須）：テンプレート確認後、生成前に必ず以下を実施すること。
  - requirements.mdから受け入れ基準を抽出する。
  - design.mdから画面・コンポーネント仕様を確認する。
  - 実装コード（index.html, style.css, app.js）を読み込む。
  - これらを完了するまでテストを開始しない。
- `./assets/test_template.md` を先に読み、テストレポートの構造を確認する（テンプレートファースト）。
- `./assets/test_case_template.md` でテストケース形式を確認する。

### 2. 生成
- `./questions/test_questions.md` を使ってテスト方針を確認する。
- 以下を実施する:
  1. 機能テストケース作成（requirements.mdのMust/Should機能）
  2. UIテスト（レスポンシブ、クロスブラウザ）
  3. エッジケーステスト（異常値、境界値）
  4. アクセシビリティチェック
  5. パフォーマンス確認
- テスト結果をtest_report.mdに記録する。
- 不具合があればbug_list.mdに記録する。

### 3. QC（必須）
- `recommended_subagents` のQC Subagent（`qa-mini-app-qc`）に評価・チェックを委譲する。
- Subagentは最初に `./evaluation/evaluation_criteria.md` をReadし、評価指標に基づいてQCを実施する。
- 指摘を最小差分で反映する（テンプレの章立ては崩さない）。
- 再度SubagentでQCする。
- これを最大3回まで繰り返し、確定する。
- 指摘に対し「修正した/しない」と理由を成果物に残す。

### 4. バックログ反映
- test_report.mdを`app/{app_name}/docs/`配下に保存する。
- 全テストPassなら test_done=true を記録。
- Failがあればmini-app-buildに戻って修正後、再テスト。
- 次アクション（追加タスク、修正依頼等）を抽出しバックログへ反映する。
- **status-updater**を呼び出してステータスを更新する。

subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - サブエージェントの指摘を反映し、反映結果（修正有無/理由）を成果物に残す

recommended_subagents:
  - qa-mini-app-qc: テストカバレッジ、テストケース品質、結果の妥当性を検査

## Resources
- questions: ./questions/test_questions.md
- assets: ./assets/test_template.md
- assets: ./assets/test_case_template.md
- evaluation: ./evaluation/evaluation_criteria.md
- triggers: ./triggers/next_action_triggers.md

## Next Action
- triggers: ./triggers/next_action_triggers.md

起動条件に従い、条件を満たすSkillを自動実行する。
