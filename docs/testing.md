# テスト方式ガイド

このリポジトリで採用しているテストの種類、役割分担、利用ツール、実行方法をまとめます。
**利用者向け** (新規メンバーのオンボーディング・案件適用の参照) を想定。

---

## 全体像

| 大区分 | 細区分 | 場所 | ツール | Docker | 速度 |
| --- | --- | --- | --- | --- | --- |
| **単体テスト** | SPI実装ロジック | `keycloak/providers/0N-*/src/test/` | JUnit 5 + Mockito + AssertJ | 不要 | <1秒/件 |
| **結合テスト** | APIレベル (Java IT) | `keycloak/providers/integration-tests/` | Testcontainers (Java) + 生HTTP | **必要** | 10秒~/spec |
| **結合テスト** | ブラウザE2E | `e2e-tests/` | Playwright + Testcontainers (Node) + Chromium | **必要** | 15秒~/spec |
| (補助) | Terraform設定検証 | `scripts/test-terraform.sh` | Terraform + curl + jq | (KC稼働) | 30秒 |

### なぜ層を分けるのか

- **単体テスト** : ロジックの**分岐を網羅** 。Mockで再現するため高速・安定 (Docker不要)。Edge case はここで全部潰す
- **結合テスト (API)** : 実Keycloakが**カスタムSPI込みで動く**ことの確認。Direct Grant 等のプログラマブルな経路で
- **結合テスト (ブラウザ)** : **画面UI・OAuth Authorization Code Flow・カスタムエラーページ・Themes** 等、APIだけでは触れない領域

3層は **検証対象が異なる** ため互いに代替不能。すべて維持する方針。

---

## 1. 単体テスト

### 役割

SPI実装クラス (Authenticator, EventListener等) の判定ロジックを **Mockコンテキスト** で検証。Keycloak本体を起動せずに、AuthenticationFlowContext や UserModel をMockitoでスタブして「この入力に対してこの分岐に入るか」を確認する。

### ツール

| ツール | 役割 | バージョン |
| --- | --- | --- |
| JUnit Jupiter | テストランナー | 5.10+ |
| Mockito | Mock生成、verify | **5.18+ (JDK 24/25対応に必須)** |
| Mockito-junit-jupiter | Mockito × JUnit5連携 | 同上 |
| AssertJ | アサーション | 3.25+ |
| Maven Surefire | 実行プラグイン | 3.2+ |

### 配置

```
keycloak/providers/0N-<pattern>/src/test/java/<package>/<ClassName>Test.java
```

命名規則: クラス名末尾 `Test` (Surefire が拾うため)。

### 実行

```bash
make test-providers          # 全モジュールの単体テスト
cd keycloak/providers/01-email-domain-allowlist && mvn test    # 特定モジュールのみ
```

### サンプル

[keycloak/providers/01-email-domain-allowlist/src/test/java/com/example/keycloak/authenticators/emaildomain/EmailDomainAllowlistAuthenticatorTest.java](../keycloak/providers/01-email-domain-allowlist/src/test/java/com/example/keycloak/authenticators/emaildomain/EmailDomainAllowlistAuthenticatorTest.java)

8ケースで以下を検証:
- 許可ドメインのユーザーは `context.success()` が呼ばれる
- 拒否ドメインのユーザーは `context.failure(ACCESS_DENIED, ...)` が呼ばれる
- 大文字小文字を無視
- 設定なし・空設定=制限なし
- メール未設定=`INVALID_USER`
- ユーザー未解決=`attempted()`

### 何をテストすべきか

- ✅ ロジックの分岐網羅 (`if/else` 各ブランチ)
- ✅ Edge case (null, 空文字, 大小文字, 不正フォーマット)
- ✅ 設定パース (`MULTIVALUED_STRING_TYPE` の `##` 区切り等)
- ❌ Keycloak実体の動き (それは結合テストで)
- ❌ 認証フロー全体 (同上)

---

## 2. 結合テスト — APIレベル (Java IT)

### 役割

**実Keycloakをコンテナで起動** し、カスタムSPI JARを読み込ませて、HTTP/OAuth API レベルでフローが期待通り動くかを検証する。
ブラウザを介さない検証 (Direct Grant、Token Introspection、Admin API 経由のRealm操作等) をカバー。

### ツール

| ツール | 役割 | バージョン |
| --- | --- | --- |
| Testcontainers Java | Dockerコンテナ起動制御 | 1.19+ |
| testcontainers-keycloak (dasniko) | Keycloak専用ラッパー | 3.4+ |
| java.net.http.HttpClient | 生HTTP呼び出し | JDK 11+ 標準 |
| keycloak-admin-client (任意) | Admin API操作 | Keycloakバージョンに合わせる |
| AssertJ | アサーション | 3.25+ |
| Maven Failsafe | 実行プラグイン | 3.2+ |
| logback-classic | ログ抑制 | 1.5+ |

### 配置

```
keycloak/providers/integration-tests/src/test/java/<package>/<ClassName>IT.java
keycloak/providers/integration-tests/src/test/resources/test-realm-<pattern>.json
```

命名規則: クラス名末尾 `IT` (Failsafe が拾うため、Surefireの `*Test` と分離される)。

### 仕組み

1. Maven reactor で SPIモジュール (`01-*` 等) を先に `package`
2. `pre-integration-test` フェーズで `maven-dependency-plugin` が SPI JAR を `target/spi-keycloak/providers/` に集約
3. テスト起動時、`@Container` でアノテートされた `KeycloakContainer` がコンテナを起動
   - SPI JARを `/opt/keycloak/providers/` に bind mount
   - `test-realm-*.json` を `/opt/keycloak/data/import/` に投入 (`--import-realm`)
4. `Wait.forHttp` で realm の well-known が 200 になるまで待機
5. テスト本体が `HttpClient` で OAuth エンドポイントを叩いてアサーション

### 実行

```bash
make test-integration                       # SPIビルド+全Java IT実行
cd providers && mvn -pl integration-tests -am verify   # 同等
```

### サンプル

[keycloak/providers/integration-tests/src/test/java/com/example/keycloak/it/EmailDomainAllowlistIT.java](../keycloak/providers/integration-tests/src/test/java/com/example/keycloak/it/EmailDomainAllowlistIT.java)

3ケース:
- Smoke: `/keycloak/realms/<realm>/.well-known/openid-configuration` が 200
- 許可ドメインの user で Direct Grant → access_token 取得
- 拒否ドメインの user で Direct Grant → invalid_grant 4xx

### 何をテストすべきか

- ✅ 実SPIが Keycloak にロードされ、認証フローの一部として動作する
- ✅ Direct Grant 等のAPI経由フロー (Resource Owner Password、Client Credentials)
- ✅ Token Introspection、UserInfo、Refresh等のOIDCエンドポイント
- ✅ Realm import が正しく完了して有効である
- ❌ ブラウザ画面のUI/CSS/JS (それは E2E)
- ❌ ユーザーがフォームに何を入力する流れ (同上)

### Realm JSON のチェックリスト (詰まりがちな点)

新規パターン用にテスト realm JSON を作るときは以下を必ずセット:

- `realm.enabled = true`, `sslRequired = "none"`
- user に `firstName`, `lastName`, `emailVerified: true`, `requiredActions: []`
  (これ無いと User Profile必須属性問題で Direct Grant が "Account is not fully set up" で詰む)
- credentials は `{"type": "password", "value": "...", "temporary": false}`
- client は `directAccessGrantsEnabled: true` (Direct Grant テスト時)
- カスタム auth flow を使うなら `topLevel: true`, `builtIn: false`, `providerId: "basic-flow"`
- realm レベルで `directGrantFlow: "<alias>"` を指定して新フローに切替

---

## 3. 結合テスト — ブラウザE2E

### 役割

**実ブラウザ (Chromium) を介して** Keycloak のログイン画面・OAuth Authorization Code Flow・カスタムエラーページ・Themes を検証する。
Java IT では到達できない領域 (UI、HTML、CSS、JS、ブラウザリダイレクト連鎖) を担当。

### ツール

| ツール | 役割 | バージョン |
| --- | --- | --- |
| Playwright | ブラウザ自動操作 | 1.45+ |
| @playwright/test | テストランナー (`*.spec.ts`) | 同上 |
| testcontainers (Node.js) | Dockerコンテナ起動制御 | 10.7+ |
| TypeScript | テストコード言語 | 5.4+ |
| Node.js | ランタイム | 18+ |
| Chromium | テスト対象ブラウザ | Playwrightが自動取得 |

### 配置

```
e2e-tests/
├── playwright.config.ts                     workers=1, screenshot/video/trace on failure
├── fixtures/
│   ├── keycloak.ts                          KeycloakContainer fixture (worker scope)
│   └── test-realm-<pattern>.json            テスト用realm定義
└── tests/
    └── <pattern>-browser.spec.ts            テスト本体
```

### 仕組み

1. `make build-providers` で SPI JAR を生成 (前提)
2. Playwright が `fixtures/keycloak.ts` を読み込み — Worker開始時に1回
3. `glob` で `keycloak/providers/*/target/*.jar` を集めて bind mount
4. `testcontainers` (Node) が Keycloakコンテナを起動 (`start-dev --import-realm`)
5. `Wait.forHttp` で realm well-known が 200 になるまで待機
6. 各テストが Playwright の `page` でログインフォームを操作
7. **OAuth redirect の捕捉**: `page.waitForRequest(req => req.url().startsWith(REDIRECT_URI))`
   (localhost:3000 等が実在しなくても URL に Authorization Code が乗っている時点で捕捉可能)
8. Worker終了でコンテナ停止

### 実行

```bash
# 初回のみ
make e2e-install                # npm install + Chromium download

# 通常実行
make test-e2e                   # SPIビルド + Playwright

# デバッグ
make test-e2e-ui                # Playwright UI mode (timeline + step-by-step)
make test-e2e-headed            # ヘッドレス無効、ブラウザ画面表示
```

### サンプル

[e2e-tests/tests/email-domain-allowlist-browser.spec.ts](../e2e-tests/tests/email-domain-allowlist-browser.spec.ts)

3ケース:
- alice ログイン成功 → `redirect_uri?code=...&state=...` への遷移を `waitForRequest` で捕捉
- eve 拒否 → カスタムエラーページ表示 ("このドメインからのログインは許可されていません")
- 間違いパスワード → KC 標準エラー (Authenticator到達せず)

### 何をテストすべきか

- ✅ ログイン画面が表示される (要素IDが期待通り)
- ✅ Authorization Code Flow で `code=` が redirect_uri に乗る
- ✅ Required Action UI (パスワード更新、属性更新等)
- ✅ カスタムエラーページの文言・レイアウト
- ✅ Theme 反映 (ロゴ、CSS、メッセージ翻訳)
- ✅ ソーシャルログイン redirect 連鎖 (Google等のスタブ可能)
- ❌ Mock で足りる純粋ロジック (それは単体)
- ❌ APIレベル直接呼び出し (それは Java IT)

---

## 4. (補助) Terraform 設定検証

### 役割

`terraform apply` 後の管理コンソール設定が期待通り動作するかを **実Keycloakに対して** チェック。
Realm/Client/User/Role等の構築が正しく完了したことの統合確認。

### ツール

- Terraform CLI 1.5+
- `keycloak/keycloak` Provider (公式)
- curl + jq (検証スクリプト内)

### 配置

```
terraform/environments/<案件>/
scripts/test-terraform.sh
```

### 実行

```bash
make tf-test                    # apply → 検証 → destroy のローテーション
```

### サンプル

[scripts/test-terraform.sh](../scripts/test-terraform.sh)

検証内容:
- `terraform apply` 成功
- testuser での Direct Grant → access_token 取得
- 間違いパスワード → invalid_grant 拒否
- `terraform destroy` で後始末 (trap で確実実行)

---

## どの層に書くか — 判断フロー

```
新しい検証ニーズ
    ↓
Q1: SPI内部のロジック分岐を確認したい
    └─ Yes → 単体テスト (Mockito)
            例: "domain判定の各エッジケース"

Q2: 実Keycloakで動かしたい
    │
    ├─ ブラウザ画面の操作 / OAuth Code Flow / Themes
    │   └─ ブラウザE2E (Playwright)
    │       例: "ログインボタン押下後にエラーページが表示される"
    │
    └─ API直接呼び出し / Direct Grant / Admin API
        └─ Java IT (Testcontainers Java)
            例: "Direct Grantでtoken取得できる"

Q3: terraform apply の結果を検証したい
    └─ scripts/test-terraform.sh
        例: "applyしたClientでDirect Grantが通る"
```

---

## 新パターン追加時のテスト整備チェックリスト

新パターン `keycloak/providers/02-<pattern>/` を追加する時:

- [ ] **単体テスト** : `keycloak/providers/02-<pattern>/src/test/java/.../<Pattern>Test.java`
      → ロジック分岐を網羅
- [ ] **Java IT** : `keycloak/providers/integration-tests/src/test/java/.../<Pattern>IT.java`
      → 該当機能のAPI挙動を実Keycloakで確認
- [ ] **テスト realm JSON** : `keycloak/providers/integration-tests/src/test/resources/test-realm-<pattern>.json`
      → User Profile 罠 (firstName/lastName/requiredActions=[]) に注意
- [ ] **ブラウザE2E** (画面UIがある場合) : `e2e-tests/tests/<pattern>-browser.spec.ts` + `e2e-tests/fixtures/test-realm-<pattern>.json`
      → カスタムフォーム・エラーページの表示確認
- [ ] **パターンレシピ** : `docs/specs/patterns/0N-<pattern>.md` を更新してテストへのリンクを追加

---

## ローカル運用とCI推奨

### 開発中 (ローカル)

| シナリオ | コマンド | 所要時間 |
| --- | --- | --- |
| 軽く確認 | `make test-providers` | 数秒 |
| API挙動含めて | `make test-integration` | ~30秒 (初回 KC pull含めず) |
| ブラウザE2Eも | `make test-e2e` | ~30-60秒 |
| 全層 | `make test-providers && make test-integration && make test-e2e` | ~1-2分 |

### CI推奨パイプライン

```
PR push
  → 単体テスト       [必須]   <1分
  → Java IT          [必須]   ~1-3分
  → ブラウザE2E      [必須]   ~2-5分
  → (mainマージ前)
       └─ Terraform設定検証  [必須]   ~1分

Nightly (mainブランチ)
  → 全層 + 古いKeycloakバージョン互換性テスト [推奨]
```

GitHub Actions等で `make test-providers` → `make test-integration` → `make test-e2e` を順に実行、失敗時は `e2e-tests/playwright-report/` をartifactとしてアップロードしておくと事後デバッグが容易。

---

## デバッグ手順 (層別)

### 単体テストが落ちた
- `keycloak/providers/0N-*/target/surefire-reports/*.txt` を確認 (アサーション失敗内容 + スタックトレース)
- IDEから単体実行してステップ実行で深掘り

### Java IT が落ちた
- `keycloak/providers/integration-tests/target/failsafe-reports/*.txt` を確認 (レスポンスボディを含む)
- Keycloakコンテナログを見たい場合:
  - 対象 IT クラスの `KeycloakContainer` ビルダーに以下を一時追加 (例は [EmailDomainAllowlistIT.java](../keycloak/providers/integration-tests/src/test/java/com/example/keycloak/it/EmailDomainAllowlistIT.java) のコメント参照):
    ```java
    .withEnv("KC_LOG_LEVEL", "INFO,org.keycloak.authentication:DEBUG,org.keycloak.services:DEBUG")
    .withLogConsumer(of -> System.err.print("[KC] " + of.getUtf8String()))
    ```
- realm.json 周りの罠は [integration-tests/CLAUDE.md](../keycloak/providers/integration-tests/CLAUDE.md) のチェックリスト

### ブラウザE2E が落ちた
- `e2e-tests/test-results/<test-name>/` 配下に screenshot/video/trace.zip が自動保存される
- Trace閲覧: `npx playwright show-trace e2e-tests/test-results/<...>/trace.zip`
  → ステップ毎の DOM/network/console を可視化
- HTMLレポート: `npx playwright show-report e2e-tests/playwright-report`
- ブラウザ実画面を見ながら再現: `make test-e2e-headed`
- Playwright UIモードで step-by-step: `make test-e2e-ui`

---

## 既知の罠 — 集約リスト

| 罠 | 影響層 | 対処 |
| --- | --- | --- |
| Mockito < 5.15 + JDK 24/25 で `AuthenticatorConfigModel` をmockできない | 単体 | parent pom の `mockito.version` を 5.18+ に |
| Maven reactor 内の sibling JAR が package 前に参照できない (MDEP-187) | Java IT | dependency-plugin の execution を `pre-integration-test` フェーズに |
| Direct Grant で `context.failure(error)` 単体呼び出しは Keycloak 500 | Java IT | OAuth2 JSON Response を渡す。`isDirectGrantFlow()` でフロー判別 |
| Keycloak 26.x User Profile が firstName/lastName を必須化 → "Account is not fully set up" | Java IT / E2E | テストuserに必ず両属性 + `requiredActions: []` |
| `getAuthServerUrl()` 末尾スラッシュで URL ダブルスラッシュ | Java IT | `baseUrl()` ヘルパーで除去 |
| 存在しない `localhost:3000` への OAuth redirect が `chrome-error` に着地 | E2E | `page.waitForRequest()` でリクエスト発火時点を捕捉 |
| Docker Desktop on Mac の socket 自動検出失敗 | Java IT / E2E | fixture で `~/.docker/run/docker.sock` を fallback で明示 |
| Maven Central に Keycloak 26.0.13 等の "未来" バージョン不存在 | Java IT (依存解決) | 実在する最新パッチ (例 26.0.8) に揃える |

---

## 関連ドキュメント

| ファイル | 内容 |
| --- | --- |
| [keycloak/providers/CLAUDE.md](../keycloak/providers/CLAUDE.md) | SPI開発の流儀全般 |
| [keycloak/providers/integration-tests/CLAUDE.md](../keycloak/providers/integration-tests/CLAUDE.md) | Java IT の仕組み・罠・realm.jsonチェックリスト |
| [e2e-tests/CLAUDE.md](../e2e-tests/CLAUDE.md) | ブラウザE2E の仕組み・デバッグ |
| [terraform/CLAUDE.md](../terraform/CLAUDE.md) | Terraform設定検証の流儀 |
| [docs/specs/patterns/](patterns/) | SPIパターンカタログ (パターン毎にテスト雛形リンク) |
| [docs/specs/task-specs/01-admin-console-config-template.md](task-specs/01-admin-console-config-template.md) | 管理コンソール設定の入力テンプレ |
