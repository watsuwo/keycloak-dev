---
spec_id: TEMPLATE-SPECS-GUIDE
title: 仕様書 (spec) の書き方ガイド
status: ready
---

# 仕様書 (spec) の書き方ガイド

このリポでは **仕様書駆動開発 (SDD)** を採用しており、各 spec ファイルに YAML **frontmatter** を付けて機械可読化しています。本ファイルはそのスキーマと命名規則のリファレンス。

> 関連: [docs/architecture.md ADR-012](../architecture.md) — SDD導入の判断記録 / [obra/superpowers](https://github.com/obra/superpowers) — workflow skills

---

## なぜ frontmatter を付けるか

- **トレーサビリティ** : `spec_id` で spec と実装/テストを双方向リンク
- **完了判定の客観化** : `acceptance_tests` への参照で「specが満たされた」が機械検査可能
- **AI/superpowers 連携** : superpowers の `writing-plans` / `executing-plans` が frontmatter を読み込んで仕事の単位を決める
- **ドリフト検出 (Phase B以降)** : `implementations` に列挙したパスが存在しない or 逆に実装が specに紐づいていないケースを CI で検知

---

## frontmatter スキーマ (最小)

```yaml
---
spec_id: <一意ID>                    # 必須: PATTERN- / TEMPLATE- / CASE- / TASK- で始まる
title: <人間向け短いタイトル>           # 必須
status: <ライフサイクル状態>            # 必須: draft | approved | implemented | deprecated | template | ready

# 任意: 該当する場合のみ
implementations:                     # この spec から導出される成果物のパス (リポルートからの相対)
  - keycloak/providers/sample-01-email-domain-allowlist/

acceptance_tests:                    # この spec を verify するテスト
  - keycloak/providers/sample-01-email-domain-allowlist/src/test/
  - keycloak/providers/integration-tests/src/test/java/.../<Name>IT.java
  - e2e-tests/tests/<name>-browser.spec.ts
---
```

将来追加しうるフィールド (今は付けなくてOK):

- `category` — 分類タグ (例: `authenticator`, `admin-console`)
- `acceptance_criteria` — `[ { id: AC-1, desc: ... }, ... ]` で受け入れ基準を構造化
- `owner` — オーナー (個人名・チーム名)
- `last_reviewed` — 最終レビュー日付
- `related_specs` — 関連 spec_id のリスト
- `produces` — テンプレートが生成する spec の ID パターン

---

## spec_id 命名規則

形式: **`<TYPE>-<DOMAIN>-<NAME>`** (UPPER + kebab-case)

| TYPE接頭辞 | 用途 | 配置場所 | 例 |
| --- | --- | --- | --- |
| `PATTERN-` | 再利用パターン (動く実例 + レシピ) | 雛形リポ `docs/specs/patterns/` | `PATTERN-AUTH-DOMAIN-ALLOWLIST` |
| `TEMPLATE-` | フォーマット雛形 (フィルインの型) | 雛形リポ `docs/*-template.md` | `TEMPLATE-CASE-SPEC` / `TEMPLATE-TASK-ADMIN-CONSOLE` |
| `CASE-` | 実案件全体の要件 | 顧客リポ `docs/case-spec.md` | `CASE-ACME-CORP` |
| `TASK-` | 実案件の作業単位 | 顧客リポ `docs/specs/task-specs/*.md` | `TASK-ACME-CORP-ADMIN-CONSOLE` |

### DOMAIN 推奨値

- `AUTH` — 認証フロー・SPI Authenticator
- `REALM` — Realm設定・属性
- `THEME` — テーマ・画面
- `INTEGRATION` — 外部システム連携 (IdP, LDAP, Webhook)
- `ADMIN` — 管理コンソール設定
- `OBSERVABILITY` — ログ・メトリクス
- (拡張可)

### NAME

- kebab-case
- 用途を表す短い名前 (例: `domain-allowlist`, `mfa-totp`, `client-confidential`)

---

## status の遷移

```
   draft ──→ approved ──→ implemented ──→ (運用中)
                                              │
                                              ↓
                                          deprecated
```

| 値 | 意味 |
| --- | --- |
| `draft` | 起票直後、まだ熟練者レビュー前 |
| `approved` | レビュー済、実装可能な粒度 |
| `implemented` | 実装完了、`implementations` と `acceptance_tests` が埋まっている |
| `deprecated` | 後継 spec に置き換えられた (削除ではなく履歴として残す) |
| `template` | テンプレート (フィルイン雛形)。ライフサイクル外 |
| `ready` | ドキュメントとして公開可能 (specs-guide.md 等のメタドキュメント用) |

---

## 書き方の例

### A. パターン (実装済み)

```yaml
---
spec_id: PATTERN-AUTH-DOMAIN-ALLOWLIST
title: Email Domain Allowlist Authenticator
status: implemented
implementations:
  - keycloak/providers/sample-01-email-domain-allowlist/
acceptance_tests:
  - keycloak/providers/sample-01-email-domain-allowlist/src/test/
  - keycloak/providers/integration-tests/src/test/java/com/example/keycloak/it/EmailDomainAllowlistIT.java
  - e2e-tests/tests/email-domain-allowlist-browser.spec.ts
---

# Email Domain Allowlist Authenticator (本文 …)
```

### B. テンプレート

```yaml
---
spec_id: TEMPLATE-CASE-SPEC
title: 案件全体の要件入力テンプレ
status: template
---

# 案件仕様書 — テンプレート (本文 …)
```

### C. 顧客リポでの実 case spec

```yaml
---
spec_id: CASE-ACME-CORP
title: ACME株式会社 認証基盤要件
status: approved
implementations:
  - terraform/environments/acme-corp/
  - keycloak/providers/02-acme-attribute-validator/
acceptance_tests:
  - keycloak/providers/integration-tests/src/test/java/.../AcmeAttributeValidatorIT.java
  - e2e-tests/tests/acme-login-browser.spec.ts
---
```

### D. 顧客リポでの task spec

```yaml
---
spec_id: TASK-ACME-CORP-ADMIN-CONSOLE
title: ACME 管理コンソール設定
status: implemented
implementations:
  - terraform/environments/acme-corp/main.tf
acceptance_tests:
  - scripts/test-terraform.sh
---
```

---

## superpowers との連携 (Phase D 実施済み)

### 汎用 workflow skill (superpowers が提供)

[obra/superpowers](https://github.com/obra/superpowers) のworkflow skill が、frontmatter の各フィールドをこう使う想定:

| superpowers skill | 使うフィールド |
| --- | --- |
| `brainstorming` | `status: draft` の spec を読み込み、`approved` までrefine |
| `writing-plans` | `acceptance_tests` を完了条件として 2-5分タスクに分解 |
| `executing-plans` | `implementations` パスに subagent dispatchで成果物を作る |
| `test-driven-development` | `acceptance_tests` を RED-GREEN-REFACTOR |
| `requesting-code-review` | spec本文 (受け入れ基準を含む) と diff を比較 |
| `finishing-a-development-branch` | `status: implemented` に昇格、 PR description に spec_id を引用 |

superpowers を入れない環境でも frontmatter は単なる YAML として読めるため、互換性あり。

### プロジェクト固有 skill ( `.claude/skills/` )

汎用 workflow skill だけでは Keycloak 開発の細かい流儀を Claude が知らないので、本リポでは [.claude/skills/](../../.claude/skills/) に **プロジェクト固有 skill** を追加してある:

| skill | いつ使われる |
| --- | --- |
| [writing-spec](../../.claude/skills/writing-spec/SKILL.md) | 新規 spec 起票・既存 spec 更新 (frontmatter スキーマ + spec_id 命名規則 + status 遷移を遵守) |
| [writing-keycloak-spi-pattern](../../.claude/skills/writing-keycloak-spi-pattern/SKILL.md) | 新 SPI パターン実装 (sample-NN-name / case-client-name dir、Maven module、META-INF/services、フロー検出ヘルパー等の規約) |
| [writing-keycloak-realm-terraform](../../.claude/skills/writing-keycloak-realm-terraform/SKILL.md) | task-spec → terraform HCL 生成 (modules/ の再利用、secrets取扱、apply検証) |
| [writing-keycloak-acceptance-tests](../../.claude/skills/writing-keycloak-acceptance-tests/SKILL.md) | 3層テスト (単体/Java IT/ブラウザE2E) 作成、既知の罠を最初から回避 |

superpowers の `writing-plans` / `executing-plans` がプランを組むときにこれらのプロジェクト固有 skill を呼び出す前提。
詳細は [.claude/skills/README.md](../../.claude/skills/README.md) 参照。

---

## 新しい spec を書く手順

1. **どの TYPE か決める** : 再利用パターンなら PATTERN、案件固有なら CASE/TASK
2. **spec_id を決める** : `<TYPE>-<DOMAIN>-<NAME>` 形式で重複しないように
3. **frontmatter を書く** : 最小スキーマ (`spec_id`, `title`, `status: draft`)
4. **本文を書く** : 既存パターン (`docs/specs/patterns/01-...md`) を参考に
5. **熟練者レビュー** : `status: approved` に昇格
6. **実装** : superpowers の writing-plans → executing-plans でドラフト → 手動仕上げ
7. **完了** : `implementations` と `acceptance_tests` を埋めて `status: implemented` に
8. **PRレビュー** : [docs/review-checklists/](../review-checklists/) のチェックリストに沿って

---

## 既存 spec の更新フロー

仕様変更があったとき:

1. spec frontmatter の `status` をそのままで本文を編集
2. 実装も同じ PR で変更
3. `acceptance_tests` を更新 (新たに検証すべき criteria を test化)
4. PR description で「spec section X を変更、impl Y を更新、test Z 追加」と書く
5. レビュアーは spec の diff と impl/test の diff を対応付けて確認

---

## 検証 (Phase B: 実装済み)

`make spec-validate` で frontmatter の整合性を機械検証できる:

```bash
make spec-validate          # 全 spec の検証 (詳細出力)
make spec-validate-quiet    # 問題があるspec のみ表示 (CI用)
```

検証内容 (forward check: spec → impl):

- spec_id の **存在 + 形式** (PATTERN-/TEMPLATE-/CASE-/TASK- で始まる)
- spec_id の **一意性** (リポ内で重複なし)
- status が有効値か (draft/approved/implemented/deprecated/template/ready)
- `implementations:` で列挙されたパスが **実在するか**
- `acceptance_tests:` で列挙されたパスが **実在するか**
- status が `implemented` なのに `implementations` が空でないか (warning)

実装は [scripts/validate-specs.py](../../scripts/validate-specs.py) (Python 3.8+ stdlib のみ、依存なし)。CI ワークフローに `make spec-validate-quiet` を組み込めば、PRで spec とコードの乖離を自動検出できる。

### Phase B 残り (今後)

逆参照 (impl → spec) の検証はまだ未実装:

- 実装ファイル側に `<!-- impl-of: SPEC-ID -->` (markdownの場合) や `// spec: SPEC-ID` (Java/TSの場合) のコメントで spec_id を明示
- validator が impl ファイルを走査して、参照先 spec_id が存在するかを検証
- 「spec_id が参照されているのに spec ファイルが消えた」「spec の `implementations` に列挙されてないのに spec_id を主張するファイルがある」を検出

これらは Phase B.1 として後付け予定。

---

## 関連ドキュメント

- [docs/architecture.md](../architecture.md) — ADR-012 SDD導入記録
- [docs/specs/case-spec-template.md](case-spec-template.md) — 案件全体テンプレ
- [docs/specs/task-specs/](task-specs/) — 作業タイプ別テンプレ
- [docs/specs/patterns/](patterns/) — パターンカタログ
- [obra/superpowers](https://github.com/obra/superpowers) — Claude Code 用 workflow skills
