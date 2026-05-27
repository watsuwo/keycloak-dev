---
name: writing-keycloak-spi-pattern
description: Use when adding a new Keycloak SPI pattern (Authenticator, EventListener, ProtocolMapper, UserStorage, etc.) to this repo. Ensures Maven multi-module conventions, SPI registration, 3-layer tests, and pattern catalog entry.
---

# Writing Keycloak SPI Pattern

新しい Keycloak SPI パターン (Authenticator / EventListener / ProtocolMapper / UserStorage / RequiredAction 等) をこのリポに追加する手順。

このプロジェクトでは **パターン = 動く実例 + spec + 3層テスト + ドキュメント** がワンセット。

## When to use

- 既存パターンを派生では足りず、新しい SPI 種別/挙動を追加したいとき
- 顧客案件で生まれた汎用ロジックを雛形リポに逆輸入するとき

## When NOT to use

- 既存パターンを「設定値だけ変えて使う」ケース (既存パターンを `realm config` で利用する)
- Theme カスタマイズ (それは `keycloak/themes/` 配下)
- 管理コンソール設定 (それは `terraform/` 配下、別 skill: `writing-keycloak-realm-terraform`)

## 前提知識

- [docs/glossary.md](../../../docs/glossary.md) で SPI種別 と Factory I/F を理解
- [keycloak/providers/CLAUDE.md](../../../keycloak/providers/CLAUDE.md) で Maven multi-module 流儀
- [docs/specs/patterns/01-email-domain-allowlist.md](../../../docs/specs/patterns/01-email-domain-allowlist.md) で既存パターン1

## 手順 (TDD ベース)

### 1. spec を書く (skill: writing-spec を利用)

新規 PATTERN spec を `docs/specs/patterns/NN-<name>.md` に起票。
最初は `status: draft` で、acceptance_criteria だけ仮置き (該当パターン解説書の構造を真似る)。

熟練者レビュー受けて `status: approved` に。

### 2. パターン番号を確定

`docs/specs/patterns/` の最大番号 +1 を採用。例: 既存が 01 → 新規は `02-<name>`。

### 3. SPI モジュールを派生

最も近い `sample-` パターンを丸ごとコピー:

```bash
# 汎用パターンの場合
cp -r keycloak/providers/sample-01-email-domain-allowlist keycloak/providers/sample-NN-<name>

# 案件固有実装の場合
cp -r keycloak/providers/sample-01-email-domain-allowlist keycloak/providers/case-<client>-<name>
```

リネーム:
- `pom.xml` の `<artifactId>` / `<name>`
- Java パッケージ `com.example.keycloak.<spi-type>.<name>`
- クラス名 `<Name>` / `<Name>Factory`
- `Factory.ID` 定数 (kebab-case)
- `src/main/resources/META-INF/services/<Factoryインタフェース完全名>` の中身を新Factory FQCNに

### 4. 親POM に追加

`keycloak/providers/pom.xml` の `<modules>` に新モジュール名を追加:

```xml
<modules>
  <module>sample-01-email-domain-allowlist</module>
  <module>sample-NN-<name></module>  <!-- 汎用パターンの場合 -->
  <!-- <module>case-<client>-<name></module> -->  <!-- 案件固有の場合 -->
</modules>
```

### 5. 単体テストを先に書く (RED)

`src/test/java/.../<Name>Test.java` でロジック分岐の期待挙動を Mockito で記述。
最初は実装が空なので失敗 (RED)。

### 6. ロジック実装 (GREEN)

`<Name>.java` の `authenticate()` / `onEvent()` / 該当メソッドを実装。
**Direct Grant 対応**: 失敗時は `context.failure(error, response)` の `response` を **フロー種別に応じて出し分け**。
`isDirectGrantFlow()` ヘルパーをコピー (パターン1の実装参考)。

```bash
make test-providers  # 単体テスト green になることを確認
```

### 7. Java IT 追加

`keycloak/providers/integration-tests/src/test/java/.../<Name>IT.java` を書く。

テスト realm JSON も `src/test/resources/test-realm-<name>.json` で用意。
**罠回避**: user に `firstName` / `lastName` / `emailVerified: true` / `requiredActions: []` を必ず設定。

```bash
make test-integration  # 実Keycloakでgreenになることを確認
```

### 8. (ブラウザUIあれば) E2E 追加

`e2e-tests/tests/<name>-browser.spec.ts` と `e2e-tests/fixtures/test-realm-<name>.json`。

OAuth redirect 検証は `page.waitForRequest(req => req.url().startsWith(REDIRECT_URI))` パターン。

```bash
make test-e2e
```

### 9. spec を implemented に昇格

`docs/specs/patterns/NN-<name>.md` の frontmatter を:

```yaml
status: implemented
implementations:
  - keycloak/providers/sample-NN-<name>/   # 汎用パターンの場合
  # - keycloak/providers/case-<client>-<name>/  # 案件固有の場合
acceptance_tests:
  - keycloak/providers/sample-NN-<name>/src/test/
  - keycloak/providers/integration-tests/src/test/java/.../<Name>IT.java
  - e2e-tests/tests/<name>-browser.spec.ts   # E2E があれば
```

### 10. CLAUDE.md と ドキュメント整備

- `keycloak/providers/sample-NN-<name>/CLAUDE.md` (または `case-<client>-<name>/CLAUDE.md`) でパターン解説
- `keycloak/providers/CLAUDE.md` のパターン一覧表に新エントリ追加
- (任意) README.md / specs/README.md のディレクトリ構成更新

### 11. 検証 + コミット

```bash
make spec-validate           # spec frontmatter 検証
make test-providers          # 単体
make test-integration        # Java IT
make test-e2e                # ブラウザE2E (該当する場合)
```

すべて green を確認、PR 作成。レビュー観点は [docs/review-checklists/spi-review.md](../../../docs/review-checklists/spi-review.md) 参照。

## superpowers との連携

- **brainstorming** : spec の draft を refine
- **writing-plans** : この skill の手順 1-11 を 2-5分タスクに分解
- **executing-plans + subagent-driven-development** : 各タスクを subagent dispatch
- **test-driven-development** : Step 5 (RED) → Step 6 (GREEN) → Step 7 RED → IT GREEN
- **requesting-code-review** : Step 11 の検証通過後、PR レビュー依頼

## Anti-patterns

- ❌ パターン番号を skip (例: 01 → 03) — 既存最大+1 を厳守
- ❌ Java パッケージ名を変えずに既存パターンの clone を作る (クラス衝突)
- ❌ `META-INF/services/` の中身を Factory のリネームに合わせて更新し忘れ (SPI が読まれない)
- ❌ `context.failure(error)` 単独呼び出し (Direct Grant で 500)
- ❌ テスト realm の user に firstName/lastName を入れ忘れ ("Account is not fully set up")
- ❌ spec を後付けで書く (実装後に implementations 埋める=可、ただし draft → approved → implemented の流れは省略しない)
- ❌ E2E 不要なパターン (フォーム表示なし) で無理に E2E 書く

## Checklist

- [ ] spec 起票 (`docs/specs/patterns/NN-<name>.md`)
- [ ] パターン番号が連番
- [ ] SPI モジュール作成 + Maven multi-module 設定済み (親POM `<modules>`)
- [ ] Java パッケージ・クラス名リネーム済み
- [ ] `META-INF/services/` 登録済み
- [ ] 単体テスト green
- [ ] Java IT green (test realm JSON の User Profile 罠回避済み)
- [ ] (該当時) E2E green
- [ ] spec の `status: implemented` + implementations + acceptance_tests 列挙
- [ ] CLAUDE.md (パターン個別 + providers全体)
- [ ] `make spec-validate` green

## Related skills

- `writing-spec` — spec 起票時に併用
- `writing-keycloak-acceptance-tests` — 3層テストの具体的な書き方

## Related docs

- [keycloak/providers/CLAUDE.md](../../../keycloak/providers/CLAUDE.md) — SPI開発の流儀
- [docs/testing.md](../../../docs/testing.md) — 3層テスト戦略・既知の罠
- [docs/review-checklists/spi-review.md](../../../docs/review-checklists/spi-review.md) — レビュー観点
