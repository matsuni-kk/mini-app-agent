# コーディング規約

## HTML

### 基本ルール
- DOCTYPE宣言: `<!DOCTYPE html>`
- 言語属性: `<html lang="ja">`
- 文字エンコーディング: `<meta charset="UTF-8">`
- viewport設定必須

### セマンティックHTML
- 適切なタグを使用: `<header>`, `<main>`, `<footer>`, `<nav>`, `<article>`, `<section>`
- 見出しは階層順: h1 → h2 → h3
- リストは `<ul>`, `<ol>` を使用

### アクセシビリティ
- 画像には必ずalt属性
- フォーム要素にはlabel必須
- フォーカス可能な要素には適切なtabindex
- ARIA属性は必要最小限

## CSS

### 命名規則（BEM）
```css
/* Block */
.card { }

/* Element */
.card__title { }
.card__content { }

/* Modifier */
.card--featured { }
.card__title--large { }
```

### 設計方針
- モバイルファースト
- CSS変数（Custom Properties）使用
- ネストは最大3階層まで

### プロパティ順序
1. レイアウト（display, position, flex等）
2. ボックスモデル（width, margin, padding等）
3. タイポグラフィ（font, color等）
4. ビジュアル（background, border等）
5. その他（transition, animation等）

### 禁止事項
- `!important` の乱用
- IDセレクタでのスタイリング
- インラインスタイル

## JavaScript

### 基本ルール
- `'use strict';` を先頭に記述
- ES6+構文を使用
- セミコロン必須

### 変数宣言
```javascript
// const優先、再代入が必要な場合のみlet
const MAX_COUNT = 10;
let currentIndex = 0;

// varは使用禁止
```

### 関数
```javascript
// アロー関数（コールバック等）
const add = (a, b) => a + b;

// 通常関数（メソッド、ホイスティング必要時）
function handleClick(event) {
    // ...
}
```

### 命名規則
| 種類 | 規則 | 例 |
|------|------|-----|
| 変数・関数 | camelCase | `userName`, `getUserData` |
| 定数 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT` |
| クラス | PascalCase | `UserProfile` |
| ファイル | kebab-case | `user-profile.js` |

### DOM操作
```javascript
// querySelector推奨
const element = document.querySelector('.selector');
const elements = document.querySelectorAll('.selector');

// addEventListener使用
element.addEventListener('click', handleClick);
```

### エラーハンドリング
```javascript
// try-catchで例外処理
try {
    const data = JSON.parse(jsonString);
} catch (error) {
    console.error('Parse error:', error);
    // フォールバック処理
}
```

### 禁止事項
- グローバル変数
- eval()
- with文
- document.write()

## ファイル構成

```
project/
├── index.html          # エントリーポイント
├── css/
│   └── style.css       # メインスタイル
├── js/
│   └── app.js          # メインスクリプト
└── assets/
    └── images/         # 画像
```

## GitHub Pages対応

### 必須要件
- index.htmlをルートに配置
- 相対パスのみ使用（`./`, `../`）
- サーバーサイド処理なし
- 外部リソースはCDN経由

### パス指定
```html
<!-- OK: 相対パス -->
<link rel="stylesheet" href="css/style.css">
<script src="js/app.js"></script>

<!-- NG: 絶対パス -->
<link rel="stylesheet" href="/css/style.css">
```
