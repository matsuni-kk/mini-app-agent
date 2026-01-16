# Mini App Agent

HTML/CSS/JavaScriptベースのミニアプリを開発し、GitHub Pagesにデプロイするエージェント。

## 機能

- **要件定義**: ユーザー要望をヒアリングし、機能要件・非機能要件を定義
- **UI/UX設計**: 画面構成、コンポーネント、ビジュアル設計を作成
- **コード実装**: HTML/CSS/JavaScriptを実装
- **テスト**: 機能テスト、UIテスト、アクセシビリティチェック
- **デプロイ**: GitHub Pagesへの自動デプロイ

## ワークフロー

```
要件定義 → 設計 → 実装 → テスト → デプロイ
                      ↑      ↓
                      └── 修正 ←┘（テスト失敗時）
```

## 使い方

### 1. 新規アプリ作成
```
「ToDoアプリを作成して」
「電卓アプリを開発したい」
「タイマーアプリを作りたい」
```

### 2. 特定工程から開始
```
「要件定義から始めて」
「設計を作成して」
「実装をお願い」
「テストを実行して」
「デプロイして」
```

## Skills

| Skill | トリガーワード |
|-------|---------------|
| mini-app-requirements | 要件定義、ミニアプリ作成、アプリ開発 |
| mini-app-design | デザイン、画面設計、UI設計 |
| mini-app-build | 実装、コーディング、ビルド |
| mini-app-test | テスト、動作確認、検証 |
| mini-app-deploy | デプロイ、公開、リリース |

## 技術スタック

- **HTML5**: セマンティックHTML、アクセシビリティ対応
- **CSS3**: BEM命名、CSS変数、モバイルファースト
- **JavaScript**: ES6+、Vanilla JS
- **ホスティング**: GitHub Pages

## ディレクトリ構成

```
mini-app_agent/
├── .claude/
│   ├── skills/           # Skillsファイル
│   │   ├── mini-app-requirements/
│   │   ├── mini-app-design/
│   │   ├── mini-app-build/
│   │   ├── mini-app-test/
│   │   └── mini-app-deploy/
│   └── agents/           # Subagents
│       └── qa-mini-app-qc.md
├── Flow/                 # 作業中ドラフト
├── Stock/                # 確定版
├── app/                  # 生成されるアプリ
├── CLAUDE.md             # エージェント設定
├── AGENTS.md             # Subagent参照
└── README.md             # このファイル
```

## 成果物

| 工程 | 成果物 |
|------|--------|
| 要件定義 | requirements.md |
| 設計 | design.md |
| 実装 | index.html, style.css, app.js |
| テスト | test_report.md |
| デプロイ | deploy_log.md, 公開URL |

## ライセンス

MIT
