---
name: browser-controller
description: "Browser Controller Chrome拡張機能を使って任意のWebサイトをプログラムから操作する汎用スキル。「ブラウザ操作」「Webサイト操作」「DOM操作」「スクレイピング」「browser control」「web automation」を依頼されたときに使用する。"
---

# Browser Controller Workflow

## Instructions
1. Preflight:
   - 概要: Browser Controller Chrome拡張機能を使用し、任意のWebサイトをプログラムから操作する。
   - 前提条件:
     - Python 3.8以上
     - Browser Controller Chrome拡張機能がインストール済み
     - 拡張機能のWebSocket接続が有効
   - ドキュメント精査原則（Preflight必須）：テンプレート確認後、生成前に必ず以下を実施すること。
     - アジェンダ・依頼文に記載された参照資料を全て読み込む。
     - Flow/Stock配下の関連資料を網羅的に検索・確認する。
     - 確認できなかった資料は「未参照一覧」として成果物に明記する。
     - これらを完了するまで生成を開始しない。
   - `./guide/guide.md` を先に読み、詳細な使用方法を確認する（テンプレートファースト）。

2. 実行:
   - スクリプト実行パス: `./scripts/browser_controller.py`
   - 実行方法:
     - `cd .cursor/skills/browser-controller/scripts && python browser_controller.py <command>`
     - `python .cursor/skills/browser-controller/scripts/browser_controller.py <command>`
   - ブリッジサーバーは自動起動（手動起動不要）。接続確認:
     - `python browser_controller.py status`

3. QC（必須）:
   - `recommended_subagents` のQC Subagentに評価・チェックを委譲する。
   - Subagentは最初に `./evaluation/evaluation_criteria.md` をReadし、評価指標に基づいてQCを実施する。
   - 指摘を最小差分で反映する。
   - 再度SubagentでQCする。これを最大3回まで繰り返し確定する。
   - 指摘に対し「修正した/しない」と理由を成果物に残す。

4. バックログ反映:
   - 次アクション（追加タスク、レビュー依頼等）を抽出しバックログへ反映する。
   - 反映先・編集制約・差分提示は AGENTS.md / CLAUDE.md の全体ルールに従う。

subagent_policy:
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - サブエージェントの指摘を反映し、反映結果（修正有無/理由）を成果物に残す

recommended_subagents:
  - qa-skill-qc: コマンド実行結果、DOM操作の成功/失敗、スクリプトエラーを検査

## CLI Reference

### タブ操作
| コマンド | 説明 |
|----------|------|
| `tabs` | タブ一覧を取得 |
| `open <url>` | 新しいタブを開く |
| `close --tab <id>` | タブを閉じる |
| `navigate <url>` | URLに移動 |
| `reload` | ページをリロード |

### DOM操作
| コマンド | 説明 |
|----------|------|
| `click <selector>` | 要素をクリック |
| `type <text> --selector <sel>` | テキストを入力 |
| `text <selector>` | テキストを取得 |
| `elements` | 操作可能な要素一覧 |
| `search <query>` | テキストで要素を検索 |

### 調査・キャプチャ
| コマンド | 説明 |
|----------|------|
| `inspect` | DOM構造を調査 |
| `screenshot --output <path>` | スクリーンショット |
| `info` | ページ情報を取得 |
| `status` | 接続状態を確認 |

### インスペクトモード
| モード | 説明 |
|--------|------|
| `summary` | ページ全体のサマリー（デフォルト） |
| `interactive` | インタラクティブ要素一覧 |
| `testids` | data-testid属性を持つ要素 |
| `tree` | body直下の要素ツリー |
| `aria` | ARIA属性を持つ要素 |
| `search` | テキスト検索 |

## バッチ実行（高速化）

複数コマンドを1リクエストで実行し、WebSocket往復回数を削減する。

### Python API

```python
# 複数コマンドを1リクエストで実行（WebSocket往復削減）
await ctrl.batch_execute([
    {'type': 'click', 'selector': '#btn1'},
    {'type': 'get_text', 'selector': 'h1'},
    {'type': 'screenshot'},
])

# 複数DOM操作を1回のexecuteScriptで実行（さらに高速）
await ctrl.batch_dom_ops([
    {'op': 'type', 'selector': '#search', 'text': 'query'},
    {'op': 'click', 'selector': '#submit'},
])

# 複数タブで並列実行
await ctrl.parallel_tabs({
    123: [{'type': 'screenshot'}],
    456: [{'type': 'get_text', 'selector': 'h1'}],
})
```

### 柔軟な要素特定（batch_dom_ops用）

| 方法 | 説明 | 例 |
|------|------|-----|
| `selector` | CSSセレクター | `'#id'`, `'.class'` |
| `xpath` | XPath式 | `'//button[text()="送信"]'` |
| `text` | テキスト部分一致 | `'ログイン'` |
| `textExact` | テキスト完全一致 | `'送信する'` |
| `role` | ARIAロール | `'button'`, `'textbox'` |
| `testId` | data-testid属性 | `'submit-btn'` |
| `ariaLabel` | aria-label属性 | `'検索'` |
| `placeholder` | placeholder属性 | `'メールアドレス'` |
| `index` | 操作可能要素の番号 | `0`, `1`, `2`... |
| `nth` | セレクター結果のN番目 | selectorと併用 |

### 操作タイプ（batch_dom_ops用）

| カテゴリ | 操作 | 説明 |
|----------|------|------|
| クリック | `click`, `click_pointer` | 通常/PointerEvent発火 |
| 入力 | `type`, `clear`, `press_key` | 入力/クリア/キー送信 |
| 取得 | `get_text`, `get_html`, `get_attr`, `get_value` | テキスト/HTML/属性/値 |
| 設定 | `set_attr` | 属性値設定 |
| スクロール | `scroll`, `scroll_into_view` | スクロール/要素まで移動 |
| フォーカス | `focus`, `blur`, `hover` | フォーカス操作 |
| フォーム | `check`, `uncheck`, `select` | チェックボックス/セレクト |
| 確認 | `exists`, `wait_visible` | 要素存在/可視確認 |

## BrowserController クラス API

### 初期化

```python
ctrl = BrowserController(
    timeout=30,        # タイムアウト（秒）
    auto_bridge=True   # ブリッジ自動起動
)
```

### タブ操作

```python
await ctrl.get_tabs()              # タブ一覧
await ctrl.new_tab(url)            # 新しいタブ
await ctrl.close_tab(tab_id)       # タブを閉じる
await ctrl.switch_tab(tab_id)      # タブ切り替え
await ctrl.get_active_tab()        # アクティブタブ取得
```

### DOM操作

```python
await ctrl.click(selector, tab_id)
await ctrl.type_text(text, selector, tab_id)
await ctrl.get_text(selector, tab_id)
await ctrl.get_html(selector, tab_id)
await ctrl.get_attribute(selector, attribute, tab_id)
```

### 要素検索

```python
await ctrl.get_elements(tab_id)
await ctrl.search_elements(query, tab_id)
await ctrl.query_selector(selector, tab_id)
await ctrl.query_selector_all(selector, tab_id)
await ctrl.wait_for_element(selector, tab_id, timeout)
```

### ページ情報

```python
await ctrl.get_page_info(tab_id)
await ctrl.get_page_text(tab_id, selector)
```

### ナビゲーション

```python
await ctrl.navigate(url, tab_id)
await ctrl.reload(tab_id)
await ctrl.go_back(tab_id)
await ctrl.go_forward(tab_id)
```

### その他

```python
await ctrl.screenshot(tab_id, save_path)
await ctrl.inspect_dom(tab_id, selector, mode, text)
await ctrl.execute_script(script, tab_id)
```

## Resources
- guide: ./guide/guide.md
- evaluation: ./evaluation/evaluation_criteria.md
- scripts: ./scripts/browser_controller.py

## Next Action
- 操作が完了したら、結果を確認し次のタスクへ進む。
- エラーが発生した場合は、`status` で接続状態を確認する。

## Subagent Execution
このSkillはサブエージェントとして独立実行可能。
- サブエージェント: `agents/browser-controller-agent.md`
- 用途: 任意のWebサイトのブラウザ自動化、DOM操作、スクレイピング
- 入力: `url`, `commands`（実行するコマンドリスト）
- 出力: 操作結果、取得データ、スクリーンショット
