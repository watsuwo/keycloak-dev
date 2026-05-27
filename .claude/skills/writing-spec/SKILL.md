---
name: writing-spec
description: Use when creating a new spec (PATTERN/TEMPLATE/CASE/TASK) for this Keycloak dev repo, or updating an existing spec's frontmatter. Ensures spec_id naming + frontmatter schema compliance.
---

# Writing Spec

このプロジェクトの spec ファイル (`docs/specs/` 配下) を新規作成・更新するときの手順とルール。
このリポは **仕様書駆動開発 (SDD)** を採用しており、各 spec は YAML frontmatter で機械可読化されている。

## When to use

- 新規パターン (PATTERN-) を `docs/specs/patterns/` に追加するとき
- 新規テンプレート (TEMPLATE-) を作成するとき
- 顧客リポで CASE-/TASK- 形式の spec を起票するとき
- 既存 spec の implementations / acceptance_tests を更新するとき
- spec_id の命名で迷ったとき

## When NOT to use

- 通常の how-to ドキュメント (testing.md, onboarding.md 等) を書くとき → frontmatter 不要
- README.md など spec ではないファイル

## frontmatter スキーマ (最小、必須)

```yaml
---
spec_id: <TYPE>-<DOMAIN>-<NAME>          # 必須、4分類接頭辞: PATTERN-/TEMPLATE-/CASE-/TASK-
title: <人間向けタイトル>                   # 必須
status: <状態>                            # 必須: draft|approved|implemented|deprecated|template|ready
implementations:                         # 任意
  - <成果物パス (リポルートから)>
acceptance_tests:                        # 任意
  - <テストパス (リポルートから)>
---
```

詳しいスキーマは [docs/specs/specs-guide.md](../../../docs/specs/specs-guide.md) を参照。

## spec_id 命名規則

| 接頭辞 | 配置 | 例 |
| --- | --- | --- |
| `PATTERN-` | `docs/specs/patterns/` (雛形リポ) | `PATTERN-AUTH-DOMAIN-ALLOWLIST` |
| `TEMPLATE-` | `docs/specs/*-template.md` (雛形リポ) | `TEMPLATE-CASE-SPEC` |
| `CASE-` | 顧客リポ `docs/case-spec.md` | `CASE-ACME-CORP` |
| `TASK-` | 顧客リポ `docs/task-specs/*.md` | `TASK-ACME-CORP-ADMIN-CONSOLE` |

DOMAIN 推奨値: `AUTH` / `REALM` / `THEME` / `INTEGRATION` / `ADMIN` / `OBSERVABILITY`

## status のライフサイクル

```
draft → approved → implemented → (運用) → deprecated
```

- 雛形/メタは `template` / `ready`
- 詳細は [specs-guide.md](../../../docs/specs/specs-guide.md#status-の遷移)

## 手順

### 1. 種類を決める

PATTERN/TEMPLATE/CASE/TASK のどれか。既存パターンとの重複がないか `docs/specs/patterns/` を確認。

### 2. spec_id を確定

`<TYPE>-<DOMAIN>-<NAME>` 形式で、リポ内で一意になるように。

### 3. ファイル配置

```
docs/specs/patterns/0N-<name>.md          (PATTERN)
docs/specs/task-specs/0N-<name>.md         (TEMPLATE-TASK-*)
docs/specs/case-spec-<name>.md             (TEMPLATE-CASE-*)
```

### 4. frontmatter を書く (最小)

```yaml
---
spec_id: PATTERN-<DOMAIN>-<NAME>
title: <短い説明>
status: draft
---
```

### 5. 本文を書く

既存パターン ([docs/specs/patterns/01-email-domain-allowlist.md](../../../docs/specs/patterns/01-email-domain-allowlist.md)) を参考に:
- 適用判断 (when to use / when NOT to use)
- 仕様
- 設定方法
- 派生・カスタマイズ方針
- 既知の限界

### 6. レビュー受けて approved に昇格

熟練者レビューで `status: approved` に。設計判断 (パターン選定・命名規則) を確定。

### 7. 実装後、implementations と acceptance_tests を埋めて implemented に

```yaml
status: implemented
implementations:
  - keycloak/providers/0N-<name>/
acceptance_tests:
  - keycloak/providers/0N-<name>/src/test/
  - keycloak/providers/integration-tests/src/test/java/.../<Name>IT.java
  - e2e-tests/tests/<name>-browser.spec.ts
```

### 8. 検証

```bash
make spec-validate
```

すべての `implementations` / `acceptance_tests` パスが実在することが機械検証される。

## superpowers との連携

- **brainstorming** : `status: draft` の spec を質問で refine → `approved` に昇格
- **writing-plans** : `acceptance_tests` を完了条件として 2-5分タスクに分解
- **test-driven-development** : `acceptance_tests` を RED-GREEN-REFACTOR

## Anti-patterns

- ❌ frontmatter なしで spec を書く (validator が拾えない)
- ❌ `spec_id` の重複 (validator が ERROR)
- ❌ `status: implemented` なのに `implementations` 空 (validator が WARN)
- ❌ 自由文だけで「テストはある」と言う (acceptance_tests に具体パス書く)
- ❌ 他リポと spec_id 衝突しそうな短すぎる ID (DOMAIN 必須)

## Checklist

- [ ] spec_id が `PATTERN-/TEMPLATE-/CASE-/TASK-` のいずれかで始まる
- [ ] spec_id がリポ内で一意 (validator で確認)
- [ ] status が有効値
- [ ] `status: implemented` なら implementations 列挙
- [ ] `acceptance_tests` の各パスが実在
- [ ] `make spec-validate` が green

## Related skills

- `writing-keycloak-spi-pattern` — SPI を伴うパターン実装時にこの spec と組み合わせ
- `writing-keycloak-acceptance-tests` — acceptance_tests の中身を書くとき
