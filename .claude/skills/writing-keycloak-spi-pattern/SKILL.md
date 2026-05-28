---
name: writing-keycloak-spi-pattern
description: Use when adding a new Keycloak SPI pattern (Authenticator, EventListener, ProtocolMapper, UserStorage, etc.) to this repo. Ensures Maven multi-module conventions, SPI registration, 3-layer tests, and pattern catalog entry.
---

# Writing Keycloak SPI Pattern

PATTERN spec の `requirements:` YAML ブロックを読み込み、Javaコード・テスト・META-INF登録・Maven module を生成する skill。
spec には「何が必要か」だけを書き、内部実装はこの skill が決定する。

## When to Use

- PATTERN spec (`docs/specs/patterns/NN-<name>.md`) に `requirements:` ブロックが書かれているとき
- 既存パターンを派生では足りず、新しい SPI 種別/挙動を追加したいとき
- 顧客案件で生まれた汎用ロジックを雛形リポに逆輸入するとき

## When NOT to Use

- 既存パターンを「設定値だけ変えて使う」ケース (auth-flow spec の `patterns[].config` で対応)
- Theme カスタマイズ (`keycloak/themes/` 配下)
- 管理コンソール設定 (`terraform/` 配下、別 skill: `writing-keycloak-realm-terraform`)

## Prerequisites

- [ ] PATTERN spec が `docs/specs/patterns/NN-<name>.md` に存在する
- [ ] spec の `requirements:` YAML ブロックに `spi_type`, `provider_id`, `display_name`, `acceptance_criteria` が埋まっている
- [ ] パターン番号が連番 (既存最大 + 1)

---

## Workflow (Spec-driven)

### Step 1: spec 読み込み

PATTERN spec ファイルを読む。`requirements:` YAML ブロックから以下を把握する:

- `spi_type` → Java インタフェース・META-INF キー (下記マッピング表参照)
- `provider_id` → `Factory.ID` 定数の値
- `display_name` → `getDisplayType()` の戻り値
- `config` → `getConfigProperties()` の内容
- `acceptance_criteria` → 単体テストのテストメソッド構成

### Step 2: Maven モジュール作成

既存の `sample-01-email-domain-allowlist` をコピーして派生する:

```bash
# 汎用パターンの場合
cp -r keycloak/providers/sample-01-email-domain-allowlist keycloak/providers/sample-NN-<name>

# 案件固有実装の場合
cp -r keycloak/providers/sample-01-email-domain-allowlist keycloak/providers/case-<client>-<name>
```

`pom.xml` を更新:
- `<artifactId>` → ディレクトリ名からプレフィックスを除いたもの (例: `ip-allowlist`)
- `<name>` → 人間向け名前

親 POM (`keycloak/providers/pom.xml`) の `<modules>` に追加。

### Step 3: Java パッケージ・クラス生成

**パッケージ命名**:

| spi_type | パッケージ | 主クラス名 | Factory クラス名 |
|---|---|---|---|
| Authenticator | `com.example.keycloak.authenticators.<name>` | `<Name>Authenticator` | `<Name>AuthenticatorFactory` |
| EventListener | `com.example.keycloak.listeners.<name>` | `<Name>EventListenerProvider` | `<Name>EventListenerProviderFactory` |
| ProtocolMapper | `com.example.keycloak.mappers.<name>` | `<Name>ProtocolMapper` | (Factory 統合、`AbstractOIDCProtocolMapper` 継承) |
| UserStorage | `com.example.keycloak.storage.<name>` | `<Name>UserStorageProvider` | `<Name>UserStorageProviderFactory` |
| RequiredAction | `com.example.keycloak.actions.<name>` | `<Name>RequiredActionProvider` | `<Name>RequiredActionFactory` |

`<name>` は `provider_id` の kebab-case をキャメルケース化したもの (例: `ip-allowlist` → `IpAllowlist`)。

**Factory クラス生成** (`<Name>Factory.java`):

`requirements.config` の各エントリを `ProviderConfigProperty` に変換する:

| YAML `type` | Java 定数 | 補足 |
|---|---|---|
| `STRING` | `ProviderConfigProperty.STRING_TYPE` | — |
| `MULTIVALUED_STRING` | `ProviderConfigProperty.MULTIVALUED_STRING_TYPE` | 値は `##` 区切りで保存 |
| `PASSWORD` | `ProviderConfigProperty.PASSWORD` | マスク表示 |
| `BOOLEAN` | `ProviderConfigProperty.BOOLEAN_TYPE` | — |
| `LIST` | `ProviderConfigProperty.LIST_TYPE` | `options` も設定 |
| `ROLE` | `ProviderConfigProperty.ROLE_TYPE` | — |
| `CLIENT` | `ProviderConfigProperty.CLIENT_LIST_TYPE` | — |

`config` が空のとき → `isConfigurable() = false`、`getConfigProperties()` は空リストを返す。

`requirements.requirement_choices` が指定されている場合、その配列を `getRequirementChoices()` に使用。
省略時は `[REQUIRED, OPTIONAL, DISABLED]`。

**主クラス生成** (`<Name>.java`):

`spi_type: Authenticator` の場合:
- `requirements_user: true` → `requiresUser()` が `true` を返す
- `authenticate()` の先頭で `context.getUser() == null` チェック
- `acceptance_criteria` を見て条件分岐と `context.success()` / `context.failure()` / `context.attempted()` の呼び分けを実装
- **Direct Grant 対応** (必須): `context.failure(error, response)` の `response` はフロー種別で出し分ける (後述)

`MULTIVALUED_STRING` の読み取り:
```java
String raw = config.getConfig().get(CONFIG_KEY);
if (raw == null || raw.isBlank()) return List.of();
return Arrays.asList(raw.split("##"));
```

### Step 4: META-INF/services 登録

`src/main/resources/META-INF/services/<META-INF キー>` に Factory の FQCN を1行で記述。

| spi_type | META-INF キー |
|---|---|
| Authenticator | `org.keycloak.authentication.AuthenticatorFactory` |
| EventListener | `org.keycloak.events.EventListenerProviderFactory` |
| ProtocolMapper | `org.keycloak.protocol.ProtocolMapper` |
| UserStorage | `org.keycloak.storage.UserStorageProviderFactory` |
| RequiredAction | `org.keycloak.authentication.RequiredActionFactory` |

### Step 5: 単体テスト生成

`acceptance_criteria` の各 AC を1テストメソッドにマッピングする:

```java
// AC-1 の例
@Test
void ac1_<camelCase(when)>() {
    // Arrange: "when" の条件をモックで再現
    // Act: authenticator.authenticate(context)
    // Assert: "then" の検証 (verify(context).success() 等)
}
```

`AuthenticationFlowContext` は `mock(AuthenticationFlowContext.class, RETURNS_DEEP_STUBS)` で作成
(`errorResponse()` 内の `context.form()` チェーンがあるため深いスタブが必要)。

### Step 6: spec frontmatter 更新

```yaml
status: implemented
implementations:
  - keycloak/providers/sample-NN-<name>/
acceptance_tests:
  - keycloak/providers/sample-NN-<name>/src/test/
  - keycloak/providers/integration-tests/src/test/java/.../<Name>IT.java
  - e2e-tests/tests/<name>-browser.spec.ts   # E2E があれば
```

### Step 7: CLAUDE.md 整備

- `keycloak/providers/sample-NN-<name>/CLAUDE.md` (パターン解説、フロー配置の注意点)
- `keycloak/providers/CLAUDE.md` のパターン一覧表に新エントリ追加

### Step 8: 検証

```bash
make spec-validate       # spec frontmatter 検証
make test-providers      # 単体テスト
make test-integration    # Java IT (Docker 必要)
```

---

## Direct Grant 対応 (必須)

`context.failure(error)` を単独で呼ぶと Direct Grant フローで **500** が返る。
`context.failure(error, response)` と必ずレスポンスを渡すこと。

レスポンスはフロー種別で出し分ける:

```java
private static Response errorResponse(AuthenticationFlowContext context,
                                      String oauthError, String description) {
    if (isDirectGrantFlow(context)) {
        OAuth2ErrorRepresentation err = new OAuth2ErrorRepresentation(oauthError, description);
        return Response.status(Response.Status.UNAUTHORIZED)
                .entity(err).type(MediaType.APPLICATION_JSON_TYPE).build();
    }
    return context.form().setError(description).createErrorPage(Response.Status.FORBIDDEN);
}

private static boolean isDirectGrantFlow(AuthenticationFlowContext context) {
    AuthenticationExecutionModel exec = context.getExecution();
    if (exec == null || exec.getParentFlow() == null) return false;
    AuthenticationFlowModel flow = context.getRealm().getDirectGrantFlow();
    return flow != null && flow.getId().equals(exec.getParentFlow());
}
```

`requirements.flows.direct_grant: true` のパターンは必ずこのヘルパーを含める。

---

## auth-flow spec との連携

`writing-keycloak-auth-flow` スキルは `patterns[].spec_id` が指す PATTERN spec を読み、
`requirements.provider_id` を Realm JSON の `authenticator` フィールドに使用する。

auth-flow spec に新パターンを追加するには:
1. PATTERN spec を `status: implemented` にする
2. auth-flow spec の `patterns:` に `spec_id` と `config` を追加

---

## Anti-patterns

- ❌ パターン番号を skip (既存最大 + 1 を厳守)
- ❌ Java パッケージ名を変えずに既存パターンの clone を作る (クラス衝突)
- ❌ `META-INF/services/` の中身を Factory リネームに合わせ忘れ (SPI が読まれない)
- ❌ `context.failure(error)` 単独呼び出し (Direct Grant で 500)
- ❌ テスト realm の user に firstName/lastName を入れ忘れ ("Account is not fully set up")
- ❌ `spec: draft` のまま実装する (draft → approved → implemented の順を省略しない)

## Checklist

- [ ] PATTERN spec の `requirements:` ブロックが埋まっている
- [ ] パターン番号が連番
- [ ] Maven module 作成 + 親 POM の `<modules>` に追加
- [ ] Java パッケージ・クラス名が規約通り
- [ ] `META-INF/services/` 登録済み
- [ ] Factory の `getConfigProperties()` が `config` ブロックと一致
- [ ] Direct Grant 対応 (`flows.direct_grant: true` のとき必須)
- [ ] 単体テストが `acceptance_criteria` をカバーしている
- [ ] spec の `status: implemented` + implementations + acceptance_tests 列挙
- [ ] CLAUDE.md (パターン個別 + providers 全体)
- [ ] `make spec-validate` green

## Related Skills

- `writing-spec` — spec 起票時に併用
- `writing-keycloak-auth-flow` — このパターンを auth flow に組み込む
- `writing-keycloak-acceptance-tests` — Java IT / E2E の詳細

## Related Docs

- [docs/specs/templates/spi-pattern-template.md](../../../docs/specs/templates/spi-pattern-template.md) — spec テンプレ (requirements YAML スキーマの正典)
- [keycloak/providers/CLAUDE.md](../../../keycloak/providers/CLAUDE.md) — SPI開発の流儀
- [docs/testing.md](../../../docs/testing.md) — 3層テスト戦略・既知の罠
