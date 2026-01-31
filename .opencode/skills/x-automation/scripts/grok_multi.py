#!/usr/bin/env python3
"""
Grok Parallel Research Tool
============================
3並列以上のGrok検索・ブレスト・情報収集を1つのスクリプトで実行

機能:
- 並列質問送信（3並列以上推奨）
- モデル選択
- DeepThink/DeepSearch設定
- 確実な回答取得
- タブ管理
- ブリッジサーバー内蔵（自動起動）

使用例:
  # 基本的な並列検索
  python grok_multi.py "質問1" "質問2" "質問3"
  
  # DeepThinkで難問を解く
  python grok_multi.py "難しい質問1" "難しい質問2" --deepthink
  
  # DeepSearchで検索
  python grok_multi.py "検索1" "検索2" --deepsearch
  
  # タブ一覧を確認
  python grok_multi.py tabs
  
  # モデル一覧を確認
  python grok_multi.py models
  
  # 単一チャット
  python grok_multi.py chat -m "質問内容"
  
  # ブリッジサーバーのみ起動（手動）
  python grok_multi.py bridge
"""

import asyncio
import json
import time
import base64
import mimetypes
import os
import sys
import socket
import subprocess
from typing import List, Dict, Optional, Any
from pathlib import Path
from contextlib import asynccontextmanager
import uuid

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


## httpx/html2text は不要（Chrome拡張経由でDOM取得するため削除）


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
# Grok Controller
# ========================================

class GrokController:
    """Grok操作の統合コントローラー"""
    
    BRIDGE_URL = "ws://localhost:9224"
    GROK_URL = "https://x.com/i/grok"
    
    def __init__(self, timeout: int = 1200, poll_interval: int = 5, auto_bridge: bool = True):
        self.timeout = timeout
        self.poll_interval = poll_interval
        self.auto_bridge = auto_bridge
        self._ws = None
        self._request_id = 0
        self._lock = asyncio.Lock()
        self._session_tabs = []
        self._load_session_tabs()

    # ========================================
    # セッション管理
    # ========================================

    def _get_session_file(self) -> Path:
        return Path.home() / ".grok_multi_session.json"

    def _load_session_tabs(self):
        session_file = self._get_session_file()
        if session_file.exists():
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    self._session_tabs = data.get('tabs', [])
            except Exception:
                self._session_tabs = []
        else:
            self._session_tabs = []

    def _save_session_tabs(self, tabs: List[Dict], turns_total: int = 1, turns_current: int = 1) -> None:
        session_file = self._get_session_file()
        try:
            session_data = {
                'tabs': tabs,
                'turns': {
                    'total': turns_total,
                    'current': turns_current,
                    'remaining': turns_total - turns_current
                }
            }
            with open(session_file, 'w') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            self._session_tabs = tabs
        except Exception as e:
            print(f"[Warning] Failed to save session: {e}")

    def _get_session_turns(self) -> Dict:
        session_file = self._get_session_file()
        if session_file.exists():
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    return data.get('turns', {'total': 1, 'current': 1, 'remaining': 0})
            except Exception:
                pass
        return {'total': 1, 'current': 1, 'remaining': 0}

    def get_session_tabs(self) -> List[int]:
        return [t.get('id') for t in self._session_tabs if t.get('id')]

    def _get_session_tab_topic(self, tab_id: int) -> Optional[str]:
        for t in self._session_tabs:
            if t.get('id') == tab_id:
                return t.get('topic')
        return None

    def _get_session_tab_md_path(self, tab_id: int) -> Optional[str]:
        for t in self._session_tabs:
            if t.get('id') == tab_id:
                return t.get('md_path')
        return None

    def _get_session_tab_url(self, tab_id: int) -> Optional[str]:
        for t in self._session_tabs:
            if t.get('id') == tab_id:
                return t.get('url')
        return None

    def _update_session_tab_md_path(self, tab_id: int, md_path: str) -> None:
        """セッションタブのmd_pathを更新"""
        for entry in self._session_tabs:
            if entry.get('id') == tab_id:
                entry['md_path'] = md_path
                turns = self._get_session_turns()
                self._save_session_tabs(self._session_tabs, turns.get('total', 1), turns.get('current', 1))
                return
        # エントリがなければ追加
        self._session_tabs.append({'id': tab_id, 'md_path': md_path})
        turns = self._get_session_turns()
        self._save_session_tabs(self._session_tabs, turns.get('total', 1), turns.get('current', 1))

    async def _build_session_entries(self, tab_ids: List[int], topic: str = None, md_paths: List[str] = None) -> List[Dict]:
        tabs = await self.get_tabs()
        by_id = {t.get('id'): t for t in tabs if t.get('id')}
        # 既存セッションからtopicとmd_pathを引き継ぐ
        existing_by_id = {t.get('id'): t for t in self._session_tabs if t.get('id')}
        entries = []
        for i, tid in enumerate(tab_ids):
            info = by_id.get(tid, {})
            existing = existing_by_id.get(tid, {})
            # topic: 引数で指定されていればそれを使用、なければ既存を引き継ぐ
            entry_topic = topic if topic is not None else existing.get('topic')
            # md_path: 引数で指定されていればそれを使用、なければ既存を引き継ぐ
            entry_md_path = md_paths[i] if md_paths and i < len(md_paths) else existing.get('md_path')
            entry = {'id': tid, 'url': info.get('url'), 'topic': entry_topic, 'md_path': entry_md_path}
            entries.append(entry)
        return entries

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
                response = await asyncio.wait_for(self._ws.recv(), timeout=30)
                return json.loads(response)
            except asyncio.TimeoutError:
                return {'error': 'Timeout waiting for response'}
    
    async def close(self):
        """WebSocket接続を閉じる"""
        if self._ws:
            await self._ws.close()
            self._ws = None

    # ========================================
    # タブロック（並列エージェント対応）
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
        """タブのロック状態を取得"""
        return await self._cmd(type='tab_lock_status', tabId=tab_id)

    async def tab_lock_status_all(self) -> Dict:
        """全ロック状態を取得"""
        return await self._cmd(type='tab_lock_status_all')

    async def tab_create_locked(self, agent_id: str, url: str = None) -> Dict:
        """新しいタブを作成してロックを取得"""
        return await self._cmd(type='tab_create_locked', agentId=agent_id, url=url or self.GROK_URL)

    async def tab_close_locked(self, tab_id: int, agent_id: str) -> Dict:
        """タブを閉じてロックを解放"""
        return await self._cmd(type='tab_close_locked', tabId=tab_id, agentId=agent_id)

    @asynccontextmanager
    async def tab_session(self, agent_id: str = None, url: str = None):
        """
        タブセッションのコンテキストマネージャー

        使用例:
            async with ctrl.tab_session('agent-1') as session:
                await session.send_message("Hello")
                response = await session.get_response()
        """
        if agent_id is None:
            agent_id = f"grok-{uuid.uuid4().hex[:8]}"

        session = GrokTabSession(self, agent_id)
        try:
            await session.start(url or self.GROK_URL)
            yield session
        finally:
            await session.close()

    # ========================================
    # タブ操作
    # ========================================
    
    async def get_tabs(self) -> List[Dict]:
        """タブ一覧を取得"""
        result = await self._cmd(type='get_tabs')
        return result.get('tabs', [])
    
    async def new_tab(self, url: str = None) -> Dict:
        """新しいGrokタブを開く"""
        return await self._cmd(type='new_tab', url=url or self.GROK_URL)
    
    async def close_tab(self, tab_id: int) -> Dict:
        """タブを閉じる"""
        return await self._cmd(type='close_tab', tabId=tab_id)
    
    async def switch_tab(self, tab_id: int) -> Dict:
        """タブを切り替える"""
        return await self._cmd(type='switch_tab', tabId=tab_id)
    
    # ========================================
    # 基本DOM操作（共通機能）
    # ========================================
    
    async def click(self, selector: str, tab_id: int = None) -> Dict:
        """要素をクリック"""
        return await self._cmd(type='click', selector=selector, tabId=tab_id)
    
    async def type_text(self, text: str, selector: str, tab_id: int = None) -> Dict:
        """テキストを入力"""
        return await self._cmd(type='type', text=text, selector=selector, tabId=tab_id)
    
    async def get_text(self, selector: str, tab_id: int = None) -> Dict:
        """テキストを取得"""
        return await self._cmd(type='get_text', selector=selector, tabId=tab_id)
    
    async def get_elements(self, tab_id: int = None) -> List[Dict]:
        """操作可能な要素一覧を取得"""
        result = await self._cmd(type='get_elements', tabId=tab_id)
        return result.get('elements', [])
    
    async def search_elements(self, query: str, tab_id: int = None) -> List[Dict]:
        """
        要素をテキストで検索
        
        Args:
            query: 検索文字列（大文字小文字を区別しない）
            tab_id: タブID
        
        Returns:
            マッチした要素のリスト
        """
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
    
    async def get_page_text(self, tab_id: int = None, selector: str = 'body') -> str:
        """ページ全体のテキストを取得"""
        result = await self.get_text(selector, tab_id)
        return result.get('text', '')
    
    # ========================================
    # スクリーンショット（共通機能）
    # ========================================
    
    async def screenshot(self, tab_id: int = None, save_path: str = None) -> Dict:
        """
        タブのスクリーンショットを撮影
        
        Args:
            tab_id: タブID（省略時はアクティブタブ）
            save_path: 保存先パス（省略時はdata URLのみ返す）
        
        Returns:
            成功時: {'success': True, 'dataUrl': '...', 'path': '...'}
        """
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
    # DOM調査（共通機能）
    # ========================================
    
    async def inspect_dom(self, tab_id: int = None, selector: str = None, mode: str = 'summary', text: str = None) -> Dict:
        """
        DOMを調査する
        
        Args:
            tab_id: タブID（省略時はアクティブタブ）
            selector: 特定セレクター（指定時はその要素を詳細調査）
            mode: 調査モード
                - summary: ページ全体のサマリー（デフォルト）
                - interactive: インタラクティブ要素一覧
                - testids: data-testid属性を持つ要素一覧
                - tree: body直下の要素ツリー
                - aria: ARIA属性を持つ要素
                - search: テキスト検索（textパラメータ必須）
            text: 検索テキスト（mode='search'時に使用）
        
        Returns:
            調査結果
        """
        options = {'mode': mode}
        if text:
            options['text'] = text
        return await self._cmd(type='inspect_dom', tabId=tab_id, selector=selector, options=options)
    
    # ========================================
    # ファイル添付（共通機能）
    # ========================================
    
    async def _wait_for_attachment_ready(self, tab_id: int, file_name: str, timeout: int = 30) -> bool:
        """ファイル添付が完了し送信可能になるまで待機"""
        start = time.time()
        while time.time() - start < timeout:
            result = await self._cmd(type='grok_check_attachment', tabId=tab_id, fileName=file_name)
            if result.get('ready'):
                return True
            if result.get('attached') and result.get('sendEnabled') and not result.get('isProcessing'):
                return True
            await asyncio.sleep(1)
        return False
    
    # ========================================
    # Grok専用機能
    # ========================================
    
    async def send_message(self, message: str, tab_id: int = None, files: List[str] = None, max_retries: int = 3) -> Dict:
        """メッセージを送信（ファイル添付対応、入力確認・リトライ付き）

        フロー:
        1. ファイルがあれば添付（確認するまでリトライ）
        2. メッセージ入力・送信（確認するまでリトライ）

        Args:
            message: 送信するメッセージ
            tab_id: タブID
            files: 添付ファイルパスのリスト（None or []なら添付なし）
            max_retries: 各ステップのリトライ回数
        """
        # Step 1: ファイル添付（指定があれば）
        if files:
            for file_path in files:
                attach_result = await self._attach_file_with_retry(file_path, tab_id, max_retries=max_retries)
                if not attach_result.get('success'):
                    return {'success': False, 'error': f"File attachment failed: {attach_result.get('error')}", 'file': file_path}

        # Step 2: メッセージ送信（リトライ付き）
        last_error = None
        for attempt in range(max_retries):
            result = await self._cmd(type='grok_send_message', message=message, tabId=tab_id)
            if result.get('success'):
                return {'success': True, 'message': message, 'tab_id': tab_id, 'files': files or []}
            last_error = result.get('error', 'Failed to send')
            await asyncio.sleep(1.5)
        return {'success': False, 'error': last_error or 'Failed after retries'}

    async def _attach_file_with_retry(self, file_path: str, tab_id: int, max_retries: int = 3, timeout: int = 30) -> Dict:
        """ファイルを添付して確認（内部用）"""
        path = Path(file_path)
        if not path.exists():
            return {'success': False, 'error': f'File not found: {file_path}'}

        with open(path, 'rb') as f:
            file_data = base64.b64encode(f.read()).decode('utf-8')

        mime_type, _ = mimetypes.guess_type(str(path))
        if not mime_type:
            mime_type = 'application/octet-stream'

        for attempt in range(max_retries):
            result = await self._cmd(
                type='grok_attach_file',
                fileData=file_data,
                fileName=path.name,
                mimeType=mime_type,
                tabId=tab_id
            )

            if not result.get('success'):
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                return result

            # ファイル処理完了まで固定待機（DOM検査するとリレンダリングでキャンセルされる可能性あり）
            await asyncio.sleep(15)
            return {'success': True, 'fileName': path.name}

        return {'success': False, 'error': f'Attachment failed after {max_retries} attempts'}
    
    async def get_response(self, tab_id: int = None) -> str:
        """回答を取得"""
        result = await self._cmd(type='grok_get_response', tabId=tab_id)
        return result.get('response', '')

    async def get_full_conversation(self, tab_id: int = None) -> List[Dict]:
        """タブ内の全会話履歴を取得（user/assistant交互）

        Returns:
            [{'role': 'user', 'content': '...'}, {'role': 'assistant', 'content': '...'}, ...]
        """
        conversation = []

        # Grokのメッセージセレクター（DOM構造に基づく）
        # userメッセージ
        user_result = await self.get_text('[data-testid="user-message"], .user-message', tab_id)
        user_messages = user_result.get('texts', []) if user_result else []

        # assistantメッセージ
        assistant_result = await self.get_text('[data-testid="assistant-message"], .assistant-message, .markdown-content', tab_id)
        assistant_messages = assistant_result.get('texts', []) if assistant_result else []

        # フォールバック：全ページテキストから抽出を試みる
        if not user_messages and not assistant_messages:
            full_content = await self._get_full_page_content(tab_id)
            if full_content:
                # 単一の応答として扱う
                conversation.append({'role': 'assistant', 'content': full_content})
                return conversation

        # 交互に組み立て
        max_len = max(len(user_messages), len(assistant_messages))
        for i in range(max_len):
            if i < len(user_messages) and user_messages[i]:
                conversation.append({'role': 'user', 'content': user_messages[i]})
            if i < len(assistant_messages) and assistant_messages[i]:
                conversation.append({'role': 'assistant', 'content': assistant_messages[i]})

        return conversation

    async def is_generating(self, tab_id: int = None) -> bool:
        """生成中かどうかを確認"""
        result = await self._cmd(type='grok_is_generating', tabId=tab_id)
        return result.get('generating', False)
    
    async def get_models(self, tab_id: int = None) -> Dict:
        """利用可能なモデル一覧を取得"""
        return await self._cmd(type='grok_get_models', tabId=tab_id)
    
    async def select_model(self, model: str, tab_id: int = None) -> Dict:
        """モデルを選択"""
        return await self._cmd(type='grok_select_model', model=model, tabId=tab_id)
    
    async def set_mode(self, mode: str, tab_id: int = None) -> Dict:
        """モードを設定（think/search等）"""
        return await self._cmd(type='grok_set_mode', mode=mode, tabId=tab_id)
    
    async def is_deepthink(self, tab_id: int = None) -> Dict:
        """DeepThink状態を確認"""
        return await self._cmd(type='grok_is_deepthink', tabId=tab_id)
    
    async def enable_deepthink(self, tab_id: int = None) -> Dict:
        """DeepThinkを有効化"""
        return await self._cmd(type='grok_enable_deepthink', tabId=tab_id)
    
    async def disable_deepthink(self, tab_id: int = None) -> Dict:
        """DeepThinkを無効化"""
        return await self._cmd(type='grok_disable_deepthink', tabId=tab_id)
    
    async def enable_deepsearch(self, tab_id: int = None) -> Dict:
        """DeepSearchを有効化"""
        return await self._cmd(type='grok_enable_deepsearch', tabId=tab_id)
    
    # ========================================
    # 並列検索
    # ========================================
    
    async def parallel_search(
        self,
        questions: List[str],
        model: str = None,
        deepthink: bool = False,
        deepsearch: bool = False,
        close_tabs: bool = True,
        turns: int = 1,
        files: List[str] = None
    ) -> List[Dict]:
        """
        複数の質問を並列で送信し、全ての応答を取得

        Args:
            questions: 質問リスト
            model: 使用するモデル
            deepthink: DeepThinkを有効化するか
            deepsearch: DeepSearchを有効化するか
            close_tabs: 回答取得後にタブを閉じるか
            turns: 会話ターン数（デフォルト: 1 = 単発）
            files: 添付するファイルのパスリスト
        """
        MAX_PARALLEL = 10
        n = len(questions)
        
        if n > MAX_PARALLEL:
            print(f"Warning: Maximum {MAX_PARALLEL} parallel queries allowed. Truncating from {n}.")
            questions = questions[:MAX_PARALLEL]
            n = MAX_PARALLEL
        
        print(f"\n{'='*60}")
        print(f"Grok Parallel Search: {n} questions")
        print('='*60)
        if model:
            print(f"Model: {model}")
        if deepthink:
            print("DeepThink: Enabled")
        if deepsearch:
            print("DeepSearch: Enabled")
        print()
        
        # 1. タブを開く
        print(f"[1/4] Opening {n} Grok tabs...")
        tab_ids = []
        for i in range(n):
            result = await self.new_tab()
            if result.get('tab', {}).get('id'):
                tab_ids.append(result['tab']['id'])
                print(f"  Tab {i+1}: ID={result['tab']['id']}")
            await asyncio.sleep(1)
        
        if len(tab_ids) != n:
            return [{'success': False, 'error': f'Failed to open tabs: {len(tab_ids)}/{n}'}]
        
        print("  Waiting for pages to load...")
        await asyncio.sleep(3)
        
        # 2. モデル/モード設定
        if model:
            print(f"\n[1.5] Selecting model: {model}...")
            for i, tid in enumerate(tab_ids):
                r = await self.select_model(model, tid)
                status = "OK" if r.get('success') else f"FAIL: {r.get('error', '')}"
                print(f"  Tab {i+1}: {status}")
                await asyncio.sleep(0.5)
        
        if deepthink:
            print(f"\n[1.6] Enabling DeepThink...")
            for i, tid in enumerate(tab_ids):
                r = await self.enable_deepthink(tid)
                status = "OK" if r.get('success') else f"FAIL: {r.get('error', '')}"
                print(f"  Tab {i+1}: {status}")
                await asyncio.sleep(0.5)
        
        if deepsearch:
            print(f"\n[1.7] Enabling DeepSearch...")
            for i, tid in enumerate(tab_ids):
                r = await self.enable_deepsearch(tid)
                status = "OK" if r.get('success') else f"FAIL: {r.get('error', '')}"
                print(f"  Tab {i+1}: {status}")
                await asyncio.sleep(0.5)
        
        # 3. 質問を送信（ファイル添付も含む）
        print(f"\n[2/4] Sending questions...")
        if files:
            print(f"Files: {', '.join(files)}")
        for i, (tid, q) in enumerate(zip(tab_ids, questions)):
            # 最初のタブにのみファイルを添付（並列時は各タブに同じファイル）
            send_files = files if files else None
            await self.send_message(q, tid, files=send_files)
            print(f"  Tab {i+1}: Sent '{q[:50]}...'")
            await asyncio.sleep(0.5)
        
        # 4. 回答を待機
        print(f"\n[3/4] Waiting for responses (timeout: {self.timeout}s)...")

        topic = self._derive_topic_from_questions(questions)
        md_paths = self._init_individual_mds(questions, model, deepthink, deepsearch, topic=topic)
        print(f"[Output] Writing to {len(md_paths)} separate MD files:")
        for i, p in enumerate(md_paths):
            print(f"  Q{i+1}: {p}")

        results = [None] * n

        async def wait_for_response(tid: int, idx: int, question: str) -> Dict:
            start = time.time()
            last_response = ""
            stable_count = 0
            fallback_attempted = False

            while True:
                elapsed = time.time() - start
                if elapsed > self.timeout:
                    if not fallback_attempted:
                        fallback_attempted = True
                        print(f"  Tab {idx+1}: Timeout - trying DOM fallback via extension...")
                        fallback_response = await self._get_full_page_content(tid)
                        if fallback_response and len(fallback_response) > 50:
                            result = {
                                'success': True, 'index': idx,
                                'question': question, 'response': fallback_response,
                                'tab_id': tid, 'elapsed': elapsed,
                                'fallback': True
                            }
                            self._write_individual_md(md_paths[idx], result)
                            results[idx] = result
                            print(f"  Tab {idx+1}: Recovered via DOM fallback ({elapsed:.1f}s) → {Path(md_paths[idx]).name}")
                            return result

                    result = {
                        'success': False, 'error': 'Timeout',
                        'index': idx, 'question': question, 'tab_id': tid,
                        'response': last_response, 'elapsed': elapsed
                    }
                    self._write_individual_md(md_paths[idx], result)
                    results[idx] = result
                    print(f"  Tab {idx+1}: Timeout ({elapsed:.1f}s)")
                    return result

                generating = await self.is_generating(tid)
                response = await self.get_response(tid)

                if response and len(response) > 5:
                    if not generating:
                        if response == last_response:
                            stable_count += 1
                            if stable_count >= 2:
                                result = {
                                    'success': True, 'index': idx,
                                    'question': question, 'response': response,
                                    'tab_id': tid, 'elapsed': elapsed
                                }
                                self._write_individual_md(md_paths[idx], result)
                                results[idx] = result
                                print(f"  Tab {idx+1}: Done ({elapsed:.1f}s) → {Path(md_paths[idx]).name}")
                                return result
                        else:
                            stable_count = 0
                    else:
                        stable_count = 0
                    last_response = response

                status = "Generating..." if generating else "Waiting..."
                print(f"  Tab {idx+1}: {status} ({int(elapsed)}s)")
                await asyncio.sleep(self.poll_interval)
        
        tasks = [asyncio.create_task(wait_for_response(tid, i, q)) 
                 for i, (tid, q) in enumerate(zip(tab_ids, questions))]
        
        await asyncio.gather(*tasks)
        
        # 5. 結果サマリー
        print(f"\n{'='*60}")
        print("[4/4] Summary")
        print('='*60)
        
        for r in results:
            if r is None:
                continue
            idx = r.get('index', 0)
            status = "OK" if r.get('success') else f"FAIL ({r.get('error')})"
            print(f"  Q{idx+1}: {status} ({r.get('elapsed', 0):.1f}s)")

        print(f"\n[Output] Saved to {len(md_paths)} files:")
        for p in md_paths:
            print(f"  - {p}")

        # セッションタブを保存（マルチターン対応）
        if turns > 1 or not close_tabs:
            session_entries = await self._build_session_entries(tab_ids, topic=topic, md_paths=md_paths)
            self._save_session_tabs(session_entries, turns_total=turns, turns_current=1)
            remaining = turns - 1
            print(f"\n[Turn 1/{turns}] Complete.")
            if remaining > 0:
                print(f"[Session] {len(tab_ids)} tabs saved. Remaining turns: {remaining}")
                print(f"[Next] Send follow-up: python grok_multi.py reply \"Q1\" \"Q2\" ...")
            else:
                print(f"[Session] Saved {len(tab_ids)} tabs for recover")
                print(f"  Use 'python grok_multi.py reply \"Q1\" \"Q2\" ...' to continue")

        # タブを閉じる（単発かつclose_tabs指定時のみ）
        if close_tabs and turns == 1:
            print(f"\n[Cleanup] Closing {len(tab_ids)} tabs...")
            for tid in tab_ids:
                await self.close_tab(tid)
            print("  Done.")

        return results
    
    def _get_flow_path(self, filename: str) -> Path:
        """Flowディレクトリ内のパスを取得"""
        from datetime import datetime
        
        now = datetime.now()
        yymm = now.strftime("%Y%m")
        yyyymmdd = now.strftime("%Y-%m-%d")
        
        script_dir = Path(__file__).resolve().parent
        flow_dir = None
        
        for parent in script_dir.parents:
            candidate = parent / "Flow"
            if candidate.exists() and candidate.is_dir():
                flow_dir = candidate
                break
        
        if flow_dir is None:
            return Path(filename)

        # アプリ名を追加: Flow/YYYYMM/YYYY-MM-DD/X/filename
        app_dir = flow_dir / yymm / yyyymmdd / "X"
        app_dir.mkdir(parents=True, exist_ok=True)
        return app_dir / filename
    
    def _init_results_md(self, questions: List[str], model: str = None, deepthink: bool = False, deepsearch: bool = False) -> str:
        """MDファイルを初期化"""
        from datetime import datetime
        
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        filename = f"grok_search_{timestamp}.md"
        save_path = self._get_flow_path(filename)
        
        lines = [
            f"# Grok Parallel Search Results",
            f"",
            f"**実行日時**: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**モデル**: {model or 'default'}",
            f"**DeepThink**: {'Enabled' if deepthink else 'Disabled'}",
            f"**DeepSearch**: {'Enabled' if deepsearch else 'Disabled'}",
            f"**質問数**: {len(questions)}",
            f"",
            "## 質問一覧",
            ""
        ]
        
        for i, q in enumerate(questions):
            lines.append(f"{i+1}. {q}")
        
        lines.extend(["", "---", "", "## 回答", ""])
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        return str(save_path)
    
    def _append_result_md(self, md_path: str, result: Dict) -> None:
        """MDファイルに結果を追記"""
        idx = result.get('index', 0) + 1
        question = result.get('question', '')
        success = result.get('success', False)
        elapsed = result.get('elapsed', 0)
        response = result.get('response', '')
        error = result.get('error', '')
        
        lines = [
            f"### Q{idx}: {question}",
            ""
        ]
        
        if success:
            lines.append(f"**ステータス**: OK ({elapsed:.1f}s)")
            lines.append("")
            lines.append(response)
        else:
            lines.append(f"**ステータス**: FAIL - {error}")
            if response:
                lines.append("")
                lines.append(f"**部分回答**: {response[:500]}")
        
        lines.extend(["", "---", ""])
        
        with open(md_path, 'a', encoding='utf-8') as f:
            f.write("\n".join(lines))

    def _sanitize_topic(self, topic: str, max_len: int = 60) -> str:
        import re
        if not topic:
            return 'untitled'
        t = str(topic).strip()
        t = re.sub(r'\s+', ' ', t)
        t = t.replace('/', '_').replace('\\', '_').replace(':', '_')
        t = re.sub(r'[\*\?"<>\|]', '_', t)
        t = t.strip(' ._').replace(' ', '_')
        if len(t) > max_len:
            t = t[:max_len]
        return t or 'untitled'

    def _derive_topic_from_questions(self, questions: List[str]) -> str:
        if not questions:
            return 'untitled'
        return self._sanitize_topic(questions[0])

    def _get_topic_flow_path(self, filename: str, topic: str = None) -> Path:
        from datetime import datetime
        now = datetime.now()
        yymm = now.strftime("%Y%m")
        yyyymmdd = now.strftime("%Y-%m-%d")
        script_dir = Path(__file__).resolve().parent
        flow_dir = None
        for parent in script_dir.parents:
            candidate = parent / "Flow"
            if candidate.exists() and candidate.is_dir():
                flow_dir = candidate
                break
        if flow_dir is None:
            return Path(filename)
        # アプリ名を追加: Flow/YYYYMM/YYYY-MM-DD/X/セッション名
        if topic:
            topic_dir = flow_dir / yymm / yyyymmdd / "X" / self._sanitize_topic(topic)
        else:
            topic_dir = flow_dir / yymm / yyyymmdd / "X"
        topic_dir.mkdir(parents=True, exist_ok=True)
        return topic_dir / filename

    def _init_individual_mds(self, questions: List[str], model: str = None, deepthink: bool = False, deepsearch: bool = False, topic: str = None) -> List[str]:
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        md_paths = []
        for i, question in enumerate(questions):
            filename = f"grok_q{i+1}_{timestamp}.md"
            save_path = self._get_topic_flow_path(filename, topic)
            lines = [
                f"# Grok Search Result",
                f"",
                f"**Query {i+1}**: {question}",
                f"**実行日時**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"**モデル**: {model or 'default'}",
                f"**DeepThink**: {'Enabled' if deepthink else 'Disabled'}",
                f"**DeepSearch**: {'Enabled' if deepsearch else 'Disabled'}",
                f"",
                "---",
                "",
                "## 回答",
                "",
                "*回答待機中...*",
                ""
            ]
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
            md_paths.append(str(save_path))
        return md_paths

    def _get_last_turn_number(self, md_path: str) -> int:
        """既存MDファイルから最後のTurn番号を取得

        ファイルが存在しない場合や、Turn形式でない場合は0を返す
        """
        import re
        path = Path(md_path)
        if not path.exists():
            return 0

        try:
            content = path.read_text(encoding='utf-8')
            matches = re.findall(r'^## Turn (\d+)', content, re.MULTILINE)
            if matches:
                return max(int(m) for m in matches)
            return 0
        except Exception:
            return 0

    def _write_full_conversation_md(self, md_path: str, conversation: List[Dict], tab_id: int, url: str, topic: str = None) -> None:
        """全会話履歴をMDファイルに書き出し（完全上書き）"""
        from datetime import datetime

        lines = [
            f"# Grok Multi-Turn Session",
            f"",
            f"**Tab ID**: {tab_id}",
            f"**URL**: {url}" if url else "",
            f"**Topic**: {topic}" if topic else "",
            f"**Recovered**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"",
        ]

        turn = 0
        for msg in conversation:
            if msg['role'] == 'user':
                lines.append(f"---")
                lines.append(f"")
                turn += 1
                lines.append(f"## Turn {turn}")
                lines.append(f"**Query**: {msg['content'][:200]}{'...' if len(msg['content']) > 200 else ''}")
                lines.append(f"")
            elif msg['role'] == 'assistant':
                lines.append(msg['content'])
                lines.append(f"")

        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))

    def _write_individual_md(self, md_path: str, result: Dict, turn: int = 1) -> None:
        """個別MDファイルに結果を書き込み（上書きまたは追記）

        turn=1の場合: ファイルヘッダー + Turn 1 を新規作成
        turn>1の場合: 既存ファイルに Turn N を追記
        """
        from datetime import datetime

        question = result.get('question', '')
        success = result.get('success', False)
        response = result.get('response', '')
        error = result.get('error', '')
        elapsed = result.get('elapsed', 0)
        tab_id = result.get('tab_id', 'unknown')

        if turn == 1:
            # 初回ターン: ファイルヘッダー + Turn 1
            lines = [
                f"# Grok Multi-Turn Session",
                f"",
                f"**Tab ID**: {tab_id}",
                f"**セッション開始**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"",
                f"---",
                f"",
                f"## Turn 1",
                f"**Query**: {question}",
                f"**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Elapsed**: {elapsed:.1f}s",
                f"**Status**: {'Success' if success else 'Failed'}",
                f""
            ]

            if error:
                lines.append(f"**Error**: {error}")
                lines.append("")

            if success and response:
                lines.append(response)
            elif response:
                lines.append(f"**部分回答**:\n{response}")
            else:
                lines.append("*回答を取得できませんでした*")

            lines.append("")

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
        else:
            # 2回目以降: 既存ファイルに追記
            with open(md_path, 'a', encoding='utf-8') as f:
                f.write(f"\n---\n\n## Turn {turn}\n")
                f.write(f"**Query**: {question}\n")
                f.write(f"**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Elapsed**: {elapsed:.1f}s\n")
                f.write(f"**Status**: {'Success' if success else 'Failed'}\n\n")
                if success:
                    f.write(response if response else "*応答が空です*")
                else:
                    f.write(f"**Error**: {error}\n")
                f.write("\n")

    async def _get_full_page_content(self, tab_id: int) -> Optional[str]:
        """
        Chrome拡張経由でページ全体のコンテンツを取得（フォールバック用）
        
        ログイン済みセッションでDOMから直接テキストを取得するため、
        httpx等の外部フェッチよりも確実に回答を取得できる。
        
        Args:
            tab_id: タブID
        
        Returns:
            ページコンテンツ、または失敗時はNone
        """
        try:
            # まず通常の回答取得を再試行
            response = await self.get_response(tab_id)
            if response and len(response) > 50:
                return response
            
            # 失敗した場合、より広範なセレクタで取得
            # Grokの回答領域を取得
            selectors = [
                '[data-testid="tweetText"]',  # ツイート形式の回答
                '[data-testid="messageText"]',  # メッセージ形式
                'article',  # 記事領域
                'main',  # メインコンテンツ
            ]
            
            for selector in selectors:
                result = await self.get_text(selector, tab_id)
                if result.get('texts'):
                    texts = [t for t in result['texts'] if len(t) > 50]
                    if texts:
                        # 最後の回答を返す
                        return texts[-1]
                elif result.get('text') and len(result.get('text', '')) > 50:
                    return result['text']
            
            # 最終手段: ページ全体のテキスト
            page_text = await self.get_page_text(tab_id)
            if page_text and len(page_text) > 100:
                return page_text
            
            return None
            
        except Exception as e:
            print(f"  [DOM Fallback] Failed: {e}")
            return None
    
    # ========================================
    # 単一チャット
    # ========================================
    
    async def chat(self, message: str, tab_id: int = None, wait: bool = True) -> Dict:
        """単一のメッセージを送信"""
        send_result = await self.send_message(message, tab_id)
        if not send_result.get('success'):
            return send_result
        
        # 送信に使用したタブIDを取得（タブ指定がない場合でも正しいタブを追跡）
        used_tab_id = send_result.get('tabId') or tab_id
        
        if not wait:
            return send_result
        
        start = time.time()
        last_response = ""
        stable_count = 0
        
        while True:
            elapsed = time.time() - start
            if elapsed > self.timeout:
                return {'success': False, 'error': 'Timeout', 'response': last_response}
            
            generating = await self.is_generating(used_tab_id)
            response = await self.get_response(used_tab_id)
            
            # 回答があり、生成中でない場合
            if response and len(response) > 0 and not generating:
                if response == last_response:
                    stable_count += 1
                    if stable_count >= 2:
                        return {'success': True, 'response': response, 'elapsed': elapsed}
                else:
                    stable_count = 0
                last_response = response

            await asyncio.sleep(self.poll_interval)


# ========================================
# Grok Tab Session（並列エージェント対応）
# ========================================

class GrokTabSession:
    """
    Grok専用タブセッション

    タブを排他的にロックし、他エージェントとの競合を防ぐ。
    セッション中は全ての操作がこのタブに対して行われる。

    使用例:
        async with ctrl.tab_session('agent-1') as session:
            await session.send_message("Hello")
            response = await session.get_response()
    """

    def __init__(self, controller: 'GrokController', agent_id: str):
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

    async def start(self, url: str = None) -> 'GrokTabSession':
        """新しいタブを作成してセッションを開始"""
        if self._owned:
            raise RuntimeError("Session already started")

        result = await self._ctrl.tab_create_locked(self._agent_id, url)
        if not result.get('success'):
            raise RuntimeError(f"Failed to create tab: {result.get('error')}")

        self._tab_id = result.get('tabId')
        self._owned = True
        return self

    async def acquire(self, tab_id: int, timeout: int = 5000) -> 'GrokTabSession':
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
    # Grok操作（セッション内タブに対して実行）
    # ========================================

    async def send_message(self, message: str) -> Dict:
        """メッセージを送信"""
        self._ensure_active()
        return await self._ctrl.send_message(message, self._tab_id)

    async def get_response(self) -> str:
        """回答を取得"""
        self._ensure_active()
        return await self._ctrl.get_response(self._tab_id)

    async def is_generating(self) -> bool:
        """生成中かどうかを確認"""
        self._ensure_active()
        return await self._ctrl.is_generating(self._tab_id)

    async def select_model(self, model: str) -> Dict:
        """モデルを選択"""
        self._ensure_active()
        return await self._ctrl.select_model(model, self._tab_id)

    async def enable_deepthink(self) -> Dict:
        """DeepThinkを有効化"""
        self._ensure_active()
        return await self._ctrl.enable_deepthink(self._tab_id)

    async def disable_deepthink(self) -> Dict:
        """DeepThinkを無効化"""
        self._ensure_active()
        return await self._ctrl.disable_deepthink(self._tab_id)

    async def enable_deepsearch(self) -> Dict:
        """DeepSearchを有効化"""
        self._ensure_active()
        return await self._ctrl.enable_deepsearch(self._tab_id)

    async def attach_file(self, file_path: str) -> Dict:
        """ファイルを添付"""
        self._ensure_active()
        return await self._ctrl.attach_file(file_path, self._tab_id)

    async def attach_files(self, file_paths: List[str]) -> List[Dict]:
        """複数ファイルを添付"""
        self._ensure_active()
        return await self._ctrl.attach_files(file_paths, self._tab_id)

    async def screenshot(self, save_path: str = None) -> Dict:
        """スクリーンショットを撮影"""
        self._ensure_active()
        return await self._ctrl.screenshot(self._tab_id, save_path)

    async def get_models(self) -> Dict:
        """利用可能なモデル一覧を取得"""
        self._ensure_active()
        return await self._ctrl.get_models(self._tab_id)

    async def click(self, selector: str) -> Dict:
        """要素をクリック"""
        self._ensure_active()
        return await self._ctrl.click(selector, self._tab_id)

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

    async def wait_for_response(self, timeout: int = None) -> Dict:
        """
        回答の完了を待機して取得

        Args:
            timeout: タイムアウト秒数（省略時はコントローラーのデフォルト）

        Returns:
            {'success': bool, 'response': str, 'elapsed': float}
        """
        self._ensure_active()
        timeout = timeout or self._ctrl.timeout
        poll_interval = self._ctrl.poll_interval

        start = time.time()
        last_response = ""
        stable_count = 0

        while True:
            elapsed = time.time() - start
            if elapsed > timeout:
                return {
                    'success': False,
                    'error': 'Timeout',
                    'response': last_response,
                    'elapsed': elapsed
                }

            generating = await self.is_generating()
            response = await self.get_response()

            if response and len(response) > 5:
                if not generating:
                    if response == last_response:
                        stable_count += 1
                        if stable_count >= 2:
                            return {
                                'success': True,
                                'response': response,
                                'elapsed': elapsed
                            }
                    else:
                        stable_count = 0
                else:
                    stable_count = 0
                last_response = response

            await asyncio.sleep(poll_interval)


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
        description='Grok Parallel Research Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 並列検索（3並列以上推奨）
  python grok_multi.py "質問1" "質問2" "質問3"
  
  # DeepThinkで難問を解く
  python grok_multi.py "難問1" "難問2" "難問3" --deepthink
  
  # DeepSearchで検索
  python grok_multi.py "検索1" "検索2" "検索3" --deepsearch
  
  # タブ一覧
  python grok_multi.py tabs
  
  # モデル一覧
  python grok_multi.py models
  
  # 単一チャット
  python grok_multi.py chat -m "質問内容"
  
  # DeepThink有効化
  python grok_multi.py deepthink
  
  # DeepSearch有効化
  python grok_multi.py deepsearch
  
  # 状態確認
  python grok_multi.py status
  
  # === 共通機能 ===
  # ファイル添付
  python grok_multi.py attach --file document.pdf --tab 123456
  
  # スクリーンショット
  python grok_multi.py screenshot --tab 123456
  
  # 要素一覧
  python grok_multi.py elements --tab 123456
  
  # 要素検索
  python grok_multi.py search-elements "送信" --tab 123456
  
  # ページテキスト取得
  python grok_multi.py page-text --tab 123456
  
  # DOM調査
  python grok_multi.py inspect summary --tab 123456
  
  # マルチターン並列（3並列×3ターン=9クエリ）
  python grok_multi.py "Q1" "Q2" "Q3" --turns 3

  # 2ターン目以降の送信
  python grok_multi.py reply "Follow1" "Follow2" "Follow3"

  # 回答再取得
  python grok_multi.py recover --tab 123456

  # ブリッジサーバーのみ起動
  python grok_multi.py bridge
"""
    )

    parser.add_argument('command', nargs='?', default='search',
                        help='Command: search, tabs, models, chat, deepthink, deepsearch, status, recover, reply, attach, screenshot, elements, search-elements, page-text, inspect, bridge')
    parser.add_argument('questions', nargs='*', help='Questions for parallel search')
    parser.add_argument('--timeout', type=int, default=1800, help='Timeout in seconds')
    parser.add_argument('--interval', type=int, default=10, help='Poll interval')
    parser.add_argument('--model', help='Model to use')
    parser.add_argument('--tab', type=int, help='Tab ID')
    parser.add_argument('--message', '-m', help='Message for chat command')
    parser.add_argument('--file', '-f', help='File to attach')
    parser.add_argument('--files', nargs='+', help='Files to attach')
    parser.add_argument('--no-auto-bridge', action='store_true', 
                        help='Disable automatic bridge server startup')
    parser.add_argument('--keep-tabs', action='store_true',
                        help='Keep tabs open after search')
    parser.add_argument('--deepthink', action='store_true',
                        help='Enable DeepThink mode')
    parser.add_argument('--deepsearch', action='store_true',
                        help='Enable DeepSearch mode')
    parser.add_argument('--turns', type=int, default=1,
                        help='Number of conversation turns (default: 1)')

    args = parser.parse_args()

    cmd = args.command.lower() if args.command else 'search'

    # --file を --files に統合
    if args.file:
        if args.files:
            args.files = [args.file] + args.files
        else:
            args.files = [args.file]

    ctrl = GrokController(
        timeout=args.timeout,
        poll_interval=args.interval,
        auto_bridge=not args.no_auto_bridge
    )

    # questionsがあればsearchコマンド
    if args.questions and cmd == 'search':
        results = await ctrl.parallel_search(
            questions=args.questions,
            model=args.model,
            deepthink=args.deepthink,
            deepsearch=args.deepsearch,
            close_tabs=not args.keep_tabs,
            turns=args.turns,
            files=args.files
        )
        print("\n=== Summary ===")
        for r in results:
            status = "OK" if r.get('success') else "FAIL"
            print(f"[{status}] Q{r.get('index', 0)+1}: {r.get('elapsed', 0):.1f}s")

    elif cmd == 'reply':
        # セッションタブに並列でフォローアップ送信
        if not args.questions:
            print("Error: reply requires questions (one per session tab)")
            return

        session_tabs = ctrl.get_session_tabs()
        turns_info = ctrl._get_session_turns()
        if not session_tabs:
            print("Error: No session tabs found. Run 'search' first.")
            return

        if len(args.questions) != len(session_tabs):
            print(f"Error: Number of questions ({len(args.questions)}) must match session tabs ({len(session_tabs)})")
            print(f"Session tabs: {session_tabs}")
            return

        current_turn = turns_info.get('current', 1) + 1
        total_turns = turns_info.get('total', 1)
        remaining = total_turns - current_turn

        print(f"\n{'='*60}")
        print(f"[Turn {current_turn}/{total_turns}] Sending follow-up queries...")
        print('='*60)

        results = []
        for i, (tab_id, question) in enumerate(zip(session_tabs, args.questions)):
            md_path = ctrl._get_session_tab_md_path(tab_id)
            print(f"  Tab {i+1} (ID: {tab_id}): Sending...")

            # メッセージ送信（入力確認・リトライ付き）
            send_result = await ctrl.send_message(question, tab_id)
            if not send_result.get('success'):
                result = {'success': False, 'error': send_result.get('error', 'Send failed'), 'tab_id': tab_id, 'index': i}
                results.append(result)
                print(f"  Tab {i+1}: FAIL - {result['error']}")
                continue

            # 回答待機
            start = time.time()
            last_response = ""
            stable_count = 0
            result = None

            while True:
                elapsed = time.time() - start
                if elapsed > args.timeout:
                    result = {'success': False, 'error': 'Timeout', 'tab_id': tab_id, 'index': i, 'elapsed': elapsed}
                    break

                generating = await ctrl.is_generating(tab_id)
                response = await ctrl.get_response(tab_id)

                if response and len(response) > 10:
                    if not generating:
                        if response == last_response:
                            stable_count += 1
                            if stable_count >= 2:
                                result = {'success': True, 'response': response, 'tab_id': tab_id, 'index': i, 'elapsed': elapsed, 'question': question}
                                break
                        else:
                            stable_count = 0
                    else:
                        stable_count = 0
                    last_response = response

                await asyncio.sleep(args.interval)

            # MDに追記
            if md_path and Path(md_path).exists():
                ctrl._write_individual_md(md_path, result, turn=current_turn)

            results.append(result)
            status = "Done" if result.get('success') else f"FAIL ({result.get('error')})"
            print(f"  Tab {i+1}: {status} ({result.get('elapsed', 0):.1f}s)")

        # セッション更新
        session_entries = await ctrl._build_session_entries(session_tabs, md_paths=[ctrl._get_session_tab_md_path(t) for t in session_tabs])
        ctrl._save_session_tabs(session_entries, turns_total=total_turns, turns_current=current_turn)

        print(f"\n[Turn {current_turn}/{total_turns}] Complete.")
        if remaining > 0:
            print(f"[Session] Remaining turns: {remaining}")
            print(f"[Next] Send follow-up: python grok_multi.py reply \"Q1\" \"Q2\" ...")
        else:
            print(f"[Complete] {len(session_tabs)} tabs × {total_turns} turns = {len(session_tabs) * total_turns} queries completed.")
            if not args.keep_tabs:
                print(f"[Cleanup] Closing {len(session_tabs)} tabs...")
                for tid in session_tabs:
                    await ctrl.close_tab(tid)
                print("  Done.")

    elif cmd == 'tabs':
        tabs = await ctrl.get_tabs()
        print(f"Open tabs: {len(tabs)}")
        for t in tabs:
            marker = '*' if t.get('active') else ' '
            print(f" {marker} [{t['id']}] {t.get('title', '')[:60]}")
            print(f"     {t.get('url', '')[:70]}")
    
    elif cmd == 'models':
        result = await ctrl.get_models(args.tab)
        print(f"Current model: {result.get('currentModel', 'Unknown')}")
        if result.get('models'):
            print("\nAvailable models:")
            for m in result['models']:
                print(f"  - {m.get('name', m)}")
    
    elif cmd == 'chat':
        msg = args.message
        if not msg:
            print("Error: --message / -m required")
            return
        result = await ctrl.chat(msg, args.tab)
        if result.get('success'):
            print(f"\n[Grok Response] ({result.get('elapsed', 0):.1f}s)")
            print(result.get('response', ''))
        else:
            print(f"Error: {result.get('error')}")
    
    elif cmd == 'deepthink':
        result = await ctrl.enable_deepthink(args.tab)
        if result.get('success'):
            print("[Grok] DeepThink enabled")
        else:
            print(f"[Grok] DeepThink failed: {result.get('error', 'Unknown error')}")
    
    elif cmd == 'deepsearch':
        result = await ctrl.enable_deepsearch(args.tab)
        if result.get('success'):
            print("[Grok] DeepSearch enabled")
        else:
            print(f"[Grok] DeepSearch failed: {result.get('error', 'Unknown error')}")
    
    elif cmd == 'status':
        # ブリッジ状態
        if BridgeServer.is_running():
            print("[Bridge] Running on ws://localhost:9224")
        else:
            print("[Bridge] Not running")
        
        # DeepThink状態
        dt_result = await ctrl.is_deepthink(args.tab)
        print(f"[Grok DeepThink] {'Enabled' if dt_result.get('enabled') else 'Disabled'}")
        
        # モデル情報
        models = await ctrl.get_models(args.tab)
        print(f"[Grok Model] {models.get('currentModel', 'Unknown')}")
    
    elif cmd == 'response':
        response = await ctrl.get_response(args.tab)
        if response:
            print(response)
        else:
            print("No response found")

    elif cmd == 'recover':
        if args.tab is None:
            print("Error: --tab required for recover")
            return
        tab_id = args.tab
        saved_md_path = ctrl._get_session_tab_md_path(tab_id)
        topic = ctrl._get_session_tab_topic(tab_id)
        create_new = False

        # md_pathがセッションにない場合は新規作成
        if not saved_md_path:
            create_new = True
            print(f"[Recover] No md_path in session for tab {tab_id}. Will create new file.")
        elif not Path(saved_md_path).exists():
            create_new = True
            print(f"[Recover] MD file does not exist: {saved_md_path}. Will create new file.")

        print(f"[Recover] Tab {tab_id} - Fetching full conversation...")
        start = time.time()

        # 生成完了を待機
        generating = await ctrl.is_generating(tab_id)
        while generating and (time.time() - start) < 120:
            print(f"[Recover] Waiting for generation to complete ({int(time.time() - start)}s)...")
            await asyncio.sleep(3)
            generating = await ctrl.is_generating(tab_id)

        # 全会話履歴を取得
        conversation = await ctrl.get_full_conversation(tab_id)
        elapsed = time.time() - start

        if not conversation:
            # フォールバック：単一応答として取得
            response = await ctrl.get_response(tab_id)
            if not response or len(response) < 10:
                response = await ctrl._get_full_page_content(tab_id)
            if response and len(response) > 10:
                conversation = [{'role': 'assistant', 'content': response}]

        if not conversation:
            print(f"[Recover] Failed: No conversation found")
            return

        url = await ctrl._get_open_tab_url(tab_id)

        # md_pathを決定（新規作成 or 上書き）
        if create_new:
            if not topic:
                topic = f"grok_tab_{tab_id}"
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"grok_chat_tab{tab_id}_{timestamp}.md"
            md_path = str(ctrl._get_topic_flow_path(filename, topic))
            print(f"[Recover] Creating new file: {md_path}")
        else:
            md_path = saved_md_path

        # 全会話をMDに書き出し
        ctrl._write_full_conversation_md(md_path, conversation, tab_id, url, topic)

        # セッションにmd_pathを保存
        ctrl._update_session_tab_md_path(tab_id, md_path)

        turn_count = len([m for m in conversation if m['role'] == 'assistant'])
        action = "Created" if create_new else "Overwritten"
        print(f"[Recover] {action} with {turn_count} turns: {md_path}")
        print(f"[Recover] Success ({elapsed:.1f}s)")

    # ========================================
    # 共通機能: ファイル添付
    # ========================================
    elif cmd == 'attach':
        file_path = args.file
        if not file_path:
            print("Error: --file required")
            return
        result = await ctrl.attach_file(file_path, args.tab)
        if result.get('success'):
            print(f"Attached: {result.get('fileName')} ({result.get('fileSize')} bytes)")
        else:
            print(f"Error: {result.get('error')}")
    
    # ========================================
    # 共通機能: スクリーンショット
    # ========================================
    elif cmd == 'screenshot' or cmd == 'ss':
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_path = f'/tmp/grok_screenshot_{timestamp}.png'
        save_path = args.file or default_path
        
        result = await ctrl.screenshot(args.tab, save_path)
        if result.get('success'):
            print(f"[Screenshot] Saved to: {result.get('path', save_path)}")
            print(f"  Tab: {result.get('title', '')}")
            print(f"  URL: {result.get('url', '')}")
        else:
            print(f"[Screenshot] Failed: {result.get('error')}")
    
    # ========================================
    # 共通機能: 要素一覧
    # ========================================
    elif cmd == 'elements':
        elements = await ctrl.get_elements(args.tab)
        print(f"Found {len(elements)} interactive elements:")
        for i, el in enumerate(elements[:50]):  # 最初の50件のみ表示
            el_type = el.get('type', 'unknown')
            text = (el.get('text') or '')[:40]
            selector = (el.get('selector') or '')[:50]
            print(f"  [{i}] {el_type}: {text}")
            print(f"       {selector}")
        if len(elements) > 50:
            print(f"  ... and {len(elements) - 50} more elements")
    
    # ========================================
    # 共通機能: 要素検索
    # ========================================
    elif cmd == 'search-elements':
        query = args.questions[0] if args.questions else None
        if not query:
            print("Error: search query required")
            print("Usage: python grok_multi.py search-elements \"検索文字列\"")
            return
        
        matches = await ctrl.search_elements(query, args.tab)
        print(f"Found {len(matches)} elements matching '{query}':")
        for el in matches:
            idx = el.get('index', '?')
            el_type = el.get('type', 'unknown')
            text = (el.get('text') or '')[:40]
            selector = (el.get('selector') or '')[:50]
            print(f"  [{idx}] {el_type}: {text}")
            print(f"       {selector}")
    
    # ========================================
    # 共通機能: ページテキスト取得
    # ========================================
    elif cmd == 'page-text':
        text = await ctrl.get_page_text(args.tab)
        print(text[:5000] if text else "No text found")
        if text and len(text) > 5000:
            print(f"\n... truncated ({len(text)} total chars)")
    
    # ========================================
    # 共通機能: DOM調査
    # ========================================
    elif cmd == 'inspect' or cmd == 'dom':
        mode = 'summary'
        selector = None
        search_text = None
        
        if args.questions:
            first_arg = args.questions[0]
            if first_arg in ['summary', 'interactive', 'testids', 'tree', 'aria', 'search']:
                mode = first_arg
                if mode == 'search' and len(args.questions) > 1:
                    search_text = args.questions[1]
            elif first_arg.startswith(('[', '.', '#', '*')):
                selector = first_arg
            else:
                mode = 'search'
                search_text = first_arg
        
        result = await ctrl.inspect_dom(args.tab, selector, mode, search_text)
        
        if result.get('success'):
            print(f"=== DOM Inspection: {result.get('url', '')} ===")
            print(f"  Title: {result.get('title', '')}")
            
            if 'summary' in result:
                s = result['summary']
                print(f"\n=== Page Summary ===")
                print(f"  Total elements: {s.get('totalElements', 0)}")
                print(f"  Interactive: {s.get('interactiveCount', 0)}")
                print(f"  With data-testid: {s.get('testIdCount', 0)}")
            
            if 'elements' in result:
                print(f"\n=== Elements ({len(result['elements'])}) ===")
                for el in result['elements'][:20]:
                    vis = 'visible' if el.get('visible') else 'hidden'
                    print(f"  <{el.get('tag')}> {vis} - {el.get('text', '')[:50]}")
        else:
            print(f"Error: {result.get('error')}")
    
    else:
        # デフォルト: 引数を質問として並列検索
        questions = [cmd] + (args.questions or [])
        if len(questions) < 3:
            questions = [
                "日本の首都はどこですか？一言で答えて。",
                "1+2+3は何ですか？数字だけで答えて。",
                "今日は何曜日ですか？曜日だけ答えて。"
            ]
        
        results = await ctrl.parallel_search(
            questions=questions,
            model=args.model,
            deepthink=args.deepthink,
            deepsearch=args.deepsearch,
            close_tabs=not args.keep_tabs
        )
        print("\n=== Summary ===")
        for r in results:
            status = "OK" if r.get('success') else "FAIL"
            print(f"[{status}] Q{r.get('index', 0)+1}: {r.get('elapsed', 0):.1f}s")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'bridge':
        run_bridge_only()
    else:
        asyncio.run(main())
