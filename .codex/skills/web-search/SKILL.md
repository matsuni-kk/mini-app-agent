---
name: web-search
description: "Web検索（複数観点・複数クエリ）を実施し、出典URLと不確実性を明記した検索結果レポートを作成する。Web検索は必ず `web-search` Subagentへ委譲して実施する。"
---

# Web Search Workflow

## Instructions
1. Preflight（推測しない）:
   - 調査テーマ、目的、想定読者、調査範囲（含む/除外）、期限を確定する。不明なら質問する。
   - 既知URLがあれば先に列挙する。
   - 本Skillのテンプレート `./assets/web_search_report_template.md` を先に読み、章立てを崩さない。
2. Web検索（必須の委譲）:
   - Web検索を行う場合は、必ず `.claude/agents/web-search.md`（Subagent: `web-search`）へ委譲する。
   - Subagentの出力を材料として、テンプレに沿って要点・出典・不確実性・未参照一覧・次アクションを整理して提出する。
3. QC（必須）:
   - `qa-skill-qc` に評価・チェックを委譲し、最小差分で反映する。

subagent_policy:
  - Web検索は必ずサブエージェントへ委譲する
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する

recommended_subagents:
  - web-search: Web検索の実行（検索/本文確認/出典整理）
  - qa-skill-qc: evaluation_criteria.mdに基づきQC

## Resources
- questions: ./questions/web_search_questions.md
- assets: ./assets/web_search_report_template.md
- evaluation: ./evaluation/evaluation_criteria.md
- triggers: ./triggers/next_action_triggers.md

## Subagent Execution
- サブエージェント: `.claude/agents/web-search.md`
- ルール: Web検索を行う場合は必ず使用する
- 入力: 調査テーマ、目的、想定読者、既知URL、調査観点、除外条件
- 出力: Web検索レポート（出典URL/発行元/日付、不確実性、未参照一覧、次アクション）

## Next Action
- triggers: ./triggers/next_action_triggers.md
