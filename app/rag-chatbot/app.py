"""
RAG Chatbot - Flask Server
Gemini APIを使用したRAGチャットボット
左側: PDFビューア、右側: チャットボット
"""

import os
import base64
import mimetypes
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, send_file
from dotenv import load_dotenv
import google.generativeai as genai

# 環境変数を読み込む
load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')

# Gemini API設定
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# データフォルダのベースパス（環境変数またはデフォルト）
BASE_DATA_PATH = os.getenv('DATA_PATH', '/Users/matuni__/Desktop/mini-app-agent/Stock/Explaza_AX_事例集')

# グローバル状態
rag_context = {
    'files': [],
    'content': '',
    'images': []
}

# 対応ファイル形式
SUPPORTED_MD_EXTENSIONS = {'.md', '.markdown', '.txt'}
SUPPORTED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}


def get_all_files():
    """データフォルダ内の全ファイルを取得"""
    base_path = Path(BASE_DATA_PATH)
    md_path = base_path / 'markdown'
    pdf_path = base_path / 'pdfs'

    files = []

    if md_path.exists():
        for file_path in sorted(md_path.glob('*.md')):
            name = file_path.stem
            pdf_file = pdf_path / f"{name}.pdf"
            files.append({
                'name': file_path.name,
                'displayName': name,
                'md_path': str(file_path),
                'pdf_path': str(pdf_file) if pdf_file.exists() else None,
                'pdf_name': f"{name}.pdf" if pdf_file.exists() else None
            })

    return files


def search_files(keyword):
    """キーワードでファイルを検索（ファイル名 + 内容）"""
    all_files = get_all_files()
    keyword_lower = keyword.lower()

    results = []
    for file in all_files:
        # ファイル名で検索
        if keyword_lower in file['name'].lower() or keyword_lower in file['displayName'].lower():
            results.append(file)
            continue

        # MDファイルの内容で検索
        md_path = Path(file['md_path'])
        if md_path.exists():
            try:
                content = md_path.read_text(encoding='utf-8').lower()
                if keyword_lower in content:
                    results.append(file)
            except Exception:
                pass

    return results


def search_with_gemini(query):
    """Gemini APIを使って関連ドキュメントを検索"""
    if not GEMINI_API_KEY:
        return search_files(query)  # フォールバック

    all_files = get_all_files()
    if not all_files:
        return []

    # 全ファイルの要約を作成
    file_summaries = []
    for i, file in enumerate(all_files):
        md_path = Path(file['md_path'])
        if md_path.exists():
            try:
                content = md_path.read_text(encoding='utf-8')
                # 最初の500文字を要約として使用
                summary = content[:500].replace('\n', ' ')
                file_summaries.append(f"{i}: {file['displayName']} - {summary}")
            except Exception:
                file_summaries.append(f"{i}: {file['displayName']}")

    # Gemini APIで関連ファイルを特定
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""以下のドキュメント一覧から、ユーザーの検索クエリに最も関連するドキュメントを選んでください。

検索クエリ: {query}

ドキュメント一覧:
{chr(10).join(file_summaries[:50])}

関連するドキュメントの番号を、関連度が高い順にカンマ区切りで最大10件返してください。
番号のみを返してください（例: 3,7,12,5）。
該当するものがない場合は「なし」と返してください。"""

        response = model.generate_content(prompt)
        response_text = response.text.strip()

        if response_text == 'なし' or not response_text:
            return []

        # 番号をパース
        indices = []
        for part in response_text.replace(' ', '').split(','):
            try:
                idx = int(part)
                if 0 <= idx < len(all_files):
                    indices.append(idx)
            except ValueError:
                continue

        return [all_files[i] for i in indices[:10]]

    except Exception as e:
        print(f'Gemini search error: {e}')
        # フォールバック: 通常の検索
        return search_files(query)


def load_selected_files(file_names):
    """選択されたファイルを読み込む"""
    all_files = get_all_files()
    base_path = Path(BASE_DATA_PATH)
    images_path = base_path / 'images'

    selected = []
    md_contents = []
    images = []

    for file_name in file_names:
        for file in all_files:
            if file['name'] == file_name:
                md_path = Path(file['md_path'])
                if md_path.exists():
                    try:
                        content = md_path.read_text(encoding='utf-8')
                        md_contents.append({
                            'name': file['name'],
                            'displayName': file['displayName'],
                            'content': content
                        })
                        selected.append({
                            'name': file['pdf_name'] or file['name'],
                            'displayName': file['displayName'],
                            'md_name': file['name'],
                            'type': 'md'
                        })
                    except Exception as e:
                        print(f'MDファイル読み込みエラー: {md_path}: {e}')
                break

    # 関連画像を読み込む
    if images_path.exists():
        for img_path in images_path.glob('*'):
            if img_path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                try:
                    mime_type, _ = mimetypes.guess_type(str(img_path))
                    with open(img_path, 'rb') as f:
                        image_data = base64.b64encode(f.read()).decode('utf-8')
                    images.append({
                        'name': img_path.name,
                        'path': str(img_path),
                        'data': image_data,
                        'mime_type': mime_type or 'image/png'
                    })
                except Exception as e:
                    print(f'画像読み込みエラー: {img_path}: {e}')

    # コンテキストを構築
    context_parts = []
    for md in md_contents:
        context_parts.append(f"## {md['displayName']}\n{md['content']}\n")

    combined_content = '\n---\n'.join(context_parts)

    return selected, combined_content, images, md_contents


def create_prompt_with_context(user_message, context):
    """RAGコンテキスト付きプロンプトを生成"""
    system_prompt = """あなたは提供されたドキュメントに基づいて質問に回答するアシスタントです。
以下のルールに従ってください：
1. 提供されたコンテキストの情報のみを使用して回答してください
2. コンテキストに情報がない場合は「提供されたドキュメントにはその情報がありません」と回答してください
3. 回答は簡潔かつ正確にしてください
4. 回答の根拠となるドキュメント名を明示してください

---
# 参照ドキュメント:
"""

    full_prompt = f"{system_prompt}\n{context}\n\n---\n# ユーザーの質問:\n{user_message}"

    return full_prompt


def find_relevant_sources(response_text, files, md_contents):
    """回答に関連するソースを特定"""
    sources = []
    response_lower = response_text.lower()

    for md in md_contents:
        name_lower = md['displayName'].lower()
        if name_lower in response_lower or md['name'].lower() in response_lower:
            sources.append({
                'name': md['name'],
                'displayName': md['displayName'],
                'type': 'md'
            })

    # ソースが見つからない場合は最初の3件を返す
    if not sources:
        for md in md_contents[:3]:
            sources.append({
                'name': md['name'],
                'displayName': md['displayName'],
                'type': 'md'
            })

    return sources


# ==========================================================================
# Routes
# ==========================================================================

@app.route('/')
def index():
    """メインページを返す"""
    return send_from_directory('.', 'index.html')


@app.route('/css/<path:filename>')
def serve_css(filename):
    """CSSファイルを返す"""
    return send_from_directory('css', filename)


@app.route('/js/<path:filename>')
def serve_js(filename):
    """JSファイルを返す"""
    return send_from_directory('js', filename)


@app.route('/api/search', methods=['POST'])
def api_search():
    """キーワードでファイルを検索（Gemini API使用）"""
    try:
        data = request.get_json()
        keyword = data.get('keyword', '').strip()

        if not keyword:
            return jsonify({'error': 'キーワードを入力してください'}), 400

        # まず通常検索を試す
        files = search_files(keyword)

        # 通常検索で見つからない場合、Gemini検索を使用
        if not files and GEMINI_API_KEY:
            files = search_with_gemini(keyword)

        return jsonify({
            'success': True,
            'count': len(files),
            'files': [{'name': f['name'], 'displayName': f['displayName']} for f in files]
        })

    except Exception as e:
        print(f'Search error: {e}')
        return jsonify({'error': '検索に失敗しました'}), 500


@app.route('/api/load', methods=['POST'])
def api_load():
    """選択されたファイルを読み込む"""
    global rag_context

    try:
        data = request.get_json()
        file_names = data.get('files', [])

        if not file_names:
            return jsonify({'error': 'ファイルを選択してください'}), 400

        files, content, images, md_contents = load_selected_files(file_names)

        if not files:
            return jsonify({'error': 'ファイルの読み込みに失敗しました'}), 400

        rag_context = {
            'files': files,
            'content': content,
            'images': images,
            'md_contents': md_contents
        }

        return jsonify({
            'success': True,
            'count': len(files),
            'files': [{'name': f['name'], 'displayName': f['displayName']} for f in files]
        })

    except Exception as e:
        print(f'Load error: {e}')
        return jsonify({'error': 'ファイルの読み込みに失敗しました'}), 500


@app.route('/api/pdf/<path:filename>')
def api_pdf(filename):
    """PDFファイルを返す"""
    try:
        pdf_path = Path(BASE_DATA_PATH) / 'pdfs' / filename
        if pdf_path.exists():
            return send_file(pdf_path, mimetype='application/pdf')
        else:
            return jsonify({'error': 'PDFが見つかりません'}), 404
    except Exception as e:
        print(f'PDF error: {e}')
        return jsonify({'error': 'PDFの読み込みに失敗しました'}), 500


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """チャットメッセージを処理"""
    global rag_context

    if not GEMINI_API_KEY:
        return jsonify({
            'error': 'Gemini APIキーが設定されていません。.envファイルにGEMINI_API_KEYを設定してください。'
        }), 500

    if not rag_context.get('files'):
        return jsonify({
            'error': 'ドキュメントが読み込まれていません。先にファイルを選択してください。'
        }), 400

    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({'error': 'メッセージを入力してください'}), 400

        # プロンプト生成
        prompt = create_prompt_with_context(
            user_message,
            rag_context['content']
        )

        # Gemini APIで回答生成
        model = genai.GenerativeModel('gemini-2.0-flash')

        # テキストと画像を含むコンテンツを作成
        content_parts = [prompt]

        # 画像がある場合は追加（最大5枚）
        for img in rag_context.get('images', [])[:5]:
            content_parts.append({
                'mime_type': img['mime_type'],
                'data': img['data']
            })

        response = model.generate_content(content_parts)
        response_text = response.text

        # 関連ソースを特定
        sources = find_relevant_sources(
            response_text,
            rag_context['files'],
            rag_context.get('md_contents', [])
        )

        return jsonify({
            'response': response_text,
            'sources': sources
        })

    except Exception as e:
        import traceback
        print(f'Chat error: {e}')
        print(traceback.format_exc())
        error_message = str(e)

        if 'quota' in error_message.lower():
            return jsonify({
                'error': 'APIのレート制限に達しました。しばらく待ってから再試行してください。'
            }), 429

        return jsonify({
            'error': f'API接続に失敗しました: {error_message}'
        }), 500


# ==========================================================================
# Main
# ==========================================================================

if __name__ == '__main__':
    if not GEMINI_API_KEY:
        print('警告: GEMINI_API_KEYが設定されていません。')
        print('.envファイルにGEMINI_API_KEY=your_api_keyを追加してください。')

    print(f'データフォルダ: {BASE_DATA_PATH}')
    print('RAG Chatbot Server starting...')
    print('http://localhost:5001 でアクセスできます')
    app.run(debug=True, port=5001)
