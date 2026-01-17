---
name: setup-github
description: "GitHub CLIのインストール・認証・設定を行う。「GitHub設定」「gh設定」「GitHubセットアップ」を依頼されたときに使用する。"
---

# Setup GitHub Workflow

GitHub CLIのインストールから認証までを対話的にサポートする。

## Instructions

### 1. 環境チェック
以下のコマンドで現在の状態を確認する:

```bash
# gh CLIがインストールされているか
gh --version

# 認証状態の確認
gh auth status
```

### 2. インストール（未インストールの場合）

#### macOS
```bash
# Homebrewでインストール
brew install gh
```

#### Windows
```bash
# wingetでインストール
winget install --id GitHub.cli

# またはscoopで
scoop install gh
```

#### Linux (Debian/Ubuntu)
```bash
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh
```

### 3. 認証

```bash
# ブラウザ認証（推奨）
gh auth login

# 対話形式で以下を選択:
# 1. GitHub.com（エンタープライズでなければこちら）
# 2. HTTPS（推奨）
# 3. Login with a web browser（推奨）
```

認証時にブラウザが開き、8桁のコードを入力する。

### 4. 認証確認

```bash
# 認証状態を確認
gh auth status

# 期待される出力:
# ✓ Logged in to github.com as USERNAME
```

### 5. 推奨設定（オプション）

```bash
# デフォルトエディタを設定
gh config set editor "code --wait"  # VSCode
gh config set editor "vim"          # Vim

# git プロトコルをHTTPSに設定
gh config set git_protocol https
```

## トラブルシューティング

### 認証エラー
```bash
# 再認証
gh auth logout
gh auth login
```

### トークンの権限不足
```bash
# 追加スコープで再認証
gh auth login --scopes "repo,read:org"
```

### SSHを使いたい場合
```bash
gh auth login -p ssh
```

## 確認コマンド

```bash
# 全体の状態確認
gh auth status
gh config list

# テスト: リポジトリ一覧取得
gh repo list --limit 5
```

## 成功条件
- `gh auth status` で「Logged in」と表示される
- `gh repo list` でリポジトリ一覧が取得できる
