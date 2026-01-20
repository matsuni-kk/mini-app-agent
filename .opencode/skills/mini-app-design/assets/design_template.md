# {{app_name}} 設計書

## 概要
- 作成日: {{today}}
- 作成者:
- ステータス: Draft
- 参照: requirements.md

## 1. 画面一覧

| 画面ID | 画面名 | 説明 | 対応機能ID |
|--------|--------|------|------------|
| S01 | {{画面名}} | {{説明}} | M1, S1 |

## 2. 画面設計

### S01: {{画面名}}

#### ワイヤーフレーム（ASCII）
```
+----------------------------------+
|  Header                    [≡]  |
+----------------------------------+
|                                  |
|  +----------------------------+  |
|  |  Main Content             |  |
|  |                           |  |
|  +----------------------------+  |
|                                  |
|  +----------------------------+  |
|  |  [Button]                 |  |
|  +----------------------------+  |
|                                  |
+----------------------------------+
|  Footer                          |
+----------------------------------+
```

#### 要素説明
| 要素 | 説明 | インタラクション |
|------|------|------------------|
| Header | {{説明}} | - |
| Main Content | {{説明}} | {{操作}} |
| Button | {{説明}} | クリックで{{動作}} |

#### レスポンシブ対応
| ブレークポイント | 幅 | レイアウト | ガター |
|------------------|-----|------------|--------|
| Mobile | ~639px | {{レイアウト}} | 16px |
| sm | 640px~ | {{レイアウト}} | 24px |
| md | 768px~ | {{レイアウト}} | 24px |
| lg | 1024px~ | {{レイアウト}} | 32px |
| xl | 1280px~ | {{レイアウト}} | 48px |

## 3. 画面遷移図

```
[S01: メイン画面]
      ↓ ボタンクリック
[S02: 詳細画面]
      ↓ 戻るボタン
[S01: メイン画面]
```

## 4. コンポーネント一覧

| コンポーネント | 説明 | 使用画面 | 再利用 |
|----------------|------|----------|--------|
| Header | ヘッダー部品 | 全画面 | Yes |
| Button | 汎用ボタン | 全画面 | Yes |

### コンポーネント詳細

#### Button
- 構成要素: ラベル、アイコン（オプション）
- バリエーション:
  - Primary: 背景色あり、主要アクション用
  - Secondary: 枠線のみ、副次アクション用
  - Disabled: グレーアウト、操作不可時
- 状態管理:
  | 状態 | 視覚変化 | トランジション |
  |------|----------|----------------|
  | default | ベースカラー | - |
  | hover | 少し濃く、影を強く | 200ms |
  | active | さらに濃く、translateY(1px) | 150ms |
  | focus | フォーカスリング表示 | 200ms |
  | disabled | 彩度を落とす、cursor: not-allowed | - |

## 5. ビジュアル設計

> 参照: design_system_principles.md

### カラースキーム

#### プライマリカラー（HSLベース）
| レベル | HSL | HEX | 用途 |
|--------|-----|-----|------|
| primary-500 | hsl({{H}}, 75%, 50%) | #{{hex}} | ベースカラー |
| primary-600 | hsl({{H}}, 80%, 42%) | #{{hex}} | hover状態 |
| primary-700 | hsl({{H}}, 85%, 35%) | #{{hex}} | active状態 |

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
| Success | Green | #22C55E | AA準拠 |
| Warning | Amber | #F59E0B | AA準拠 |
| Error | Red | #EF4444 | AA準拠 |
| Info | Blue | #3B82F6 | AA準拠 |

### タイポグラフィ

#### フォントスタック
```css
--font-sans: system-ui, -apple-system, sans-serif;
```

#### サイズスケール（モジュラースケール 1.25）
| 要素 | サイズ | line-height | 太さ | 用途 |
|------|--------|-------------|------|------|
| h1 | 2.25rem (36px) | 1.25 | 700 | ページタイトル |
| h2 | 1.875rem (30px) | 1.25 | 700 | セクション見出し |
| h3 | 1.5rem (24px) | 1.3 | 600 | サブセクション |
| h4 | 1.25rem (20px) | 1.4 | 600 | 小見出し |
| body | 1rem (16px) | 1.5 | 400 | 本文 |
| small | 0.875rem (14px) | 1.5 | 400 | 補足テキスト |
| caption | 0.75rem (12px) | 1.4 | 400 | キャプション |

#### レスポンシブタイポグラフィ（clamp使用）
```css
--font-size-fluid-lg: clamp(1.25rem, 1rem + 1vw, 1.5rem);
--font-size-fluid-xl: clamp(1.5rem, 1.2rem + 1.5vw, 2rem);
```

## 6. 技術設計

### ファイル構成
```
{{app_name}}/
├── index.html
├── css/
│   └── style.css
├── js/
│   └── app.js
├── assets/
│   └── images/
└── README.md
```

### HTML構造
```html
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{app_name}}</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header class="header">...</header>
    <main class="main">...</main>
    <footer class="footer">...</footer>
    <script src="js/app.js"></script>
</body>
</html>
```

### CSS設計方針
- 命名規則: BEM（Block__Element--Modifier）
- レスポンシブ: モバイルファースト
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
    --c-primary: #{{hex}};
    --c-primary-hover: #{{hex}};
    --c-primary-active: #{{hex}};
    --c-bg: #F9FAFB;
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
    --font-size-sm: 0.875rem;
    --font-size-base: 1rem;
    --font-size-lg: 1.125rem;
    --font-size-xl: 1.25rem;
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
    --ring-color: rgba(59, 130, 246, 0.35);
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
- 状態管理: {{方式}}

## 7. アクセシビリティ

### 基本要件
- セマンティックHTML使用
- alt属性必須
- フォーカス可視化（:focus-visible使用）
- 十分なコントラスト比（WCAG AA: 4.5:1以上）

### コントラスト比チェックリスト
| 組み合わせ | 比率 | 判定 |
|------------|------|------|
| テキスト / 背景 | {{比率}} | AA/AAA |
| ボタンテキスト / ボタン背景 | {{比率}} | AA/AAA |
| リンク / 背景 | {{比率}} | AA/AAA |

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
- Enter/Spaceでボタン/リンク操作
- Escapeでモーダル/ドロップダウン閉じる

## 変更履歴

| 日付 | 変更者 | 変更内容 |
|------|--------|----------|
| {{today}} | - | 初版作成 |

---
**承認状況**: 未承認
**承認日時**: -
