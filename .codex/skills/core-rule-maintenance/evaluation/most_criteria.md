# Most Criteria（必須修正）- Core Rule Maintenance

## 構造チェック（Pass/Fail）

致命的欠損。いずれかがFailの場合、成果物確定不可。

| 項目 | 基準 | 判定 |
|------|------|------|
| セクション構造維持 | CLAUDE.mdの7セクション構成が崩れていない | Pass/Fail |
| 変数参照整合性 | パス辞書の変数参照が全て解決可能 | Pass/Fail |
| WF索引整合性 | 参照先Skillが全て存在する | Pass/Fail |
| 3環境同期実施 | update_agent_master.pyを実行済み | Pass/Fail |
| Skills/Assets統一 | skills配下（assets/questions/evaluation/triggers/scripts含む）が同期で統一されている | Pass/Fail |
| 循環参照なし | パス辞書/WF索引に循環参照がない | Pass/Fail |
| 最小差分 | 変更は必要最小限に留まっている | Pass/Fail |

## 内容チェック（Pass/Fail）

整合性と正確性。元資料との整合性。

| 項目 | 基準 | 判定 |
|------|------|------|
| 整合性 | 変更内容が既存ルールと矛盾しない | Pass/Fail |
| 完全性 | 影響を受ける関連箇所も更新されている | Pass/Fail |
| 未記載項目の明示 | 不明項目は「未記載」「不明」と明記されている | Pass/Fail |

## 許容不可項目

以下はMust Fix対象。例外なし。

- セクション構造の破壊
- 変数参照の未解決
- 存在しないSkillへの参照
- 3環境同期未実施
- Skills/Assetsの非統一
- 循環参照
- 既存ルールとの矛盾
- 影響範囲の未更新
