# Kimi Parallel Research Skill

Browser Controller拡張機能を使ってKimi（kimi.com）で3並列以上のウェブ検索・ブレスト・情報収集を実行する。

## トリガー

- 「Kimi検索」「Kimi並列検索」「Kimiで調べて」「Kimiでブレスト」「Kimiリサーチ」

## クエリ設計ルール

1. フルコンテキストで渡す: 各クエリは独立コンテキストとして成立させる。背景情報・前提・制約・目的を各クエリ本文に含める。Kimiは他のタブの内容を知らないため、省略禁止。
2. 関連ファイルは添付: 関連する情報がファイルにある場合は添付する（最大10ファイル）。ファイルを読んで口頭で伝えるのではなく、ファイル自体を渡す。
3. 目的と検索対象を明記: 各クエリの冒頭に「何の目的で」「何を検索/議論するのか」を明示する。
4. 背景情報は徹底的に詳しく: 「なぜこの質問をするのか」「どういう文脈でこの情報が必要なのか」を省略せずに書く。
5. 極めて詳細に: クエリ自体を詳細に設計し、回答も詳細に返してもらうよう指示する。曖昧な表現や省略は禁止。
6. 同一セッションで継続: 複数の追加質問は新規チャットを立てず、同じ会話セッションにchatで追加する。前回の回答が完了していることを確認してから次の質問を送信する。

### クエリ設計の構造（5W1H + 背景）
```
【背景・文脈】
- 現在の状況: □□という状態である
- 経緯: ××があったため、△△を検討している
- なぜこの質問をするのか: 〇〇を決定/解決するために必要な情報である

【目的】〇〇のために△△を調査する

【Who】誰が関係するか（対象者、ステークホルダー）
【What】具体的に知りたいこと
【When】時期・期間・タイミングの制約
【Where】地域・市場・対象範囲
【Why】なぜそれが重要か、どう活用するか
【How】どのようなアプローチ・手法・形式で知りたいか

【制約】あれば記載（日本語のみ、最新情報のみ、信頼性高いソースのみ等）
【期待する出力形式】箇条書き/表形式/比較表/詳細説明 等

【回答の詳細度】
- 可能な限り詳細かつ網羅的に回答してください
- 具体例、数値、事例を豊富に含めてください
- 表面的な説明ではなく、深掘りした分析を提供してください
- 結論だけでなく、その根拠と理由も詳しく説明してください
```

## 機能

- 並列質問送信（3並列以上推奨、最大10並列）
- モデル選択（K2.5 Thinking等）
- 確実な回答取得（本文のみ、Thinking内容は分離）
- Markdown自動保存（Flow/YYYYMM/YYYY-MM-DD/topic/）
- タブ管理
- マルチターン対話（chat）
- 既存タブからの再取得（recover）

## 使用方法

### 1. 並列検索（基本）

```bash
python3 .github/skills/kimi-parallel-research/scripts/kimi_multi.py \
  "質問1" "質問2" "質問3"
```

### 2. モデル指定

```bash
python3 .github/skills/kimi-parallel-research/scripts/kimi_multi.py \
  "質問1" "質問2" "質問3" \
  --model "K2.5 Thinking"
```

### 3. タブ一覧確認

```bash
python3 .github/skills/kimi-parallel-research/scripts/kimi_multi.py tabs
```

### 4. モデル一覧確認

```bash
python3 .github/skills/kimi-parallel-research/scripts/kimi_multi.py models --tab <tab_id>
```

### 5. マルチターン対話（既存セッションで追加質問）

```bash
python3 .github/skills/kimi-parallel-research/scripts/kimi_multi.py chat "追加の質問"
```

### 6. 再取得（既存タブから回答を取得）

```bash
python3 .github/skills/kimi-parallel-research/scripts/kimi_multi.py recover
```

## 出力

- 各質問ごとに個別のMarkdownファイルを生成
- 保存先: `Flow/YYYYMM/YYYY-MM-DD/<topic>/kimi_q<N>_<timestamp>.md`
- マルチターン時は同一ファイルに追記

## 前提条件

1. Browser Controller拡張機能がインストール・有効化されていること
2. ブリッジサーバーが起動していること（`ws://localhost:9224`）
3. Kimiにログイン済みのブラウザセッションがあること

## 拡張機能コマンド

| コマンド | 説明 |
|---------|------|
| `kimi_send_message` | メッセージを送信 |
| `kimi_get_response` | 応答を取得 |
| `kimi_is_generating` | 生成中か確認 |
| `kimi_get_models` | モデル一覧取得 |
| `kimi_select_model` | モデル選択 |
| `kimi_new_chat` | 新規チャット開始 |
| `kimi_get_full_conversation` | 会話全体取得 |

## Resources

- scripts: ./scripts/kimi_multi.py
- extension: Stock/chrome_extensions/browser_controller/extension/handlers/kimi.js

## Next Action

- 検索結果を使って分析・レポート作成
- 追加質問でマルチターン深掘り
- 結果をNotionやドキュメントに整理
