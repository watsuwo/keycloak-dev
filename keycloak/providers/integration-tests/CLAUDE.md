# keycloak/providers/integration-tests/ — Keycloak統合テスト

Testcontainersで実Keycloakを起動してSPIの挙動を検証するモジュール。

## なぜ別モジュールか

- 単体テスト (各SPIモジュール内、`mvn test`) はMockitoでロジックのみ高速検証
- **統合テスト (このモジュール、`mvn verify`)** は実Keycloakコンテナを起動してフロー全体を検証
- 単体テストはCIで毎回実行、統合テストは少し重いのでフェーズ分離 (Surefire vs Failsafe) で混在を避ける

## 仕組み

1. `mvn` のビルド順序で先にSPIモジュール (`01-email-domain-allowlist` 等) がJARを生成
2. このモジュールの `process-test-resources` フェーズで `maven-dependency-plugin` が SPI JARを `target/spi-providers/` にコピー
3. Failsafeフェーズで `*IT.java` が起動 → `KeycloakContainer` を Testcontainers で起動
4. `withProviderLibsFrom()` で `target/spi-providers/*.jar` をKeycloakにマウント
5. `withRealmImportFile()` でテスト用Realm JSONを取り込み (`--import-realm` 相当)
6. 起動したKeycloakに対してAdmin Client/HTTPで操作 → 期待動作をアサーション

## ディレクトリ構造

```
integration-tests/
├── pom.xml                                       依存と Failsafe 設定
├── CLAUDE.md                                     このファイル
└── src/test/
    ├── java/com/example/keycloak/it/
    │   └── EmailDomainAllowlistIT.java            パターン1の統合テスト
    └── resources/
        ├── test-realm-email-domain.json           テスト用Realm定義 (パターン1用)
        └── logback-test.xml                       ログ抑制設定
```

## 実行方法

```bash
# 統合テストのみ実行 (要 Docker daemon)
make test-integration

# 単体 + 統合の全テスト
make test-all
```

## 新しいパターンに統合テストを追加する手順

1. このディレクトリ配下に `<Pattern>IT.java` を追加 (Failsafeが拾うので命名重要)
2. 必要なら `src/test/resources/test-realm-<pattern>.json` を作成
3. `KeycloakContainer` のセットアップは `EmailDomainAllowlistIT` を参考に
4. 新パターンSPIモジュールへの依存を `pom.xml` に追加 (`<scope>runtime</scope>`)

## 既知の注意点

- **Docker daemonが必要** : WSL2/Mac/Linuxどれでも Docker Desktop か Engine が動いていること
- **初回起動** : Keycloak イメージを pull するので数分かかる場合がある
- **テスト並列実行** : Testcontainers は同一テストクラス内ではコンテナ共有 (`@Container static`)、クラス間は別コンテナ
- **ポート競合** : `KeycloakContainer` はランダムポートを使うため衝突しない
- **`getAuthServerUrl()` は末尾スラッシュ付き** : URL構築時は重複スラッシュを避けるよう `baseUrl()` ヘルパーで除去している

## デバッグの定石

- **テスト落ちたらまず failsafe-report** : `target/failsafe-reports/*.txt` にアサーションメッセージとレスポンスボディがある
- **Keycloak側のログを見たい** : `EmailDomainAllowlistIT` の `withEnv("KC_LOG_LEVEL"...)` と `withLogConsumer(...)` をコメントアウト外して再実行 — 認証フローの各ステップ・required actions・例外スタックがコンソールに出る
- **realm import の罠**:
  - User Profile が `firstName`/`lastName` を必須属性扱いするため、テストユーザーには必ず両方設定する (なければ UPDATE_PROFILE が自動付与されて Direct Grant が "Account is not fully set up" で弾かれる)
  - `requiredActions: []` だけでは不十分なケースがある (上記が真の原因)
  - `emailVerified: true` を明示しないと VERIFY_EMAIL が required になることも

## テスト realm を書くときのチェックリスト

新しいパターン用のテストrealm JSONを作るときは:

1. `realm.enabled = true`, `sslRequired = "none"`
2. user に `firstName`, `lastName`, `emailVerified: true`, `requiredActions: []`
3. credentials は `{ "type": "password", "value": "...", "temporary": false }`
4. client は `directAccessGrantsEnabled: true` (Direct Grantテストする場合)
5. カスタム auth flow を使うなら `topLevel: true`, `builtIn: false`, `providerId: "basic-flow"`
6. realm レベルで `directGrantFlow: "<alias>"` を指定して新フローに切替
