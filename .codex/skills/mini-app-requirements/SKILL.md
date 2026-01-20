---
name: mini-app-requirements
description: "ミニアプリの要件定義を実施する。「要件定義」「ミニアプリ作成」「アプリ開発」を依頼されたときに使用する。"
---

# Mini App Requirements Workflow

ユーザー要望からミニアプリの要件を定義する。主成果物はrequirements.md（機能要件・非機能要件・成功基準）。

## Instructions

### 1. Preflight（事前確認）
- ドキュメント精査原則（Preflight必須）：テンプレート確認後、生成前に必ず以下を実施すること。
  - ユーザーの要望・目的を全て読み込む。
  - Flow/Stock配下の関連資料（類似アプリ・参考デザイン等）を網羅的に検索・確認する。
  - 確認できなかった資料は「未参照一覧」として成果物に明記する。
  - これらを完了するまで生成を開始しない。
- `./assets/requirements_template.md` を先に読み、章立て・必須項目・項目順序を確認する（テンプレートファースト）。

### 2. 生成
- `./questions/requirements_questions.md` を使って必要情報を収集する。
- 以下を明確化する:
  1. アプリの目的・ゴール
  2. 対象ユーザー（ペルソナ）
  3. 機能要件（Must/Should/Could）
  4. 非機能要件（レスポンシブ、ブラウザ対応等）
  5. 成功基準・KPI
- テンプレート構造を崩さずにrequirements.mdを作成する。
- 元資料にない項目は省略せず「未記載」または「不明」と明記する。

### 3. QC（必須）
- `recommended_subagents` のQC Subagent（`qa-mini-app-qc`）に評価・チェックを委譲する。
- Subagentは最初に `./evaluation/evaluation_criteria.md` をReadし、評価指標に基づいてQCを実施する。
- 指摘を最小差分で反映する（テンプレの章立ては崩さない）。
- 再度SubagentでQCする。
- これを最大3回まで繰り返し、確定する。
- 指摘に対し「修正した/しない」と理由を成果物に残す。

### 4. バックログ反映
- requirements.mdを`app/{app_name}/docs/`配下に保存する。
- 次アクション（追加タスク、レビュー依頼等）を抽出しバックログへ反映する。
- requirements_done=true を記録してから次工程へ進む。
- **status-updater**を呼び出してステータスを更新する。

subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - サブエージェントの指摘を反映し、反映結果（修正有無/理由）を成果物に残す

recommended_subagents:
  - qa-mini-app-qc: 要件の完全性、曖昧表現排除、実現可能性を検査
  - web-researcher: 技術要件の実現可能性、外部サービス仕様の確認

## Resources
- questions: ./questions/requirements_questions.md
- assets: ./assets/requirements_template.md
- evaluation: ./evaluation/evaluation_criteria.md
- triggers: ./triggers/next_action_triggers.md

## Next Action
- triggers: ./triggers/next_action_triggers.md

起動条件に従い、条件を満たすSkillを自動実行する。
