---
name: x-automation
description: "Browser Controller拡張機能を使ってX（x.com）を操作する自動化スキル。ユーザー抽出・過去投稿収集・投稿下書き作成・新着DMリスト化・ホームタイムライン取得などを実行。「X操作」「x.com自動化」「タイムライン収集」「投稿アーカイブ」を依頼されたときに使用する。"
---

# X Automation Workflow

## Overview
Browser Controller Chrome拡張機能を使用し、X（x.com）を自動操作する。
- ユーザー抽出: ページ上からユーザー名をリスト化
- 過去投稿収集: 指定ユーザーの投稿をスクロール収集しMarkdown化
- 投稿下書き: 投稿入力欄にテキストをセット（投稿はしない）
- 新着DMリスト: 未読/新着メッセージを抽出
- ホームタイムライン: ホーム画面（For you/Following）の投稿を収集
- Grok: Grok（X内のGrok UI）を並列操作して検索/ブレストを実行

## 前提条件
- Python 3.8以上
- Browser Controller Chrome拡張機能がインストール済み
- Xにログイン済みであること（手動ログイン前提）

## Instructions

### 0. Grok（並列リサーチ）
Grokは `grok_multi.py` で操作する（ChatGPT Skillから移行）。

**クエリ設計ルール**:
1. フルコンテキストで渡す: 各クエリは独立コンテキストとして成立させる。背景情報・前提・制約・目的を各クエリ本文に含める。Grokは他のタブの内容を知らないため、省略禁止。
2. 関連ファイルは添付: 関連する情報がファイルにある場合は添付する（最大10ファイル）。ファイルを読んで口頭で伝えるのではなく、ファイル自体を渡す。
3. 目的と検索対象を明記: 各クエリの冒頭に「何の目的で」「何を検索/議論するのか」を明示する。
4. 背景情報は徹底的に詳しく: 「なぜこの質問をするのか」「どういう文脈でこの情報が必要なのか」を省略せずに書く。
5. 極めて詳細に: クエリ自体を詳細に設計し、回答も詳細に返してもらうよう指示する。曖昧な表現や省略は禁止。
6. 同一セッションで継続: 複数の追加質問は新規チャットを立てず、同じ会話セッションにreplyで追加する。前回の回答が完了していることを確認してから次の質問を送信する。

**クエリ設計の構造（5W1H + 背景）**:
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

```bash
# Grok タブ一覧
python .claude/skills/x-automation/scripts/grok_multi.py tabs

# Grok 並列検索（3並列以上推奨）
python .claude/skills/x-automation/scripts/grok_multi.py "Q1" "Q2" "Q3"

# DeepThink / DeepSearch
python .claude/skills/x-automation/scripts/grok_multi.py "Q1" "Q2" "Q3" --deepthink
python .claude/skills/x-automation/scripts/grok_multi.py "Q1" "Q2" "Q3" --deepsearch

# ファイル添付
python .claude/skills/x-automation/scripts/grok_multi.py "Q1" "Q2" "Q3" --file /path/to/doc.pdf
```

マルチターン並列（search後の継続質問）:
- 並列検索後に継続質問する場合、`reply`コマンドで全タブ分の質問を同時に指定する。
- 例: 3並列3往復
  ```bash
  # 1ターン目: 3並列検索（turnsで予定ターン数を宣言）
  python .claude/skills/x-automation/scripts/grok_multi.py "Q1" "Q2" "Q3" --turns 3

  # 2ターン目: reply で3つの追加質問を同時指定
  python .claude/skills/x-automation/scripts/grok_multi.py reply "Follow1" "Follow2" "Follow3"

  # 3ターン目: 同様に3つ指定
  python .claude/skills/x-automation/scripts/grok_multi.py reply "Final1" "Final2" "Final3"
  ```
- 制約:
  - `reply`の質問数はセッションタブ数と一致させる（3並列なら3つ）
  - 1つのタブだけに追加質問はできない（全タブ一括）
  - `--turns`で宣言したターン数分だけ往復する
- 出力（タブごとに1ファイル・全ターンを統合）:
  - 各タブごとに1つのMDファイルを作成し、全ターンの会話を同一ファイルに記録する。
  - 保存先: `Flow/YYYYMM/YYYY-MM-DD/<topic>/grok_q{N}_{timestamp}.md`
  - 3並列3往復の場合 → 3ファイル（各ファイルに3ターン分）
  - セッション: `~/.grok_multi_session.json` に `tabId/url/md_path` を保存する。

- 再取得（全会話取得・上書き）:
  - `python .claude/skills/x-automation/scripts/grok_multi.py recover --tab <tab_id>`
  - **全会話履歴を取得**して元のMDファイルを完全上書きする
  - 3ターン続いたタブなら3ターン分全部取得して上書き
  - セッションに`md_path`が保存されている必要がある（なければエラー）
  - 新規ファイルやrecoverフォルダは作成しない

### 1. Preflight
- ドキュメント精査原則（Preflight必須）：テンプレート確認後、生成前に必ず以下を実施すること。
  - アジェンダ・依頼文に記載された参照資料を全て読み込む。
  - Flow/Stock配下の関連資料（前回議事録・要望リスト・プロジェクトREADME等）を網羅的に検索・確認する。
  - 確認できなかった資料は「未参照一覧」として成果物に明記する。
  - これらを完了するまで生成を開始しない。
- `./assets/x_automation_template.md` を先に読み、章立て・必須項目・項目順序を確認する（テンプレートファースト）。
- `./questions/x_automation_questions.md` を使って必要情報を収集する。
- 実行モードを確定する（自由度を絞る）。

### 2. 実行準備
- ブリッジサーバー起動確認：
  ```bash
  python .claude/skills/browser-controller/scripts/browser_controller.py status
  ```

### 検証手順（最小スモーク）
```bash
# X: ユーザー投稿（フィルタ付き）
python .claude/skills/browser-controller/scripts/browser_controller.py \
  x_tweets_to_md yugen_matuni --max 10 --min-likes 1 --timeout 60

# X: ホームタイムライン
python .claude/skills/browser-controller/scripts/browser_controller.py \
  x_home_to_md --max 10 --timeout 60

# 生成ファイル確認（先頭数行が出ていればOK）
ls -la Flow/*/*/x/x_yugen_matuni_posts.md Flow/*/*/x/x_home_timeline.md
```

### 3. X 機能

#### 3.1 ユーザー抽出
ページ上のユーザー名を抽出してリスト化する。

| コマンド | 説明 |
|----------|------|
| `x_users` | ユーザー抽出（現在タブまたは指定タブ） |

```bash
# ユーザー抽出（デフォルト: 現在タブ）
python .claude/skills/browser-controller/scripts/browser_controller.py x_users --limit 200

# 特定タブで抽出
python .claude/skills/browser-controller/scripts/browser_controller.py x_users --limit 50 --tab 123456
```

#### 3.2 投稿下書き作成
投稿入力欄にテキストをセットします（投稿はしない）。

| コマンド | 説明 |
|----------|------|
| `x_draft` | 下書きテキストをセット |

```bash
# 下書き作成
python .claude/skills/browser-controller/scripts/browser_controller.py x_draft "投稿内容を入力"
```

#### 3.3 新着DMリスト
DM画面から未読/新着スレッドを抽出します。

| コマンド | 説明 |
|----------|------|
| `x_dms` | 新着DMリスト化 |

```bash
# DMリスト取得
python .claude/skills/browser-controller/scripts/browser_controller.py x_dms --limit 50
```

#### 3.4 過去投稿収集
指定ユーザーの過去投稿をスクロール収集し、Markdown化します。

| コマンド | 説明 |
|----------|------|
| `x_tweets_to_md` | 指定ユーザーの投稿をMarkdown化（Flowに保存） |

```bash
# 単一ユーザーの投稿収集
python .claude/skills/browser-controller/scripts/browser_controller.py x_tweets_to_md elonmusk --max 100

# 複数ユーザーの投稿収集
python .claude/skills/browser-controller/scripts/browser_controller.py x_tweets_to_md elonmusk jack --max 200

# 最大件数指定
python .claude/skills/browser-controller/scripts/browser_controller.py x_tweets_to_md elonmusk --max 1000 --timeout 60

# フィルタ（>= 下限）
python .claude/skills/browser-controller/scripts/browser_controller.py \
  x_tweets_to_md elonmusk --max 300 \
  --min-likes 100 --min-reposts 50 --min-bookmarks 10 \
  --query "keyword" --author elonmusk \
  --timeout 60

# リプライ/リポストを除外
python .claude/skills/browser-controller/scripts/browser_controller.py \
  x_tweets_to_md elonmusk --max 300 \
  --no-replies --no-reposts \
  --timeout 60
```

**出力先**: `Flow/YYYYMM/YYYY-MM-DD/x/x_<username>_posts.md`

#### 3.5 ホームタイムライン取得
ホーム画面のタイムライン（For you / Following）の投稿を収集してMarkdown化します。

| コマンド | 説明 |
|----------|------|
| `x_home_to_md` | ホームタイムラインをMarkdown化（Flowに保存） |

```bash
python .claude/skills/browser-controller/scripts/browser_controller.py x_home_to_md --max 100 --timeout 60
```

**出力先**: `Flow/YYYYMM/YYYY-MM-DD/x/x_home_timeline.md`

**制約**:
- アルゴリズムに依存するため「厳密な上位100件」保証なし

### 4. 結果統合
- 各コマンドの実行結果を確認し、必要に応じて再実行。
- Markdownファイルは自動的に `Flow/YYYYMM/YYYY-MM-DD/x/` 配下に保存されます。

### 5. QC（必須）
- `recommended_subagents` のQC Subagentに評価を委譲する。
- Subagentは `./evaluation/evaluation_criteria.md` に基づきQCを実施する。
- 指摘があれば修正し、最大3回まで繰り返し確定する。

### 6. バックログ反映
- 実装済みの機能、未実装の機能、追加検証が必要な項目をバックログへ反映する。

## subagent_policy
- 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
- 指摘の反映は最小差分で行う
- 指摘に対し「修正した/しない」と理由を最終成果物に残す

## recommended_subagents
- qa-skill-qc: 必須セクション維持、機能欠損、差分最小、検証手順の不足を検査

## Resources
- questions: ./questions/x_automation_questions.md
- assets: ./assets/x_automation_template.md
- evaluation: ./evaluation/evaluation_criteria.md
- scripts: ./scripts/grok_multi.py
- scripts: （browser-controller/scripts/browser_controller.py を再利用）

## Next Action
- 実装済みの X 機能（x_users/x_draft/x_dms/x_tweets_to_md/x_home_to_md）の動作確認。
- フィルタ（min likes/reposts/bookmarks + query + author）の閾値調整と精度確認。
