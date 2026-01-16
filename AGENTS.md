# Mini App Agent - Agents Reference

## Subagents

### qa-mini-app-qc
- **パス**: `.claude/agents/qa-mini-app-qc.md`
- **用途**: ミニアプリ開発の全工程における品質保証（QC）
- **対応Skills**: 全Skills（requirements, design, build, test, deploy）
- **評価基準**: 各Skillの `evaluation/evaluation_criteria.md`

## Task Tool Subagent Types

| Type | 用途 |
|------|------|
| qa-mini-app-qc | 成果物の品質チェック |

## Subagent Policy

```yaml
subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - サブエージェントの指摘を反映し、反映結果（修正有無/理由）を成果物に残す
```

## QC判定基準

| 判定 | 条件 |
|------|------|
| Pass | 全Criticalチェック項目がPass かつ スコア80点以上 |
| Conditional Pass | 全Criticalチェック項目がPass かつ スコア60-79点 |
| Fail | CriticalチェックにFailあり または スコア60点未満 |

## Skills → Subagent マッピング

| Skill | recommended_subagents | QC観点 |
|-------|----------------------|--------|
| mini-app-requirements | qa-mini-app-qc | 要件の完全性、曖昧表現排除、実現可能性 |
| mini-app-design | qa-mini-app-qc | 要件整合性、UI/UXベストプラクティス、実装可能性 |
| mini-app-build | qa-mini-app-qc | コード品質、設計整合性、GitHub Pages互換性 |
| mini-app-test | qa-mini-app-qc | テストカバレッジ、テストケース品質、結果妥当性 |
| mini-app-deploy | qa-mini-app-qc | デプロイ成功確認、公開URL動作、セキュリティ |
