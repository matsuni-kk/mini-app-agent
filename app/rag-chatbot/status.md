# rag-chatbot ステータス

## 基本情報
- アプリ名: rag-chatbot
- 作成日: 2026-01-30
- 現在フェーズ: Build完了

## フェーズ進捗

| フェーズ | ステータス | QCスコア | 完了日 |
|----------|------------|----------|--------|
| Requirements | **完了** | 92/100 | 2026-01-30 |
| Design | **完了** | 88/100 | 2026-01-30 |
| Build | **完了** | 87/100 | 2026-01-30 |
| Test | 未着手 | - | - |
| Review | 未着手 | - | - |
| Deploy | 対象外 | - | - |

## 成果物

### ドキュメント
- [x] requirements.md
- [x] design.md
- [ ] test_report.md
- [ ] review_report.md

### コード
- [x] index.html
- [x] css/style.css
- [x] js/app.js
- [x] app.py (Flask)
- [x] requirements.txt
- [x] .env.example

## UI概要
- **左側パネル**: PDFビューア（タブ切替）
- **右側パネル**: AIチャットボット
- **機能**:
  - キーワード検索でファイル選択（最大10件）
  - 選択したMDをRAGコンテキストとして使用
  - 参照ソースをクリックで該当PDFに切替

## 特記事項
- ローカルサーバー専用アプリ（Vercel/GitHub Pagesデプロイ対象外）
- Gemini APIを使用したRAGチャットボット
- Python Flask + Vanilla JS構成
- データフォルダ: Stock/Explaza_AX_事例集（markdown/, pdfs/, images/）

## 起動方法
```bash
cd app/rag-chatbot
pip install -r requirements.txt
cp .env.example .env
# .envにGEMINI_API_KEYを設定
python app.py
# http://localhost:5000 でアクセス
```

## 次のアクション
**→ mini-app-test**: テスト実行を実施

## 履歴
| 日時 | イベント |
|------|----------|
| 2026-01-30 | 実装完了（QC Pass 87点） |
| 2026-01-30 | 設計完了（QC Pass 88点） |
| 2026-01-30 | 要件定義完了（QC Pass 92点） |
