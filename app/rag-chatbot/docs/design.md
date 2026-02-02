# rag-chatbot 設計書

## 概要
- 作成日: 2026-01-30
- 作成者: -
- ステータス: Draft
- 参照: requirements.md

## 1. 画面一覧

| 画面ID | 画面名 | 説明 | 対応機能ID |
|--------|--------|------|------------|
| S01 | メイン画面 | チャットUI、フォルダ指定、会話表示 | M1, M2, M3, M4, S1, S2, S3, C1 |

## 2. 画面設計

### S01: メイン画面

#### ワイヤーフレーム（ASCII）
```
+--------------------------------------------------+
|  RAG Chatbot                            [Clear]  |
+--------------------------------------------------+
|                                                  |
|  +--------------------------------------------+  |
|  |  Folder: [________________________] [Load] |  |
|  |  Status: 5 files loaded (3 MD, 2 images)   |  |
|  +--------------------------------------------+  |
|                                                  |
|  +--------------------------------------------+  |
|  |                                            |  |
|  |  [User] こんにちは                          |  |
|  |                                            |  |
|  |  [Bot] こんにちは！何かお手伝いできますか？   |  |
|  |        📄 参照: doc1.md, doc2.md            |  |
|  |                                            |  |
|  |  [User] このプロジェクトの概要は？            |  |
|  |                                            |  |
|  |  [Bot] このプロジェクトは...                 |  |
|  |        📄 参照: overview.md                 |  |
|  |        🖼️ 参照: diagram.png                |  |
|  |                                            |  |
|  |  ●●● (Loading...)                          |  |
|  |                                            |  |
|  +--------------------------------------------+  |
|                                                  |
|  +--------------------------------------------+  |
|  | [Message input...                ] [Send]  |  |
|  +--------------------------------------------+  |
|                                                  |
+--------------------------------------------------+
```

#### 要素説明
| 要素 | 説明 | インタラクション |
|------|------|------------------|
| Header | アプリタイトル、クリアボタン | - |
| Folder Input | RAGソースフォルダのパス入力 | パス入力後Loadボタンで読み込み |
| Status | 読み込んだファイル数・種類を表示 | - |
| Chat Area | 会話履歴を表示するスクロール領域 | 自動スクロール |
| User Message | ユーザーの質問を右寄せで表示 | - |
| Bot Message | AIの回答を左寄せで表示 | - |
| Source Reference | 参照したMD/画像ファイル名を表示 | クリックで詳細表示（将来拡張） |
| Loading Indicator | API応答待ち中のアニメーション | - |
| Message Input | 質問入力フォーム | Enter/Sendボタンで送信 |
| Send Button | メッセージ送信ボタン | クリックで送信 |
| Clear Button | 会話履歴をクリア | クリックで確認後クリア |

#### レスポンシブ対応
| ブレークポイント | 幅 | レイアウト | ガター |
|------------------|-----|------------|--------|
| Desktop | 1024px~ | 固定幅800px中央寄せ | 32px |

※ローカル開発用途のためPC専用。レスポンシブ非対応。

## 3. 画面遷移図

```
[S01: メイン画面]
      ↓ フォルダ指定 + Load
[S01: メイン画面（ファイル読み込み済み）]
      ↓ 質問送信
[S01: メイン画面（回答表示）]
      ↓ Clearボタン
[S01: メイン画面（初期状態）]
```

※単一画面アプリのため遷移なし

## 4. コンポーネント一覧

| コンポーネント | 説明 | 使用画面 | 再利用 |
|----------------|------|----------|--------|
| Header | アプリヘッダー | S01 | No |
| FolderInput | フォルダパス入力 | S01 | No |
| ChatArea | 会話履歴表示エリア | S01 | No |
| MessageBubble | メッセージ吹き出し | S01 | Yes |
| SourceReference | 参照ソース表示 | S01 | Yes |
| LoadingIndicator | ローディングアニメーション | S01 | Yes |
| MessageInput | 入力フォーム | S01 | No |
| Button | 汎用ボタン | S01 | Yes |

### コンポーネント詳細

#### Button
- 構成要素: ラベル、アイコン（オプション）
- 最小サイズ: 44x44px（フィッツの法則準拠、タッチ/クリックターゲット確保）
- バリエーション:
  - Primary: 背景色あり、主要アクション用（Send, Load）
  - Secondary: 枠線のみ、副次アクション用（Clear）
  - Disabled: グレーアウト、操作不可時
- 状態管理:
  | 状態 | 視覚変化 | トランジション |
  |------|----------|----------------|
  | default | ベースカラー | - |
  | hover | 少し濃く、影を強く | 200ms |
  | active | さらに濃く、translateY(1px) | 150ms |
  | focus | フォーカスリング表示 | 200ms |
  | disabled | 彩度を落とす、cursor: not-allowed | - |

#### MessageBubble
- 構成要素: アバター、メッセージ本文、参照ソース
- バリエーション:
  - User: 右寄せ、プライマリカラー背景
  - Bot: 左寄せ、グレー背景
- マークダウン対応: 太字、リスト、コードブロック

#### LoadingIndicator
- 3つのドットが順番にバウンスするアニメーション
- 位置: チャットエリア下部

## 5. ビジュアル設計

> 参照: design_system_principles.md

### カラースキーム

#### プライマリカラー（HSLベース）
| レベル | HSL | HEX | 用途 |
|--------|-----|-----|------|
| primary-500 | hsl(220, 75%, 50%) | #2563EB | ベースカラー |
| primary-600 | hsl(220, 80%, 42%) | #1D4ED8 | hover状態 |
| primary-700 | hsl(220, 85%, 35%) | #1E40AF | active状態 |

#### グレースケール
| レベル | 用途 | HEX |
|--------|------|-----|
| gray-50 | 背景（ライト） | #F9FAFB |
| gray-100 | 背景（セカンダリ） | #F3F4F6 |
| gray-200 | ボーダー | #E5E7EB |
| gray-500 | ミュートテキスト | #6B7280 |
| gray-900 | メインテキスト | #111827 |

#### セマンティックカラー
| 用途 | カラー | HEX | コントラスト比 |
|------|--------|-----|----------------|
| Success | Green | #22C55E | 4.5:1以上 |
| Warning | Amber | #F59E0B | 4.5:1以上 |
| Error | Red | #EF4444 | 4.5:1以上 |
| Info | Blue | #3B82F6 | 4.5:1以上 |

#### メッセージバブルカラー
| 種類 | 背景色 | テキスト色 |
|------|--------|-----------|
| User | primary-500 (#2563EB) | white |
| Bot | gray-100 (#F3F4F6) | gray-900 |

### タイポグラフィ

#### フォントスタック
```css
--font-sans: system-ui, -apple-system, sans-serif;
--font-mono: ui-monospace, SFMono-Regular, monospace;
```

#### サイズスケール（モジュラースケール 1.25）
| 要素 | サイズ | line-height | 太さ | 用途 |
|------|--------|-------------|------|------|
| h1 | 1.5rem (24px) | 1.25 | 700 | アプリタイトル |
| body | 1rem (16px) | 1.5 | 400 | メッセージ本文 |
| small | 0.875rem (14px) | 1.5 | 400 | 参照ソース、ステータス |
| caption | 0.75rem (12px) | 1.4 | 400 | タイムスタンプ |

## 6. 技術設計

### ファイル構成
```
rag-chatbot/
├── index.html          # フロントエンドHTML
├── css/
│   └── style.css       # スタイルシート
├── js/
│   └── app.js          # フロントエンドJS
├── app.py              # Flaskサーバー
├── .env.example        # 環境変数テンプレート
├── requirements.txt    # Python依存関係
└── docs/
    ├── requirements.md
    └── design.md
```

### HTML構造
```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG Chatbot</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div class="app">
        <header class="header">
            <h1 class="header__title">RAG Chatbot</h1>
            <div class="header__actions">
                <button class="btn btn--secondary" id="clearBtn">Clear</button>
            </div>
        </header>

        <section class="folder-input">
            <label for="folderPath">Folder Path:</label>
            <input type="text" id="folderPath" placeholder="/path/to/documents">
            <button class="btn btn--primary" id="loadBtn">Load</button>
            <p class="folder-input__status" id="loadStatus"></p>
        </section>

        <main class="chat-area" id="chatArea" aria-live="polite">
            <!-- Messages will be inserted here -->
        </main>

        <footer class="message-input">
            <input type="text" id="messageInput" placeholder="Type your message..." aria-label="Message input">
            <button class="btn btn--primary" id="sendBtn">Send</button>
        </footer>
    </div>
    <script src="js/app.js"></script>
</body>
</html>
```

### CSS設計方針
- 命名規則: BEM（Block__Element--Modifier）
- CSS変数使用（デザイントークン）
- 8pxグリッドシステム準拠

```css
:root {
    /* ==================
       Spacing (8px Grid)
       ================== */
    --space-unit: 0.5rem; /* 8px */
    --space-1: 0.25rem;   /* 4px */
    --space-2: 0.5rem;    /* 8px */
    --space-3: 0.75rem;   /* 12px */
    --space-4: 1rem;      /* 16px */
    --space-6: 1.5rem;    /* 24px */
    --space-8: 2rem;      /* 32px */
    --space-12: 3rem;     /* 48px */

    /* ==================
       Colors
       ================== */
    --c-primary: #2563EB;
    --c-primary-hover: #1D4ED8;
    --c-primary-active: #1E40AF;
    --c-bg: #F9FAFB;
    --c-bg-secondary: #F3F4F6;
    --c-fg: #111827;
    --c-muted: #6B7280;
    --c-border: #E5E7EB;
    --c-success: #22C55E;
    --c-warning: #F59E0B;
    --c-error: #EF4444;

    /* ==================
       Typography
       ================== */
    --font-sans: system-ui, -apple-system, sans-serif;
    --font-mono: ui-monospace, SFMono-Regular, monospace;
    --font-size-sm: 0.875rem;
    --font-size-base: 1rem;
    --font-size-lg: 1.125rem;
    --font-size-xl: 1.5rem;
    --leading-normal: 1.5;
    --leading-tight: 1.25;

    /* ==================
       Effects
       ================== */
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 12px;
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);

    /* ==================
       Motion
       ================== */
    --ease-standard: cubic-bezier(0.2, 0, 0, 1);
    --dur-quick: 150ms;
    --dur-base: 200ms;

    /* ==================
       Focus Ring
       ================== */
    --ring-color: rgba(37, 99, 235, 0.35);
    --ring-size: 3px;
    --ring-offset: 2px;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
    :root {
        --dur-quick: 1ms;
        --dur-base: 1ms;
    }
}
```

### JavaScript設計方針
- ES6+ 構文使用
- DOM操作: querySelector / addEventListener
- 状態管理: シンプルなオブジェクトベース
- API通信: fetch API

```javascript
// 状態管理
const state = {
    messages: [],
    loadedFiles: [],
    isLoading: false
};

// APIエンドポイント
const API = {
    load: '/api/load',
    chat: '/api/chat'
};
```

### Flask API設計

#### エンドポイント
| Method | Path | 説明 | Request | Response |
|--------|------|------|---------|----------|
| POST | /api/load | フォルダ読み込み | `{ "path": "/path" }` | `{ "files": [...], "count": 5 }` |
| POST | /api/chat | 質問送信 | `{ "message": "..." }` | `{ "response": "...", "sources": [...] }` |
| GET | / | HTMLページ | - | index.html |

## 7. アクセシビリティ

### 基本要件
- セマンティックHTML使用
- alt属性必須（画像参照表示時）
- フォーカス可視化（:focus-visible使用）
- 十分なコントラスト比（WCAG AA: 4.5:1以上）

### コントラスト比チェックリスト
| 組み合わせ | 比率 | 判定 |
|------------|------|------|
| gray-900 / gray-50 | 15.8:1 | AAA |
| white / primary-500 | 4.6:1 | AA |
| gray-500 / gray-50 | 4.6:1 | AA |

### フォーカスリング設計
```css
.btn:focus-visible {
    outline: none;
    box-shadow:
        0 0 0 var(--ring-offset) #fff,
        0 0 0 calc(var(--ring-offset) + var(--ring-size)) var(--ring-color);
}
```

### アニメーション配慮
```css
@media (prefers-reduced-motion: reduce) {
    * { transition-duration: 1ms !important; }
}
```

### キーボード操作
- Tab/Shift+Tabで全要素にアクセス可能
- Enterでメッセージ送信
- フォーカス: 入力フォームへの自動フォーカス

### WAI-ARIA
- `aria-live="polite"` - チャットエリアの更新通知
- `aria-label` - 入力フォームのラベル

## 変更履歴

| 日付 | 変更者 | 変更内容 |
|------|--------|----------|
| 2026-01-30 | - | 初版作成 |

---
**承認状況**: 未承認
**承認日時**: -
