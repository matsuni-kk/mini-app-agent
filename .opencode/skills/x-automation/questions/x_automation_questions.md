# X Automation Questions

## 必須入力項目

1. **対象機能**: 実行するX機能を選択してください（カンマ区切り）
   - `x_users`: ユーザー抽出
   - `x_draft`: 投稿下書き作成
   - `x_dms`: 新着DMリスト
   - `x_tweets_to_md`: 過去投稿収集
   - `x_home_to_md`: ホームタイムライン取得

2. **対象ユーザー**: 投稿収集の場合、対象となるユーザー名を入力してください（@handleの形式可）
   - 例: `elonmusk`, `@yugen_matuni`

3. **収集件数**: 投稿収集・タイムライン取得の場合、収集する最大件数を入力してください
   - デフォルト:
     - `x_tweets_to_md`（過去投稿）: 1000
     - `x_home_to_md`（ホーム）: 100
   - 例: `100`, `500`, `2000`

## 任意入力項目

4. **フィルタ（過去投稿収集）**: like/リポスト/ブクマ/本文/作者で絞り込みたい場合
   - `--min-likes <n>`
   - `--min-reposts <n>`
   - `--min-bookmarks <n>`
   - `--query "keyword"`
   - `--author <handle>`（`@`なし推奨）
   - `--no-replies`（リプライ除外）
   - `--no-reposts`（リポスト除外）

5. **タブ指定**: 特定タブで実行する場合、タブIDを入力してください
   - 指定なし: アクティブタブまたは自動判断
   - 例: `123456`

6. **制約・前提**:
   - X（x.com）に手動でログイン済みであること
   - Browser Controller拡張機能がChromeにインストール済みであること

7. **出力先**: 結果ファイルの保存先を指定してください
   - デフォルト: `Flow/YYYYMM/YYYY-MM-DD/x/`
   - カスタムパス: 現状未対応（必要なら機能追加）

## トラブルシューティング

### エラー: "Unknown command: x_*"
- **原因**: 拡張機能が古いService Workerを使用している
- **対処**: `chrome://extensions/` で拡張機能をReloadする

### エラー: "Cannot access contents of page. Extension manifest must request permission..."
- **原因**: ページに対する権限が不足している
- **対処**:
  1. `chrome://extensions/` を開く
  2. Browser Controller の詳細を開く
 3. 「サイトへのアクセス」を「すべてのサイト」または `https://x.com/*` に設定する
