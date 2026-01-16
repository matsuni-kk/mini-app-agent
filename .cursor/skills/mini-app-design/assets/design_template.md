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
- Desktop (1024px+): {{レイアウト}}
- Tablet (768px-1023px): {{レイアウト}}
- Mobile (-767px): {{レイアウト}}

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

## 5. ビジュアル設計

### カラースキーム
| 用途 | カラー | HEX |
|------|--------|-----|
| Primary | {{色名}} | #{{hex}} |
| Secondary | {{色名}} | #{{hex}} |
| Background | {{色名}} | #{{hex}} |
| Text | {{色名}} | #{{hex}} |
| Border | {{色名}} | #{{hex}} |
| Error | Red | #E53935 |
| Success | Green | #43A047 |

### タイポグラフィ
| 要素 | フォント | サイズ | 太さ |
|------|----------|--------|------|
| 見出し1 | system-ui | 24px | 700 |
| 見出し2 | system-ui | 20px | 600 |
| 本文 | system-ui | 16px | 400 |
| 補足 | system-ui | 14px | 400 |

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
- CSS変数使用

```css
:root {
    --color-primary: #{{hex}};
    --color-secondary: #{{hex}};
    --font-base: 16px;
    --spacing-unit: 8px;
}
```

### JavaScript設計方針
- ES6+ 構文使用
- DOM操作: querySelector / addEventListener
- 状態管理: {{方式}}

## 7. アクセシビリティ

- セマンティックHTML使用
- alt属性必須
- フォーカス可視化
- 十分なコントラスト比（WCAG AA）

## 変更履歴

| 日付 | 変更者 | 変更内容 |
|------|--------|----------|
| {{today}} | - | 初版作成 |

---
**承認状況**: 未承認
**承認日時**: -
