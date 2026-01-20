# Mini App Deploy 評価指標

## 必須チェック項目

### 構造チェック（Pass/Fail）

| 項目 | 基準 | 重要度 |
|------|------|--------|
| リポジトリ作成 | GitHubプライベートリポジトリが作成されている | Critical |
| コードpush | 全ソースコードがpushされている | Critical |
| Vercelデプロイ | Vercelでデプロイが成功している | Critical |
| 公開URL動作 | 公開URLでアプリが正常動作する | Critical |
| deploy_log作成 | デプロイログが記録されている | High |

### 内容チェック（スコアリング）

| 観点 | 評価基準 | 配点 |
|------|----------|------|
| 完全性 | 全ファイルがデプロイされ、機能が動作する | 30 |
| 動作確認 | 公開URLで全Must機能がテスト時と同様に動作する | 30 |
| ドキュメント | deploy_log.md, README.mdが適切に更新されている | 20 |
| セキュリティ | 機密情報が含まれていない、HTTPS有効、リポジトリがPrivate | 20 |

### 許容例外

- カスタムドメイン未設定（必須ではない）
- README.md未更新（軽微）

## 採点基準

- **Pass**: 全Criticalチェック項目がPass かつ スコア80点以上
- **Conditional Pass**: 全Criticalチェック項目がPass かつ スコア60-79点
- **Fail**: CriticalチェックにFailあり または スコア60点未満

## QC報告フォーマット

```
### QC結果: [Pass/Conditional Pass/Fail]
スコア: [XX]/100

#### 構造チェック
- [ ] リポジトリ作成（Private）: [Pass/Fail]
- [ ] コードpush: [Pass/Fail]
- [ ] Vercelデプロイ: [Pass/Fail]
- [ ] 公開URL動作: [Pass/Fail]
- [ ] deploy_log作成: [Pass/Fail]

#### 内容チェック
- 完全性: [XX]/30
- 動作確認: [XX]/30
- ドキュメント: [XX]/20
- セキュリティ: [XX]/20

#### 指摘事項
1. [指摘内容]

#### 推奨修正
1. [修正提案]
```

## 公開URL動作確認チェックリスト

- [ ] 公開URLにアクセスできる
- [ ] 全Must機能が動作する
- [ ] CSSが正しく適用されている
- [ ] JavaScriptが正常動作する
- [ ] 画像・アセットが表示される
- [ ] レスポンシブが機能する（対応の場合）
- [ ] コンソールにエラーが出ない
