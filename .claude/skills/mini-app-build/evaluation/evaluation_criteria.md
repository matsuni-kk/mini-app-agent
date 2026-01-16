# Mini App Build 評価指標

## 必須チェック項目

### 構造チェック（Pass/Fail）

| 項目 | 基準 | 重要度 |
|------|------|--------|
| ファイル構成 | design.mdで定義されたファイル構成と一致する | Critical |
| 機能実装 | requirements.mdのMust機能が全て実装されている | Critical |
| GitHub Pages互換 | 相対パス使用、静的ファイルのみ、index.htmlがルートにある | Critical |
| HTML妥当性 | セマンティックHTML、DOCTYPE宣言、meta viewport | High |
| コーディング規約 | coding_standards.mdに準拠している | High |

### 内容チェック（スコアリング）

| 観点 | 評価基準 | 配点 |
|------|----------|------|
| 機能完全性 | 全Must機能が正常動作する | 30 |
| コード品質 | 命名規則、コメント、構造化が適切 | 25 |
| 設計整合性 | design.mdの仕様通りに実装されている | 25 |
| 保守性 | 可読性が高く、変更が容易なコード | 20 |

### 許容例外

- Should/Could機能が未実装（優先度により）
- 画像最適化が未実施（後工程で対応可）

## 採点基準

- **Pass**: 全Criticalチェック項目がPass かつ スコア80点以上
- **Conditional Pass**: 全Criticalチェック項目がPass かつ スコア60-79点
- **Fail**: CriticalチェックにFailあり または スコア60点未満

## QC報告フォーマット

```
### QC結果: [Pass/Conditional Pass/Fail]
スコア: [XX]/100

#### 構造チェック
- [ ] ファイル構成: [Pass/Fail]
- [ ] 機能実装: [Pass/Fail]
- [ ] GitHub Pages互換: [Pass/Fail]
- [ ] HTML妥当性: [Pass/Fail]
- [ ] コーディング規約: [Pass/Fail]

#### 内容チェック
- 機能完全性: [XX]/30
- コード品質: [XX]/25
- 設計整合性: [XX]/25
- 保守性: [XX]/20

#### 指摘事項
1. [指摘内容]

#### 推奨修正
1. [修正提案]
```

## 動作確認チェックリスト

- [ ] ローカルでindex.htmlを開いて正常表示される
- [ ] 全Must機能が動作する
- [ ] コンソールにエラーが出ない
- [ ] レスポンシブ対応が機能する（対応の場合）
