# Skill Distribution 評価ガイド

## 評価構造

本評価体系は **Most/More** 構造を採用しています。

- **Most（必須項目）**: Pass/Fail判定。いずれかがFailの場合、評価全体がFailとなります。
- **More（採点項目）**: 100点満点でスコアリング。品質の程度を測定します。

## 判定基準

| 結果 | 条件 |
|------|------|
| **Pass** | 全Most項目がPass かつ Moreスコア80点以上 |
| **Conditional Pass** | 全Most項目がPass かつ Moreスコア60-79点 |
| **Fail** | Most項目にFailあり または Moreスコア60点未満 |

## 許容例外

- 配布先リポジトリが存在しない場合（削除済み等）はスキップ扱い
- `.claude`ディレクトリが存在しないリポジトリは対象外
- `new_only`モードでの既存フォルダスキップは正常動作

## QC報告フォーマット

```
### QC結果: [Pass/Conditional Pass/Fail]
Moreスコア: [XX]/100

#### Most（必須項目）
- [ ] 配布完了: [Pass/Fail]
- [ ] ファイル整合性: [Pass/Fail]
- [ ] エラーなし: [Pass/Fail]
- [ ] 除外適用: [Pass/Fail]

#### More（採点項目）
- 配布成功率: [XX]/30
- ファイル完全性: [XX]/25
- モード適用: [XX]/25
- レポート品質: [XX]/20
- エラーハンドリング: [XX]/20

#### 指摘事項
1. [指摘内容]

#### 推奨修正
1. [修正提案]
```

## 検証手順

### 1. 配布先確認

```bash
# 配布先リポジトリ数を確認
find /Users/matuni__/Desktop -path "*/.opencode/skills/{skill-name}" -type d | wc -l
```

### 2. ファイル整合性確認

```bash
# 配布元のファイル数
find /Users/matuni__/Desktop/browser-controller-agent/.opencode/skills/{skill-name} -type f | wc -l

# 配布先のファイル数（サンプル）
find /Users/matuni__/Desktop/{repo}/.opencode/skills/{skill-name} -type f | wc -l
```

### 3. SKILL.md存在確認

```bash
# 全配布先でSKILL.mdが存在するか
find /Users/matuni__/Desktop -path "*/.opencode/skills/{skill-name}/SKILL.md" -type f | wc -l
```

## 関連ファイル

- [Most（必須項目）](./most_criteria.md)
- [More（採点項目）](./more_criteria.md)
