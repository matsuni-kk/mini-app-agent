# Skill配布レポート

## 概要
- 実行日時: {{datetime}}
- 配布元: browser-controller-agent
- 配布Skill: {{skill_names}}
- 配布モード: {{mode}}

## 配布結果

### {{skill_name}}

| # | リポジトリ | 結果 | 備考 |
|---|-----------|------|------|
| 1 | {{repo_name}} | {{status}} | {{note}} |

### ステータス凡例
- `Updated`: 既存フォルダを上書き
- `Created`: 新規作成
- `Skipped`: new_onlyモードでスキップ
- `Error`: エラー発生

## サマリー

| 項目 | 件数 |
|------|------|
| 配布先リポジトリ | {{total}} |
| 更新（Updated） | {{updated}} |
| 新規（Created） | {{created}} |
| スキップ（Skipped） | {{skipped}} |
| エラー（Error） | {{errors}} |

## エラー詳細

{{#if errors}}
| リポジトリ | エラー内容 |
|-----------|-----------|
| {{repo}} | {{error_message}} |
{{/if}}

## 配布ファイル一覧

配布されたファイル:
```
{{skill_name}}/
├── SKILL.md
├── assets/
│   └── *.md
├── questions/
│   └── *.md
├── evaluation/
│   └── evaluation_criteria.md
└── scripts/
    └── *.py
```

## 次アクション

- [ ] 配布先リポジトリでSkillが正常に読み込まれることを確認
- [ ] エラーが発生したリポジトリの原因調査
- [ ] 新規配布リポジトリのCLAUDE.md更新（必要な場合）

## 変更履歴

| 日付 | 変更者 | 変更内容 |
|------|--------|----------|
| {{today}} | - | 初版作成 |
