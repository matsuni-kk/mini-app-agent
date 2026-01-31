# X Automation Template

## 概要
- 作成日: {{today}}
- 作成者:
- ステータス: Draft

## 実行結果

### 実行日時
- 日付: {{meta.timestamp}}

### 使用したコマンド
```bash
{{command}}
```

### 実行環境
- Chromeバージョン: {{chrome_version}}
- OS: {{os_version}}
- Xログイン状態: {{x_login_status}}

## 結果

### ユーザー抽出
- 実行コマンド: `{{x_users_command}}`
- ユーザー数: {{user_count}}
- 出力先: {{user_list_output}}

### 投稿下書き
- 実行コマンド: `{{x_draft_command}}`
- 下書きテキスト: `{{draft_text}}`
- テキスト長: {{draft_length}} 文字

### 新着DMリスト
- 実行コマンド: `{{x_dms_command}}`
- DM数: {{dm_count}}
- 未読数: {{unread_count}}
- 出力先: {{dm_list_output}}

### 過去投稿収集
- 実行コマンド: `{{x_posts_command}}`
- 対象ユーザー: `{{target_users}}`
- 収集件数: {{collected_count}} / {{max_count}}
- 出力先: `{{posts_md_output}}`

## ホームタイムライン取得
- 実行コマンド: `{{x_home_command}}`
- 収集件数: `{{home_count}} / {{max_count}}`
- 出力先: `{{home_md_output}}`

## 出力ファイル一覧
- `x_<username>_posts.md`
- `x_home_timeline.md`

## フィルタ
- like/repost/bookmark/本文/作者 で絞り込む場合は `--min-likes/--min-reposts/--min-bookmarks/--query/--author` を使用

## 備考
- 収集した投稿には、通常投稿・リプライ・リポストが含まれます
- Xのアルゴリズムにより、収集順序は動的に変化します
- ホームタイムラインは「For you」「Following」タブにより結果が異なります

## 変更履歴

| 日付 | 変更者 | 変更内容 |
|------|--------|----------|
| {{today}} | - | 初版作成 |
