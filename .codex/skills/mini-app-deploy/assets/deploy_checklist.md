# Deploy チェックリスト

## Phase 1: デプロイ前確認

### テスト結果確認
- [ ] test_report.mdの総合判定がPassである
- [ ] 全Must機能がPassである
- [ ] Critical不具合が0件である
- [ ] High不具合が0件である（または許容済み）

### ファイル確認
- [ ] index.htmlがルートに存在する
- [ ] css/style.cssが存在する
- [ ] js/app.jsが存在する
- [ ] 全てのパスが相対パスである
- [ ] 外部リソースはCDN経由またはローカルに存在する

### 環境確認
- [ ] GitHubアカウントにログイン済み
- [ ] gh CLIが認証済み（`gh auth status`）
- [ ] Vercel CLIがインストール済み（`vercel --version`）
- [ ] Vercel CLIが認証済み（`vercel whoami`）
- [ ] リポジトリ名が決定している

## Phase 2: デプロイ実行

### リポジトリ作成
- [ ] `gh repo create` でプライベートリポジトリ作成
- [ ] 公開設定がPrivateであることを確認

### コード push
- [ ] `git init` でローカルリポジトリ初期化
- [ ] `git add .` で全ファイルをステージング
- [ ] `git commit` で初回コミット
- [ ] `git push` でリモートにpush

### Vercelデプロイ
- [ ] `vercel` で初回デプロイ（プレビュー）
- [ ] `vercel --prod` で本番デプロイ
- [ ] プロジェクト設定を確認

## Phase 3: デプロイ後確認

### 動作確認
- [ ] Vercelダッシュボードでデプロイ成功を確認
- [ ] 公開URL（https://{{project}}.vercel.app）にアクセス可能
- [ ] 全Must機能が本番環境で動作する
- [ ] レスポンシブ表示が正常

### 記録
- [ ] deploy_log.mdに記録
- [ ] README.mdにデプロイ情報を追記
- [ ] ユーザーに公開URLを報告

## 必須完了条件
**以下が完了するまでデプロイ完了としない：**
- 公開URLで全機能が正常動作する
- deploy_log.mdが作成されている
- ユーザーに公開URLを報告済み
