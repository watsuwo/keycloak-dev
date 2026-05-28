# .claude/skills/ — プロジェクト固有スキル

[obra/superpowers](https://github.com/obra/superpowers) の workflow と組み合わせて使う、 **このプロジェクト (Keycloakカスタマイズ開発) 固有のスキル** を置く場所。

## スキル一覧

| name | description |
| --- | --- |
| [writing-spec](writing-spec/SKILL.md) | 新規 spec ファイル (PATTERN-/TEMPLATE-/CASE-/TASK-) の起票・更新。frontmatter 規約と spec_id 命名の保証 |
| [writing-keycloak-spi-pattern](writing-keycloak-spi-pattern/SKILL.md) | 新 SPI 実装 (Authenticator/EventListener等)。 0N-<name> ディレクトリ・Maven module・META-INF/services・3層テスト・spec frontmatter 更新まで一通り |
| [writing-keycloak-realm-terraform](writing-keycloak-realm-terraform/SKILL.md) | task-spec → Terraform HCL の起こし。Realm/Client/Role/IdP/SMTP の HCL 規約 + `keycloak/keycloak` provider 利用 |
| [writing-keycloak-realm-json](writing-keycloak-realm-json/SKILL.md) | case spec (CLIENTS-INDEX + CLIENT-*) → `keycloak/realms/<案件>.json` 生成・更新 |
| [writing-keycloak-auth-flow](writing-keycloak-auth-flow/SKILL.md) | auth-flow spec の YAML ブロック → Realm JSON の `authenticationFlows` + Terraform 生成・更新 |
| [writing-keycloak-acceptance-tests](writing-keycloak-acceptance-tests/SKILL.md) | spec の acceptance_criteria を3層 (単体/Java IT/E2E) で verify する手順。既知の罠 (User Profile必須属性・OAuth redirect等) 回避 |

## superpowers との関係

| superpowers の汎用 skill | 本プロジェクト固有 skill |
| --- | --- |
| brainstorming / writing-plans / executing-plans (汎用 workflow) | writing-spec が「何を作るか」の起点を作る |
| test-driven-development (TDD 一般) | writing-keycloak-acceptance-tests が Keycloak固有のテスト構造を提供 |
| writing-skills (skill を書く skill) | 本ディレクトリの各 SKILL.md がこの慣行に沿う |

superpowers の汎用 skill は `/plugin install superpowers@claude-plugins-official` で入る。本ディレクトリの固有 skill はリポにcommitされていて、 clone 直後から利用可能。

## このディレクトリの位置づけ

- **superpowers 不要** : これらの skill は Markdown ドキュメントとしてだけでも有用 (Claude/人どちらも参照可)
- **superpowers ありで真価** : 各 skill 内の "Integration with superpowers" セクションが workflow への接続点を明示

## 新しい skill を追加する手順

1. `.claude/skills/<skill-name>/SKILL.md` を作る
2. frontmatter:
   ```yaml
   ---
   name: <skill-name>
   description: Use when ... (明確なトリガー条件)
   ---
   ```
3. 本文構成 (推奨):
   - `When to Use` / `When NOT to Use`
   - `Prerequisites` (前提)
   - `Workflow` (Step 1〜N)
   - `Acceptance Criteria for This Skill` (skill 完了の判定)
   - `Common Pitfalls`
   - `Integration with superpowers`
4. 既存 skill (writing-spec 等) を雛形に
5. このREADME 表に追記

## 関連

- [docs/specs/specs-guide.md](../../docs/specs/specs-guide.md) — spec 規約 + superpowers 連携の全体像
- [docs/architecture.md ADR-012](../../docs/architecture.md) — SDD + superpowers 採用 ADR
- [obra/superpowers](https://github.com/obra/superpowers) — workflow skills 本体
