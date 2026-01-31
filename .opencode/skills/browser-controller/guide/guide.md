# Browser Controller - 仕様書

## 概要
Chrome拡張機能「Browser Controller」を使った汎用ブラウザ自動操作システム。
WebSocket経由でPythonから任意のWebサイトをプログラム制御する。

## アーキテクチャ

### 通信方式: WebSocket（固定）
```
[Python browser_controller.py] 
    ↓ WebSocket (ws://localhost:9224)
[Bridge Server（browser_controller.py内蔵）]
    ↓ WebSocket
[Chrome拡張機能 background.js]
    ↓ chrome.scripting.executeScript
[任意のWebページ]
```

**重要**: Native MessagingやCDPへの移行は禁止。WebSocket方式を維持すること。

## ファイル構成

```
{{AGENT_CONFIG_DIR}}/skills/browser-controller/
├── SKILL.md                   ← Skill定義
├── guide/
│   └── guide.md               ← この仕様書
├── scripts/
│   └── browser_controller.py  ← メインPythonスクリプト（依存自動インストール）
│                                 - WebSocketクライアント
│                                 - ブリッジサーバー内蔵
│                                 - CLI実装
└── assets/                    ← アセット（テンプレート等）
```

**前提条件**:
- Python 3.8以上（websocketsは初回実行時に自動インストール）
- Browser Controller Chrome拡張機能がインストール済み

## コンポーネント詳細

### 1. Bridge Server（browser_controller.py内蔵）

**役割**: Chrome拡張機能とPythonクライアント間のWebSocket中継

**ポート**: 9224

**動作**:
1. `ws://localhost:9224` でWebSocketサーバーを起動
2. Chrome拡張機能からの接続を待機（`extension_connected`メッセージ）
3. Pythonクライアントからのコマンドを拡張機能に転送
4. 拡張機能からの応答をクライアントに返却

**起動方法**:
```bash
# フォアグラウンド
python browser_controller.py bridge

# バックグラウンド（自動起動される）
# コマンド実行時にブリッジが起動していなければ自動で起動
```

### 2. Chrome拡張機能（background.js）

**接続先**: `ws://localhost:9224`

**接続時の動作**:
1. WebSocket接続を確立
2. `{ type: 'extension_connected' }` を送信
3. 以降、コマンドを待機

**Keep-alive**:
- 20秒ごとにpingを送信
- chrome.alarmsで24秒ごとにService Workerを維持

**対応コマンド（汎用）**:

| type | 説明 | パラメータ |
|------|------|-----------|
| **基本** |||
| `ping` | 疎通確認 | - |
| `get_tabs` | タブ一覧取得 | - |
| `get_active_tab` | アクティブタブ取得 | - |
| `new_tab` | 新規タブ | url |
| `close_tab` | タブを閉じる | tabId |
| `switch_tab` | タブ切替 | tabId |
| `navigate` | URL移動 | url, tabId? |
| `reload` | ページリロード | tabId? |
| `go_back` | 戻る | tabId? |
| `go_forward` | 進む | tabId? |
| **DOM操作** |||
| `click` | 要素クリック | selector, tabId?, index? |
| `type` | テキスト入力 | text, selector, tabId?, index? |
| `get_text` | テキスト取得 | selector, tabId? |
| `get_html` | HTML取得 | selector, tabId? |
| `get_attribute` | 属性取得 | selector, attribute, tabId? |
| `press_enter` | Enterキー送信 | selector?, tabId? |
| `scroll` | スクロール | direction, amount, tabId? |
| `get_elements` | 操作可能要素一覧 | tabId? |
| `query_selector` | セレクタで要素取得 | selector, tabId? |
| `query_selector_all` | セレクタで全要素取得 | selector, tabId? |
| `wait_for_element` | 要素待機 | selector, tabId?, timeout? |
| `execute_script` | スクリプト実行 | script, tabId? |
| `screenshot` | スクリーンショット | tabId? |
| **ページ情報** |||
| `get_page_info` | ページ情報取得 | tabId? |
| `get_page_text` | ページテキスト取得 | tabId?, selector? |
| `inspect_dom` | DOM調査 | tabId?, selector?, mode?, text? |
| **管理** |||
| `reload_extension` | 拡張機能リロード | - |

### 3. Python CLI（browser_controller.py）

**使用例**:
```bash
# スクリプトの場所
cd .opencode/skills/browser-controller/scripts

# ブリッジサーバー起動（フォアグラウンド）
python browser_controller.py bridge

# 接続状態確認
python browser_controller.py status

# タブ一覧
python browser_controller.py tabs

# 新しいタブを開く
python browser_controller.py open "https://example.com"

# 要素をクリック
python browser_controller.py click "button.submit" --tab 123456

# テキスト入力
python browser_controller.py type "検索ワード" --selector "input#search"

# テキスト取得
python browser_controller.py text "h1.title"

# 要素検索
python browser_controller.py search "ログイン"

# スクリーンショット
python browser_controller.py screenshot --output page.png

# DOM調査
python browser_controller.py inspect
python browser_controller.py inspect --mode interactive
python browser_controller.py inspect --mode testids
```

## BrowserController クラス API

### 初期化

```python
from browser_controller import BrowserController

ctrl = BrowserController(
    timeout=30,        # タイムアウト（秒）
    auto_bridge=True   # ブリッジ自動起動
)
```

### タブ操作

```python
# タブ一覧取得
tabs = await ctrl.get_tabs()

# 新しいタブを開く
result = await ctrl.new_tab('https://example.com')
tab_id = result['tab']['id']

# タブを閉じる
await ctrl.close_tab(tab_id)

# タブ切り替え
await ctrl.switch_tab(tab_id)

# アクティブタブ取得
tab = await ctrl.get_active_tab()
```

### DOM操作

```python
# クリック
await ctrl.click('button.submit', tab_id)
await ctrl.click('li.item', tab_id, index=2)  # 3番目の要素

# テキスト入力
await ctrl.type_text('検索ワード', 'input#search', tab_id)

# テキスト取得
text = await ctrl.get_text('h1.title', tab_id)

# HTML取得
html = await ctrl.get_html('div.content', tab_id)

# 属性取得
href = await ctrl.get_attribute('a.link', 'href', tab_id)
```

### 要素検索

```python
# 操作可能な要素一覧
elements = await ctrl.get_elements(tab_id)

# テキストで要素検索
results = await ctrl.search_elements('ログイン', tab_id)

# CSSセレクタで単一要素取得
element = await ctrl.query_selector('div.result', tab_id)

# CSSセレクタで全要素取得
elements = await ctrl.query_selector_all('li.item', tab_id)

# 要素待機（出現まで待つ）
result = await ctrl.wait_for_element('div.result', tab_id, timeout=30)
if result['success']:
    print('要素が見つかりました')
```

### ページ情報

```python
# ページ情報取得
info = await ctrl.get_page_info(tab_id)
# { url, title, readyState }

# ページテキスト取得
text = await ctrl.get_page_text(tab_id)
text = await ctrl.get_page_text(tab_id, 'div.content')  # 特定セクション
```

### ナビゲーション

```python
# URL移動
await ctrl.navigate('https://example.com/page2', tab_id)

# リロード
await ctrl.reload(tab_id)

# 戻る/進む
await ctrl.go_back(tab_id)
await ctrl.go_forward(tab_id)
```

### その他

```python
# スクリーンショット
await ctrl.screenshot(tab_id, 'output.png')

# DOM調査
result = await ctrl.inspect_dom(tab_id, mode='interactive')
result = await ctrl.inspect_dom(tab_id, mode='testids')
result = await ctrl.inspect_dom(tab_id, mode='search', text='ログイン')

# カスタムスクリプト実行
result = await ctrl.execute_script('return document.title;', tab_id)
```

## インスペクトモード

| モード | 説明 |
|--------|------|
| `summary` | ページ全体のサマリー（デフォルト） |
| `interactive` | インタラクティブ要素一覧（button, a, input等） |
| `testids` | data-testid属性を持つ要素 |
| `tree` | body直下の要素ツリー |
| `aria` | ARIA属性を持つ要素 |
| `search` | テキスト検索 |

## 設定

### デフォルト値
| 項目 | 値 |
|------|-----|
| タイムアウト | 30秒 |
| WebSocketポート | 9224 |

## 使用パターン

### パターン1: フォーム入力と送信

```python
import asyncio
from browser_controller import BrowserController

async def fill_form():
    ctrl = BrowserController()
    
    # フォームページを開く
    result = await ctrl.new_tab('https://example.com/form')
    tab_id = result['tab']['id']
    await asyncio.sleep(2)  # ページ読み込み待機
    
    # フォーム入力
    await ctrl.type_text('山田太郎', 'input[name="name"]', tab_id)
    await ctrl.type_text('test@example.com', 'input[name="email"]', tab_id)
    
    # 送信
    await ctrl.click('button[type="submit"]', tab_id)
    
    # 結果待機
    await ctrl.wait_for_element('div.success', tab_id, timeout=10)
    
    # 結果取得
    message = await ctrl.get_text('div.success', tab_id)
    print(f'結果: {message}')

asyncio.run(fill_form())
```

### パターン2: ページスクレイピング

```python
async def scrape_page():
    ctrl = BrowserController()
    
    # ページを開く
    result = await ctrl.new_tab('https://example.com/list')
    tab_id = result['tab']['id']
    await asyncio.sleep(2)
    
    # アイテム一覧を取得
    items = await ctrl.query_selector_all('div.item', tab_id)
    
    for i, item in enumerate(items.get('elements', [])):
        # 各アイテムの詳細を取得
        title = await ctrl.get_text(f'div.item:nth-child({i+1}) h2', tab_id)
        price = await ctrl.get_text(f'div.item:nth-child({i+1}) .price', tab_id)
        print(f'{title}: {price}')

asyncio.run(scrape_page())
```

### パターン3: 動的コンテンツの監視

```python
async def monitor_changes():
    ctrl = BrowserController()
    
    result = await ctrl.new_tab('https://example.com/live')
    tab_id = result['tab']['id']
    
    last_value = None
    while True:
        current = await ctrl.get_text('span.counter', tab_id)
        if current != last_value:
            print(f'変更検出: {last_value} -> {current}')
            last_value = current
        await asyncio.sleep(1)

asyncio.run(monitor_changes())
```

## トラブルシューティング

### 接続できない場合

1. **ブリッジサーバーが起動しているか確認**
   ```bash
   python browser_controller.py status
   lsof -i :9224
   ```

2. **Chrome拡張機能を再ロード**
   - `chrome://extensions/` を開く
   - Browser Controllerの更新ボタンをクリック
   - Service Workerのリンクをクリックしてログ確認

3. **ブリッジサーバーを再起動**
   ```bash
   # 既存プロセスを終了
   pkill -f "browser_controller.*bridge"
   
   # 再起動
   python browser_controller.py bridge &
   ```

### websockets v14+の並列処理制限

**問題**: 同じWebSocket接続で同時にsend/recvするとエラー

**対策**: `asyncio.Lock()`による排他制御を実装済み

### Service Workerのライフサイクル

**問題**: Chromeは30秒でService Workerを停止する

**対策**:
- chrome.alarmsで24秒ごとにkeep-alive
- WebSocket pingで20秒ごとに通信

### 要素が見つからない場合

1. **セレクタを確認**
   ```bash
   python browser_controller.py inspect --mode interactive --tab <tabId>
   ```

2. **ページ読み込み完了を待つ**
   ```python
   await ctrl.wait_for_element('div.content', tab_id, timeout=10)
   ```

3. **動的要素の場合は待機時間を追加**
   ```python
   await asyncio.sleep(2)
   ```

## 関連スキル

- `chatgpt-parallel-research`: ChatGPT専用の並列検索ツール（このスキルを基盤として使用）

## ユーザーの好み

- Python 1ファイルで完結（可能な限り）
- 手動操作を最小化
- WebSocket方式を維持（Native Messaging/CDPは使わない）

## 変更履歴

| 日付 | 変更内容 |
|------|----------|
| 2026-01-12 | 仕様書作成 |
| 2026-01-12 | chatgpt_multi.pyから汎用部分を分離してbrowser_controller.pyを作成 |
