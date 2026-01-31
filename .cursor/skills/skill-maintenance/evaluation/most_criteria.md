# Most Criteria（必須修正）

## 構造チェック（Pass/Fail）

致命的欠損。いずれかがFailの場合、成果物確定不可。

| 項目 | 基準 | 判定 |
|------|------|------|
| テンプレート準拠 | 必須セクション（frontmatter/Instructions/Resources/Next Action）が存在する | Pass/Fail |
| 必須セクション維持 | 既存Skillの必須セクション区切りが崩れていない | Pass/Fail |
| 機能欠損なし | 既存機能・ロジック・定義が欠損していない | Pass/Fail |

## 内容チェック（Pass/Fail）

変更・保守の正確性。元Skillとの整合性。

| 項目 | 基準 | 判定 |
|------|------|------|
| 差分最小性 | 変更が最小差分で行われている（不要な変更がない） | Pass/Fail |
| 整合性 | AGENTS.md/CLAUDE.md/パス辞書との整合が取れている | Pass/Fail |
| 検証手順明示 | 変更後の検証手順・確認方法が明記されている | Pass/Fail |

## 許容不可項目

以下はMust Fix対象。例外なし。

- 必須セクションの欠落（frontmatter/Instructions/Resources/Next Action）
- 既存セクション区切りの崩壊
- 既存機能・ロジック・定義の欠損
- 不要な変更（最小差分違反）
- AGENTS.md/CLAUDE.md/パス辞書との不整合
- 検証手順の未記載
