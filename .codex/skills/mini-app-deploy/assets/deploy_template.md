# {{app_name}} デプロイログ

## 概要
- 作成日: {{today}}
- 実施者:
- ステータス: {{成功/失敗}}

## 1. デプロイ情報

### リポジトリ
- リポジトリ名: {{repo_name}}
- URL: https://github.com/{{username}}/{{repo_name}}
- 公開設定: Public / Private

### GitHub Pages
- 公開URL: https://{{username}}.github.io/{{repo_name}}/
- ソースブランチ: main
- ソースディレクトリ: / (root)

## 2. デプロイ手順

### 実行コマンド

```bash
# リポジトリ作成
gh repo create {{repo_name}} --public --source=. --remote=origin

# または既存リポジトリにpush
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/{{username}}/{{repo_name}}.git
git push -u origin main
```

### GitHub Pages設定
1. Settings → Pages
2. Source: Deploy from a branch
3. Branch: main, / (root)
4. Save

## 3. 確認結果

### デプロイステータス
- [ ] リポジトリ作成: 成功/失敗
- [ ] コードpush: 成功/失敗
- [ ] GitHub Pages設定: 成功/失敗
- [ ] Actions完了: 成功/失敗

### 動作確認
- [ ] 公開URLアクセス: 成功/失敗
- [ ] 全機能動作: 成功/失敗
- [ ] レスポンシブ: 成功/失敗

## 4. トラブルシューティング

### 発生した問題
| 問題 | 原因 | 対処 |
|------|------|------|
| {{問題}} | {{原因}} | {{対処}} |

## 5. 次のステップ

- [ ] ユーザーへの報告
- [ ] ドメイン設定（カスタムドメインの場合）
- [ ] アクセス解析設定（必要な場合）

## 変更履歴

| 日付 | 変更者 | 変更内容 |
|------|--------|----------|
| {{today}} | - | 初回デプロイ |
