# Vercel デプロイガイド

## 1. 前提条件

### 必要なもの
- GitHubアカウント
- Vercelアカウント（GitHubでサインアップ推奨）
- Vercel CLI（オプション、推奨）
- gh CLI（GitHub CLI）インストール済み

### Vercel CLIインストール
```bash
# npm
npm install -g vercel

# または pnpm
pnpm install -g vercel
```

### 認証確認
```bash
# Vercel CLIの認証
vercel login

# gh CLIの認証状態を確認
gh auth status

# 未認証の場合
gh auth login
```

## 2. デプロイ方法

### 方法A: Vercel CLI（推奨）

```bash
# プロジェクトディレクトリに移動
cd app/{{app_name}}

# 初回デプロイ（対話形式）
vercel

# 本番デプロイ
vercel --prod
```

対話形式での質問：
1. Set up and deploy? → Y
2. Which scope? → 自分のアカウントを選択
3. Link to existing project? → N（新規の場合）
4. Project name? → アプリ名を入力
5. Directory? → ./ （現在のディレクトリ）

### 方法B: GitHubリポジトリ連携

```bash
# 1. GitHubにプライベートリポジトリ作成
gh repo create {{repo_name}} --private --source=. --remote=origin --push

# 2. Vercelダッシュボードでインポート
# https://vercel.com/new にアクセス
# → Import Git Repository
# → GitHubリポジトリを選択
# → Deploy
```

### 方法C: 既存リポジトリにpush後、Vercel連携

```bash
# 1. ローカルでgit初期化
cd app/{{app_name}}
git init

# 2. ファイルをステージング・コミット
git add .
git commit -m "Initial commit"

# 3. GitHubリポジトリ作成・push
gh repo create {{repo_name}} --private --source=. --remote=origin --push

# 4. VercelでGitHubリポジトリをインポート
```

## 3. プロジェクト設定

### 静的サイト設定（HTML/CSS/JS）

Vercelは静的サイトを自動検出するため、特別な設定は不要。

必要に応じて `vercel.json` を作成：

```json
{
  "version": 2,
  "builds": [
    { "src": "**/*", "use": "@vercel/static" }
  ]
}
```

### 出力ディレクトリ指定

プロジェクトルートに `index.html` がない場合：

```json
{
  "outputDirectory": "."
}
```

## 4. デプロイ確認

### CLI確認
```bash
# デプロイ一覧
vercel ls

# 最新デプロイの詳細
vercel inspect <deployment-url>

# ログ確認
vercel logs <deployment-url>
```

### 公開URL
- プレビュー: `https://{{project-name}}-{{hash}}.vercel.app`
- 本番: `https://{{project-name}}.vercel.app`

## 5. よくある問題と対処

### 404エラー
- **原因**: index.htmlがルートにない
- **対処**: index.htmlをプロジェクトルートに配置、または `vercel.json` で出力ディレクトリを指定

### CSS/JSが読み込まれない
- **原因**: パスが間違っている
- **対処**: 相対パス（`./css/style.css`）を使用

### 画像が表示されない
- **原因**: パスが間違っている or ファイルがない
- **対処**: パスを確認し、ファイルをコミット

### デプロイ失敗
- **原因**: ビルドエラー
- **対処**: `vercel logs` でエラー内容を確認

## 6. 更新デプロイ

### CLI経由
```bash
# 変更をコミット（GitHub連携時）
git add .
git commit -m "Update: {{変更内容}}"
git push

# または直接デプロイ
vercel --prod
```

### GitHub連携時
pushするだけで自動デプロイ（プレビュー）。
本番への昇格はVercelダッシュボードまたは `vercel --prod`。

## 7. カスタムドメイン（オプション）

### 設定手順
1. Vercelダッシュボード → Project → Settings → Domains
2. ドメインを追加
3. DNS設定を実施

### DNS設定
```
Type: CNAME
Name: www（またはサブドメイン）
Value: cname.vercel-dns.com

# または Aレコード
Type: A
Name: @
Value: 76.76.21.21
```

## 8. 環境変数（必要な場合）

### CLI設定
```bash
vercel env add VARIABLE_NAME
```

### ダッシュボード設定
Project → Settings → Environment Variables

## 9. プライベートリポジトリからのデプロイ

Vercelは無料プランでもプライベートリポジトリからのデプロイをサポート：

1. GitHubでプライベートリポジトリを作成
2. VercelでGitHubアプリを認証（初回のみ）
3. リポジトリをインポート
4. 自動デプロイ有効

**注意**: サイト自体は公開URLでアクセス可能（コードは非公開）
