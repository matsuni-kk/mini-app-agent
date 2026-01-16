# GitHub Pages デプロイガイド

## 1. 前提条件

### 必要なもの
- GitHubアカウント
- gh CLI（GitHub CLI）インストール済み
- git インストール済み

### 認証確認
```bash
# gh CLIの認証状態を確認
gh auth status

# 未認証の場合
gh auth login
```

## 2. デプロイ方法

### 方法A: gh CLIで新規リポジトリ作成 + push（推奨）

```bash
# プロジェクトディレクトリに移動
cd {{app_name}}

# リポジトリ作成とpushを一度に実行
gh repo create {{repo_name}} --public --source=. --remote=origin --push

# または対話形式で
gh repo create
```

### 方法B: 手動でリポジトリ作成 + push

```bash
# 1. GitHubでリポジトリを作成（Web UI or gh CLI）
gh repo create {{repo_name}} --public

# 2. ローカルでgit初期化
cd {{app_name}}
git init

# 3. ファイルをステージング・コミット
git add .
git commit -m "Initial commit"

# 4. リモート追加・push
git branch -M main
git remote add origin https://github.com/{{username}}/{{repo_name}}.git
git push -u origin main
```

## 3. GitHub Pages設定

### Web UIで設定

1. リポジトリページを開く
2. **Settings** タブをクリック
3. 左メニューから **Pages** を選択
4. **Source** で以下を設定:
   - **Deploy from a branch** を選択
   - **Branch**: `main`
   - **Folder**: `/ (root)`
5. **Save** をクリック

### gh CLIで設定（対応している場合）

```bash
# ページ設定を有効化
gh api -X PUT repos/{{username}}/{{repo_name}}/pages \
  -f source='{"branch":"main","path":"/"}'
```

## 4. デプロイ確認

### Actions確認
```bash
# デプロイワークフローの状態を確認
gh run list --repo {{username}}/{{repo_name}}

# 最新のrunの詳細を確認
gh run view --repo {{username}}/{{repo_name}}
```

### 公開URL確認
- 公開URL: `https://{{username}}.github.io/{{repo_name}}/`
- 反映まで数分かかる場合あり

## 5. よくある問題と対処

### 404エラー
- **原因**: index.htmlがルートにない
- **対処**: index.htmlをリポジトリルートに配置

### CSS/JSが読み込まれない
- **原因**: 絶対パスを使用している
- **対処**: 相対パス（`./css/style.css`）に修正

### 画像が表示されない
- **原因**: パスが間違っている or ファイルがない
- **対処**: パスを確認し、ファイルをコミット

### Actions失敗
- **原因**: 権限設定の問題
- **対処**: Settings → Actions → General で権限を確認

## 6. 更新デプロイ

```bash
# 変更をコミット
git add .
git commit -m "Update: {{変更内容}}"

# push（自動でPages更新）
git push
```

## 7. カスタムドメイン（オプション）

### 設定手順
1. Settings → Pages → Custom domain
2. ドメインを入力
3. DNSでCNAMEレコードを設定
4. Enforce HTTPS を有効化

### DNSレコード
```
Type: CNAME
Name: www（または@）
Value: {{username}}.github.io
```
