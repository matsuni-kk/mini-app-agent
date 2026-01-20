# Build Template

## index.html テンプレート

```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{{app_description}}">
    <title>{{app_name}}</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header class="header">
        <h1 class="header__title">{{app_name}}</h1>
    </header>

    <main class="main">
        <!-- メインコンテンツ -->
    </main>

    <footer class="footer">
        <p class="footer__text">&copy; {{year}} {{app_name}}</p>
    </footer>

    <script src="js/app.js"></script>
</body>
</html>
```

## style.css テンプレート

```css
/* ==========================================================================
   CSS Variables
   ========================================================================== */
:root {
    /* Colors */
    --color-primary: #3498db;
    --color-secondary: #2ecc71;
    --color-background: #ffffff;
    --color-text: #333333;
    --color-border: #e0e0e0;
    --color-error: #e53935;
    --color-success: #43a047;

    /* Typography */
    --font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-size-base: 16px;
    --font-size-sm: 14px;
    --font-size-lg: 20px;
    --font-size-xl: 24px;

    /* Spacing */
    --spacing-xs: 4px;
    --spacing-sm: 8px;
    --spacing-md: 16px;
    --spacing-lg: 24px;
    --spacing-xl: 32px;

    /* Border Radius */
    --radius-sm: 4px;
    --radius-md: 8px;
    --radius-lg: 16px;

    /* Shadows */
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.1);
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
}

/* ==========================================================================
   Reset & Base
   ========================================================================== */
*,
*::before,
*::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html {
    font-size: var(--font-size-base);
}

body {
    font-family: var(--font-family);
    color: var(--color-text);
    background-color: var(--color-background);
    line-height: 1.6;
}

/* ==========================================================================
   Layout
   ========================================================================== */
.header {
    padding: var(--spacing-md);
    background-color: var(--color-primary);
    color: white;
}

.header__title {
    font-size: var(--font-size-xl);
    font-weight: 700;
}

.main {
    min-height: calc(100vh - 120px);
    padding: var(--spacing-lg);
}

.footer {
    padding: var(--spacing-md);
    text-align: center;
    background-color: var(--color-border);
}

/* ==========================================================================
   Components
   ========================================================================== */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-sm) var(--spacing-md);
    font-size: var(--font-size-base);
    font-weight: 500;
    border: none;
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: opacity 0.2s;
}

.btn:hover {
    opacity: 0.9;
}

.btn:focus {
    outline: 2px solid var(--color-primary);
    outline-offset: 2px;
}

.btn--primary {
    background-color: var(--color-primary);
    color: white;
}

.btn--secondary {
    background-color: transparent;
    border: 1px solid var(--color-primary);
    color: var(--color-primary);
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* ==========================================================================
   Responsive
   ========================================================================== */
@media (max-width: 767px) {
    .main {
        padding: var(--spacing-md);
    }
}
```

## app.js テンプレート

```javascript
/**
 * {{app_name}} - Main Application
 */

'use strict';

// ==========================================================================
// DOM Elements
// ==========================================================================
const elements = {
    // DOM要素をここに定義
};

// ==========================================================================
// State
// ==========================================================================
const state = {
    // アプリケーション状態をここに定義
};

// ==========================================================================
// Functions
// ==========================================================================

/**
 * アプリケーションを初期化する
 */
function init() {
    // 初期化処理
    bindEvents();
}

/**
 * イベントリスナーを設定する
 */
function bindEvents() {
    // イベントリスナーをここに設定
}

/**
 * UIを更新する
 */
function render() {
    // UI更新処理
}

// ==========================================================================
// Event Handlers
// ==========================================================================

// ==========================================================================
// Initialize
// ==========================================================================
document.addEventListener('DOMContentLoaded', init);
```

## ファイル構成

```
{{app_name}}/
├── index.html          # メインHTML
├── css/
│   └── style.css       # スタイルシート
├── js/
│   └── app.js          # メインスクリプト
├── assets/
│   └── images/         # 画像ファイル（必要に応じて）
└── README.md           # プロジェクト説明
```
