# Skill Skeleton Template

新規Skill作成時のテンプレート。`{skill-name}` を実際のSkill名に置換して使用する。

---

## フォルダ構造

```
{{AGENT_CONFIG_DIR}}/skills/{skill-name}/
├── SKILL.md
├── assets/
│   └── {name}_template.md
├── questions/
│   └── {name}_questions.md
├── evaluation/           # 評価基準（Most/More 2層構造）
│   ├── evaluation_guide.md   # 評価レベル定義・採点基準・使い方
│   ├── most_criteria.md      # 必須修正項目（致命的欠損）
│   └── more_criteria.md      # 推奨修正項目（品質向上）+ Good（保持項目）
├── triggers/             # 必須: WF連携の起動条件
│   └── next_action_triggers.md
└── scripts/              # 任意
    └── {script_name}.py
```

`{{AGENT_CONFIG_DIR}}` は実行環境に応じて決定:
- Cursor: `.cursor`
- Claude Code: `.claude`
- Codex: `.codex`

---

## SKILL.md テンプレート

```markdown
---
name: {skill-name}
description: "{Skill説明}。{トリガーキーワード}を依頼されたときに使用する。"
---

# {Skill Name} Workflow

## Instructions
0. **{分岐名}（分岐判定）**:  ← ※分岐が必要な場合のみ追加
   - {Skill名}開始前に、以下の{N}条件をチェックする:
     1. **{条件名1}**: {検証可能な条件記述}
     2. **{条件名2}**: {検証可能な条件記述}
     3. **{条件名3}**: {検証可能な条件記述}
     4. **{条件名4}**: {検証可能な条件記述}
   
   - **判定ロジック**:
     - {ALL/ANY/NONE} 条件を満たす → {アクションA}（Step 1以降へ継続）
     - {ALL/ANY/NONE} 条件を満たさない → `{分岐先skill名}` Skillを直接実行
   
   - **分岐時の引き継ぎ情報**:
     - 満たさなかった条件とその理由
     - 現時点で判明している情報
     - 参照した資料リスト

1. Preflight:
   - ドキュメント精査原則（Preflight必須）：テンプレート確認後、生成前に必ず以下を実施すること。
     - アジェンダ・依頼文に記載された参照資料を全て読み込む。
     - Flow/Stock配下の関連資料（前回議事録・要望リスト・プロジェクトREADME等）を網羅的に検索・確認する。
     - 確認できなかった資料は「未参照一覧」として成果物に明記する。
     - これらを完了するまで生成を開始しない。
   - 参照すべき既存資料があれば読み込み、前提・不足情報・未参照を整理する（推測しない）。
   - `./assets/{name}_template.md` を先に読み、章立て・必須項目・項目順序を確認する（テンプレートファースト）。
2. 生成:
   - `./questions/{name}_questions.md` を使って必要情報を収集し、テンプレ構造を崩さずにドキュメントを作成/更新する。
   - 元資料にない項目は省略せず「未記載」または「不明」と明記する。
3. QC（必須）:
    - `recommended_subagents` のQC Subagentに評価・チェックを委譲する。
    - Subagentは以下を順にReadし、評価を実施する:
      1. `./evaluation/evaluation_guide.md`（評価レベル定義・採点基準・QC報告フォーマット）
      2. `./evaluation/most_criteria.md`（必須修正項目チェック）
      3. `./evaluation/more_criteria.md`（推奨修正項目スコアリング）
    - Most（必須）項目は未修正時Fail、More（推奨）項目はスコアリング（80点以上Pass）
    - 指摘を最小差分で反映する（テンプレの章立ては崩さない）。
    - 再度SubagentでQCする。
    - これを最大3回まで繰り返し、確定する。
    - 指摘に対し「修正した/しない」と理由を成果物に残す。
4. バックログ反映:
   - 次アクション（追加タスク、レビュー依頼等）を抽出しバックログへ反映する。
   - 反映先・編集制約・差分提示は AGENTS.md / CLAUDE.md の全体ルールに従う。

subagent_policy:
  - **{条件}時の分岐**: Step 0で{条件}を満たさない場合は`{分岐先skill名}` Skillを直接実行する ← ※分岐がある場合のみ
  - 品質ループ（QC/チェック/フィードバック）は必ずサブエージェントへ委譲する
  - サブエージェントの指摘を反映し、反映結果（修正有無/理由）を成果物に残す

recommended_subagents:
  - qa-{skill-name}: {QC観点の説明}

## Resources
- questions: ./questions/{name}_questions.md
- assets: ./assets/{name}_template.md
- evaluation: ./evaluation/evaluation_guide.md
- evaluation: ./evaluation/most_criteria.md
- evaluation: ./evaluation/more_criteria.md
- triggers: ./triggers/next_action_triggers.md
- scripts: ./scripts/

## Next Action
- triggers: ./triggers/next_action_triggers.md

起動条件に従い、条件を満たすSkillを自動実行する。
```

---

## Subagent Execution 追加セクション（該当するSkillのみ追記）

このSkillがSubagentとして独立実行される場合、SKILL.md末尾に以下を追加する：

```markdown
## Subagent Execution
このSkillはサブエージェントとして独立実行可能。
- サブエージェント: `agents/{subagent-name}.md`
- 用途: {並列画像取得、バックグラウンドダウンロード等}
- 入力: {`image_url`, `purpose`, `genre`, `title`, `filename`等}
- 出力: {保存先パス、処理結果等}
```

---

## evaluation/ テンプレート

### evaluation_guide.md（共通定義）

```markdown
# {Skill Name} 評価ガイド

## 評価レベル定義

### Most（必須修正 - Must Fix）
**定義**: 致命的欠損や構造的問題。未修正時は成果物を確定できない。
**対象ファイル**: `most_criteria.md`

**基準**:
- データ整合性の欠如（構文エラー、必須項目欠落）
- 論理的破綻（矛盾、循環論法）
- フォーマット不整合（テンプレート準拠違反）
- ハルシネーション（事実誤認・元資料にない推測）

**対応**:
- 未修正項目がある場合は `Fail`
- 修正完了まで成果物を確定しない

### More（推奨修正 - Nice to Have）
**定義**: 品質向上のための改善提案。リソースと優先度で判断可能。
**対象ファイル**: `more_criteria.md`

**基準**:
- 表現の改善（具体性、明瞭性、簡潔さ）
- 追跡可能性の向上（出典・根拠の明示）
- 網羅性の向上（多角的視点・エッジケース）
- 使いやすさ（再利用性、検索性）

**対応**:
- 未修正でも `Pass` 可能（記録に留める）
- 時間許容時に実施

### Good（評価・保持項目）
**定義**: 特に優れていた点。次回も維持すべき要素。
**記録場所**: `more_criteria.md` の末尾

## 採点基準

| 判定 | 条件 |
|------|------|
| **Pass** | 全Most項目がPass かつ Moreスコア80点以上 |
| **Conditional Pass** | 全Most項目がPass かつ Moreスコア60-79点（軽微な修正で確定可） |
| **Fail** | Most項目にFailあり または Moreスコア60点未満（再生成が必要） |

## QC報告フォーマット

```markdown
### QC結果: [Pass/Conditional Pass/Fail]

#### Most（必須修正）
- [x] 項目名: Pass
- [ ] 項目名: Fail → 修正必須: [具体的な問題]

**判定**: [Most全Pass/MostにFailあり]

#### More（推奨修正）
スコア: [XX]/100

| 観点 | 得点 | コメント |
|------|------|----------|
| [観点名] | [XX]/[配点] | [簡潔な評価] |

#### Good（保持項目）
- [ ] [優れていた点1]
- [ ] [優れていた点2]

#### 指摘事項
1. **[Most/More]** [項目名]: [指摘内容]
   - 影響: [致命的/軽微]
   - 修正案: [具体的な改善案]

#### 推奨対応
- [ ] **Most** #[番号]: [対応アクション]（必須）
- [ ] **More** #[番号]: [対応アクション]（推奨）
```

## 使い方

### Step 1: Mostチェック（生成直後）
→ most_criteria.md で致命的欠損をチェック

### Step 2: Moreチェック（Most修正後）
→ more_criteria.md で品質向上提案を確認

### Step 3: 最終判定
→ QC報告フォーマットで結果を記録
```

### most_criteria.md（必須修正項目）

```markdown
# Most Criteria（必須修正）

## 構造チェック（Pass/Fail）

致命的欠損。いずれかがFailの場合、成果物確定不可。

| 項目 | 基準 | 判定 |
|------|------|------|
| {チェック項目1} | {基準} | Pass/Fail |
| {チェック項目2} | {基準} | Pass/Fail |
| {チェック項目3} | {基準} | Pass/Fail |

## 内容チェック（Pass/Fail）

| 項目 | 基準 | 判定 |
|------|------|------|
| {チェック項目4} | {基準} | Pass/Fail |
| {チェック項目5} | {基準} | Pass/Fail |

## 許容不可項目

以下はMust Fix対象。例外なし。

- {致命的欠損1}
- {致命的欠損2}
```

### more_criteria.md（推奨修正項目 + Good）

```markdown
# More Criteria（推奨修正）

## 内容チェック（スコアリング）

品質向上のための改善提案。未修正でも合格可能。

| 観点 | 評価基準 | 配点 |
|------|----------|------|
| {観点1} | {評価基準} | {配点} |
| {観点2} | {評価基準} | {配点} |
| {観点3} | {評価基準} | {配点} |

**合計**: 100点

## 推奨項目一覧

### {カテゴリ名1}
- [ ] {チェック項目}
- [ ] {チェック項目}

### {カテゴリ名2}
- [ ] {チェック項目}
- [ ] {チェック項目}

## 許容例外（More対象）

以下は修正推奨だが、未修正でも合格可能。

- {許容される例外1}
- {許容される例外2}

## Good（保持項目）

評価時に特に優れていた点を記録し、次回も維持する。

```markdown
### Goodポイント
- [ ] {優れていた点1}
- [ ] {優れていた点2}
```
```

---

## questions テンプレート

```markdown
# {Skill Name} Questions

## 必須入力項目

1. **目的**: このドキュメントの目的は？
2. **対象**: 対象となるプロジェクト/範囲は？
3. **期待成果**: 最終的な成果物・アウトプットは？

## 任意入力項目

4. **制約**: 制約条件・前提条件は？
5. **参照資料**: 参照すべき既存資料は？
6. **関係者**: ステークホルダー・レビューアは？
```

---

## assets テンプレート

```markdown
# {Document Name}

## 概要
- 作成日: {{today}}
- 作成者:
- ステータス: Draft

## {セクション1}

{内容}

## {セクション2}

{内容}

## {セクション3}

{内容}

## 変更履歴

| 日付 | 変更者 | 変更内容 |
|------|--------|----------|
| {{today}} | - | 初版作成 |
```

---

## triggers/next_action_triggers.md テンプレート

```markdown
# {Skill Name} Next Action Triggers

## Step 0 分岐判定（最優先）  ← ※分岐がある場合のみ追加

### {分岐先Skill名} へ分岐（Skill直接実行）
- 条件: Step 0の{分岐名}で{ALL/ANY/NONE}条件を満たさない場合
- トリガー: 以下のいずれかに該当する場合
  - {条件1の具体的なトリガー}
  - {条件2の具体的なトリガー}
  - {条件3の具体的なトリガー}
  - {条件4の具体的なトリガー}
- アクション: `{分岐先skill名}` Skillを直接実行し、{分岐先での処理内容}
- 引き継ぎ: {引き継ぎ項目リスト}

### {継続先Skill名} へ遷移
- 条件: Step 0の{分岐名}で{ALL/ANY/NONE}条件を満たし、{現Skill名}が完了した場合
- トリガー: {成果物/状態の条件}
- アクション: {継続先}へ遷移し、{継続先での処理内容}

## 自動実行ルール
**以下の条件を満たす場合は、該当Skillを必ず実行すること（WF自動継続）。**
条件判定はSkill完了時に自動で行い、スキップ条件に該当しない限り次Skillへ進む。

## 起動条件テーブル

| ID | 起動条件 | 実行Skill | 優先度 | 備考 |
|----|---------|-----------|--------|------|
| T1 | {検証可能な条件を記載} | `{skill-name}` | 1 | {補足} |
| T2 | {検証可能な条件を記載} | `{skill-name}` | 2 | {補足} |

## スキップ条件
以下の場合のみ、起動条件を満たしても実行をスキップできる:
- ユーザーが明示的に「{現Skill名}のみ」と指定した場合
- {その他のスキップ条件}

## 条件判定ロジック
1. Skill完了時、起動条件テーブルを上から順に評価する
2. 条件を満たす行があれば、スキップ条件を確認する
3. スキップ条件に該当しなければ、該当Skillを実行する
4. 複数条件が該当する場合は、優先度順に全て実行する
```

### 起動条件の書き方

**検証可能な条件を書くこと（曖昧表現NG）**

| NG例 | OK例 |
|------|------|
| 「必要なら」 | 「成果物に〜セクションが存在する」 |
| 「〜したい場合」 | 「〜が未作成（ファイル不存在）」 |
| 「〜が求められる場合」 | 「〜フィールドが空欄/未記載」 |

**詳細は `./assets/next_action_triggers_spec.md` を参照。**

---

## 分岐処理（Branching Logic）

分岐処理を含むSkillを作成する場合は、以下のドキュメントを参照すること：

- **仕様書**: `./assets/branching_logic_spec.md`
- **記述場所**: 
  - SKILL.md: `## Instructions` の Step 0
  - Subagent: `## Critical First Step`
  - triggers: `## Step 0 分岐判定（最優先）`

### 分岐処理が必要なケース

| ケース | 説明 | 例 |
|--------|------|-----|
| 前提条件チェック | 実行前に前提が揃っているか確認 | goal-discovery: ゴール確定チェック |
| 状態ベース分岐 | 成果物の状態で次Skillを選択 | 仮説確定→goal-discovery / 未確定→hypothesis-validation |
| 複数パス分岐 | 条件により複数の委譲先がある | 商談→engagement-strategy / MTG→pmbok-agenda |

### チェックリスト

分岐処理を追加する際は `./assets/branching_logic_spec.md` の「10. チェックリスト」を確認すること。
