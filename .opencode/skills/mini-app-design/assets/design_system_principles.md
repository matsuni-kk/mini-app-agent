# UIデザインシステム原則

ミニアプリ開発のための包括的なUIデザイン原則とテンプレート集。
思想的なガイドラインから具体的なCSS実装例まで網羅。

> **参考資料**: ADS（AI Design System）、sophia-design-support、最強のデザイン支援エージェント設計

---

## 0. 設計思想

### 0.1 トレンドと鉄則の分離

**鉄則（構造）**: ユーザーの認知と行動に直結するルール
- 視覚階層、操作の一貫性、誤操作耐性、可読性、アクセシビリティ
- **壊すとUXが崩れる不変のルール**

**トレンド（表層）**: 視覚表現の選択肢
- ネオブルータリズム、ガラスモーフィズム、3D要素、ダークモード
- **安全に適用するにはガードレールが必要**

### 0.2 認知科学原則のUI適用

| 法則 | 原則 | UIへの適用 |
|------|------|-----------|
| ヒックの法則 | 選択肢が増えると意思決定が遅くなる | 主要導線は3〜7個に圧縮 |
| フィッツの法則 | ターゲットが大きく近いほど押しやすい | 主CTAは44×44px以上、親指が届く位置 |
| ミラーの法則 | 短期記憶には限界がある | フォームはステップ分割、一覧は意味のある塊で |
| ヤコブの法則 | ユーザーは「いつものやり方」を期待 | ナビゲーションは慣れた型を優先 |
| 美的ユーザビリティ効果 | 美しいものは使いやすく感じる | トレンドは適用レイヤーを限定 |

### 0.3 デザイン品質の数値化（ADS統合）

**品質 ≠ 印象** という整理を置き、主観的なフィードバックを客観的なスコアで制御する。

```
総合品質評価 = 情報密度 × コンテキスト × 美的評価 × 発見可能性
```

#### 強調システム（Emphasis System）

視覚要素の目立ち具合を定量化。CTAの優先度設計に使用。

```
総合強調度 = コントラスト × サイズ × 余白 × 面積 × 動き × 太さ
```

| 要素 | 測定方法 | 目安 |
|------|----------|------|
| コントラスト | 背景との色差（WCAG比） | 4.5:1以上で高 |
| サイズ | 周囲要素との相対比 | 1.5倍以上で強調 |
| 余白 | 周辺の空間量 | 広いほど視線集中 |
| 面積 | 占有面積の割合 | 大きいほど支配的 |
| 動き | アニメーション有無 | あれば最優先 |
| 太さ | フォントウェイト | 600以上で強調 |

#### 美的評価（Aesthetic Evaluation）

```
美的評価 = ブランド適合度 × 色彩調和 × 統一性
```

| 指標 | 評価観点 |
|------|----------|
| ブランド適合度 | ブランドカラー・トーンとの一致 |
| 色彩調和 | 補色・類似色・トライアドの整合性 |
| 統一性 | パターン・余白・形状の一貫性 |

#### 情報密度（Information Density）

```
情報密度 = 有効情報量 / 視覚面積
```

- **高すぎる**: 認知負荷が高く離脱を招く
- **低すぎる**: スクロール量が増え効率低下
- **適正値**: 1画面で主要タスクが完結する範囲

#### コンテキストシステム

ユーザーの状況に応じたUI適応を評価。

| コンテキスト | 考慮事項 |
|-------------|----------|
| デバイス | タッチ vs マウス、画面サイズ |
| 時間帯 | ダークモード推奨時間 |
| ユーザー習熟度 | 初回 vs リピーター |
| タスク緊急度 | 即座のフィードバック必要性 |

### 0.4 ワークフロー（Generate→Govern→Review→Learn）

デザインの品質を継続的に改善するサイクル。

```
┌─────────────────────────────────────────────────────┐
│  Generate   →   Govern   →   Review   →   Learn    │
│  (生成)         (統制)       (評価)       (学習)    │
└─────────────────────────────────────────────────────┘
```

| フェーズ | 内容 |
|----------|------|
| Generate | デザイン案を複数パターン生成 |
| Govern | デザイントークン・原則に沿って制約 |
| Review | ADS指標でスコアリング、人間レビュー |
| Learn | フィードバックを次回生成にフィードバック |

---

## 1. グリッドシステムと余白の法則

### 1.1 8pxグリッドシステム

**なぜ8px？**
- 視覚的なリズム（整って見える）
- 意思決定を減らす（迷わない）
- コンポーネントの再利用性が上がる
- 多くのデバイスの解像度で割り切れる

**運用ルール**
- メイン: 8px単位（8, 16, 24, 32, 48, 64...）
- サブ: 4px単位（4, 12, 20...）密度調整用
- 例外: 1-2px（ボーダー、影のみ）

### 1.2 スペーシングスケール

| Token | px | rem | 用途 |
|-------|-----|------|------|
| space-0 | 0 | 0 | 余白なし |
| space-1 | 4 | 0.25 | 密なUI、アイコン周り |
| space-2 | 8 | 0.5 | 基本単位、最小の標準余白 |
| space-3 | 12 | 0.75 | ラベルと入力の間 |
| space-4 | 16 | 1 | 標準padding、標準gap |
| space-6 | 24 | 1.5 | カード内ブロック間 |
| space-8 | 32 | 2 | セクション内のまとまり |
| space-10 | 40 | 2.5 | 強い区切り |
| space-12 | 48 | 3 | サブセクション間 |
| space-16 | 64 | 4 | ページ内の大区切り |
| space-20 | 80 | 5 | 余白多めUI |
| space-24 | 96 | 6 | ヒーロー、最上位 |

### 1.3 余白の3階層

1. **内側（Inset）**: コンポーネントのpadding
2. **要素間（Inter-element）**: ボタンとラベル、カード内の行間
3. **セクション間（Layout/Section）**: ページの塊同士、モーダル外枠

### 1.4 CSS変数定義

```css
:root {
  /* 基本単位 */
  --space-unit: 0.5rem; /* 8px */

  /* スケールトークン */
  --space-0: 0;
  --space-1: calc(var(--space-unit) / 2);     /* 4px */
  --space-2: var(--space-unit);                /* 8px */
  --space-3: calc(var(--space-unit) * 1.5);    /* 12px */
  --space-4: calc(var(--space-unit) * 2);      /* 16px */
  --space-6: calc(var(--space-unit) * 3);      /* 24px */
  --space-8: calc(var(--space-unit) * 4);      /* 32px */
  --space-12: calc(var(--space-unit) * 6);     /* 48px */
  --space-16: calc(var(--space-unit) * 8);     /* 64px */

  /* セマンティックトークン（横方向） */
  --space-inline-xs: var(--space-1);
  --space-inline-sm: var(--space-2);
  --space-inline-md: var(--space-4);
  --space-inline-lg: var(--space-6);

  /* セマンティックトークン（縦方向） */
  --space-stack-xs: var(--space-2);
  --space-stack-sm: var(--space-3);
  --space-stack-md: var(--space-4);
  --space-stack-lg: var(--space-6);
  --space-stack-xl: var(--space-8);

  /* セクション余白 */
  --space-section-sm: var(--space-8);
  --space-section-md: var(--space-12);
  --space-section-lg: var(--space-16);
}
```

---

## 2. タイポグラフィ階層とスケール

### 2.1 モジュラースケール

| 比率 | 特徴 | 用途 |
|------|------|------|
| 1.125 (Major Second) | 控えめな階層 | 情報密度の高いUI |
| 1.2 (Minor Third) | バランス良い | 一般的なWebアプリ |
| 1.25 (Major Third) | 適度なコントラスト | マーケティング/LP |
| 1.333 (Perfect Fourth) | 強い階層 | 大見出し重視 |

### 2.2 フォントサイズ階層

```css
:root {
  /* Base: 16px */
  --font-size-xs: 0.75rem;    /* 12px - caption */
  --font-size-sm: 0.875rem;   /* 14px - small text */
  --font-size-base: 1rem;     /* 16px - body */
  --font-size-lg: 1.125rem;   /* 18px - large body */
  --font-size-xl: 1.25rem;    /* 20px - h6 */
  --font-size-2xl: 1.5rem;    /* 24px - h5 */
  --font-size-3xl: 1.875rem;  /* 30px - h4 */
  --font-size-4xl: 2.25rem;   /* 36px - h3 */
  --font-size-5xl: 3rem;      /* 48px - h2 */
  --font-size-6xl: 3.75rem;   /* 60px - h1 */
}
```

### 2.3 Line-heightの最適値

| 用途 | line-height | 理由 |
|------|-------------|------|
| 見出し | 1.1 - 1.25 | 大きい文字は詰めて良い |
| 本文 | 1.5 - 1.6 | 読みやすさ重視 |
| UI要素 | 1.2 - 1.4 | ボタン、ラベル等 |
| 長文 | 1.6 - 1.8 | 記事、ドキュメント |

```css
:root {
  --leading-none: 1;
  --leading-tight: 1.25;
  --leading-snug: 1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
  --leading-loose: 2;
}
```

### 2.4 フォントウェイト

```css
:root {
  --font-weight-normal: 400;    /* 本文 */
  --font-weight-medium: 500;    /* 強調 */
  --font-weight-semibold: 600;  /* 小見出し */
  --font-weight-bold: 700;      /* 見出し */
}
```

### 2.5 レスポンシブタイポグラフィ（clamp）

```css
:root {
  /* clamp(最小値, 推奨値, 最大値) */
  --font-size-fluid-sm: clamp(0.875rem, 0.8rem + 0.25vw, 1rem);
  --font-size-fluid-base: clamp(1rem, 0.9rem + 0.5vw, 1.125rem);
  --font-size-fluid-lg: clamp(1.25rem, 1rem + 1vw, 1.5rem);
  --font-size-fluid-xl: clamp(1.5rem, 1.2rem + 1.5vw, 2rem);
  --font-size-fluid-2xl: clamp(2rem, 1.5rem + 2vw, 3rem);
  --font-size-fluid-3xl: clamp(2.5rem, 2rem + 2.5vw, 4rem);
}

h1 { font-size: var(--font-size-fluid-3xl); }
h2 { font-size: var(--font-size-fluid-2xl); }
h3 { font-size: var(--font-size-fluid-xl); }
```

### 2.6 フォントスタック

```css
:root {
  /* System UI */
  --font-sans: system-ui, -apple-system, BlinkMacSystemFont,
    'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans JP', 'Hiragino Sans', sans-serif;

  /* Monospace */
  --font-mono: ui-monospace, SFMono-Regular,
    'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace;
}
```

---

## 3. カラーシステム

### 3.1 カラースケール構造

**基本構成**
- Primary: ブランドカラー（50-900）
- Secondary: 補助色
- Accent: アクセント
- Gray: 中立色（50-900）
- Semantic: success, warning, error, info

### 3.2 HSLベースのスケール生成

**原則**
- H（色相）は固定
- S（彩度）は明るい色ほど低く
- L（明度）で階層を作る

```css
:root {
  /* Primary - Blue (H: 220) */
  --primary-50: hsl(220, 100%, 97%);
  --primary-100: hsl(220, 95%, 93%);
  --primary-200: hsl(220, 90%, 85%);
  --primary-300: hsl(220, 85%, 75%);
  --primary-400: hsl(220, 80%, 60%);
  --primary-500: hsl(220, 75%, 50%);  /* Base */
  --primary-600: hsl(220, 80%, 42%);
  --primary-700: hsl(220, 85%, 35%);
  --primary-800: hsl(220, 90%, 25%);
  --primary-900: hsl(220, 95%, 15%);

  /* Gray (Neutral) */
  --gray-50: hsl(220, 10%, 98%);
  --gray-100: hsl(220, 10%, 95%);
  --gray-200: hsl(220, 10%, 90%);
  --gray-300: hsl(220, 10%, 80%);
  --gray-400: hsl(220, 10%, 65%);
  --gray-500: hsl(220, 10%, 50%);
  --gray-600: hsl(220, 10%, 40%);
  --gray-700: hsl(220, 10%, 30%);
  --gray-800: hsl(220, 10%, 20%);
  --gray-900: hsl(220, 10%, 10%);
}
```

### 3.3 セマンティックカラー

```css
:root {
  /* Success - Green */
  --success-light: hsl(142, 70%, 95%);
  --success-base: hsl(142, 70%, 45%);
  --success-dark: hsl(142, 70%, 30%);

  /* Warning - Amber */
  --warning-light: hsl(45, 95%, 95%);
  --warning-base: hsl(45, 95%, 50%);
  --warning-dark: hsl(45, 95%, 35%);

  /* Error - Red */
  --error-light: hsl(0, 85%, 95%);
  --error-base: hsl(0, 85%, 55%);
  --error-dark: hsl(0, 85%, 40%);

  /* Info - Cyan */
  --info-light: hsl(195, 85%, 95%);
  --info-base: hsl(195, 85%, 50%);
  --info-dark: hsl(195, 85%, 35%);
}
```

### 3.4 ダークモード対応

```css
:root {
  /* Light mode */
  --c-bg: var(--gray-50);
  --c-bg-secondary: var(--gray-100);
  --c-fg: var(--gray-900);
  --c-fg-secondary: var(--gray-600);
  --c-border: var(--gray-200);
}

[data-theme="dark"] {
  --c-bg: var(--gray-900);
  --c-bg-secondary: var(--gray-800);
  --c-fg: var(--gray-50);
  --c-fg-secondary: var(--gray-400);
  --c-border: var(--gray-700);
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --c-bg: var(--gray-900);
    --c-bg-secondary: var(--gray-800);
    --c-fg: var(--gray-50);
    --c-fg-secondary: var(--gray-400);
    --c-border: var(--gray-700);
  }
}
```

### 3.5 アクセシビリティ（WCAG 2.1）

| レベル | コントラスト比 | 用途 |
|--------|---------------|------|
| AA（通常テキスト） | 4.5:1以上 | 本文、ラベル |
| AA（大テキスト） | 3:1以上 | 18px以上、14px bold以上 |
| AAA（通常テキスト） | 7:1以上 | 最高レベル |
| AAA（大テキスト） | 4.5:1以上 | 見出し |

**確認ツール**: WebAIM Contrast Checker, Stark

---

## 4. コンポーネント状態管理

### 4.1 基本状態

| 状態 | 説明 | 主な視覚変化 |
|------|------|-------------|
| default | 基本状態 | ブランド色/中立色 |
| hover | ポインタが乗った | 少し濃く、影を強く |
| active | 押下中 | さらに濃く、沈み込み |
| focus | キーボードフォーカス | フォーカスリング |
| disabled | 操作不可 | 彩度を落とす |

### 4.2 状態優先順位

```
disabled > focus > active > hover > default
```

- `disabled`は最優先で上書き
- `focus`は付加要素として重ねる
- `active`はhoverより強い変化

### 4.3 トランジション時間

```css
:root {
  --ease-standard: cubic-bezier(0.2, 0, 0, 1);
  --dur-quick: 150ms;   /* 微小反応 */
  --dur-base: 200ms;    /* デフォルト */
  --dur-slow: 300ms;    /* 大きな変化 */
}

/* アクセシビリティ対応 */
@media (prefers-reduced-motion: reduce) {
  :root {
    --dur-quick: 1ms;
    --dur-base: 1ms;
    --dur-slow: 1ms;
  }
}
```

### 4.4 フォーカスリングスタイル

```css
:root {
  --ring-color: rgba(37, 99, 235, 0.35);
  --ring-size: 3px;
  --ring-offset: 2px;
}

/* :focus-visible でキーボード操作時のみ表示 */
.btn:focus-visible {
  outline: none;
  box-shadow:
    0 0 0 var(--ring-offset) rgba(255, 255, 255, 0.9),
    0 0 0 calc(var(--ring-offset) + var(--ring-size)) var(--ring-color);
}
```

---

## 5. レスポンシブブレークポイント

### 5.1 標準ブレークポイント

| Token | 幅 | デバイス |
|-------|-----|----------|
| sm | 640px | 大きめスマホ |
| md | 768px | タブレット縦 |
| lg | 1024px | タブレット横/ノートPC |
| xl | 1280px | デスクトップ |
| 2xl | 1536px | 大画面 |

### 5.2 モバイルファースト実装

```css
/* Base: mobile */
.container { padding: var(--space-4); }

@media (min-width: 640px) {
  .container { padding: var(--space-6); }
}

@media (min-width: 768px) {
  .container { padding: var(--space-8); }
}

@media (min-width: 1024px) {
  .container { padding: var(--space-12); }
}
```

---

## 6. 完全なCSS変数テンプレート

```css
:root {
  /* ==================
     Spacing
     ================== */
  --space-unit: 0.5rem;
  --space-0: 0;
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-12: 3rem;
  --space-16: 4rem;
  --space-24: 6rem;

  /* ==================
     Typography
     ================== */
  --font-sans: system-ui, -apple-system, sans-serif;
  --font-mono: ui-monospace, monospace;

  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  --font-size-2xl: 1.5rem;
  --font-size-3xl: 1.875rem;
  --font-size-4xl: 2.25rem;

  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;

  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* ==================
     Colors
     ================== */
  --primary-500: hsl(220, 75%, 50%);
  --primary-600: hsl(220, 80%, 42%);
  --primary-700: hsl(220, 85%, 35%);

  --gray-50: hsl(220, 10%, 98%);
  --gray-100: hsl(220, 10%, 95%);
  --gray-200: hsl(220, 10%, 90%);
  --gray-300: hsl(220, 10%, 80%);
  --gray-400: hsl(220, 10%, 65%);
  --gray-500: hsl(220, 10%, 50%);
  --gray-600: hsl(220, 10%, 40%);
  --gray-700: hsl(220, 10%, 30%);
  --gray-800: hsl(220, 10%, 20%);
  --gray-900: hsl(220, 10%, 10%);

  --success: hsl(142, 70%, 45%);
  --warning: hsl(45, 95%, 50%);
  --error: hsl(0, 85%, 55%);
  --info: hsl(195, 85%, 50%);

  /* Semantic */
  --c-bg: var(--gray-50);
  --c-fg: var(--gray-900);
  --c-muted: var(--gray-500);
  --c-border: var(--gray-200);
  --c-primary: var(--primary-500);

  /* ==================
     Effects
     ================== */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 9999px;

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);

  /* ==================
     Motion
     ================== */
  --ease-standard: cubic-bezier(0.2, 0, 0, 1);
  --dur-quick: 150ms;
  --dur-base: 200ms;
  --dur-slow: 300ms;

  /* ==================
     Focus Ring
     ================== */
  --ring-color: rgba(37, 99, 235, 0.35);
  --ring-size: 3px;
  --ring-offset: 2px;

  /* ==================
     Breakpoints (doc)
     ================== */
  --bp-sm: 640px;
  --bp-md: 768px;
  --bp-lg: 1024px;
  --bp-xl: 1280px;
}
```

---

## 7. 実装チェックリスト

### グリッド・余白
- [ ] 余白は8px/4pxの倍数に揃っているか
- [ ] セマンティックトークンを使っているか
- [ ] レスポンシブで余白が適切に変化するか

### タイポグラフィ
- [ ] フォントサイズの階層が明確か
- [ ] line-heightが用途に適切か
- [ ] レスポンシブでサイズが変化するか

### カラー
- [ ] コントラスト比がWCAG AA以上か
- [ ] セマンティックカラーが統一されているか
- [ ] ダークモードに対応しているか

### 状態管理
- [ ] 全状態（hover/active/focus/disabled）が定義されているか
- [ ] :focus-visibleでフォーカスリングを表示しているか
- [ ] disabledで操作不可が明確か

### アクセシビリティ
- [ ] prefers-reduced-motionに対応しているか
- [ ] キーボード操作で全要素にアクセスできるか
- [ ] 色だけに依存した情報伝達になっていないか

---

*Generated from ChatGPT Parallel Research - 2026-01-20*
