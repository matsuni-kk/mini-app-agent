#!/usr/bin/env python3
"""
Browser Controller - 汎用ブラウザ操作ツール
==========================================
Browser Controller Chrome拡張機能を使って任意のWebサイトを操作

機能:
- タブ操作（開く/閉じる/切り替え）
- DOM操作（クリック/入力/テキスト取得）
- 要素検索（セレクター/テキスト）
- スクリーンショット
- ページ情報取得
- ブリッジサーバー内蔵（自動起動）

使用例:
  # タブ一覧
  python browser_controller.py tabs
  
  # 新しいタブを開く
  python browser_controller.py open "https://example.com"
  
  # 要素をクリック
  python browser_controller.py click "button.submit" --tab 123456
  
  # テキスト入力
  python browser_controller.py type "Hello World" --selector "input#search"
  
  # テキスト取得
  python browser_controller.py text "h1.title"
  
  # 要素検索
  python browser_controller.py search "ログイン"
  
  # スクリーンショット
  python browser_controller.py screenshot --output page.png
  
  # DOM調査
  python browser_controller.py inspect
  python browser_controller.py inspect --mode interactive
  
  # ブリッジサーバーのみ起動
  python browser_controller.py bridge
"""

import asyncio
import json
import time
import socket
import subprocess
import sys
import os
import base64
import uuid
from typing import List, Dict, Optional, Any
from pathlib import Path
from contextlib import asynccontextmanager
# NOTE: This script aims for runtime compatibility; strict typing is best-effort.

# WebSocketライブラリ（自動インストール）
def _ensure_websockets():
    """websocketsがなければ自動インストール"""
    try:
        import websockets
        return websockets
    except ImportError:
        print("[Auto-install] Installing websockets...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "websockets", "--user", "-q"],
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "websockets", "--break-system-packages", "-q"],
                stderr=subprocess.DEVNULL
            )
        import websockets
        return websockets

websockets = _ensure_websockets()
from websockets.server import serve


# ========================================
# Bridge Server (内蔵)
# ========================================

class BridgeServer:
    """拡張機能とPythonクライアント間のWebSocketブリッジサーバー"""
    
    PORT = 9224
    
    def __init__(self):
        self.extension_ws = None
        self.pending = {}
        self.running = False
    
    @staticmethod
    def is_running() -> bool:
        """ブリッジサーバーが起動中かチェック"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(1)
            sock.connect(('localhost', BridgeServer.PORT))
            sock.close()
            return True
        except (socket.error, socket.timeout):
            return False
    
    async def handler(self, ws):
        """WebSocket接続ハンドラー"""
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=5.0)
            data = json.loads(msg)
            
            if data.get('type') == 'extension_connected':
                print("[Bridge] Chrome extension connected")
                self.extension_ws = ws
                
                async for message in ws:
                    try:
                        resp = json.loads(message)
                        if resp.get('type') == 'ping':
                            continue
                        req_id = resp.get('requestId')
                        if req_id and req_id in self.pending:
                            self.pending[req_id].set_result(resp)
                    except json.JSONDecodeError:
                        pass
                
                print("[Bridge] Chrome extension disconnected")
                self.extension_ws = None
                return
            
            async def process_command(cmd_data):
                if self.extension_ws is None:
                    await ws.send(json.dumps({'error': 'Extension not connected'}))
                    return
                
                req_id = cmd_data.get('requestId') or f"r{id(cmd_data)}"
                cmd_data['requestId'] = req_id
                
                future = asyncio.get_event_loop().create_future()
                self.pending[req_id] = future
                
                try:
                    await self.extension_ws.send(json.dumps(cmd_data))
                    response = await asyncio.wait_for(future, timeout=30.0)
                    await ws.send(json.dumps(response))
                except asyncio.TimeoutError:
                    await ws.send(json.dumps({'error': 'Timeout', 'requestId': req_id}))
                finally:
                    self.pending.pop(req_id, None)
            
            await process_command(data)
            
            async for message in ws:
                try:
                    cmd_data = json.loads(message)
                    await process_command(cmd_data)
                except json.JSONDecodeError:
                    pass
                
        except Exception as e:
            print(f"[Bridge] Error: {e}")
    
    async def run(self):
        """ブリッジサーバーを起動"""
        self.running = True
        print(f"[Bridge] Starting on ws://localhost:{self.PORT}")
        print("[Bridge] Waiting for Chrome extension connection...")
        print("[Bridge] Press Ctrl+C to stop\n")
        
        async with serve(self.handler, 'localhost', self.PORT):
            await asyncio.Future()
    
    @staticmethod
    def start_background():
        """バックグラウンドプロセスでブリッジサーバーを起動"""
        script_path = os.path.abspath(__file__)
        process = subprocess.Popen(
            [sys.executable, script_path, 'bridge'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        for _ in range(30):
            time.sleep(0.1)
            if BridgeServer.is_running():
                print(f"[Bridge] Started in background (PID: {process.pid})")
                return True
        
        print("[Bridge] Failed to start")
        return False


# ========================================
# Browser Controller
# ========================================

class BrowserController:
    """汎用ブラウザ操作コントローラー"""
    
    BRIDGE_URL = "ws://localhost:9224"
    
    def __init__(self, timeout: int = 30, auto_bridge: bool = True):
        self.timeout = timeout
        self.auto_bridge = auto_bridge
        self._ws = None
        self._request_id = 0
        self._lock = asyncio.Lock()
    
    # ========================================
    # WebSocket通信
    # ========================================
    
    async def connect(self):
        """ブリッジサーバーに接続（必要なら自動起動）"""
        if self._ws is None or (hasattr(self._ws, 'closed') and self._ws.closed) or (hasattr(self._ws, 'state') and self._ws.state.name == 'CLOSED'):
            if self.auto_bridge and not BridgeServer.is_running():
                print("[Bridge] Not running, starting automatically...")
                if not BridgeServer.start_background():
                    raise ConnectionError("Failed to start bridge server")
                await asyncio.sleep(0.5)
            
            try:
                self._ws = await websockets.connect(self.BRIDGE_URL)
            except Exception as e:
                raise ConnectionError(f"Failed to connect to bridge server: {e}")
    
    async def _cmd(self, **kwargs) -> Dict:
        """コマンドを送信して応答を待つ"""
        async with self._lock:
            await self.connect()
            self._request_id += 1
            req_id = f"r{self._request_id}"
            kwargs['requestId'] = req_id
            
            await self._ws.send(json.dumps(kwargs))
            
            try:
                response = await asyncio.wait_for(self._ws.recv(), timeout=self.timeout)
                return json.loads(response)
            except asyncio.TimeoutError:
                return {'error': 'Timeout waiting for response'}
    
    # ========================================
    # タブ操作
    # ========================================
    
    async def get_tabs(self) -> List[Dict]:
        """タブ一覧を取得"""
        result = await self._cmd(type='get_tabs')
        return result.get('tabs', [])
    
    async def new_tab(self, url: str) -> Dict:
        """新しいタブを開く"""
        return await self._cmd(type='new_tab', url=url)
    
    async def close_tab(self, tab_id: int) -> Dict:
        """タブを閉じる"""
        return await self._cmd(type='close_tab', tabId=tab_id)
    
    async def switch_tab(self, tab_id: int) -> Dict:
        """タブを切り替える"""
        return await self._cmd(type='switch_tab', tabId=tab_id)
    
    async def get_active_tab(self) -> Optional[Dict]:
        """アクティブタブを取得"""
        tabs = await self.get_tabs()
        for tab in tabs:
            if tab.get('active'):
                return tab
        return tabs[0] if tabs else None

    async def find_tab_by_url(self, url_pattern: str, exact_match: bool = False) -> Optional[Dict]:
        """URLパターンでタブを検索"""
        tabs = await self.get_tabs()
        pattern = url_pattern.lower()
        for tab in tabs:
            tab_url = (tab.get('url') or '').lower()
            if exact_match:
                if tab_url == pattern:
                    return tab
            else:
                if pattern in tab_url:
                    return tab
        return None
    
    # ========================================
    # DOM操作
    # ========================================
    
    async def click(self, selector: str, tab_id: int = None) -> Dict:
        """要素をクリック"""
        return await self._cmd(type='click', selector=selector, tabId=tab_id)

    async def click_text(self, text: str, tab_id: int = None, exact: bool = False) -> Dict:
        """テキストで要素を探してクリック"""
        return await self._cmd(type='click_text', tabId=tab_id, text=text, exact=exact)
    
    async def type_text(self, text: str, selector: str, tab_id: int = None) -> Dict:
        """テキストを入力"""
        return await self._cmd(type='type', text=text, selector=selector, tabId=tab_id)
    
    async def get_text(self, selector: str, tab_id: int = None) -> Dict:
        """テキストを取得"""
        return await self._cmd(type='get_text', selector=selector, tabId=tab_id)
    
    async def get_html(self, selector: str = 'body', tab_id: int = None) -> Dict:
        """HTMLを取得"""
        return await self._cmd(type='get_html', selector=selector, tabId=tab_id)
    
    async def get_attribute(self, selector: str, attribute: str, tab_id: int = None) -> Dict:
        """属性値を取得"""
        return await self._cmd(type='get_attribute', selector=selector, attribute=attribute, tabId=tab_id)
    
    # ========================================
    # 要素検索
    # ========================================
    
    async def get_elements(self, tab_id: int = None) -> List[Dict]:
        """操作可能な要素一覧を取得"""
        result = await self._cmd(type='get_elements', tabId=tab_id)
        return result.get('elements', [])
    
    async def search_elements(self, query: str, tab_id: int = None) -> List[Dict]:
        """要素をテキストで検索"""
        elements = await self.get_elements(tab_id)
        query_lower = query.lower()
        matches = []
        
        for i, el in enumerate(elements):
            text = (el.get('text') or '').lower()
            selector = (el.get('selector') or '').lower()
            el_type = (el.get('type') or '').lower()
            
            if query_lower in text or query_lower in selector or query_lower in el_type:
                matches.append({'index': i, **el})
        
        return matches
    
    async def query_selector(self, selector: str, tab_id: int = None) -> Dict:
        """CSSセレクターで要素を検索"""
        return await self._cmd(type='query_selector', selector=selector, tabId=tab_id)
    
    async def query_selector_all(self, selector: str, tab_id: int = None) -> Dict:
        """CSSセレクターで複数要素を検索"""
        return await self._cmd(type='query_selector_all', selector=selector, tabId=tab_id)
    
    # ========================================
    # ページ情報
    # ========================================
    
    async def get_page_info(self, tab_id: int = None) -> Dict:
        """ページ情報を取得"""
        tab = None
        if tab_id:
            tabs = await self.get_tabs()
            tab = next((t for t in tabs if t['id'] == tab_id), None)
        else:
            tab = await self.get_active_tab()
        
        if not tab:
            return {'error': 'Tab not found'}
        
        return {
            'id': tab.get('id'),
            'url': tab.get('url'),
            'title': tab.get('title'),
            'active': tab.get('active')
        }
    
    async def get_page_text(self, tab_id: int = None, selector: str = 'body') -> str:
        """ページ全体のテキストを取得"""
        result = await self.get_text(selector, tab_id)
        return result.get('text', '')
    
    async def wait_for_element(self, selector: str, tab_id: int = None, timeout: int = 30) -> Dict:
        """要素が出現するまで待機"""
        start = time.time()
        while time.time() - start < timeout:
            result = await self.query_selector(selector, tab_id)
            if result.get('found'):
                return {'success': True, 'element': result}
            await asyncio.sleep(0.5)
        return {'success': False, 'error': 'Element not found within timeout'}
    
    # ========================================
    # スクリーンショット
    # ========================================
    
    async def screenshot(self, tab_id: int = None, save_path: str = None) -> Dict:
        """スクリーンショットを撮影"""
        result = await self._cmd(type='screenshot', tabId=tab_id)
        
        if result.get('success') and save_path and result.get('dataUrl'):
            data_url = result['dataUrl']
            if ',' in data_url:
                base64_data = data_url.split(',')[1]
                with open(save_path, 'wb') as f:
                    f.write(base64.b64decode(base64_data))
                result['path'] = save_path
        
        return result
    
    # ========================================
    # DOM調査
    # ========================================
    
    async def inspect_dom(self, tab_id: int = None, selector: str = None, mode: str = 'summary', text: str = None) -> Dict:
        """DOMを調査"""
        options = {'mode': mode}
        if text:
            options['text'] = text
        return await self._cmd(type='inspect_dom', tabId=tab_id, selector=selector, options=options)
    
    # ========================================
    # JavaScript実行
    # ========================================
    
    async def execute_script(self, script: str, tab_id: int = None) -> Dict:
        """JavaScriptを実行"""
        return await self._cmd(type='execute_script', script=script, tabId=tab_id)
    
    # ========================================
    # ナビゲーション
    # ========================================
    
    async def navigate(self, url: str, tab_id: int = None) -> Dict:
        """URLに移動"""
        return await self._cmd(type='navigate', url=url, tabId=tab_id)
    
    async def reload(self, tab_id: int = None) -> Dict:
        """ページをリロード"""
        return await self._cmd(type='reload', tabId=tab_id)
    
    async def go_back(self, tab_id: int = None) -> Dict:
        """戻る"""
        return await self._cmd(type='go_back', tabId=tab_id)
    
    async def go_forward(self, tab_id: int = None) -> Dict:
        """進む"""
        return await self._cmd(type='go_forward', tabId=tab_id)

    # ========================================
    # バッチ実行（高速化用）
    # ========================================

    async def batch_execute(self, commands: List[Dict]) -> Dict:
        """
        複数コマンドを1リクエストで実行（WebSocket往復回数を削減）

        Args:
            commands: コマンドのリスト
                例: [
                    {'type': 'click', 'selector': '#btn1'},
                    {'type': 'type', 'selector': '#input', 'text': 'hello'},
                    {'type': 'screenshot'}
                ]

        Returns:
            {'type': 'batch_result', 'success': True, 'results': [...], 'count': N}

        使用例:
            results = await ctrl.batch_execute([
                {'type': 'click', 'selector': '.menu'},
                {'type': 'get_text', 'selector': 'h1'},
            ])
            for r in results.get('results', []):
                print(r)
        """
        return await self._cmd(type='batch_execute', commands=commands)

    async def batch_dom_ops(self, operations: List[Dict], tab_id: int = None) -> Dict:
        """
        複数DOM操作を1回のexecuteScriptで実行（さらに高速）

        Args:
            operations: 操作のリスト。各操作は以下の形式:

            【要素特定方法】（優先順位順、いずれか1つを指定）
                - selector: CSSセレクター（'#id', '.class', 'div > span'）
                - xpath: XPath式（'//button[contains(text(), "送信")]'）
                - text: テキスト内容で検索（部分一致）
                - textExact: テキスト内容で検索（完全一致）
                - role: ARIAロール（'button', 'link', 'textbox'）
                - testId: data-testid属性値
                - ariaLabel: aria-label属性値
                - placeholder: placeholder属性値
                - index: 操作可能要素のインデックス（0始まり）
                - nth: セレクター結果のN番目（selectorと併用）

            【操作タイプ】(op)
                クリック系:
                - 'click': 通常クリック
                - 'click_pointer': PointerEvent発火（React等のSPA向け）

                入力系:
                - 'type': テキスト入力 (text=入力値, append=True で追記)
                - 'clear': 入力欄クリア
                - 'press_key': キー送信 (key='Enter'/'Tab'/'Escape'等)

                取得系:
                - 'get_text': テキスト取得
                - 'get_html': HTML取得 (outer=True で outerHTML)
                - 'get_attr': 属性値取得 (attr='href'等)
                - 'get_value': 入力値取得

                設定系:
                - 'set_attr': 属性値設定 (attr, value)

                スクロール系:
                - 'scroll': スクロール (direction='up'/'down'/'left'/'right', amount=500)
                - 'scroll_into_view': 要素までスクロール (smooth=True, block='center')

                フォーカス系:
                - 'focus': フォーカス
                - 'blur': フォーカス解除
                - 'hover': ホバー

                フォーム系:
                - 'check': チェックボックスON
                - 'uncheck': チェックボックスOFF
                - 'select': セレクトボックス選択 (value=選択値)

                確認系:
                - 'exists': 要素存在確認
                - 'wait_visible': 要素可視確認（同期チェックのみ）

            tab_id: 対象タブID（省略時はアクティブタブ）

        Returns:
            {'type': 'batch_dom_result', 'success': True, 'results': [...], 'count': N}

        使用例:
            # 基本: CSSセレクター
            results = await ctrl.batch_dom_ops([
                {'op': 'type', 'selector': '#search', 'text': 'query'},
                {'op': 'click', 'selector': '#submit'},
            ])

            # テキストで要素を探してクリック
            results = await ctrl.batch_dom_ops([
                {'op': 'click', 'text': 'ログイン'},
                {'op': 'click', 'textExact': '送信'},
            ])

            # XPathで複雑な条件指定
            results = await ctrl.batch_dom_ops([
                {'op': 'click', 'xpath': '//button[contains(@class, "primary")]'},
                {'op': 'type', 'xpath': '//input[@name="email"]', 'text': 'test@example.com'},
            ])

            # ARIAロール/属性で検索
            results = await ctrl.batch_dom_ops([
                {'op': 'click', 'role': 'button', 'nth': 2},  # 3番目のbutton
                {'op': 'type', 'ariaLabel': '検索', 'text': 'キーワード'},
                {'op': 'type', 'placeholder': 'メールアドレス', 'text': 'a@b.com'},
            ])

            # data-testid（テスト用ID）
            results = await ctrl.batch_dom_ops([
                {'op': 'click', 'testId': 'submit-button'},
            ])

            # React等のSPA向けクリック
            results = await ctrl.batch_dom_ops([
                {'op': 'click_pointer', 'selector': '.react-button'},
            ])

            # フォーム操作
            results = await ctrl.batch_dom_ops([
                {'op': 'select', 'selector': '#country', 'value': '日本'},
                {'op': 'check', 'selector': '#agree'},
                {'op': 'press_key', 'key': 'Tab'},
            ])
        """
        return await self._cmd(type='batch_dom_ops', tabId=tab_id, operations=operations)

    async def parallel_tabs(self, tab_commands: Dict[int, List[Dict]]) -> Dict[int, Dict]:
        """
        複数タブで並列にコマンドを実行

        Args:
            tab_commands: {tab_id: [commands...], ...}

        Returns:
            {tab_id: batch_result, ...}

        使用例:
            results = await ctrl.parallel_tabs({
                123: [{'type': 'screenshot'}],
                456: [{'type': 'get_text', 'selector': 'h1'}],
            })
        """
        tasks = []
        tab_ids = []
        for tab_id, commands in tab_commands.items():
            # 各タブへの操作にtabIdを付与
            cmds_with_tab = []
            for cmd in commands:
                cmd_copy = cmd.copy()
                cmd_copy['tabId'] = tab_id
                cmds_with_tab.append(cmd_copy)
            tasks.append(self.batch_execute(cmds_with_tab))
            tab_ids.append(tab_id)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {tid: res for tid, res in zip(tab_ids, results)}

    # ========================================
    # NotebookLM (notebooklm.google.com)
    # ========================================

    async def notebooklm_list_notebooks(self, tab_id: int = None, limit: int = 100) -> Dict:
        options = {'limit': limit}
        return await self._cmd(type='notebooklm_list_notebooks', tabId=tab_id, options=options)

    async def notebooklm_create_notebook(self, tab_id: int = None, title: str = None, timeout_ms: int = 15000) -> Dict:
        options = {'title': title, 'timeoutMs': timeout_ms}
        return await self._cmd(type='notebooklm_create_notebook', tabId=tab_id, options=options)

    async def notebooklm_open_add_source(self, tab_id: int = None, open_upload_dialog: bool = True) -> Dict:
        options = {'openUploadDialog': open_upload_dialog}
        return await self._cmd(type='notebooklm_open_add_source', tabId=tab_id, options=options)

    async def notebooklm_upload_source_dropzone(
        self,
        file_data_base64: str,
        file_name: str,
        mime_type: str,
        tab_id: int = None,
        close_dialog: bool = False,
        timeout_ms: int = 10000,
    ) -> Dict:
        options = {'closeDialog': close_dialog, 'timeoutMs': timeout_ms}
        return await self._cmd(
            type='notebooklm_upload_source_dropzone',
            tabId=tab_id,
            fileData=file_data_base64,
            fileName=file_name,
            mimeType=mime_type,
            options=options,
        )

    async def notebooklm_open_customize(self, kind: str, tab_id: int = None) -> Dict:
        return await self._cmd(type='notebooklm_open_customize', tabId=tab_id, kind=kind)

    async def notebooklm_generate_artifact(self, kind: str, tab_id: int = None, prompt: str = None, length: str = None, confirm: bool = False) -> Dict:
        options = {'prompt': prompt, 'length': length, 'confirm': confirm}
        return await self._cmd(type='notebooklm_generate_artifact', tabId=tab_id, kind=kind, options=options)

    async def notebooklm_close_dialog(self, tab_id: int = None) -> Dict:
        return await self._cmd(type='notebooklm_close_dialog', tabId=tab_id)

    async def notebooklm_list_artifacts(self, tab_id: int = None, limit: int = 50) -> Dict:
        options = {'limit': limit}
        return await self._cmd(type='notebooklm_list_artifacts', tabId=tab_id, options=options)

    async def notebooklm_wait_artifacts(self, tab_id: int = None, baseline_count: int = 0, min_count: int = None, timeout_ms: int = 120000) -> Dict:
        options = {'baselineCount': baseline_count, 'minCount': min_count, 'timeoutMs': timeout_ms}
        return await self._cmd(type='notebooklm_wait_artifacts', tabId=tab_id, options=options)

    async def notebooklm_download_artifact(self, tab_id: int = None, index: Any = 'latest', text_includes: str = None) -> Dict:
        options = {'index': index, 'textIncludes': text_includes}
        return await self._cmd(type='notebooklm_download_artifact', tabId=tab_id, options=options)

    async def notebooklm_delete_from_home(self, title: str, tab_id: int = None, confirm: bool = False) -> Dict:
        options = {'confirm': confirm}
        return await self._cmd(type='notebooklm_delete_from_home', tabId=tab_id, title=title, options=options)

    async def notebooklm_list_notes(self, tab_id: int = None, limit: int = 50) -> Dict:
        options = {'limit': limit}
        return await self._cmd(type='notebooklm_list_notes', tabId=tab_id, options=options)

    async def notebooklm_add_note(self, content: str, tab_id: int = None, title: str = None) -> Dict:
        options = {'title': title}
        return await self._cmd(type='notebooklm_add_note', tabId=tab_id, content=content, options=options)

    async def notebooklm_get_note(self, index: int, tab_id: int = None) -> Dict:
        return await self._cmd(type='notebooklm_get_note', tabId=tab_id, index=index, options={})

    async def notebooklm_delete_note(self, index: int, tab_id: int = None, confirm: bool = False) -> Dict:
        options = {'confirm': confirm}
        return await self._cmd(type='notebooklm_delete_note', tabId=tab_id, index=index, options=options)

    # ========================================
    # X (x.com)
    # ========================================

    async def x_list_users(self, tab_id: int = None, limit: int = 200) -> Dict:
        return await self._cmd(type='x_list_users', tabId=tab_id, limit=limit)

    async def x_create_draft(self, text: str, tab_id: int = None, ensure_home: bool = True) -> Dict:
        options = {'ensureHome': ensure_home}
        return await self._cmd(type='x_create_draft', tabId=tab_id, text=text, options=options)

    async def x_list_new_dms(self, tab_id: int = None, limit: int = 50, auto_navigate: bool = True) -> Dict:
        options = {'autoNavigate': auto_navigate}
        return await self._cmd(type='x_list_new_dms', tabId=tab_id, limit=limit, options=options)

    async def x_posts_start(
        self,
        username: str,
        max_count: int = 1000,
        include_replies: bool = True,
        include_reposts: bool = True,
        min_likes: int = 0,
        min_reposts: int = 0,
        min_bookmarks: int = 0,
        query: str = None,
        author: str = None
    ) -> Dict:
        options = {
            'includeTweets': True,
            'includeReplies': include_replies,
            'includeReposts': include_reposts,
            'minLikes': min_likes,
            'minReposts': min_reposts,
            'minBookmarks': min_bookmarks,
            'query': query,
            'author': author
        }
        return await self._cmd(type='x_posts_start', username=username, maxCount=max_count, options=options)

    async def x_posts_next(self, session_id: str) -> Dict:
        return await self._cmd(type='x_posts_next', sessionId=session_id)

    async def x_posts_stop(self, session_id: str) -> Dict:
        return await self._cmd(type='x_posts_stop', sessionId=session_id)

    async def x_home_start(self, max_count: int = 100, include_replies: bool = True, include_reposts: bool = True) -> Dict:
        options = {
            'includeTweets': True,
            'includeReplies': include_replies,
            'includeReposts': include_reposts
        }
        return await self._cmd(type='x_home_start', maxCount=max_count, options=options)

    async def x_home_next(self, session_id: str) -> Dict:
        return await self._cmd(type='x_home_next', sessionId=session_id)

    async def x_home_stop(self, session_id: str) -> Dict:
        return await self._cmd(type='x_home_stop', sessionId=session_id)

    # ========================================
    # Tab Lock (タブ排他制御)
    # ========================================

    async def tab_lock_acquire(self, tab_id: int, agent_id: str, timeout: int = 5000) -> Dict:
        """タブのロックを取得"""
        return await self._cmd(type='tab_lock_acquire', tabId=tab_id, agentId=agent_id, timeout=timeout)

    async def tab_lock_release(self, tab_id: int, agent_id: str) -> Dict:
        """タブのロックを解放"""
        return await self._cmd(type='tab_lock_release', tabId=tab_id, agentId=agent_id)

    async def tab_lock_release_all(self, agent_id: str) -> Dict:
        """エージェントの全ロックを解放"""
        return await self._cmd(type='tab_lock_release_all', agentId=agent_id)

    async def tab_lock_status(self, tab_id: int) -> Dict:
        """タブのロック状態を確認"""
        return await self._cmd(type='tab_lock_status', tabId=tab_id)

    async def tab_lock_status_all(self) -> Dict:
        """全ロック状態を確認"""
        return await self._cmd(type='tab_lock_status_all')

    async def tab_create_locked(self, agent_id: str, url: str = 'about:blank') -> Dict:
        """新しいタブを作成してロックを取得"""
        return await self._cmd(type='tab_create_locked', agentId=agent_id, url=url)

    async def tab_close_locked(self, tab_id: int, agent_id: str) -> Dict:
        """タブを閉じてロックを解放"""
        return await self._cmd(type='tab_close_locked', tabId=tab_id, agentId=agent_id)

    # ========================================
    # Tab Session (エージェント用セッション管理)
    # ========================================

    @asynccontextmanager
    async def tab_session(self, url: str = 'about:blank', agent_id: str = None):
        """
        エージェント用タブセッションのコンテキストマネージャ

        使用例:
            async with ctrl.tab_session('https://example.com') as session:
                await session.click('button')
                await session.type_text('hello', 'input')
                # セッション終了時に自動でタブを閉じてロック解放

        Args:
            url: 開くURL
            agent_id: エージェント識別子（未指定時は自動生成）

        Yields:
            TabSession: タブ操作用セッション
        """
        session = TabSession(self, agent_id or f"agent_{uuid.uuid4().hex[:8]}")
        try:
            await session.start(url)
            yield session
        finally:
            await session.close()

    async def acquire_existing_tab(self, tab_id: int, agent_id: str = None, timeout: int = 5000):
        """
        既存タブのロックを取得してセッションを開始

        Args:
            tab_id: ロックを取得するタブID
            agent_id: エージェント識別子
            timeout: ロック取得タイムアウト（ミリ秒）

        Returns:
            TabSession: タブ操作用セッション
        """
        session = TabSession(self, agent_id or f"agent_{uuid.uuid4().hex[:8]}")
        await session.acquire(tab_id, timeout)
        return session


class TabSession:
    """
    エージェント専用タブセッション

    タブを排他的にロックし、他エージェントとの競合を防ぐ。
    セッション中は全ての操作がこのタブに対して行われる。
    """

    def __init__(self, controller: BrowserController, agent_id: str):
        self._ctrl = controller
        self._agent_id = agent_id
        self._tab_id: Optional[int] = None
        self._owned = False

    @property
    def tab_id(self) -> Optional[int]:
        """現在のタブID"""
        return self._tab_id

    @property
    def agent_id(self) -> str:
        """エージェント識別子"""
        return self._agent_id

    @property
    def is_active(self) -> bool:
        """セッションがアクティブかどうか"""
        return self._tab_id is not None and self._owned

    async def start(self, url: str = 'about:blank') -> 'TabSession':
        """新しいタブを作成してセッションを開始"""
        if self._owned:
            raise RuntimeError("Session already started")

        result = await self._ctrl.tab_create_locked(self._agent_id, url)
        if not result.get('success'):
            raise RuntimeError(f"Failed to create tab: {result.get('error')}")

        self._tab_id = result.get('tabId')
        self._owned = True
        return self

    async def acquire(self, tab_id: int, timeout: int = 5000) -> 'TabSession':
        """既存タブのロックを取得"""
        if self._owned:
            raise RuntimeError("Session already started")

        result = await self._ctrl.tab_lock_acquire(tab_id, self._agent_id, timeout)
        if not result.get('success'):
            raise RuntimeError(f"Failed to acquire tab lock: {result.get('error')}")

        self._tab_id = tab_id
        self._owned = True
        return self

    async def close(self, keep_tab: bool = False):
        """セッションを終了（タブを閉じるかロックのみ解放）"""
        if not self._owned:
            return

        if keep_tab:
            await self._ctrl.tab_lock_release(self._tab_id, self._agent_id)
        else:
            await self._ctrl.tab_close_locked(self._tab_id, self._agent_id)

        self._tab_id = None
        self._owned = False

    async def release(self):
        """ロックのみ解放（タブは閉じない）"""
        await self.close(keep_tab=True)

    def _ensure_active(self):
        """セッションがアクティブであることを確認"""
        if not self.is_active:
            raise RuntimeError("Session is not active")

    # ========================================
    # DOM操作（セッション内タブに対して実行）
    # ========================================

    async def navigate(self, url: str) -> Dict:
        """URLに移動"""
        self._ensure_active()
        return await self._ctrl.navigate(url, self._tab_id)

    async def click(self, selector: str) -> Dict:
        """要素をクリック"""
        self._ensure_active()
        return await self._ctrl.click(selector, self._tab_id)

    async def click_text(self, text: str, exact: bool = False) -> Dict:
        """テキストで要素を探してクリック"""
        self._ensure_active()
        return await self._ctrl.click_text(text, self._tab_id, exact)

    async def type_text(self, text: str, selector: str) -> Dict:
        """テキストを入力"""
        self._ensure_active()
        return await self._ctrl.type_text(text, selector, self._tab_id)

    async def get_text(self, selector: str) -> Dict:
        """テキストを取得"""
        self._ensure_active()
        return await self._ctrl.get_text(selector, self._tab_id)

    async def get_elements(self) -> List[Dict]:
        """操作可能な要素一覧を取得"""
        self._ensure_active()
        return await self._ctrl.get_elements(self._tab_id)

    async def screenshot(self, save_path: str = None) -> Dict:
        """スクリーンショットを撮影（注意: タブがアクティブになる）"""
        self._ensure_active()
        return await self._ctrl.screenshot(self._tab_id, save_path)

    async def execute_script(self, script: str) -> Dict:
        """JavaScriptを実行"""
        self._ensure_active()
        return await self._ctrl.execute_script(script, self._tab_id)

    async def wait_for_element(self, selector: str, timeout: int = 30) -> Dict:
        """要素が出現するまで待機"""
        self._ensure_active()
        return await self._ctrl.wait_for_element(selector, self._tab_id, timeout)

    async def get_page_info(self) -> Dict:
        """ページ情報を取得"""
        self._ensure_active()
        return await self._ctrl.get_page_info(self._tab_id)

    async def reload(self) -> Dict:
        """ページをリロード"""
        self._ensure_active()
        return await self._ctrl.reload(self._tab_id)

    # ========================================
    # 拡張メソッド（プロバイダ固有操作も可能）
    # ========================================

    async def cmd(self, **kwargs) -> Dict:
        """任意のコマンドを実行（tabIdは自動付与）"""
        self._ensure_active()
        kwargs['tabId'] = self._tab_id
        return await self._ctrl._cmd(**kwargs)


# ========================================
# CLI
# ========================================

def run_bridge_only():
    """ブリッジサーバーのみをフォアグラウンドで起動"""
    server = BridgeServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\n[Bridge] Stopped")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Browser Controller - 汎用ブラウザ操作ツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # タブ一覧
  python browser_controller.py tabs
  
  # 新しいタブを開く
  python browser_controller.py open "https://example.com"
  
  # 要素をクリック
  python browser_controller.py click "button.submit" --tab 123456
  
  # テキスト入力
  python browser_controller.py type "Hello" --selector "input#search"
  
  # テキスト取得
  python browser_controller.py text "h1.title"
  
  # 要素検索
  python browser_controller.py search "ログイン"
  
  # スクリーンショット
  python browser_controller.py screenshot --output page.png
  
  # DOM調査
  python browser_controller.py inspect
  python browser_controller.py inspect --mode interactive
  
  # NotebookLM: ノートブック一覧
  python browser_controller.py notebooklm_list
  
  # NotebookLM: ノートブック作成
  python browser_controller.py notebooklm_create "My Notebook"

  # X: ユーザー抽出
  python browser_controller.py x_users --limit 200
  
  # X: 投稿下書きを作成（投稿はしない）
  python browser_controller.py x_draft "hello from automation"
  
  # X: 新着DMをリスト化
  python browser_controller.py x_dms --limit 50
  
   # X: 指定ユーザーの過去投稿をMarkdown化（Flowに保存）
   python browser_controller.py x_tweets_to_md elonmusk jack --max 1000
   
   # X: フィルタ（いいね/リポスト/ブクマ/本文/作者）
   python browser_controller.py x_tweets_to_md elonmusk --max 200 --min-likes 100 --query "keyword" --author elonmusk

  
  # X: ホームタイムライン上位N件をMarkdown化（Flowに保存）
  python browser_controller.py x_home_to_md --max 100

  # タブロック: 状態確認
  python browser_controller.py lock_status

  # タブロック: 新規タブを作成してロック
  python browser_controller.py lock_create --agent myagent --url "https://example.com"

  # タブロック: 既存タブをロック
  python browser_controller.py lock_acquire 123456 --agent myagent

  # タブロック: ロック解放
  python browser_controller.py lock_release 123456 --agent myagent

  # ブリッジサーバーのみ起動
  python browser_controller.py bridge

  # 接続状態確認
  python browser_controller.py status
"""
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        default='status',
        help='Command: tabs, open, click, type, text, search, screenshot, inspect, notebooklm_list, notebooklm_create, notebooklm_add_source, notebooklm_upload_dropzone, notebooklm_customize, notebooklm_generate, notebooklm_close_dialog, notebooklm_artifacts, notebooklm_wait_artifacts, notebooklm_download, notebooklm_md_to_iv, notebooklm_delete, x_users, x_draft, x_dms, x_tweets_to_md, x_home_to_md, lock_status, lock_create, lock_acquire, lock_release, lock_release_all, bridge, status'
    )
    parser.add_argument('args', nargs='*', help='Command arguments')
    parser.add_argument('--tab', type=int, help='Tab ID')
    parser.add_argument('--selector', '-s', help='CSS selector')
    parser.add_argument('--text', '-t', help='Text to search and click')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--mode', '-m', help='Inspect mode: summary, interactive, testids, tree, aria, search')
    parser.add_argument('--limit', type=int, help='Limit for listing (x_users, x_dms)')
    parser.add_argument('--max', type=int, help='Max items (x_tweets_to_md, x_home_to_md)')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds')
    parser.add_argument('--confirm', action='store_true', help='Confirm destructive actions')
    parser.add_argument('--min-likes', dest='min_likes', type=int, help='Min likes for filtering (X)')
    parser.add_argument('--min-reposts', dest='min_reposts', type=int, help='Min reposts for filtering (X)')
    parser.add_argument('--min-bookmarks', dest='min_bookmarks', type=int, help='Min bookmarks for filtering (X)')
    parser.add_argument('--query', type=str, help='Keyword filter for post text (X)')
    parser.add_argument('--author', type=str, help='Author handle filter (X, without @)')
    parser.add_argument('--no-replies', action='store_true', help='Exclude replies (X)')
    parser.add_argument('--no-reposts', action='store_true', help='Exclude reposts/retweets (X)')
    parser.add_argument('--no-auto-bridge', action='store_true', help='Disable automatic bridge server startup')
    parser.add_argument('--agent', type=str, help='Agent ID for tab locking')
    parser.add_argument('--url', type=str, help='URL for tab creation')
    
    args = parser.parse_args()
    cmd = args.command.lower() if args.command else 'status'
    
    # ブリッジサーバーのみ起動
    if cmd == 'bridge':
        run_bridge_only()
        return
    
    ctrl = BrowserController(
        timeout=args.timeout,
        auto_bridge=not args.no_auto_bridge
    )
    
    if cmd == 'tabs':
        tabs = await ctrl.get_tabs()
        print(f"Open tabs: {len(tabs)}")
        for t in tabs:
            marker = '*' if t.get('active') else ' '
            print(f" {marker} [{t['id']}] {t.get('title', '')[:60]}")
            print(f"     {t.get('url', '')[:70]}")
    
    elif cmd == 'open':
        url = args.args[0] if args.args else 'https://www.google.com'
        result = await ctrl.new_tab(url)
        if result.get('tab'):
            print(f"[Tab] Opened: ID={result['tab']['id']}")
            print(f"  URL: {url}")
        else:
            print(f"[Error] {result.get('error')}")
    
    elif cmd == 'close':
        tab_id = args.tab or (int(args.args[0]) if args.args else None)
        if not tab_id:
            print("Error: --tab or tab ID required")
            return
        result = await ctrl.close_tab(tab_id)
        if result.get('success'):
            print(f"[Tab] Closed: {tab_id}")
        else:
            print(f"[Error] {result.get('error')}")
    
    elif cmd == 'click':
        selector = args.args[0] if args.args else args.selector
        text = getattr(args, 'text', None)

        if text:
            # テキストで要素を探してクリック
            result = await ctrl.click_text(text, args.tab, exact=False)
            if result.get('success'):
                print(f"[Click] text='{text}' → {result.get('tag', '?')}")
            else:
                print(f"[Error] {result.get('error')}")
        elif selector:
            result = await ctrl.click(selector, args.tab)
            if result.get('success'):
                print(f"[Click] {selector}")
            else:
                print(f"[Error] {result.get('error')}")
        else:
            print("Error: --selector or --text required")
    
    elif cmd == 'type':
        text = args.args[0] if args.args else None
        selector = args.selector
        if not text or not selector:
            print("Error: text and --selector required")
            return
        result = await ctrl.type_text(text, selector, args.tab)
        if result.get('success'):
            print(f"[Type] '{text}' → {selector}")
        else:
            print(f"[Error] {result.get('error')}")
    
    elif cmd == 'text':
        selector = args.args[0] if args.args else args.selector or 'body'
        result = await ctrl.get_text(selector, args.tab)
        if result.get('text'):
            print(result['text'])
        elif result.get('texts'):
            for t in result['texts']:
                print(t)
        else:
            print(f"[Error] {result.get('error', 'No text found')}")
    
    elif cmd == 'search':
        query = args.args[0] if args.args else None
        if not query:
            print("Error: search query required")
            return
        matches = await ctrl.search_elements(query, args.tab)
        print(f"Found {len(matches)} elements matching '{query}'")
        for el in matches[:20]:
            idx = el.get('index', 0)
            text = (el.get('text') or '')[:60]
            selector = (el.get('selector') or '')[:60]
            el_type = el.get('type') or ''
            print(f"  [{idx:3d}] {el_type:8s} | {text}")
            if selector:
                print(f"         selector: {selector}")
    
    elif cmd == 'screenshot':
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_path = args.output or f'screenshot_{timestamp}.png'
        
        result = await ctrl.screenshot(args.tab, save_path)
        if result.get('success'):
            print(f"[Screenshot] Saved to: {result.get('path', save_path)}")
        else:
            print(f"[Error] {result.get('error')}")
    
    elif cmd == 'inspect':
        mode = args.mode or 'summary'
        search_text = args.args[0] if args.args and mode == 'search' else None
        
        result = await ctrl.inspect_dom(args.tab, None, mode, search_text)
        
        if result.get('success'):
            print(f"=== DOM Inspection ===")
            print(f"  URL: {result.get('url', '')}")
            print(f"  Title: {result.get('title', '')}")
            
            if 'summary' in result:
                s = result['summary']
                print(f"\n=== Page Summary ===")
                print(f"  Total elements: {s.get('totalElements', 0)}")
                print(f"  Buttons: {s.get('buttons', 0)}, Links: {s.get('links', 0)}, Inputs: {s.get('inputs', 0)}")
            
            if 'interactive' in result:
                print(f"\n=== Interactive Elements ({len(result['interactive'])}) ===")
                for el in result.get('interactive', [])[:30]:
                    print(f"  [{el.get('index')}] <{el.get('tag')}> {el.get('text', '')[:40]}")
            
            if 'testIds' in result:
                print(f"\n=== data-testid Elements ({len(result['testIds'])}) ===")
                for el in result.get('testIds', []):
                    print(f"  [{el.get('tag')}] {el.get('testId')}: {el.get('text', '')[:50]}")
            
            if 'matches' in result:
                print(f"\n=== Search Results ({len(result['matches'])}) ===")
                for el in result.get('matches', []):
                    print(f"  <{el.get('tag')}> {el.get('text', '')[:80]}")
        else:
            print(f"[Error] {result.get('error')}")
    
    elif cmd == 'status':
        if BridgeServer.is_running():
            print("[Bridge] Running on ws://localhost:9224")
            tabs = await ctrl.get_tabs()
            print(f"[Tabs] {len(tabs)} tabs open")
        else:
            print("[Bridge] Not running")

    elif cmd == 'reload_extension':
        result = await ctrl._cmd(type='reload_extension')
        if result.get('success'):
            print("[Extension] Reloading...")
            print("[Extension] Wait a few seconds for reconnection")
        else:
            print(f"[Error] {result.get('error', 'Unknown error')}")

    elif cmd == 'info':
        info = await ctrl.get_page_info(args.tab)
        print(f"[Page Info]")
        print(f"  ID: {info.get('id')}")
        print(f"  URL: {info.get('url')}")
        print(f"  Title: {info.get('title')}")
        print(f"  Active: {info.get('active')}")
    
    elif cmd == 'navigate' or cmd == 'goto':
        url = args.args[0] if args.args else None
        if not url:
            print("Error: URL required")
            return
        result = await ctrl.navigate(url, args.tab)
        if result.get('success') or result.get('type') == 'navigated':
            print(f"[Navigate] {url}")
        else:
            print(f"[Error] {result.get('error')}")
    
    elif cmd == 'reload':
        result = await ctrl.reload(args.tab)
        if result.get('success'):
            print("[Reload] Done")
        else:
            print(f"[Error] {result.get('error')}")
    
    elif cmd == 'elements':
        elements = await ctrl.get_elements(args.tab)
        print(f"Found {len(elements)} elements")
        for i, el in enumerate(elements[:50]):
            text = (el.get('text') or '')[:50]
            selector = (el.get('selector') or '')[:50]
            el_type = el.get('type') or ''
            print(f"  [{i:3d}] {el_type:8s} | {text:50s} | {selector}")

    # ========================================
    # NotebookLM commands
    # ========================================

    elif cmd == 'notebooklm_list':
        limit = args.limit or (int(args.args[0]) if args.args else 100)
        result = await ctrl.notebooklm_list_notebooks(args.tab, limit=limit)
        if result.get('success') and result.get('notebooks') is not None:
            notebooks = result.get('notebooks') or []
            print(f"[NotebookLM] Notebooks: {len(notebooks)}")
            for nb in notebooks[:50]:
                title = (nb.get('title') or '').strip()
                url = nb.get('url')
                print(f" - {title}")
                if url:
                    print(f"    {url}")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'notebooklm_create':
        title = ' '.join(args.args).strip() if args.args else None
        result = await ctrl.notebooklm_create_notebook(args.tab, title=title)
        if result.get('success'):
            print("[NotebookLM] Notebook created")
            if result.get('url'):
                print(f"  {result.get('url')}")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'notebooklm_add_source':
        result = await ctrl.notebooklm_open_add_source(args.tab, open_upload_dialog=True)
        if result.get('success'):
            print("[NotebookLM] Source dialog opened")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'notebooklm_upload_dropzone':
        if len(args.args) < 1:
            print("Error: file path required")
            return
        file_path = args.args[0]
        try:
            p = Path(file_path)
            data = p.read_bytes()
        except Exception as e:
            print(f"Error: failed to read file: {e}")
            return

        file_b64 = base64.b64encode(data).decode('utf-8')
        mime = 'text/markdown' if p.suffix.lower() in ['.md', '.markdown'] else 'application/octet-stream'

        result = await ctrl.notebooklm_upload_source_dropzone(
            file_b64,
            p.name,
            mime,
            tab_id=args.tab,
            close_dialog=False,
        )
        if result.get('success'):
            print(f"[NotebookLM] Upload attempted: {result.get('fileName')}")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'notebooklm_customize':
        kind = (args.args[0] if args.args else '').strip()
        if kind not in ['audio', 'video', 'infographic', 'slides']:
            print("Error: kind must be one of: audio, video, infographic, slides")
            return
        result = await ctrl.notebooklm_open_customize(kind, args.tab)
        if result.get('success'):
            print(f"[NotebookLM] Customize opened: {kind}")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'notebooklm_generate':
        kind = (args.args[0] if args.args else '').strip()
        if kind not in ['audio', 'video', 'infographic', 'slides']:
            print("Error: kind must be one of: audio, video, infographic, slides")
            return
        result = await ctrl.notebooklm_generate_artifact(kind, args.tab, confirm=bool(args.confirm))
        if result.get('success'):
            print(f"[NotebookLM] Generation started: {kind}")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'notebooklm_close_dialog':
        result = await ctrl.notebooklm_close_dialog(args.tab)
        if result.get('success'):
            print("[NotebookLM] Dialog closed")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'notebooklm_artifacts':
        limit = args.limit or (int(args.args[0]) if args.args else 50)
        result = await ctrl.notebooklm_list_artifacts(args.tab, limit=limit)
        if result.get('success'):
            arts = result.get('artifacts') or []
            print(f"[NotebookLM] Artifacts: {len(arts)}")
            for a in arts[:20]:
                print(f" - [{a.get('index')}] {str(a.get('text') or '')[:80]}")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'notebooklm_wait_artifacts':
        baseline = int(args.args[0]) if args.args else 0
        result = await ctrl.notebooklm_wait_artifacts(args.tab, baseline_count=baseline)
        if result.get('success'):
            print(f"[NotebookLM] Artifacts ready (count={result.get('count')})")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'notebooklm_download':
        result = await ctrl.notebooklm_download_artifact(args.tab, index='latest')
        if result.get('success'):
            print("[NotebookLM] Download triggered")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'notebooklm_md_to_iv':
        if len(args.args) < 1:
            print("Error: md file path required")
            return

        md_path = Path(args.args[0])
        if not md_path.exists():
            print(f"Error: file not found: {md_path}")
            return

        title = ' '.join(args.args[1:]).strip() if len(args.args) > 1 else md_path.stem

        home = await ctrl.new_tab('https://notebooklm.google.com/')
        tab_id = (home.get('tab') or {}).get('id')
        if not tab_id:
            print("[Error] Failed to open NotebookLM tab")
            return

        print(f"[NotebookLM] Opened tab with ID: {tab_id}")

        # Wait for navigation to commit; new_tab can return before URL is ready.
        deadline = time.time() + 20
        while time.time() < deadline:
            info = await ctrl.get_page_info(tab_id)
            url = (info.get('url') or '').strip()
            if url.startswith('https://notebooklm.google.com/'):
                break
            await asyncio.sleep(0.25)

        print(f"[NotebookLM] Home page loaded, creating notebook: {title}")
        created = await ctrl.notebooklm_create_notebook(tab_id, title=title, timeout_ms=30000)
        if not created.get('success'):
            # Retry once: NotebookLM home can render progressively and first click can miss.
            await asyncio.sleep(1.0)
            created = await ctrl.notebooklm_create_notebook(tab_id, title=title, timeout_ms=30000)
        if not created.get('success'):
            print(f"[Error] create notebook: {created.get('error')}")
            return

        # After creating the notebook, the tab may have been replaced. Find the correct tab.
        created_url = (created.get('url') or '').strip()
        if not created_url:
            print(f"[Error] create notebook returned no URL")
            return

        print(f"[NotebookLM] Notebook created: {created_url}")

        # Navigate to the created URL with addSource=true parameter
        if 'addSource=' not in created_url:
            joiner = '&' if '?' in created_url else '?'
            created_url = f"{created_url}{joiner}addSource=true"

        print(f"[NotebookLM] Navigating to: {created_url}")
        await ctrl.navigate(created_url, tab_id)
        await asyncio.sleep(2.0)

        # Re-query the tabs list to find the tab that now has the created URL
        # (the original tab_id may have been invalidated)
        url_base = created_url.split('?')[0].split('&')[0]
        print(f"[NotebookLM] Finding tab with URL containing: {url_base[:60]}...")
        new_tab = await ctrl.find_tab_by_url(url_base, exact_match=False)

        if not new_tab:
            print(f"[Error] Could not find tab with URL matching notebook")
            print(f"[NotebookLM] Listing all tabs for debugging:")
            all_tabs = await ctrl.get_tabs()
            for t in all_tabs:
                print(f"  [{t.get('id')}] {t.get('url', '')[:80]}")
            return

        tab_id = new_tab.get('id')
        print(f"[NotebookLM] Found notebook tab with ID: {tab_id}")

        try:
            data = md_path.read_bytes()
        except Exception as e:
            print(f"[Error] read file: {e}")
            return

        file_b64 = base64.b64encode(data).decode('utf-8')

        # Ensure subsequent commands target the notebook tab explicitly.
        await ctrl.switch_tab(tab_id)
        await asyncio.sleep(0.5)

        opened = await ctrl.notebooklm_open_add_source(tab_id, open_upload_dialog=True)
        if not opened.get('success'):
            print(f"[Error] open upload dialog: {opened.get('error')}")
            return

        uploaded = await ctrl.notebooklm_upload_source_dropzone(file_b64, md_path.name, 'text/markdown', tab_id=tab_id)
        if not uploaded.get('success'):
            print(f"[Error] upload: {uploaded.get('error')}")
            return

        await ctrl.notebooklm_close_dialog(tab_id)

        # Wait for artifacts to appear after source upload (may take several seconds)
        await asyncio.sleep(10.0)

        arts0 = await ctrl.notebooklm_list_artifacts(tab_id, limit=200)
        baseline = int(arts0.get('count') or 0) if arts0.get('success') else 0

        if not args.confirm:
            print("[NotebookLM] Uploaded source. Stop here because generation requires --confirm")
            return

        # Infographic - New UI: click edit button, close dialog to auto-generate
        custom0 = await ctrl.notebooklm_open_customize('infographic', tab_id)
        if not custom0.get('success'):
            print(f"[Error] open infographic customize: {custom0.get('error')}")
            return
        await ctrl.notebooklm_close_dialog(tab_id)
        await asyncio.sleep(1.0)
        await ctrl.notebooklm_wait_artifacts(tab_id, baseline_count=baseline, timeout_ms=600000)
        await ctrl.notebooklm_download_artifact(tab_id, index='latest')

        arts1 = await ctrl.notebooklm_list_artifacts(tab_id, limit=200)
        baseline1 = int(arts1.get('count') or baseline) if arts1.get('success') else baseline

        # Slides - New UI: click edit button, close dialog to auto-generate
        custom1 = await ctrl.notebooklm_open_customize('slides', tab_id)
        if not custom1.get('success'):
            print(f"[Error] open slides customize: {custom1.get('error')}")
            return
        await ctrl.notebooklm_close_dialog(tab_id)
        await asyncio.sleep(1.0)
        await ctrl.notebooklm_wait_artifacts(tab_id, baseline_count=baseline1, timeout_ms=600000)
        await ctrl.notebooklm_download_artifact(tab_id, index='latest')

        arts2 = await ctrl.notebooklm_list_artifacts(tab_id, limit=200)
        baseline2 = int(arts2.get('count') or baseline1) if arts2.get('success') else baseline1

        # Video - New UI: click edit button, close dialog to auto-generate
        custom2 = await ctrl.notebooklm_open_customize('video', tab_id)
        if not custom2.get('success'):
            print(f"[Error] open video customize: {custom2.get('error')}")
            return
        await ctrl.notebooklm_close_dialog(tab_id)
        await asyncio.sleep(1.0)
        await ctrl.notebooklm_wait_artifacts(tab_id, baseline_count=baseline2, timeout_ms=600000)
        await ctrl.notebooklm_download_artifact(tab_id, index='latest')

        print("[NotebookLM] Workflow complete (upload + infographic + slides + video + download triggered)")

    elif cmd == 'notebooklm_delete':
        title = ' '.join(args.args).strip() if args.args else ''
        if not title:
            print("Error: notebook title required")
            return
        result = await ctrl.notebooklm_delete_from_home(title, args.tab, confirm=bool(args.confirm))
        if result.get('success'):
            print("[NotebookLM] Delete initiated (confirmation dialog may appear)")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'notebooklm_notes':
        limit = args.limit or (int(args.args[0]) if args.args else 50)
        result = await ctrl.notebooklm_list_notes(args.tab, limit=limit)
        if result.get('success'):
            notes = result.get('notes') or []
            print(f"[NotebookLM] Notes: {len(notes)}")
            for n in notes[:30]:
                text_preview = (n.get('text') or '')[:80].replace('\n', ' ')
                print(f" [{n.get('index')}] {text_preview}")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'notebooklm_add_note':
        content = ' '.join(args.args).strip() if args.args else ''
        if not content:
            print("Error: note content required")
            return
        result = await ctrl.notebooklm_add_note(content, args.tab)
        if result.get('success'):
            print(f"[NotebookLM] Note added (length={result.get('contentLength')})")
        else:
            print(f"[Error] {result.get('error')}")
            if result.get('debug'):
                print(f"[Debug] {result.get('debug')}")

    elif cmd == 'notebooklm_get_note':
        if not args.args:
            print("Error: note index required")
            return
        idx = int(args.args[0])
        result = await ctrl.notebooklm_get_note(idx, args.tab)
        if result.get('success'):
            print(f"[NotebookLM] Note #{result.get('index')}")
            if result.get('title'):
                print(f"  Title: {result.get('title')}")
            print(f"  Text ({result.get('textLength')} chars):")
            print(result.get('text', ''))
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'notebooklm_delete_note':
        if not args.args:
            print("Error: note index required")
            return
        idx = int(args.args[0])
        result = await ctrl.notebooklm_delete_note(idx, args.tab, confirm=bool(args.confirm))
        if result.get('success'):
            print(f"[NotebookLM] Note #{idx} deleted")
        else:
            print(f"[Error] {result.get('error')}")

    # ========================================
    # X commands
    # ========================================

    elif cmd == 'x_users':
        limit = args.limit or (int(args.args[0]) if args.args else 200)
        result = await ctrl.x_list_users(args.tab, limit=limit)
        if result.get('success') and result.get('users') is not None:
            users = result.get('users') or []
            print(f"[X] Users: {len(users)}")
            for u in users[:50]:
                print(f" - @{u.get('username')}  {u.get('url')}")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'x_draft':
        text = ' '.join(args.args) if args.args else ''
        if not text:
            print("Error: draft text required")
            return
        result = await ctrl.x_create_draft(text, args.tab, ensure_home=True)
        if result.get('success'):
            print(f"[X] Draft set (len={result.get('textLength')})")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'x_dms':
        limit = args.limit or (int(args.args[0]) if args.args else 50)
        result = await ctrl.x_list_new_dms(args.tab, limit=limit, auto_navigate=True)
        if result.get('success'):
            convos = result.get('conversations') or []
            unread = result.get('unreadCount')
            print(f"[X] DMs: {len(convos)} (unread={unread})")
            for c in convos[:30]:
                flag = 'unread' if c.get('unread') else 'read'
                print(f" - [{flag}] {c.get('href')}")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'x_tweets_to_md':
        usernames = [a for a in args.args if a and not a.startswith('-')]
        if not usernames:
            print("Error: at least 1 username required")
            return
        max_count = args.max or 1000

        from datetime import date
        out_dir = Path('Flow') / date.today().strftime('%Y%m') / date.today().strftime('%Y-%m-%d') / 'x'
        out_dir.mkdir(parents=True, exist_ok=True)

        results_summary = []

        for raw in usernames:
            username = raw.lstrip('@')
            print(f"[X] Collecting @{username} (max={max_count})...")

            start = await ctrl.x_posts_start(
                username,
                max_count=max_count,
                include_replies=(not bool(args.no_replies)),
                include_reposts=(not bool(args.no_reposts)),
                min_likes=(args.min_likes or 0),
                min_reposts=(args.min_reposts or 0),
                min_bookmarks=(args.min_bookmarks or 0),
                query=args.query,
                author=args.author
            )
            if not start.get('success'):
                results_summary.append({'username': username, 'success': False, 'error': start.get('error')})
                print(f"[X] Failed to start: {start.get('error')}")
                continue

            session_id = start.get('sessionId')
            if not session_id:
                results_summary.append({'username': username, 'success': False, 'error': 'Missing sessionId from x_posts_start'})
                print("[X] Failed to start: missing sessionId")
                continue

            all_posts = []
            all_posts.extend(start.get('posts') or [])
            done = bool(start.get('done'))

            loops = 0
            user_error = None
            try:
                while not done:
                    loops += 1
                    if loops > 2000:
                        user_error = 'Loop limit reached'
                        break

                    nxt = await ctrl.x_posts_next(session_id)
                    if not nxt.get('success'):
                        user_error = nxt.get('error')
                        print(f"[X] Fetch failed: {nxt.get('error')}")
                        done = True
                        break

                    all_posts.extend(nxt.get('posts') or [])
                    done = bool(nxt.get('done'))

                    if len(all_posts) >= max_count:
                        done = True
            finally:
                if session_id:
                    try:
                        await ctrl.x_posts_stop(session_id)
                    except Exception as e:
                        print(f"[X] Stop failed: {e}")

            if user_error:
                results_summary.append({'username': username, 'success': False, 'error': user_error})
                continue

            md_path = out_dir / f"x_{username}_posts.md"

            lines = []
            lines.append(f"# X Posts: @{username}\n")
            lines.append(f"- Generated: {date.today().isoformat()}")
            lines.append(f"- Max count: {max_count}")
            lines.append(f"- Collected: {len(all_posts)}\n")

            for p in all_posts[:max_count]:
                pid = p.get('id')
                url = p.get('url')
                created_at = p.get('createdAt')
                text_body = (p.get('text') or '').strip()

                lines.append('---')
                lines.append(f"## {created_at or ''}")
                if url:
                    lines.append(url)
                if pid:
                    lines.append(f"- id: {pid}")
                if p.get('isReply'):
                    lines.append(f"- reply: true")
                if p.get('isRepost'):
                    lines.append(f"- repost: true")
                lines.append('')
                lines.append(text_body)
                lines.append('')

            md_path.write_text('\n'.join(lines), encoding='utf-8')

            results_summary.append({'username': username, 'success': True, 'count': min(len(all_posts), max_count), 'path': str(md_path)})
            print(f"[X] Saved: {md_path} ({min(len(all_posts), max_count)} posts)")

        ok = [r for r in results_summary if r.get('success')]
        ng = [r for r in results_summary if not r.get('success')]
        print(f"\n[X] Done. success={len(ok)} fail={len(ng)}")
        for r in ng:
            print(f" - FAIL @{r.get('username')}: {r.get('error')}")

    elif cmd == 'x_home_to_md':
        max_count = args.max or 100

        from datetime import date
        out_dir = Path('Flow') / date.today().strftime('%Y%m') / date.today().strftime('%Y-%m-%d') / 'x'
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"[X] Collecting home timeline (max={max_count})...")

        start = await ctrl.x_home_start(max_count=max_count, include_replies=True, include_reposts=True)
        if not start.get('success'):
            print(f"[X] Failed to start: {start.get('error')}")
            return

        session_id = start.get('sessionId')
        if not session_id:
            print("[X] Failed to start: missing sessionId")
            return

        all_posts = []
        all_posts.extend(start.get('posts') or [])
        done = bool(start.get('done'))

        loops = 0
        user_error = None
        try:
            while not done:
                loops += 1
                if loops > 2000:
                    user_error = 'Loop limit reached'
                    break

                nxt = await ctrl.x_home_next(session_id)
                if not nxt.get('success'):
                    user_error = nxt.get('error')
                    print(f"[X] Fetch failed: {nxt.get('error')}")
                    done = True
                    break

                all_posts.extend(nxt.get('posts') or [])
                done = bool(nxt.get('done'))

                if len(all_posts) >= max_count:
                    done = True
        finally:
            if session_id:
                try:
                    await ctrl.x_home_stop(session_id)
                except Exception as e:
                    print(f"[X] Stop failed: {e}")

        if user_error:
            print(f"[X] Failed: {user_error}")
            return

        md_path = out_dir / f"x_home_timeline.md"

        lines = []
        lines.append(f"# X Home Timeline\n")
        lines.append(f"- Generated: {date.today().isoformat()}")
        lines.append(f"- Max count: {max_count}")
        lines.append(f"- Collected: {min(len(all_posts), max_count)}\n")

        for p in all_posts[:max_count]:
            pid = p.get('id')
            url = p.get('url')
            author = p.get('author')
            created_at = p.get('createdAt')
            text_body = (p.get('text') or '').strip()

            lines.append('---')
            lines.append(f"## {created_at or ''}")
            if author:
                lines.append(f"- author: @{author}")
            if url:
                lines.append(url)
            if pid:
                lines.append(f"- id: {pid}")
            if p.get('isReply'):
                lines.append(f"- reply: true")
            if p.get('isRepost'):
                lines.append(f"- repost: true")
            lines.append('')
            lines.append(text_body)
            lines.append('')

        md_path.write_text('\n'.join(lines), encoding='utf-8')
        print(f"[X] Saved: {md_path} ({min(len(all_posts), max_count)} posts)")

        return

    # ========================================
    # Tab Lock commands
    # ========================================

    elif cmd == 'lock_status':
        result = await ctrl.tab_lock_status_all()
        print("[TabLock] Status:")
        tabs = result.get('tabs', {})
        agents = result.get('agents', {})

        if not tabs and not agents:
            print("  No active locks")
        else:
            if tabs:
                print("  Locked tabs:")
                for tab_id, info in tabs.items():
                    owner = info.get('owner', 'unknown')
                    queue_len = info.get('queueLength', 0)
                    print(f"    Tab {tab_id}: owner={owner}, queue={queue_len}")
            if agents:
                print("  Active agents:")
                for agent_id, tab_ids in agents.items():
                    print(f"    {agent_id}: tabs={tab_ids}")

    elif cmd == 'lock_create':
        agent_id = args.agent or f"cli_{uuid.uuid4().hex[:8]}"
        url = args.url or 'about:blank'

        result = await ctrl.tab_create_locked(agent_id, url)
        if result.get('success'):
            print(f"[TabLock] Created and locked tab:")
            print(f"  Tab ID: {result.get('tabId')}")
            print(f"  Agent: {agent_id}")
            print(f"  URL: {url}")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'lock_acquire':
        tab_id = int(args.args[0]) if args.args else args.tab
        if not tab_id:
            print("Error: tab ID required")
            return

        agent_id = args.agent or f"cli_{uuid.uuid4().hex[:8]}"
        timeout = args.timeout * 1000 if args.timeout else 5000

        result = await ctrl.tab_lock_acquire(tab_id, agent_id, timeout)
        if result.get('success'):
            print(f"[TabLock] Acquired lock:")
            print(f"  Tab ID: {tab_id}")
            print(f"  Agent: {agent_id}")
            if result.get('alreadyOwned'):
                print("  (already owned)")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'lock_release':
        tab_id = int(args.args[0]) if args.args else args.tab
        if not tab_id:
            print("Error: tab ID required")
            return

        agent_id = args.agent
        if not agent_id:
            print("Error: --agent required")
            return

        result = await ctrl.tab_lock_release(tab_id, agent_id)
        if result.get('success'):
            print(f"[TabLock] Released lock:")
            print(f"  Tab ID: {tab_id}")
            print(f"  Agent: {agent_id}")
        else:
            print(f"[Error] {result.get('error')}")

    elif cmd == 'lock_release_all':
        agent_id = args.agent
        if not agent_id:
            print("Error: --agent required")
            return

        result = await ctrl.tab_lock_release_all(agent_id)
        if result.get('success'):
            released = result.get('releasedTabs', [])
            print(f"[TabLock] Released all locks for {agent_id}:")
            print(f"  Released tabs: {released}")
        else:
            print(f"[Error] {result.get('error')}")

    else:
        print(f"Unknown command: {cmd}")
        print("Use --help for usage information")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'bridge':
        run_bridge_only()
    else:
        asyncio.run(main())
