---
name: mini-app-design
description: "ミニアプリのUI/UX設計を実施する。「デザイン」「画面設計」「UI設計」を依頼されたときに使用する。"
---

# Mini App Design Workflow

要件定義書に基づきUI/UX・技術設計を行う。主成果物はdesign.md（画面構成・コンポーネント設計・技術スタック）。

## Instructions

### 1. Preflight（事前確認）
- ドキュメント精査原則（Preflight必須）：テンプレート確認後、生成前に必ず以下を実施すること。
  - requirements.mdを全て読み込み、機能要件・非機能要件を把握する。
  - Flow/Stock配下の関連資料（参考デザイン・UIライブラリ等）を検索・確認する。
  - 確認できなかった資料は「未参照一覧」として成果物に明記する。
  - これらを完了するまで生成を開始しない。
- `./assets/design_template.md` を先に読み、章立て・必須項目・項目順序を確認する（テンプレートファースト）。
- `./assets/design_system_principles.md` を参照し、UIデザインの原則を適用する（デザインシステム準拠）。

### 2. 生成
- `./questions/design_questions.md` を使って必要情報を収集する。
- 以下を明確化する:
  1. 画面構成・ワイヤーフレーム（ASCII表現）
  2. コンポーネント一覧と仕様
  3. カラースキーム・タイポグラフィ
  4. レスポンシブ対応方針
  5. ファイル構成（HTML/CSS/JS）
- テンプレート構造を崩さずにdesign.mdを作成する。
- 元資料にない項目は省略せず「未記載」または「不明」と明記する。

### 3. QC（必須）
- `recommended_subagents` のQC Subagent（`qa-mini-app-qc`）に評価・チェックを委譲する。
- Subagentは最初に `./evaluation/evaluation_criteria.md` をReadし、評価指標に基づいてQCを実施する。
- 指摘を最小差分で反映する（テンプレの章立ては崩さない）。
- 再度SubagentでQCする。
- これを最大3回まで繰り返し、確定する。
- 指摘に対し「修正した/しない」と理由を成果物に残す。

### 4. バックログ反映
- design.mdを`app/{app_name}/docs/`配下に保存する。
- 次アクション（追加タスク、レビュー依頼等）を抽出しバックログへ反映する。
- design_done=true を記録してから次工程へ進む。
- **status-updater**を呼び出してステータスを更新する。

subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - サブエージェントの指摘を反映し、反映結果（修正有無/理由）を成果物に残す

recommended_subagents:
  - qa-mini-app-qc: 要件との整合性、UI/UXベストプラクティス、実装可能性を検査
  - web-researcher: UIライブラリ、デザインパターン、アクセシビリティ基準の調査

## Resources
- questions: ./questions/design_questions.md
- assets: ./assets/design_template.md
- design_system: ./assets/design_system_principles.md
- evaluation: ./evaluation/evaluation_criteria.md
- triggers: ./triggers/next_action_triggers.md

## Next Action
- triggers: ./triggers/next_action_triggers.md

起動条件に従い、条件を満たすSkillを自動実行する。
