#!/usr/bin/env python3
"""Notion AI Parallel Search Tool (Self-Contained)

Notion AI (https://www.notion.so/ai) を複数タブで並列実行し、結果をMarkdown保存する。

設計方針:
- **自己完結型**: browser_controller.pyに依存せず、このファイル単独で動作
- 3並列以上（search）をデフォルトとし、少数は search1 を提供
- 回答抽出は `body` のテキストから「最後のプロンプト以降」を切り出す
"""

from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import os
import re
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ========================================
# WebSocket auto-install
# ========================================

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
# Bridge Server (embedded)
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
# Browser Controller (embedded)
# ========================================

class BrowserController:
    """汎用ブラウザ操作コントローラー（最小実装）"""

    BRIDGE_URL = "ws://localhost:9224"

    def __init__(self, timeout: int = 30, auto_bridge: bool = True):
        self.timeout = timeout
        self.auto_bridge = auto_bridge
        self._ws = None
        self._request_id = 0
        self._lock = asyncio.Lock()

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

            try:
                await self._ws.send(json.dumps(kwargs))
            except Exception as e:
                # Reconnect on send failure
                self._ws = None
                await self.connect()
                await self._ws.send(json.dumps(kwargs))

            try:
                response = await asyncio.wait_for(self._ws.recv(), timeout=self.timeout)
                return json.loads(response)
            except asyncio.TimeoutError:
                return {'error': 'Timeout waiting for response'}
            except Exception as e:
                # Reconnect on receive failure
                self._ws = None
                return {'error': f'Connection error: {str(e)}'}

    # === Tab operations ===

    async def get_tabs(self) -> List[Dict]:
        """タブ一覧を取得"""
        result = await self._cmd(type='get_tabs')
        return result.get('tabs', [])

    async def tab_create_locked(self, agent_id: str, url: str = 'about:blank') -> Dict:
        """新しいタブを作成してロックを取得"""
        return await self._cmd(type='tab_create_locked', agentId=agent_id, url=url)

    async def tab_close_locked(self, tab_id: int, agent_id: str) -> Dict:
        """タブを閉じてロックを解放"""
        return await self._cmd(type='tab_close_locked', tabId=tab_id, agentId=agent_id)

    # === DOM operations ===

    async def click(self, selector: str, tab_id: int = None) -> Dict:
        """要素をクリック"""
        return await self._cmd(type='click', selector=selector, tabId=tab_id)

    async def type_text(self, text: str, selector: str, tab_id: int = None) -> Dict:
        """テキストを入力"""
        return await self._cmd(type='type', text=text, selector=selector, tabId=tab_id)

    async def get_text(self, selector: str, tab_id: int = None) -> Dict:
        """テキストを取得"""
        return await self._cmd(type='get_text', selector=selector, tabId=tab_id)

    async def execute_script(self, script: str, tab_id: int = None) -> Dict:
        """JavaScriptを実行"""
        return await self._cmd(type='execute_script', script=script, tabId=tab_id)


# ========================================
# Notion AI specific logic
# ========================================

def _now_stamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _today_dir() -> Tuple[str, str]:
    now = dt.datetime.now()
    return now.strftime("%Y%m"), now.strftime("%Y-%m-%d")


def _sanitize_topic(s: str, max_len: int = 80) -> str:
    s = s.strip().replace("\n", " ")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^A-Za-z0-9\-_\sぁ-んァ-ン一-龥]", "_", s)
    s = s.strip().replace(" ", "_")
    if not s:
        return "notionai"
    return s[:max_len]


def _extract_answer(full_text: str, prompt: str) -> str:
    """`body` textから回答らしき部分を抽出。

    ルール:
    - 最後に出現するプロンプト文字列以降を候補にする
    - UIノイズの境界として「コンテキストを追加」等があればそこで切る
    """
    p = prompt.strip()
    if not p:
        return full_text.strip()

    key = p[:32]

    idx = full_text.rfind(p)
    if idx == -1 and key:
        idx = full_text.rfind(key)
    if idx == -1:
        # Don't fall back to full page text; keep waiting until the prompt is visible.
        return ""

    tail = full_text[idx + len(p) :]
    tail = tail.lstrip("\n\r \t")

    for stop in [
        "\nコンテキストを追加",
        "\nClaude ",
        "\nすべてのソース",
        "\n質問や検索、",
    ]:
        cut = tail.find(stop)
        if cut != -1:
            tail = tail[:cut]
            break

    return tail.strip()


async def _get_page_text_with_iframes(ctrl: BrowserController, tab_id: int) -> str:
    """Return innerText from body using get_text (CSP-safe)."""
    # Use get_text instead of execute_script to avoid CSP issues
    result = await ctrl.get_text('body', tab_id)
    if isinstance(result, dict):
        return result.get("text", "")
    return str(result) if result else ""


async def _extract_links(ctrl: BrowserController, tab_id: int) -> List[Dict[str, str]]:
    """Extract citation links from Notion AI response using JavaScript."""
    try:
        script = """
        (() => {
            const links = Array.from(document.querySelectorAll('body a'));
            const result = [];
            const seen = new Set();

            links.forEach(a => {
                const href = a.href;
                const text = a.textContent.trim();

                // Filter out Notion internal links, fragments, and javascript
                if (!href || href.startsWith('#') || href.startsWith('javascript:')) {
                    return;
                }

                // Filter out Notion.so internal links (keep external citations only)
                if (href.includes('notion.so') || href.includes('notion.com')) {
                    return;
                }

                // Remove duplicates
                if (!seen.has(href)) {
                    seen.add(href);
                    result.push({
                        url: href,
                        text: text || href
                    });
                }
            });

            return result;
        })()
        """
        result = await ctrl.execute_script(script, tab_id)

        if isinstance(result, list):
            return result
        return []
    except Exception:
        return []


async def _wait_for_element_ready(ctrl: BrowserController, selector: str, tab_id: int, timeout: int = 10) -> bool:
    """Wait for element to be present and interactable using get_text (CSP-safe)."""
    start = dt.datetime.now()
    while (dt.datetime.now() - start).total_seconds() < timeout:
        try:
            # Use get_text instead of execute_script to avoid CSP issues
            result = await ctrl.get_text(selector, tab_id)
            if result and not result.get('error'):
                return True
        except Exception:
            pass
        await asyncio.sleep(0.5)
    return False


async def _wait_for_send_button_enabled(ctrl: BrowserController, tab_id: int, timeout: int = 10) -> bool:
    """Wait for send button to be enabled by checking if it's clickable."""
    start = dt.datetime.now()
    while (dt.datetime.now() - start).total_seconds() < timeout:
        try:
            # Try to get text from the button - if successful, it exists
            result = await ctrl.get_text('[data-testid="agent-send-message-button"]', tab_id)
            if result and not result.get('error'):
                # Button exists, assume it's enabled after textbox has content
                return True
        except Exception:
            pass
        await asyncio.sleep(0.5)
    return False


async def _press_enter_on_prompt(ctrl: BrowserController, tab_id: int) -> None:
    script = r"""(() => {
  const sel = '[role="textbox"]';
  const el = document.querySelector(sel) || document.activeElement;
  if (!el) return false;
  el.focus();
  const evt = new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true });
  el.dispatchEvent(evt);
  return true;
})()"""
    await ctrl.execute_script(script, tab_id)


@dataclass
class RunResult:
    tab_id: int
    url: str
    prompt: str
    answer: str
    raw_text_path: Path
    md_path: Path
    links: List[Dict[str, str]] = None


async def _wait_for_stable_answer(ctrl: BrowserController, tab_id: int, prompt: str, *, interval: float, timeout: int) -> Tuple[str, str, List[Dict[str, str]]]:
    start = dt.datetime.now()
    last: Optional[str] = None
    stable = 0
    raw_text = ""
    no_change_count = 0
    max_no_change = 3  # If no change for 3 intervals, consider it stable

    p = prompt.strip()
    key = p[:32] if p else ""

    while (dt.datetime.now() - start).total_seconds() < timeout:
        raw_text = await _get_page_text_with_iframes(ctrl, tab_id)

        # Require the prompt to appear in page text first.
        if key and (key not in raw_text) and (p not in raw_text):
            await asyncio.sleep(interval)
            continue

        answer = _extract_answer(raw_text, prompt)

        # Accept answers with at least 10 characters
        if answer and len(answer) >= 10:
            if last == answer:
                no_change_count += 1
                # If answer hasn't changed for max_no_change intervals, consider stable
                if no_change_count >= max_no_change:
                    links = await _extract_links(ctrl, tab_id)
                    return raw_text, answer, links
            else:
                no_change_count = 0
            last = answer

        await asyncio.sleep(interval)

    # Return whatever we have at timeout
    links = await _extract_links(ctrl, tab_id)
    return raw_text, _extract_answer(raw_text, prompt) if raw_text else "", links


async def _open_and_send(ctrl: BrowserController, *, agent_id: str, prompt: str, base_url: str = "https://www.notion.so/ai") -> int:
    created = await ctrl.tab_create_locked(agent_id, url=base_url)
    if not created.get("success"):
        raise RuntimeError(f"Failed to create locked tab: {created}")
    tab_id = int(created.get("tabId"))

    # Wait for page to load - longer wait for initial load
    await asyncio.sleep(5)

    # Focus prompt input and send - with retry logic
    prompt_sel = '[role="textbox"]'
    key = prompt.strip()[:32]
    max_retries = 3

    for attempt in range(max_retries):
        # Wait for textbox to be ready
        if not await _wait_for_element_ready(ctrl, prompt_sel, tab_id, timeout=10):
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
                continue
            else:
                raise RuntimeError(f"Textbox not ready after {max_retries} attempts")

        # Click and type
        await ctrl.click(prompt_sel, tab_id)
        await asyncio.sleep(0.3)
        await ctrl.type_text(prompt, prompt_sel, tab_id)
        await asyncio.sleep(0.5)

        # Verify text was entered by checking the textbox content
        textbox_result = await ctrl.get_text(prompt_sel, tab_id)
        textbox_text = ""
        if isinstance(textbox_result, dict):
            textbox_text = textbox_result.get("text", "")

        if key in textbox_text:
            # Text successfully entered, wait for send button to be enabled
            if not await _wait_for_send_button_enabled(ctrl, tab_id, timeout=10):
                if attempt < max_retries - 1:
                    # Clear and retry
                    await ctrl.click(prompt_sel, tab_id)
                    clear_script = """(() => {
                        const el = document.querySelector('[role="textbox"]');
                        if (el) {
                            el.focus();
                            el.textContent = '';
                            el.innerText = '';
                        }
                    })()"""
                    await ctrl.execute_script(clear_script, tab_id)
                    await asyncio.sleep(0.5)
                    continue

            # Send button is enabled, click it
            await ctrl.click('[data-testid="agent-send-message-button"]', tab_id)
            await asyncio.sleep(0.8)

            # Verify the prompt appears in the page after sending
            raw_text = await _get_page_text_with_iframes(ctrl, tab_id)
            if key in raw_text:
                return tab_id

            # Fallback: try Enter key
            await ctrl.click(prompt_sel, tab_id)
            await _press_enter_on_prompt(ctrl, tab_id)
            await asyncio.sleep(0.8)
            raw_text = await _get_page_text_with_iframes(ctrl, tab_id)
            if key in raw_text:
                return tab_id

        # Text not entered, clear and retry
        if attempt < max_retries - 1:
            # Clear textbox
            await ctrl.click(prompt_sel, tab_id)
            clear_script = """(() => {
                const el = document.querySelector('[role="textbox"]');
                if (el) {
                    el.focus();
                    el.textContent = '';
                    el.innerText = '';
                }
            })()"""
            await ctrl.execute_script(clear_script, tab_id)
            await asyncio.sleep(0.5)

    return tab_id


async def _send_prompt_with_retry(ctrl: BrowserController, tab_id: int, prompt: str, *, max_retries: int = 3) -> bool:
    """既存タブにプロンプトを送信（入力確認・リトライ付き）。成功時True、失敗時False。"""
    prompt_sel = '[role="textbox"]'
    key = prompt.strip()[:32]

    for attempt in range(max_retries):
        if not await _wait_for_element_ready(ctrl, prompt_sel, tab_id, timeout=10):
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
                continue
            return False

        await ctrl.click(prompt_sel, tab_id)
        await asyncio.sleep(0.3)
        await ctrl.type_text(prompt, prompt_sel, tab_id)
        await asyncio.sleep(0.5)

        textbox_result = await ctrl.get_text(prompt_sel, tab_id)
        textbox_text = textbox_result.get("text", "") if isinstance(textbox_result, dict) else ""

        if key in textbox_text:
            if not await _wait_for_send_button_enabled(ctrl, tab_id, timeout=10):
                if attempt < max_retries - 1:
                    await ctrl.click(prompt_sel, tab_id)
                    await ctrl.execute_script("document.querySelector('[role=\"textbox\"]').textContent=''", tab_id)
                    await asyncio.sleep(0.5)
                    continue

            await ctrl.click('[data-testid="agent-send-message-button"]', tab_id)
            await asyncio.sleep(0.8)
            raw_text = await _get_page_text_with_iframes(ctrl, tab_id)
            if key in raw_text:
                return True

            await ctrl.click(prompt_sel, tab_id)
            await _press_enter_on_prompt(ctrl, tab_id)
            await asyncio.sleep(0.8)
            raw_text = await _get_page_text_with_iframes(ctrl, tab_id)
            if key in raw_text:
                return True

        if attempt < max_retries - 1:
            await ctrl.click(prompt_sel, tab_id)
            await ctrl.execute_script("document.querySelector('[role=\"textbox\"]').textContent=''", tab_id)
            await asyncio.sleep(0.5)

    return False


def _update_session_tab_md_path(session_path: Path, tab_id: int, md_path: str) -> None:
    """セッションファイル内の指定タブのmd_pathを更新"""
    if not session_path.exists():
        return
    try:
        session = json.loads(session_path.read_text(encoding="utf-8"))
        updated = False
        for t in session.get("tabs", []):
            tid = t.get("id") or t.get("tabId")
            if tid and int(tid) == tab_id:
                t["md_path"] = md_path
                updated = True
                break
        if updated:
            session_path.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


def _write_result_md(path: Path, *, prompt: str, answer: str, tab_id: int, url: str, links: List[Dict[str, str]] = None, turn: int = 1) -> None:
    """MDファイルに結果を書き込み（新規作成または追記）

    turn=1の場合: ファイルヘッダー + Turn 1 を新規作成
    turn>1の場合: 既存ファイルに Turn N を追記
    """
    from datetime import datetime

    if turn == 1:
        # 初回ターン: ファイルヘッダー + Turn 1
        lines = []
        lines.append(f"# Notion AI Multi-Turn Session")
        lines.append("")
        lines.append("## セッション情報")
        lines.append(f"- Tab ID: {tab_id}")
        lines.append(f"- URL: {url}")
        lines.append(f"- セッション開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Turn 1")
        lines.append(f"**Prompt**: {prompt}")
        lines.append(f"**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append(answer if answer else "(waiting...)")

        # Add citation links if available
        if links and len(links) > 0:
            lines.append("")
            lines.append("### 参照リンク")
            for i, link in enumerate(links, 1):
                link_text = link.get('text', '')
                link_url = link.get('url', '')
                if link_text and link_text != link_url:
                    lines.append(f"{i}. [{link_text}]({link_url})")
                else:
                    lines.append(f"{i}. {link_url}")

        lines.append("")
        path.write_text("\n".join(lines), encoding="utf-8")
    else:
        # 2回目以降: 既存ファイルに追記
        with open(path, 'a', encoding='utf-8') as f:
            f.write(f"\n---\n\n## Turn {turn}\n")
            f.write(f"**Prompt**: {prompt}\n")
            f.write(f"**Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(answer if answer else "*回答を取得できませんでした*")

            # Add citation links if available
            if links and len(links) > 0:
                f.write("\n\n### 参照リンク\n")
                for i, link in enumerate(links, 1):
                    link_text = link.get('text', '')
                    link_url = link.get('url', '')
                    if link_text and link_text != link_url:
                        f.write(f"{i}. [{link_text}]({link_url})\n")
                    else:
                        f.write(f"{i}. {link_url}\n")

            f.write("\n")


async def cmd_status(ctrl: BrowserController) -> int:
    tabs = await ctrl.get_tabs()
    print(f"[Bridge] {ctrl.BRIDGE_URL}")
    print(f"[Tabs] {len(tabs)} tabs open")
    return 0


async def cmd_tabs(ctrl: BrowserController) -> int:
    tabs = await ctrl.get_tabs()
    for t in tabs:
        tid = t.get("id")
        title = (t.get("title") or "").strip()
        url = (t.get("url") or "").strip()
        active = "*" if t.get("active") else " "
        print(f"{active} [{tid}] {title}\n    {url}")
    return 0


async def cmd_search(
    ctrl: BrowserController,
    prompts: List[str],
    *,
    mode: str,
    interval: float,
    timeout: int,
    close_tabs: bool,
    save_raw: bool,
    repo_root: Path,
    turns: int = 1,
) -> int:
    if mode == "search" and len(prompts) < 3:
        raise SystemExit("search requires 3+ prompts. Use 'search1' for sequential execution.")
    if len(prompts) < 1:
        raise SystemExit("No prompts provided")

    month, day = _today_dir()
    topic = _sanitize_topic(prompts[0])
    # アプリ名を追加: Flow/YYYYMM/YYYY-MM-DD/Notion/セッション名
    outdir = repo_root / "Flow" / month / day / "Notion" / topic
    outdir.mkdir(parents=True, exist_ok=True)

    results: List[RunResult] = []
    start_ts = _now_stamp()

    async def run_one(i: int, p: str, tab_id: int = None) -> RunResult:
        agent_id = f"notionai_multi_{start_ts}_{i+1}"

        # If tab_id is provided, reuse it; otherwise create a new tab
        if tab_id is None:
            tab_id = await _open_and_send(ctrl, agent_id=agent_id, prompt=p)
        else:
            # Tab already created, just send the prompt with verification
            prompt_sel = '[role="textbox"]'
            key = p.strip()[:32]
            max_retries = 3

            for attempt in range(max_retries):
                # Wait for textbox to be ready
                if not await _wait_for_element_ready(ctrl, prompt_sel, tab_id, timeout=10):
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        continue
                    else:
                        break

                await ctrl.click(prompt_sel, tab_id)
                await asyncio.sleep(0.3)
                await ctrl.type_text(p, prompt_sel, tab_id)
                await asyncio.sleep(0.5)

                # Verify text was entered
                textbox_result = await ctrl.get_text(prompt_sel, tab_id)
                textbox_text = ""
                if isinstance(textbox_result, dict):
                    textbox_text = textbox_result.get("text", "")

                if key in textbox_text:
                    # Wait for send button to be enabled
                    if not await _wait_for_send_button_enabled(ctrl, tab_id, timeout=10):
                        if attempt < max_retries - 1:
                            await ctrl.click(prompt_sel, tab_id)
                            clear_script = """(() => {
                                const el = document.querySelector('[role="textbox"]');
                                if (el) {
                                    el.focus();
                                    el.textContent = '';
                                    el.innerText = '';
                                }
                            })()"""
                            await ctrl.execute_script(clear_script, tab_id)
                            await asyncio.sleep(0.5)
                            continue

                    # Text entered successfully, send
                    await ctrl.click('[data-testid="agent-send-message-button"]', tab_id)
                    await asyncio.sleep(0.8)

                    # Verify the prompt appears after sending
                    raw_text = await _get_page_text_with_iframes(ctrl, tab_id)
                    if key in raw_text:
                        break

                    # Fallback: try Enter key
                    await ctrl.click(prompt_sel, tab_id)
                    await _press_enter_on_prompt(ctrl, tab_id)
                    await asyncio.sleep(0.8)
                    raw_text = await _get_page_text_with_iframes(ctrl, tab_id)
                    if key in raw_text:
                        break

                # Clear and retry if not last attempt
                if attempt < max_retries - 1:
                    await ctrl.click(prompt_sel, tab_id)
                    clear_script = """(() => {
                        const el = document.querySelector('[role="textbox"]');
                        if (el) {
                            el.focus();
                            el.textContent = '';
                            el.innerText = '';
                        }
                    })()"""
                    await ctrl.execute_script(clear_script, tab_id)
                    await asyncio.sleep(0.5)

        raw_text, answer, links = await _wait_for_stable_answer(ctrl, tab_id, p, interval=interval, timeout=timeout)
        url = ""
        for t in await ctrl.get_tabs():
            if int(t.get("id")) == tab_id:
                url = t.get("url") or ""
                break

        ts = _now_stamp()
        raw_path = outdir / f"notionai_q{i+1}_{ts}.raw.txt"
        md_path = outdir / f"notionai_q{i+1}_{ts}.md"
        if save_raw:
            raw_path.write_text(raw_text, encoding="utf-8")
        _write_result_md(md_path, prompt=p, answer=answer, tab_id=tab_id, url=url, links=links)

        if close_tabs:
            await ctrl.tab_close_locked(tab_id, agent_id)

        return RunResult(tab_id=tab_id, url=url, prompt=p, answer=answer, raw_text_path=raw_path, md_path=md_path, links=links)

    if mode == "search1":
        # Sequential on one tab.
        agent_id = f"notionai_multi_{start_ts}_single"
        created = await ctrl.tab_create_locked(agent_id, url="https://www.notion.so/ai")
        if not created.get("success"):
            raise RuntimeError(f"Failed to create locked tab: {created}")
        tab_id = int(created.get("tabId"))
        url = ""

        # Wait for initial page load
        await asyncio.sleep(3)

        prompt_sel = '[role="textbox"]'
        for i, p in enumerate(prompts):
            key = p.strip()[:32]
            max_retries = 3

            for attempt in range(max_retries):
                # Wait for textbox to be ready
                if not await _wait_for_element_ready(ctrl, prompt_sel, tab_id, timeout=10):
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)
                        continue
                    else:
                        break

                # Click and type
                await ctrl.click(prompt_sel, tab_id)
                await asyncio.sleep(0.3)
                await ctrl.type_text(p, prompt_sel, tab_id)
                await asyncio.sleep(0.5)

                # Verify text was entered
                textbox_result = await ctrl.get_text(prompt_sel, tab_id)
                textbox_text = ""
                if isinstance(textbox_result, dict):
                    textbox_text = textbox_result.get("text", "")

                if key in textbox_text:
                    # Wait for send button to be enabled
                    if not await _wait_for_send_button_enabled(ctrl, tab_id, timeout=10):
                        if attempt < max_retries - 1:
                            await ctrl.click(prompt_sel, tab_id)
                            clear_script = """(() => {
                                const el = document.querySelector('[role="textbox"]');
                                if (el) {
                                    el.focus();
                                    el.textContent = '';
                                    el.innerText = '';
                                }
                            })()"""
                            await ctrl.execute_script(clear_script, tab_id)
                            await asyncio.sleep(0.5)
                            continue

                    # Text entered successfully, send
                    await ctrl.click('[data-testid="agent-send-message-button"]', tab_id)
                    break
                elif attempt < max_retries - 1:
                    # Clear and retry
                    await ctrl.click(prompt_sel, tab_id)
                    clear_script = """(() => {
                        const el = document.querySelector('[role="textbox"]');
                        if (el) {
                            el.focus();
                            el.textContent = '';
                            el.innerText = '';
                        }
                    })()"""
                    await ctrl.execute_script(clear_script, tab_id)
                    await asyncio.sleep(0.5)

            raw_text, answer, links = await _wait_for_stable_answer(ctrl, tab_id, p, interval=interval, timeout=timeout)

            for t in await ctrl.get_tabs():
                if int(t.get("id")) == tab_id:
                    url = t.get("url") or ""
                    break

            ts = _now_stamp()
            raw_path = outdir / f"notionai_q{i+1}_{ts}.raw.txt"
            md_path = outdir / f"notionai_q{i+1}_{ts}.md"
            if save_raw:
                raw_path.write_text(raw_text, encoding="utf-8")
            _write_result_md(md_path, prompt=p, answer=answer, tab_id=tab_id, url=url, links=links)
            results.append(RunResult(tab_id=tab_id, url=url, prompt=p, answer=answer, raw_text_path=raw_path, md_path=md_path, links=links))

        if close_tabs:
            await ctrl.tab_close_locked(tab_id, agent_id)

    else:
        # Parallel on multiple tabs - create all tabs first, then send prompts
        tab_ids = []
        for i, p in enumerate(prompts):
            agent_id = f"notionai_multi_{start_ts}_{i+1}"
            created = await ctrl.tab_create_locked(agent_id, url="https://www.notion.so/ai")
            if not created.get("success"):
                raise RuntimeError(f"Failed to create locked tab: {created}")
            tab_id = int(created.get("tabId"))
            tab_ids.append(tab_id)
            await asyncio.sleep(1.0)  # Longer delay between tab creations for stability

        # Wait for all tabs to load - longer wait for parallel execution
        await asyncio.sleep(10)

        # Now send prompts and wait for results in parallel
        tasks = [run_one(i, p, tab_id=tab_ids[i]) for i, p in enumerate(prompts)]
        results = await asyncio.gather(*tasks)

    # Save a small session file for convenience (ChatGPT/Grokと同じ形式)
    session = {
        "topic": topic,
        "outdir": str(outdir),
        "createdAt": start_ts,
        "tabs": [
            {
                "id": r.tab_id,
                "url": r.url,
                "topic": topic,
                "prompt": r.prompt,
                "md_path": str(r.md_path),
            }
            for r in results
        ],
        "turns": {
            "total": turns,
            "current": 1,
            "remaining": turns - 1
        }
    }
    session_path = Path.home() / ".notionai_multi_session.json"
    session_path.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[Turn 1/{turns}] Complete.")
    if turns > 1:
        remaining = turns - 1
        print(f"[Session] {len(results)} tabs saved. Remaining turns: {remaining}")
        print(f"[Next] Send follow-up: python notionai_multi.py reply \"Q1\" \"Q2\" ...")
    for r in results:
        print(str(r.md_path))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="notionai_multi.py", description="Notion AI parallel prompt runner")

    p.add_argument("command", nargs="?", default="search", help="search (default), search1, tabs, status, recover, reply, bridge")
    p.add_argument("prompts", nargs="*", help="prompts")

    p.add_argument("--interval", type=float, default=3.0, help="polling interval seconds")
    p.add_argument("--timeout", type=int, default=300, help="timeout seconds per prompt")
    p.add_argument("--close-tabs", action="store_true", help="close tabs after completion")
    p.add_argument("--raw", action="store_true", help="save raw body text (may contain sensitive content)")
    p.add_argument("--no-raw", action="store_true", help="deprecated; keep for compatibility")
    p.add_argument("--tab", type=int, default=None, help="tab id for recover")
    p.add_argument("--prompt", type=str, default=None, help="prompt text for recover extraction")
    p.add_argument("--turns", type=int, default=1, help="Number of conversation turns (default: 1)")
    return p


def run_bridge_only():
    """ブリッジサーバーのみをフォアグラウンドで起動"""
    server = BridgeServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("\n[Bridge] Stopped")


async def main_async(argv: List[str]) -> int:
    known = {"search", "search1", "tabs", "status", "recover", "reply", "bridge"}
    if argv and not argv[0].startswith("-") and argv[0] not in known:
        argv = ["search"] + argv
    args = build_parser().parse_args(argv)
    # If options were specified before prompts, argparse may treat the first prompt as `command`.
    # Recover by shifting it into prompts when it's not a known command.
    if args.command and args.command not in known:
        args.prompts = [args.command] + (args.prompts or [])
        args.command = "search"

    # Bridge command
    if args.command == "bridge":
        run_bridge_only()
        return 0

    # Determine repo root
    repo_root = Path(__file__).resolve().parents[4]

    ctrl = BrowserController(timeout=30, auto_bridge=True)

    cmd = args.command
    save_raw = bool(args.raw) and not bool(args.no_raw)
    if cmd == "status":
        return await cmd_status(ctrl)
    if cmd == "tabs":
        return await cmd_tabs(ctrl)
    if cmd == "recover":
        if args.tab is None:
            raise SystemExit("recover requires --tab")

        # セッションからmd_pathとpromptを取得
        session_path = Path.home() / ".notionai_multi_session.json"
        session = {}
        if session_path.exists():
            try:
                session = json.loads(session_path.read_text(encoding="utf-8"))
            except Exception:
                session = {}

        prompt = args.prompt
        saved_md_path = None
        topic = None
        create_new = False
        if isinstance(session, dict):
            for t in session.get("tabs", []) or []:
                try:
                    tab_id = t.get("id") or t.get("tabId")
                    if int(tab_id) == int(args.tab):
                        prompt = prompt or t.get("prompt")
                        saved_md_path = t.get("md_path") or t.get("md")
                        topic = t.get("topic")
                        break
                except Exception:
                    continue

        # md_pathがセッションにない場合は新規作成
        if not saved_md_path:
            create_new = True
            print(f"[Recover] No md_path in session for tab {args.tab}. Will create new file.")
        elif not Path(saved_md_path).exists():
            create_new = True
            print(f"[Recover] MD file does not exist: {saved_md_path}. Will create new file.")

        url = ""
        for t in await ctrl.get_tabs():
            if int(t.get("id")) == int(args.tab):
                url = t.get("url") or ""
                break

        print(f"[Recover] Tab {args.tab} - Fetching full page content...")

        # 全ページテキストを取得（Notion AIは全文取得が基本）
        raw_text = await _get_page_text_with_iframes(ctrl, int(args.tab))
        links = await _extract_links(ctrl, int(args.tab))

        # プロンプトがあれば回答部分を抽出、なければ全文
        if prompt:
            answer = _extract_answer(raw_text, prompt)
            if not answer:
                # 抽出できなかった場合は全文を使用
                answer = raw_text
        else:
            answer = raw_text

        # md_pathを決定（新規作成 or 上書き）
        if create_new:
            if not topic:
                topic = _sanitize_topic(prompt[:40] if prompt else f"notionai_tab_{args.tab}")
            month, day = _today_dir()
            # アプリ名を追加: Flow/YYYYMM/YYYY-MM-DD/Notion/セッション名
            outdir = repo_root / "Flow" / month / day / "Notion" / topic
            outdir.mkdir(parents=True, exist_ok=True)
            ts = _now_stamp()
            md_path = outdir / f"notionai_chat_tab{args.tab}_{ts}.md"
            print(f"[Recover] Creating new file: {md_path}")
        else:
            md_path = Path(saved_md_path)

        # MDファイルに書き出し
        action = "Creating" if create_new else "Overwriting"
        print(f"[Recover] {action} with full content: {md_path}")
        _write_result_md(md_path, prompt=prompt or "(full page)", answer=answer, tab_id=int(args.tab), url=url, links=links)

        # セッションにmd_pathを保存
        _update_session_tab_md_path(session_path, int(args.tab), str(md_path))

        if save_raw:
            ts = _now_stamp()
            raw_path = md_path.parent / f"notionai_chat_tab{args.tab}_{ts}.raw.txt"
            raw_path.write_text(raw_text, encoding="utf-8")

        print(f"[Recover] Success: {md_path}")
        return 0

    if cmd == "reply":
        # セッションタブに並列でフォローアップ送信
        if not args.prompts:
            raise SystemExit("reply requires prompts (one per session tab)")

        session_path = Path.home() / ".notionai_multi_session.json"
        if not session_path.exists():
            raise SystemExit("No session found. Run 'search' first.")

        session = json.loads(session_path.read_text(encoding="utf-8"))
        session_tabs = session.get("tabs", [])
        turns_info = session.get("turns", {"total": 1, "current": 1, "remaining": 0})

        if len(args.prompts) != len(session_tabs):
            raise SystemExit(f"Number of prompts ({len(args.prompts)}) must match session tabs ({len(session_tabs)})")

        current_turn = turns_info.get("current", 1) + 1
        total_turns = turns_info.get("total", 1)
        remaining = total_turns - current_turn

        print(f"\n{'='*60}")
        print(f"[Turn {current_turn}/{total_turns}] Sending follow-up queries...")
        print('='*60)

        for i, (tab_info, prompt) in enumerate(zip(session_tabs, args.prompts)):
            tab_id = tab_info.get("tabId") or tab_info.get("id")
            md_path = tab_info.get("md") or tab_info.get("md_path")
            print(f"  Tab {i+1} (ID: {tab_id}): Sending...")

            # プロンプト送信（入力確認・リトライ付き）
            send_ok = await _send_prompt_with_retry(ctrl, tab_id, prompt)
            if not send_ok:
                print(f"  Tab {i+1}: FAIL - Failed to send prompt after retries")
                continue

            # 回答待機
            raw_text, answer, links = await _wait_for_stable_answer(
                ctrl, tab_id, prompt,
                interval=args.interval,
                timeout=args.timeout
            )

            # MDに追記
            if md_path and Path(md_path).exists():
                _write_result_md(
                    Path(md_path),
                    prompt=prompt,
                    answer=answer,
                    tab_id=tab_id,
                    url="",
                    links=links,
                    turn=current_turn
                )

            status = "Done" if answer else "FAIL"
            print(f"  Tab {i+1}: {status}")

        # セッション更新
        session["turns"] = {
            "total": total_turns,
            "current": current_turn,
            "remaining": remaining
        }
        session_path.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")

        print(f"\n[Turn {current_turn}/{total_turns}] Complete.")
        if remaining > 0:
            print(f"[Session] Remaining turns: {remaining}")
            print(f"[Next] Send follow-up: python notionai_multi.py reply \"Q1\" \"Q2\" ...")
        else:
            print(f"[Complete] {len(session_tabs)} tabs × {total_turns} turns = {len(session_tabs) * total_turns} queries completed.")
            if args.close_tabs:
                print(f"[Cleanup] Closing tabs...")
                for t in session_tabs:
                    await ctrl.close_tab(t.get("id"))
                print("  Done.")
        return 0

    # default: search/search1
    mode = "search" if cmd == "search" else cmd
    prompts = args.prompts
    return await cmd_search(
        ctrl,
        prompts,
        mode=mode,
        interval=args.interval,
        timeout=args.timeout,
        close_tabs=args.close_tabs,
        save_raw=save_raw,
        repo_root=repo_root,
        turns=args.turns,
    )


def main() -> int:
    try:
        return asyncio.run(main_async(sys.argv[1:]))
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
