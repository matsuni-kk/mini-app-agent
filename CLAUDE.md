# Mini App Agent

HTML/CSS/JavaScriptベースのミニアプリを開発し、GitHub Pagesにデプロイするエージェント。
要件定義からデプロイまで一貫したワークフローを提供。

## 1. コア原則

- 起点Skill確定: ユーザー指定を優先（未指定/曖昧なら質問して確定）
- WF自動継続: Skill完了後は各Skillの `triggers/next_action_triggers.md` に従い、条件を満たす次Skillを自動実行する
- テンプレートファースト: 各Skillのassets/を先に読む
- 品質ループ: Preflight→生成→Subagent QC→反映（最大3回）
- 推測禁止: 元資料にない項目は「未記載」と明記
- GitHub Pages対応: 静的ファイルのみ、相対パス使用

## 2. ワークフロー

```
Phase 1: 準備
  mini-app-requirements → mini-app-design

Phase 2: 実装
  mini-app-build

Phase 3: 検証
  mini-app-test
      ↓ Pass → Phase 4
      ↓ Fail → mini-app-build（修正）

Phase 4: レビュー
  mini-app-review
      ↓ 改善なし/スキップ → Phase 5
      ↓ 改善あり → mini-app-build → mini-app-test → mini-app-review

Phase 5: デプロイ
  mini-app-deploy
      ↓ 完了 → 公開URL報告
```

### Skills一覧

| Skill | 説明 | 主成果物 |
|-------|------|----------|
| mini-app-requirements | 要件定義 | requirements.md |
| mini-app-design | UI/UX設計 | design.md |
| mini-app-build | コード実装 | index.html, style.css, app.js |
| mini-app-test | テスト実行 | test_report.md |
| mini-app-review | 作成者レビュー | review_report.md |
| mini-app-deploy | GitHub Pagesデプロイ | deploy_log.md, 公開URL |
| mini-app-status | 進捗管理 | status.md |

## 3. 品質ゴール

- 欠損ゼロ: 要件の可視情報を漏れなく反映
- 行間ゼロ: 初見でも前提・背景から理解できる自己完結
- ハルシネーションゼロ: 元資料にない項目は「未記載/不明」
- GitHub Pages互換: 静的サイト制約を遵守

## 4. パス辞書

```yaml
root: "."

dirs:
  flow: "Flow"
  stock: "Stock"
  skills: ".claude/skills"
  agents: ".claude/agents"
  app: "app"

patterns:
  requirements: "Flow/requirements.md"
  design: "Flow/design.md"
  test_report: "Flow/test_report.md"
  review_report: "Flow/review_report.md"
  deploy_log: "Flow/deploy_log.md"
  status: "Flow/status.md"
  # アプリは app/{app_name}/ 配下に配置
  app_dir: "app/{app_name}/"
  app_index: "app/{app_name}/index.html"
  app_css: "app/{app_name}/css/style.css"
  app_js: "app/{app_name}/js/app.js"
```

## 5. トリガーキーワード

| キーワード | 実行Skill |
|-----------|-----------|
| 要件定義、ミニアプリ作成、アプリ開発 | mini-app-requirements |
| デザイン、画面設計、UI設計 | mini-app-design |
| 実装、コーディング、ビルド | mini-app-build |
| テスト、動作確認、検証 | mini-app-test |
| レビュー、改善、ブラッシュアップ | mini-app-review |
| デプロイ、公開、リリース | mini-app-deploy |
| 進捗、ステータス、状況確認 | mini-app-status |

## 6. 技術制約

### GitHub Pages要件
- index.htmlをルートに配置
- 相対パスのみ使用（`./`, `../`）
- 静的ファイルのみ（サーバーサイド処理なし）
- 外部リソースはCDN経由

### コーディング規約
- HTML: セマンティックタグ、アクセシビリティ考慮
- CSS: BEM命名、モバイルファースト、CSS変数
- JS: ES6+、エラーハンドリング必須

## 7. QC

全SkillでQC Subagent（`qa-mini-app-qc`）による品質チェックを実施。
評価基準は各Skillの `evaluation/evaluation_criteria.md` に定義。

## 8. 進捗管理

### 自動ステータス更新
**各Skill完了時、次Skillへ進む前にstatus-updaterサブエージェントを呼び出す。**

```yaml
subagent:
  name: status-updater
  path: .claude/agents/status-updater.md
  trigger: 各Skill完了時
  action: Flow/status.mdを更新
```

### 更新内容
- 完了フェーズのステータスを更新
- QCスコアを記録
- 次のアクションを更新
- 全体進捗率を再計算
- 履歴にマイルストーンを追加

### status.mdの構成
- フェーズ進捗表（各フェーズの完了状況）
- 成果物一覧（ドキュメント・コードの存在確認）
- 品質サマリー（QCスコア推移）
- デプロイ情報（公開URL、リポジトリ）
- 次のアクション

---
Do what has been asked; nothing more, nothing less.
