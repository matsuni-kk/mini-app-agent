---
name: mini-app-build
description: "ミニアプリのコード実装を行う。「実装」「コーディング」「ビルド」を依頼されたときに使用する。"
---

# Mini App Build Workflow

設計書に基づきHTML/CSS/JavaScriptを実装する。主成果物はindex.html・style.css・app.js等のソースコード。

## Instructions

### 1. Preflight（事前確認）
- ドキュメント精査原則（Preflight必須）：テンプレート確認後、生成前に必ず以下を実施すること。
  - requirements.mdとdesign.mdを全て読み込む。
  - 画面設計・コンポーネント仕様・ファイル構成を把握する。
  - 既存コードがあれば確認し、差分のみ実装する。
  - これらを完了するまで生成を開始しない。
- `./assets/build_template.md` を先に読み、HTML/CSS/JSの基本構造を確認する（テンプレートファースト）。
- `./assets/coding_standards.md` でコーディング規約を確認する。

### 2. 生成
- `./questions/build_questions.md` を使って実装方針を確認する。
- 以下を実装する:
  1. index.html（セマンティックHTML、アクセシビリティ考慮）
  2. css/style.css（BEM命名、モバイルファースト、CSS変数）
  3. js/app.js（ES6+、エラーハンドリング）
  4. その他必要なアセット
- GitHub Pages対応を確認:
  - 相対パスのみ使用
  - 静的ファイルのみ（サーバーサイド処理なし）
  - index.htmlをルートに配置

### 3. QC（必須）
- `recommended_subagents` のQC Subagent（`qa-mini-app-qc`）に評価・チェックを委譲する。
- Subagentは最初に `./evaluation/evaluation_criteria.md` をReadし、評価指標に基づいてQCを実施する。
- 指摘を最小差分で反映する。
- 再度SubagentでQCする。
- これを最大3回まで繰り返し、確定する。
- 指摘に対し「修正した/しない」と理由をコメントに残す。

### 4. バックログ反映
- ソースコードを`app/{app_name}/`配下に保存する。
- 次アクション（追加タスク、レビュー依頼等）を抽出しバックログへ反映する。
- build_done=true を記録してから次工程へ進む。
- **status-updater**を呼び出してステータスを更新する。

subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - サブエージェントの指摘を反映し、反映結果（修正有無/理由）を成果物に残す

recommended_subagents:
  - qa-mini-app-qc: コード品質、設計整合性、GitHub Pages互換性を検査

## Resources
- questions: ./questions/build_questions.md
- assets: ./assets/build_template.md
- assets: ./assets/coding_standards.md
- evaluation: ./evaluation/evaluation_criteria.md
- triggers: ./triggers/next_action_triggers.md

## Next Action
- triggers: ./triggers/next_action_triggers.md

起動条件に従い、条件を満たすSkillを自動実行する。
