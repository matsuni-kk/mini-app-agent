#!/usr/bin/env python3
"""
Kimi Parallel Research Tool
===========================
3並列以上のKimi検索・ブレスト・情報収集を1つのスクリプトで実行

機能:
- 並列質問送信（3並列以上推奨）
- モデル選択（K2.5 Thinking等）
- 確実な回答取得（本文のみ）
- Markdown自動保存
- タブ管理
- マルチターン対話

使用例:
  # 基本的な並列検索
  python kimi_multi.py "質問1" "質問2" "質問3"

  # タブ一覧を確認
  python kimi_multi.py tabs

  # モデル一覧を確認
  python kimi_multi.py models --tab <tab_id>

  # 既存セッションで追加質問
  python kimi_multi.py chat "追加質問"

  # 既存タブから回答を再取得
  python kimi_multi.py recover
"""

import asyncio
import json
import time
import os
import sys
import socket
import subprocess
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime
import re

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


# ========================================
# Kimi Controller
# ========================================

class KimiController:
    """Kimi操作の統合コントローラー"""

    BRIDGE_URL = "ws://localhost:9224"
    KIMI_BASE_URL = "https://www.kimi.com/"

    def __init__(self, timeout: int = 600, poll_interval: int = 3):
        self.timeout = timeout
        self.poll_interval = poll_interval
        self._ws = None
        self._request_id = 0
        self._lock = asyncio.Lock()
        self._session_tabs = []
        self._load_session_tabs()

    # ========================================
    # WebSocket通信
    # ========================================

    async def connect(self):
        """ブリッジサーバーに接続"""
        if self._ws is None or (hasattr(self._ws, 'closed') and self._ws.closed):
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

    # ========================================
    # タブ操作
    # ========================================

    async def get_tabs(self) -> List[Dict]:
        """タブ一覧を取得"""
        result = await self._cmd(type='get_tabs')
        return result.get('tabs', [])

    async def get_kimi_tabs(self) -> List[Dict]:
        """Kimiタブのみ取得"""
        tabs = await self.get_tabs()
        return [t for t in tabs if 'kimi.com' in t.get('url', '')]

    async def new_tab(self, url: str) -> Dict:
        """新しいタブを開く"""
        return await self._cmd(type='new_tab', url=url)

    async def close_tab(self, tab_id: int) -> Dict:
        """タブを閉じる"""
        return await self._cmd(type='close_tab', tabId=tab_id)

    async def switch_tab(self, tab_id: int) -> Dict:
        """タブを切り替える"""
        return await self._cmd(type='switch_tab', tabId=tab_id)

    async def screenshot(self, tab_id: int = None, save_path: str = None) -> Dict:
        """スクリーンショットを撮影"""
        result = await self._cmd(type='screenshot', tabId=tab_id)

        if result.get('success') and save_path and result.get('dataUrl'):
            import base64
            data_url = result['dataUrl']
            if ',' in data_url:
                base64_data = data_url.split(',')[1]
                with open(save_path, 'wb') as f:
                    f.write(base64.b64decode(base64_data))
                result['path'] = save_path

        return result

    # ========================================
    # セッション管理
    # ========================================

    def _get_session_file(self) -> Path:
        """セッションファイルのパスを取得"""
        return Path.home() / ".kimi_multi_session.json"

    def _load_session_tabs(self):
        """前回のセッションタブを復元"""
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

    def _save_session_tabs(self, tabs: List[Dict]) -> None:
        """セッションタブを保存"""
        session_file = self._get_session_file()
        try:
            session_data = {'tabs': tabs}
            with open(session_file, 'w') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            self._session_tabs = tabs
        except Exception as e:
            print(f"[Warning] Failed to save session: {e}")

    def get_session_tabs(self) -> List[int]:
        """現在のセッションタブIDリストを取得"""
        return [t.get('id') for t in self._session_tabs if t.get('id')]

    # ========================================
    # Kimi専用機能
    # ========================================

    async def send_message(self, message: str, tab_id: int = None) -> Dict:
        """メッセージを送信"""
        return await self._cmd(type='kimi_send_message', message=message, tabId=tab_id)

    async def get_response(self, tab_id: int = None) -> str:
        """回答を取得（core get_textを使用、CSP回避）"""
        # kimi_get_response がCSPでブロックされる場合があるため、
        # core.js の get_text を使用
        result = await self._cmd(type='get_text', tabId=tab_id, selector='[class*="assistant"]')
        if result.get('success') and result.get('text'):
            text = result.get('text', '')
            # Thinking部分を除去して実際の応答のみ返す
            return self._extract_response(text)
        return ''

    def _extract_response(self, text: str) -> str:
        """Thinking部分を除去して実際の応答を抽出"""
        if not text:
            return ''

        # Kimiの応答パターン:
        # 1. "Think" で始まるセクション（英語の内部推論）
        # 2. 実際の応答（日本語が多い）

        lines = text.split('\n')
        response_start_idx = 0

        # Thinkingセクションの終わりを探す
        # 日本語で始まる行（ひらがな・カタカナ・漢字）を応答開始とみなす
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue

            # 日本語文字で始まるかチェック
            first_char = stripped[0] if stripped else ''
            is_japanese_start = (
                '\u3040' <= first_char <= '\u309f' or  # ひらがな
                '\u30a0' <= first_char <= '\u30ff' or  # カタカナ
                '\u4e00' <= first_char <= '\u9fff'     # 漢字
            )

            # Thinking関連の英語キーワードをスキップ
            thinking_keywords = [
                'Think', 'The user', 'This is', 'I should', 'Respond', 'Provide',
                'Keep', 'No tools', 'Let me', 'I will', 'I need', 'First',
                'simple request', 'doesn\'t require'
            ]
            is_thinking_line = any(stripped.startswith(kw) for kw in thinking_keywords)

            if is_japanese_start and not is_thinking_line:
                response_start_idx = i
                break

        # 応答部分を抽出
        response_lines = lines[response_start_idx:]

        # UIボタンテキストを除去
        result = '\n'.join(response_lines)
        result = re.sub(r'\n?(Copy|Edit|Share|Retry|Regenerate)$', '', result, flags=re.MULTILINE)
        return result.strip()

    async def is_generating(self, tab_id: int = None) -> bool:
        """生成中かどうかを確認"""
        result = await self._cmd(type='kimi_is_generating', tabId=tab_id)
        return result.get('generating', False)

    async def get_models(self, tab_id: int = None) -> Dict:
        """利用可能なモデル一覧を取得"""
        return await self._cmd(type='kimi_get_models', tabId=tab_id)

    async def select_model(self, model: str, tab_id: int = None) -> Dict:
        """モデルを選択"""
        return await self._cmd(type='kimi_select_model', model=model, tabId=tab_id)

    async def new_chat(self, tab_id: int = None) -> Dict:
        """新しいチャットを開始"""
        return await self._cmd(type='kimi_new_chat', tabId=tab_id)

    async def get_full_conversation(self, tab_id: int = None) -> List[Dict]:
        """会話全体を取得"""
        result = await self._cmd(type='kimi_get_full_conversation', tabId=tab_id)
        if result.get('success'):
            return result.get('messages', [])
        return []

    # ========================================
    # 並列検索
    # ========================================

    async def parallel_search(
        self,
        questions: List[str],
        model: str = None,
        close_tabs: bool = False
    ) -> List[Dict]:
        """
        複数の質問を並列で送信し、全ての応答を取得

        Args:
            questions: 質問リスト（3個以上推奨）
            model: 使用するモデル（例: 'K2.5 Thinking'）
            close_tabs: 回答取得後にタブを閉じるか

        Returns:
            各質問に対する結果のリスト
        """
        MAX_PARALLEL = 10
        MIN_PARALLEL = 1
        n = len(questions)

        if n < MIN_PARALLEL:
            return [{'success': False, 'error': 'No questions provided'}]

        if n > MAX_PARALLEL:
            print(f"Warning: Maximum {MAX_PARALLEL} parallel queries allowed. Truncating.")
            questions = questions[:MAX_PARALLEL]
            n = MAX_PARALLEL

        print(f"\n{'='*60}")
        print(f"Kimi Parallel Search: {n} questions")
        print('='*60)
        if model:
            print(f"Model: {model}")
        print()

        # 1. タブを開く
        print(f"[1/4] Opening {n} Kimi tabs...")
        tab_ids = []
        for i in range(n):
            result = await self.new_tab(self.KIMI_BASE_URL)
            if result.get('tab', {}).get('id'):
                tab_ids.append(result['tab']['id'])
                print(f"  Tab {i+1}: ID={result['tab']['id']}")
            await asyncio.sleep(1.5)

        if len(tab_ids) != n:
            return [{'success': False, 'error': f'Failed to open tabs: {len(tab_ids)}/{n}'}]

        print("  Waiting for pages to load...")
        await asyncio.sleep(4)

        # 2. モデル設定（オプション）
        if model:
            print(f"\n[1.5] Selecting model: {model}...")
            for i, tid in enumerate(tab_ids):
                r = await self.select_model(model, tid)
                status = "OK" if r.get('success') else f"FAIL: {r.get('error', '')}"
                print(f"  Tab {i+1}: {status}")
                await asyncio.sleep(0.5)

        # 3. 質問を送信
        print(f"\n[2/4] Sending questions...")
        for i, (tid, q) in enumerate(zip(tab_ids, questions)):
            send_result = await self.send_message(q, tid)
            status = "OK" if send_result.get('success') else f"FAIL: {send_result.get('error', '')}"
            print(f"  Tab {i+1}: Sent '{q[:50]}...' ({status})")
            await asyncio.sleep(0.5)

        # 4. 回答を待機
        print(f"\n[3/4] Waiting for responses (timeout: {self.timeout}s)...")

        topic = self._sanitize_topic(questions[0])
        md_paths = self._init_individual_mds(questions, model, topic)
        print(f"[Output] Writing to {len(md_paths)} MD files:")
        for i, p in enumerate(md_paths):
            print(f"  Q{i+1}: {p}")

        results = [None] * n

        async def wait_for_response(tid: int, idx: int, question: str) -> Dict:
            start = time.time()
            last_response = ""
            stable_count = 0
            MIN_RESPONSE_LEN = 10
            STABLE_THRESHOLD = 3

            while True:
                elapsed = time.time() - start

                if elapsed > self.timeout:
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
                            if stable_count >= STABLE_THRESHOLD:
                                if len(response) < MIN_RESPONSE_LEN:
                                    stable_count = 0
                                    await asyncio.sleep(self.poll_interval)
                                    continue

                                await asyncio.sleep(2)
                                final_response = await self.get_response(tid)

                                if final_response and final_response != response:
                                    last_response = final_response
                                    stable_count = 0
                                    await asyncio.sleep(self.poll_interval)
                                    continue

                                if final_response:
                                    response = final_response

                                result = {
                                    'success': True, 'index': idx,
                                    'question': question, 'response': response,
                                    'tab_id': tid, 'elapsed': elapsed
                                }
                                self._write_individual_md(md_paths[idx], result)
                                results[idx] = result
                                print(f"  Tab {idx+1}: Done ({elapsed:.1f}s)")
                                return result
                        else:
                            stable_count = 0
                    else:
                        stable_count = 0
                    last_response = response

                status = "Generating..." if generating else "Waiting..."
                print(f"  Tab {idx+1}: {status} ({int(elapsed)}s)")
                await asyncio.sleep(self.poll_interval)

        # 並列で応答を待機
        tasks = [wait_for_response(tid, i, q) for i, (tid, q) in enumerate(zip(tab_ids, questions))]
        await asyncio.gather(*tasks)

        # セッション保存
        session_entries = [{'id': tid, 'question': q} for tid, q in zip(tab_ids, questions)]
        self._save_session_tabs(session_entries)

        # 5. サマリー
        print(f"\n[4/4] Summary")
        print('='*60)

        success_count = sum(1 for r in results if r and r.get('success'))
        print(f"Success: {success_count}/{n}")

        for i, r in enumerate(results):
            if r:
                status = "OK" if r.get('success') else f"FAIL: {r.get('error', '')}"
                resp_len = len(r.get('response', ''))
                print(f"  Q{i+1}: {status} ({resp_len} chars)")

        print(f"\nMD files saved to: {Path(md_paths[0]).parent}")

        if close_tabs:
            print("\nClosing tabs...")
            for tid in tab_ids:
                await self.close_tab(tid)

        return results

    # ========================================
    # Markdown出力
    # ========================================

    def _sanitize_topic(self, topic: str, max_len: int = 60) -> str:
        """トピック名をファイル名に使える形式に変換"""
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

    def _get_flow_path(self, filename: str, topic: str = None) -> Path:
        """Flow/YYYYMM/YYYY-MM-DD/topic/ 配下のパスを生成"""
        now = datetime.now()

        # プロジェクトルートを探す
        current = Path.cwd()
        flow_base = None
        for _ in range(5):
            candidate = current / 'Flow'
            if candidate.exists():
                flow_base = candidate
                break
            current = current.parent

        if not flow_base:
            flow_base = Path.cwd() / 'Flow'

        # パス構築: Flow/YYYYMM/YYYY-MM-DD/Kimi/セッション名
        year_month = now.strftime('%Y%m')
        date_str = now.strftime('%Y-%m-%d')

        if topic:
            save_dir = flow_base / year_month / date_str / "Kimi" / topic
        else:
            save_dir = flow_base / year_month / date_str / "Kimi"

        save_dir.mkdir(parents=True, exist_ok=True)
        return save_dir / filename

    def _init_individual_mds(self, questions: List[str], model: str = None, topic: str = None) -> List[str]:
        """各クエリごとのMDファイルを初期化"""
        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        md_paths = []

        for i, question in enumerate(questions):
            filename = f"kimi_q{i+1}_{timestamp}.md"
            save_path = self._get_flow_path(filename, topic)

            lines = [
                f"# Kimi Search Result - Q{i+1}",
                f"",
                f"**実行日時**: {now.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**モデル**: {model or 'default'}",
                f"",
                f"## 質問",
                f"",
                f"{question}",
                f"",
                f"---",
                f"",
                f"## 回答",
                f"",
                f"(waiting...)",
                f""
            ]

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))

            md_paths.append(str(save_path))

        return md_paths

    def _write_individual_md(self, md_path: str, result: Dict, turn: int = 1) -> None:
        """個別MDファイルに結果を書き込み"""
        question = result.get('question', '')
        success = result.get('success', False)
        elapsed = result.get('elapsed', 0)
        response = result.get('response', '')
        error = result.get('error', '')
        tab_id = result.get('tab_id', 'N/A')

        if turn == 1:
            lines = [
                f"# Kimi Multi-Turn Session",
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

            if success and response:
                lines.append(response)
            elif not success:
                lines.append(f"**Error**: {error}")
                if response:
                    lines.append(f"\n**部分回答**:\n```\n{response[:500]}\n```")
            else:
                lines.append(f"*応答が空です*")

            lines.append("")

            with open(md_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
        else:
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

    # ========================================
    # マルチターン対話
    # ========================================

    async def chat(self, message: str, tab_id: int = None) -> Dict:
        """既存セッションで追加質問"""
        if tab_id is None:
            session_tabs = self.get_session_tabs()
            if not session_tabs:
                return {'success': False, 'error': 'No session tabs. Run parallel_search first.'}
            tab_id = session_tabs[0]

        print(f"Sending to tab {tab_id}: {message[:50]}...")

        send_result = await self.send_message(message, tab_id)
        if not send_result.get('success'):
            return send_result

        # 応答を待機
        start = time.time()
        last_response = ""
        stable_count = 0

        while time.time() - start < self.timeout:
            generating = await self.is_generating(tab_id)
            response = await self.get_response(tab_id)

            if response and len(response) > 5 and not generating:
                if response == last_response:
                    stable_count += 1
                    if stable_count >= 3:
                        elapsed = time.time() - start
                        print(f"Response received ({elapsed:.1f}s)")
                        return {
                            'success': True,
                            'response': response,
                            'tab_id': tab_id,
                            'elapsed': elapsed
                        }
                else:
                    stable_count = 0
                last_response = response

            await asyncio.sleep(self.poll_interval)

        return {'success': False, 'error': 'Timeout', 'response': last_response}

    # ========================================
    # 再取得（recover）
    # ========================================

    async def recover(self) -> List[Dict]:
        """既存タブから回答を再取得"""
        session_tabs = self.get_session_tabs()
        if not session_tabs:
            print("No session tabs found.")
            return []

        print(f"Recovering from {len(session_tabs)} tabs...")
        results = []

        now = datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M%S")

        for i, tid in enumerate(session_tabs):
            response = await self.get_response(tid)

            if response:
                filename = f"kimi_chat_tab{tid}_{timestamp}.md"
                save_path = self._get_flow_path(filename, 'recover')

                lines = [
                    f"# Kimi Recovered Response",
                    f"",
                    f"**Tab ID**: {tid}",
                    f"**取得日時**: {now.strftime('%Y-%m-%d %H:%M:%S')}",
                    f"",
                    f"---",
                    f"",
                    f"## Response",
                    f"",
                    response
                ]

                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write("\n".join(lines))

                print(f"  Tab {tid}: {len(response)} chars -> {save_path}")
                results.append({'tab_id': tid, 'response': response, 'path': str(save_path)})
            else:
                print(f"  Tab {tid}: No response")
                results.append({'tab_id': tid, 'response': '', 'error': 'No response'})

        return results


# ========================================
# CLI Entry Point
# ========================================

async def main():
    import argparse

    parser = argparse.ArgumentParser(description='Kimi Parallel Research Tool')
    parser.add_argument('questions', nargs='*', help='Questions for parallel search')
    parser.add_argument('--model', '-m', help='Model name (e.g., "K2.5 Thinking")')
    parser.add_argument('--tab', '-t', type=int, help='Specific tab ID')
    parser.add_argument('--timeout', type=int, default=600, help='Timeout in seconds')
    parser.add_argument('--close', action='store_true', help='Close tabs after completion')

    args = parser.parse_args()

    ctrl = KimiController(timeout=args.timeout)

    # コマンド判定
    if args.questions:
        cmd = args.questions[0].lower() if args.questions else ''

        if cmd == 'tabs':
            # タブ一覧
            tabs = await ctrl.get_kimi_tabs()
            print(f"\nKimi Tabs ({len(tabs)}):")
            for t in tabs:
                print(f"  ID={t.get('id')}: {t.get('url', '')[:60]}")
            return

        elif cmd == 'models':
            # モデル一覧
            result = await ctrl.get_models(args.tab)
            if result.get('success'):
                print(f"\nCurrent: {result.get('currentModel')}")
                print("Available models:")
                for m in result.get('models', []):
                    mark = '*' if m.get('selected') else ' '
                    print(f"  {mark} {m.get('name')}")
            else:
                print(f"Error: {result.get('error')}")
            return

        elif cmd == 'chat':
            # マルチターン対話
            if len(args.questions) < 2:
                print("Usage: kimi_multi.py chat 'your question'")
                return
            message = args.questions[1]
            result = await ctrl.chat(message, args.tab)
            if result.get('success'):
                print(f"\n{result.get('response')}")
            else:
                print(f"Error: {result.get('error')}")
            return

        elif cmd == 'recover':
            # 再取得
            await ctrl.recover()
            return

        else:
            # 並列検索
            results = await ctrl.parallel_search(
                questions=args.questions,
                model=args.model,
                close_tabs=args.close
            )
            return results

    else:
        parser.print_help()


if __name__ == '__main__':
    asyncio.run(main())
