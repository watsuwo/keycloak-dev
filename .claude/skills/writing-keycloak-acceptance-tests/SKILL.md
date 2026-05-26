---
name: writing-keycloak-acceptance-tests
description: Use when writing tests (unit, Java integration, or browser E2E) that verify a Keycloak SPI pattern's acceptance_criteria in this project. Encodes the 3-layer test architecture and the known pitfalls (User Profile必須属性 / Direct Grant 500 / Mockito JDK24+ / OAuth redirect chrome-error 等).
---

# Writing Keycloak Acceptance Tests

このプロジェクトの3層テスト構成 (単体 / Java IT / ブラウザE2E) で acceptance test を書く skill。
spec の `acceptance_criteria` を verify する責務範囲。

[docs/testing.md](../../../docs/testing.md) (3層 + 既知の罠の正本) と既存 [パターン1のテスト](../../../keycloak/providers/01-email-domain-allowlist/src/test/) を参照。

## When to Use

- 新 SPI パターン (`writing-keycloak-spi-pattern` skill 内 Step 5) でテストを追加するとき
- 既存パターンのテストにケース追加・修正するとき
- spec の `acceptance_criteria` を新規に test 化するとき (TDD の RED フェーズ)

## When NOT to Use

- Terraform 設定検証 (`scripts/test-terraform.sh` が担う、`writing-keycloak-realm-terraform` skill の責務)
- ロジック以外の手動受け入れ試験 (チェックリスト形式、PR description で記録)

## 3層の使い分け

| 層 | 場所 | 何をテスト | コマンド | Docker | 速度 |
| --- | --- | --- | --- | --- | --- |
| 単体 | `keycloak/providers/0N-*/src/test/` | ロジック分岐 (Mockコンテキスト) | `make test-providers` | 不要 | <1秒/件 |
| Java IT | `keycloak/providers/integration-tests/src/test/` | 実Keycloak API挙動 (Direct Grant等) | `make test-integration` | 必要 | ~10秒/spec |
| ブラウザE2E | `e2e-tests/tests/` | UI/Auth Code Flow/カスタムエラーページ | `make test-e2e` | 必要 | ~15秒/spec |

**3層は検証対象が異なる → 互いに代替不能。** 新パターン追加時は3層すべて書くのが原則 (画面UIが無いパターンは E2E 省略可)。

## Workflow

### Step 1: spec の acceptance_criteria を読み込む

```yaml
# 例: docs/specs/patterns/0N-<name>.md
acceptance_criteria:
  - id: AC-1
    desc: 許可ユーザーは Direct Grant でトークン取得できる
  - id: AC-2
    desc: 拒否ユーザーは invalid_grant で拒否される
```

各 AC を「どの層で verify するか」マップする:

| AC のタイプ | 主担当層 |
| --- | --- |
| ロジック分岐 (if/else 各枝) | 単体 |
| API応答 (token取得・status code・JSON形式) | Java IT |
| 画面UI動作 (form 入力・redirect・カスタムエラーページ表示) | E2E |

### Step 2: 単体テスト (Mockito + JUnit5)

配置: `keycloak/providers/0N-<name>/src/test/java/.../<Name>Test.java`

雛形 (パターン1から):
```java
class EmailDomainAllowlistAuthenticatorTest {
    private AuthenticationFlowContext context;
    @BeforeEach
    void setUp() {
        context = mock(AuthenticationFlowContext.class, RETURNS_DEEP_STUBS);
        // ... user, configModel をモック
    }

    @Test
    void allowedDomain_succeeds() {
        // ... when().thenReturn() で入力構成
        authenticator.authenticate(context);
        verify(context).success();
    }
}
```

ポイント:
- `RETURNS_DEEP_STUBS` 必須 (`context.form().setError().createErrorPage()` の chain 用)
- 全分岐 (成功/失敗/edge case) をカバー
- Mockito 5.18+ 必須 (JDK 24/25 対応、`mockito.version` を親POMで管理済み)

### Step 3: Java IT (Testcontainers + 生HTTP)

配置:
- テスト本体: `keycloak/providers/integration-tests/src/test/java/.../<Name>IT.java` (末尾 `IT` 必須、Failsafeが拾う)
- テスト realm: `keycloak/providers/integration-tests/src/test/resources/test-realm-<name>.json`

雛形 (パターン1 IT から):
```java
@Testcontainers
class <Name>IT {
    @Container
    static final KeycloakContainer KEYCLOAK = new KeycloakContainer("quay.io/keycloak/keycloak:26.0")
        .withProviderLibsFrom(loadSpiJars())
        .withRealmImportFile("/test-realm-<name>.json");

    @Test void smoke_wellKnownReachable() { ... }
    @Test void allowedX_canObtainToken() { ... }
    @Test void disallowedX_isRejected() { ... }
}
```

ポイント:
- `baseUrl()` ヘルパーで `getAuthServerUrl()` の末尾スラッシュを除去 (URL ダブルスラッシュ防止)
- 生 `java.net.http.HttpClient` で OAuth エンドポイントを叩き、レスポンスボディを assert
- smoke test (`/realms/<realm>/.well-known/openid-configuration` 200) を必ず1本入れる

### Step 4: テスト realm JSON の罠回避

`keycloak/providers/integration-tests/src/test/resources/test-realm-<name>.json` で **必ず** :

```json
{
  "users": [
    {
      "username": "alice",
      "email": "alice@example.com",
      "firstName": "Alice",            // ← 必須 (User Profile 必須属性)
      "lastName": "Test",              // ← 必須
      "emailVerified": true,           // ← VERIFY_EMAIL を回避
      "enabled": true,
      "credentials": [
        { "type": "password", "value": "password", "temporary": false }
      ],
      "requiredActions": []            // ← 必須 (空配列で明示)
    }
  ],
  "clients": [
    {
      "directAccessGrantsEnabled": true,  // ← Direct Grant テスト時
      // ...
    }
  ],
  "authenticationFlows": [
    {
      "alias": "...",
      "topLevel": true,
      "builtIn": false,
      "providerId": "basic-flow",
      // ...
    }
  ],
  "directGrantFlow": "<カスタムflowのalias>"   // ← realm レベルで bind
}
```

これらを抜くと "Account is not fully set up" で Direct Grant が詰む既知の罠。

### Step 5: ブラウザE2E (Playwright + testcontainers Node)

該当する場合のみ (画面UI/カスタムエラーページ/OAuth redirect の検証):

配置:
- テスト本体: `e2e-tests/tests/<name>-browser.spec.ts`
- テスト realm: `e2e-tests/fixtures/test-realm-<name>.json` (Browser Flow 設定)

雛形 (パターン1 spec から):
```typescript
test('alice can complete browser login', async ({ page, kcUrl }) => {
    await page.goto(buildAuthUrl(kcUrl));
    await page.locator('#username').fill('alice');
    await page.locator('#password').fill('password');

    // OAuth redirect 捕捉 (chrome-error 着地回避)
    const [request] = await Promise.all([
        page.waitForRequest(req => req.url().startsWith(REDIRECT_URI), { timeout: 15_000 }),
        page.locator('#kc-login').click(),
    ]);
    expect(request.url()).toMatch(/code=[^&]+/);
});
```

ポイント:
- `redirect_uri` (例: localhost:3000) は実サーバ不要、`waitForRequest` でリクエスト発火時点を捕捉
- `page.waitForURL()` / `page.route()` は cross-origin redirect で chrome-error 着地するので使わない (ADR-010 参照)
- fixture (`e2e-tests/fixtures/keycloak.ts`) は worker scope、`make build-providers` で生成されたJARを bind mount

### Step 6: 全層を走らせて green を確認

```bash
make test-providers       # 単体
make test-integration     # Java IT
make test-e2e             # ブラウザ E2E
```

落ちたら:
- 単体: `keycloak/providers/0N-*/target/surefire-reports/*.txt`
- Java IT: `keycloak/providers/integration-tests/target/failsafe-reports/*.txt`
- E2E: `e2e-tests/test-results/<test>/` (screenshot + video + trace)

### Step 7: spec の acceptance_tests 欄を更新

```yaml
acceptance_tests:
  - keycloak/providers/0N-<name>/src/test/java/.../<Name>Test.java
  - keycloak/providers/integration-tests/src/test/java/.../<Name>IT.java
  - e2e-tests/tests/<name>-browser.spec.ts
```

`make spec-validate` で green を確認。

## Acceptance Criteria for This Skill

- [ ] spec の各 `acceptance_criteria` が **少なくとも1層で verify** されている
- [ ] 単体テストは全分岐網羅 (成功/失敗/edge case)
- [ ] テスト realm JSON が User Profile必須属性問題を回避 (firstName/lastName/emailVerified/requiredActions)
- [ ] Java IT 名末尾が `IT` (Failsafe pick up)
- [ ] (E2E書く場合) `waitForRequest` で OAuth redirect 捕捉、`waitForURL` 使ってない
- [ ] `make test-providers && make test-integration && make test-e2e` が全部 green
- [ ] spec の `acceptance_tests` 欄が3層のテストファイル列挙
- [ ] `make spec-validate` green

## Common Pitfalls

| アンチパターン | 正しいやり方 |
| --- | --- |
| Mockito で `verify(context).failure(...)` の deep stubs 抜け | `mock(..., RETURNS_DEEP_STUBS)` を BeforeEach で設定 |
| Java IT のクラス名末尾が `Test` (`*Test.java`) | Failsafe は `*IT.java` を拾う。Surefire と分離 |
| テストユーザーに firstName/lastName 抜け | 必ず両方 + `emailVerified:true` + `requiredActions:[]` |
| `context.failure(error)` 単独呼び出し | `OAuth2ErrorRepresentation` を JSON Response で渡す (ADR-009) |
| `getAuthServerUrl()` を末尾スラッシュ付きで連結 | `baseUrl()` ヘルパーで除去 |
| E2E で `page.waitForURL(/code=/)` | `chrome-error` 着地、Timeoutする。`waitForRequest` 使う (ADR-010) |
| Mockito 5.11 を使い続け | parent pom で `mockito.version` 5.18+ (JDK 24/25 必須) |
| sibling JAR が package 前で copy-dependencies 失敗 (MDEP-187) | dependency-plugin の execution を `pre-integration-test` フェーズに |
| 単体だけ書いて IT/E2E スキップ | 検証対象が異なる、3層原則。スキップ理由を PR description に明記 |

## Integration with superpowers

- `test-driven-development` → AC を RED 化 (failing test) → 実装で GREEN → REFACTOR
- `writing-plans` → 各 AC をテスト追加タスクに分解
- `verification-before-completion` → Step 6 の3層 green を完了判定
- `systematic-debugging` → テスト落ちたら surefire/failsafe report → コンテナログ → trace の順
