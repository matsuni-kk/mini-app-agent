# Most Criteria（必須修正）

## 構造チェック（Pass/Fail）

致命的欠損。いずれかがFailの場合、成果物確定不可。

| 項目 | 基準 | 判定 |
|------|------|------|
| フロントマター準拠 | 必須フィールド（name/description）が存在する | Pass/Fail |
| name形式 | ケバブケース形式である | Pass/Fail |
| skills整合性 | skillsフィールドで指定されたSkillが実在する（省略可） | Pass/Fail |
| 推奨セクション | Expertise Overview/Domain Coverage が存在する | Pass/Fail |

## 内容チェック（Pass/Fail）

Subagentの品質と整合性。

| 項目 | 基準 | 判定 |
|------|------|------|
| 単一責任原則 | 1エージェント1専門領域を守っている | Pass/Fail |
| 論理的一貫性 | 矛盾、飛躍がない | Pass/Fail |
| ハルシネーションなし | 事実誤認がない | Pass/Fail |

## 許容不可項目

以下はMust Fix対象。例外なし。

- フロントマター必須フィールド欠落
- name形式違反（ケバブケースでない）
- 存在しないSkillの参照
- 単一責任原則違反（複数領域を横断）
- 論理的矛盾
- 事実誤認
