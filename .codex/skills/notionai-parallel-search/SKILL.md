---
name: notionai-parallel-search
description: "Browser Controller拡張機能を使ってNotion AIで3並列以上の社内検索・抽出を実行し、結果をMarkdown保存する。複数タブでの並列実行、既存タブの再取得、セッション管理に対応。『NotionAIで検索』『Notion AI 並列検索』『Notion AIで社内ナレッジ検索』『Notion AIでコンテキスト収集』を依頼されたときに使用する。Notion情報の検索時には最優先で利用する。"
---

# Notion AI Parallel Search Workflow

## Instructions
1. Preflight:
   - 概要: Browser Controller Chrome拡張機能を使用し、Notion AI（https://www.notion.so/ai）で**3並列以上**のプロンプト実行（社内検索/抽出）を行い、結果をMarkdownに保存する。
   - 前提条件:
     - Notionにログイン済みであること
     - Notion AIが利用可能であること（権限/プラン/ワークスペース制限など）
   - ドキュメント精査原則（Preflight必須）：テンプレート確認後、生成前に必ず以下を実施すること。
     - アジェンダ・依頼文に記載された参照資料を全て読み込む。
     - Flow/Stock配下の関連資料（前回実行ログ・タスク定義等）を網羅的に検索・確認する。
     - 確認できなかった資料は「未参照一覧」として成果物に明記する。
     - これらを完了するまで生成を開始しない。
   - `./assets/notionai_research_template.md` を先に読み、章立て・必須項目・項目順序を確認する（テンプレートファースト）。
   - `./questions/notionai_research_questions.md` を使って必要情報（対象会社/ワークスペース、検索観点、出力形式、機密範囲）を確定する。
   - クエリ（プロンプト）を3個以上に分割・設計する（`search` 使用時は必須）。
   - クエリ設計ルール:
     1. フルコンテキストで渡す: 各プロンプトは独立コンテキストとして成立させる。背景情報・前提・制約・目的を各プロンプト本文に含める。Notion AIは他のタブの内容を知らないため、省略禁止。
     2. 関連ファイルは添付: 関連する情報がファイルにある場合は添付する（最大10ファイル）。ファイルを読んで口頭で伝えるのではなく、ファイル自体を渡す。
     3. 目的と検索対象を明記: 各プロンプトの冒頭に「何の目的で」「何を検索/議論するのか」を明示する。
     4. 背景情報は徹底的に詳しく: 「なぜこの質問をするのか」「どういう文脈でこの情報が必要なのか」を省略せずに書く。
     5. 極めて詳細に: クエリ自体を詳細に設計し、回答も詳細に返してもらうよう指示する。曖昧な表現や省略は禁止。
     6. 同一セッションで継続: 複数の追加質問は新規チャットを立てず、同じ会話セッションにreplyで追加する。前回の回答が完了していることを確認してから次の質問を送信する。
   - クエリ設計の構造（5W1H + 背景）:
     ```
     【背景・文脈】
     - 現在の状況: □□という状態である
     - 経緯: ××があったため、△△を検討している
     - なぜこの質問をするのか: 〇〇を決定/解決するために必要な情報である

     【目的】〇〇のために△△を調査する

     【Who】誰が関係するか（対象者、ステークホルダー）
     【What】具体的に知りたいこと
     【When】時期・期間・タイミングの制約
     【Where】対象ワークスペース・チーム・プロジェクト範囲
     【Why】なぜそれが重要か、どう活用するか
     【How】どのようなアプローチ・手法・形式で知りたいか

     【制約】あれば記載（特定チームのみ、直近1ヶ月のみ等）
     【期待する出力形式】箇条書き/表形式/比較表/詳細説明 等

     【回答の詳細度】
     - 可能な限り詳細かつ網羅的に回答してください
     - 具体例、数値、事例を豊富に含めてください
     - 表面的な説明ではなく、深掘りした分析を提供してください
     - 結論だけでなく、その根拠と理由も詳しく説明してください
     ```
   - 安全策: 明示的なページ操作・編集の指示がない限り、各プロンプトに「情報収集のみでページ更新・作成は行わない」旨を付記する。
   - 注意: Notion AI UIの「コンテキストを追加」はコンテキスト選択用であり、検索クエリ入力欄ではない。並列検索はプロンプト入力欄（textbox）に対して行う。

2. 実行:
   - スクリプトの動作原理:
     - CSP制約回避: Notion AIページはContent Security Policyが厳しいため、`get_text`（Content Script経由）でDOM取得を行う
     - 並列実行戦略: 全タブを先に作成（0.5秒間隔）→5秒待機（ページロード完了）→各タブへのプロンプト入力と回答待機を並列実行
     - 入力検証: プロンプトがテキストボックスに正しく入力されたかを確認し、失敗時は最大3回リトライ
     - 送信確認: テキストボックス内容の確認（第1段階）に加え、送信後にページ全体からプロンプトの存在を確認（第2段階）。両段階とも失敗する場合のみEnterキー送信をフォールバックとして試行
     - 安定性検出: 回答テキストが3ポーリング連続で変化しなければ「完了」と判定（最小10文字以上）
     - 引用リンク抽出: JavaScriptでページ内の全`<a>`タグを取得し、外部URL（notion.so/notion.com以外）のみをフィルタリングして「参照リンク」セクションに記載
   - 接続確認:
     - `python .codex/skills/notionai-parallel-search/scripts/notionai_multi.py status`
   - 3並列以上（search）:
     - `python .codex/skills/notionai-parallel-search/scripts/notionai_multi.py "P1" "P2" "P3"`
     - 生ログ（body全文）の保存を有効化する場合（機微情報が含まれる可能性あり）:
       - `python .codex/skills/notionai-parallel-search/scripts/notionai_multi.py "P1" "P2" "P3" --raw`
   - 単一タブ逐次（search1）:
     - `python .codex/skills/notionai-parallel-search/scripts/notionai_multi.py search1 "P1" "P2"`
   - 既存タブの再取得（全文取得・上書き）:
     - `python .codex/skills/notionai-parallel-search/scripts/notionai_multi.py recover --tab <tab_id>`
     - **全ページテキストを取得**して元のMDファイルを完全上書きする
     - セッションに`md_path`が保存されている必要がある（なければエラー）
     - 新規ファイルやrecoverフォルダは作成しない
     - `--prompt`を指定すると回答部分を抽出、省略時は全文

   - マルチターン並列（search後の継続質問）:
     - 並列検索後に継続質問する場合、`reply`コマンドで全タブ分の質問を同時に指定する。
     - 例: 3並列3往復
       ```bash
       # 1ターン目: 3並列検索（turnsで予定ターン数を宣言）
       python .codex/skills/notionai-parallel-search/scripts/notionai_multi.py "P1" "P2" "P3" --turns 3

       # 2ターン目: reply で3つの追加質問を同時指定
       python .codex/skills/notionai-parallel-search/scripts/notionai_multi.py reply "Follow1" "Follow2" "Follow3"

       # 3ターン目: 同様に3つ指定
       python .codex/skills/notionai-parallel-search/scripts/notionai_multi.py reply "Final1" "Final2" "Final3"
       ```
     - 制約:
       - `reply`の質問数はセッションタブ数と一致させる（3並列なら3つ）
       - 1つのタブだけに追加質問はできない（全タブ一括）
       - `--turns`で宣言したターン数分だけ往復する

   - 出力（タブごとに1ファイル・全ターンを統合）:
     - 各タブごとに1つのMDファイルを作成し、全ターンの会話を同一ファイルに記録する。
     - 保存先: `Flow/YYYYMM/YYYY-MM-DD/<topic>/notionai_q{N}_{timestamp}.md`
     - 3並列3往復の場合 → 3ファイル（各ファイルに3ターン分）
     - デバッグ用（任意）: `notionai_q{N}_{timestamp}.raw.txt`（`--raw` 指定時のみ）
     - recoverは元のMDファイルを上書きする（新規ファイルは作成しない）

   - セッション:
     - `~/.notionai_multi_session.json` に最新実行の `topic/outdir/tabId/url/md_path` を保存する。

   - 動作確認:
     - MD出力ファイルが `Flow/YYYYMM/YYYY-MM-DD/<topic>/` に生成されること
     - MD内の「## Turn 1」セクションに抽出結果が含まれること
     - マルチターン時は同一ファイルに「## Turn 2」等が追記されること
     - セッションファイル `~/.notionai_multi_session.json` にtabId/prompt/mdパスが記録されること

3. 結果統合:
   - 収集した個別MDを `./assets/notionai_research_template.md` 形式で統合する。
   - 参照元（Notionページ名/URL）を必ず残す。元資料にない項目は「未記載/不明」と明記する。

4. Troubleshooting:
   - 症状: プロンプトがテキストボックスに入らない
     - 原因: Notion AI UIの読み込み遅延またはDOM不安定
     - 手順: スクリプトが自動3回リトライ。失敗する場合はページリロード後に再実行
   - 症状: 回答が空（0文字）または「(waiting...)」のまま
     - 原因: 安定性検出が10文字未満を無視、またはタイムアウト
     - 手順: `--timeout 600` 等で延長、または `recover --tab <id> --prompt "..."` で再取得
   - 症状: 回答が長くて取得が途中で止まる/更新されない
     - 手順: `recover --tab <tab_id>` で全文取得・上書き（recoverは全ページテキストを再取得して元MDを上書きする）
   - 症状: `body` テキストがサイドバー等のノイズを含む
     - 手順: ログには `raw` を残しつつ、抽出ロジック（プロンプト末尾から「コンテキストを追加」まで）でノイズを抑制する。

5. QC（必須）:
   - `./evaluation/evaluation_criteria.md` に基づきQCする。
   - 指摘があれば追加プロンプトや `recover` を実行して再取得し、最大3回まで反映する。

6. バックログ反映:
   - セレクタ不安定・抽出精度不足等があれば改善タスクとしてバックログへ反映する。

subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - 指摘の反映は最小差分で行う
  - 指摘に対し「修正した/しない」と理由を最終成果物に残す

recommended_subagents:
  - qa-skill-qc: 3並列要件、MD保存、出典明記、抽出欠損、機密マスクを検査

## Resources
- questions: ./questions/notionai_research_questions.md
- assets: ./assets/notionai_research_template.md
- evaluation: ./evaluation/evaluation_criteria.md
- scripts: ./scripts/notionai_multi.py

## Next Action
- 取得結果をもとに、設計・実装・追加調査の次アクションへ進む。
- 指摘が出た場合は、追加検索または再取得を実行して再QCする。

## Subagent Execution
このSkillはサブエージェントとして独立実行可能。
- サブエージェント: `.claude/agents/notionai-parallel-search.md`
- 用途: Notion AIの並列検索・抽出、結果のMD保存
- 入力: `search_prompts`（3個以上推奨）, `timeout`, `interval`, `close_tabs`, `raw`
- 出力: 個別MD（Flow配下）とセッションファイル（ホーム配下）
