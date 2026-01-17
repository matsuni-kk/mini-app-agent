# {{app_name}} デプロイログ

## 概要
- 作成日: {{today}}
- 実施者:
- ステータス: {{成功/失敗}}

## 1. デプロイ情報

### リポジトリ
- リポジトリ名: {{repo_name}}
- URL: https://github.com/{{username}}/{{repo_name}}
- 公開設定: Private

### Vercel
- 公開URL: https://{{project_name}}.vercel.app
- プロジェクト名: {{project_name}}
- 環境: Production

## 2. デプロイ手順

### 実行コマンド

```bash
# GitHubリポジトリ作成（プライベート）
gh repo create {{repo_name}} --private --source=. --remote=origin --push

# Vercelデプロイ
cd app/{{app_name}}
vercel --prod
```

### または既存リポジトリにpush後、Vercel連携

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
gh repo create {{repo_name}} --private --source=. --remote=origin --push

# Vercelダッシュボードからインポート or CLI
vercel --prod
```

## 3. 確認結果

### デプロイステータス
- [ ] リポジトリ作成: 成功/失敗
- [ ] コードpush: 成功/失敗
- [ ] Vercelデプロイ: 成功/失敗

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
- [ ] カスタムドメイン設定（必要な場合）
- [ ] アクセス解析設定（必要な場合）

## 変更履歴

| 日付 | 変更者 | 変更内容 |
|------|--------|----------|
| {{today}} | - | 初回デプロイ |
