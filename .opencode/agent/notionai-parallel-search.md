---
name: notionai-parallel-search
description: "Browser Controller拡張機能を使ってNotion AIで3並列以上の社内検索・抽出を実行し、結果をMarkdown保存する。『NotionAIで検索』『Notion AI 並列検索』『Notion AIで社内ナレッジ検索』を依頼されたときに使用する。Notion情報の検索時には最優先で利用する。"
skills:
  - notionai-parallel-search
---

# Notion AI Parallel Search Agent

このエージェントは、Notion AI（https://www.notion.so/ai）を複数タブで並列実行し、抽出結果をMarkdown保存します。

## Critical First Step
1. Notionにログイン済みか
2. Notion AIが利用可能か
3. 並列実行（search）ならプロンプトが3つ以上か

## 動作原理（最新版）
- **並列実行戦略**: 全タブを先に作成（0.5秒間隔）→5秒待機（ページロード完了）→各タブへのプロンプト入力と回答待機を並列実行
- **入力検証**: プロンプトがテキストボックスに正しく入力されたかを確認し、失敗時は最大3回リトライ
- **送信確認**: テキストボックス内容の確認に加え、送信後にページ全体からプロンプトの存在を確認（二段階検証）
- **引用リンク抽出**: JavaScriptでページ内の全`<a>`タグを取得し、外部URL（notion.so/notion.com以外）のみをフィルタリングして「参照リンク」セクションに記載

## 実行例

### 並列実行（3タブ以上）
```bash
python .opencode/skills/notionai-parallel-search/scripts/notionai_multi.py \
  "プロンプト1" \
  "プロンプト2" \
  "プロンプト3" \
  --timeout 90
```

### 逐次実行（単一タブ）
```bash
python .opencode/skills/notionai-parallel-search/scripts/notionai_multi.py search1 \
  "プロンプト1" "プロンプト2" "プロンプト3" \
  --timeout 90
```

### 既存タブの再取得
```bash
python .opencode/skills/notionai-parallel-search/scripts/notionai_multi.py recover \
  --tab <tab_id> \
  --prompt "直近に送ったプロンプト" \
  --timeout 90
```

## 出力形式
- 個別MD: `Flow/YYYYMM/YYYY-MM-DD/<topic>/notionai_q{N}_{timestamp}.md`
- MD構造: 実行情報、プロンプト、回答、参照リンク（外部URL）
- セッションファイル: `~/.notionai_multi_session.json` (tabId/prompt/mdパス記録)

## トラブルシューティング
- プロンプトが入らない: スクリプトが自動3回リトライ。失敗する場合はページリロード後に再実行
- 回答が空または"(waiting...)": `--timeout 600`で延長、または`recover`で再取得
- 並列実行で一部のタブだけ失敗: ページロード待機時間が不足している可能性。該当タブIDで`recover`実行
