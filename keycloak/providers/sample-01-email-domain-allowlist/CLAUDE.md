# Email Domain Allowlist Authenticator

ユーザーのメールアドレスのドメインが、設定された許可リストに含まれている場合のみログインを許可するAuthenticator。

このディレクトリは **パターン1** の実装サンプルであり、Authenticator SPIの構造を学ぶ起点として扱う。詳細レシピは [docs/specs/patterns/01-email-domain-allowlist.md](../../../docs/specs/patterns/01-email-domain-allowlist.md) を参照。

## ファイル構成

```
01-email-domain-allowlist/
├── pom.xml
├── CLAUDE.md                              ← このファイル
└── src/
    ├── main/
    │   ├── java/com/example/keycloak/authenticators/emaildomain/
    │   │   ├── EmailDomainAllowlistAuthenticator.java        判定ロジック本体
    │   │   └── EmailDomainAllowlistAuthenticatorFactory.java SPI登録 + 設定UI定義
    │   └── resources/META-INF/services/
    │       └── org.keycloak.authentication.AuthenticatorFactory  ServiceLoader登録
    └── test/java/.../EmailDomainAllowlistAuthenticatorTest.java  単体テスト (Mockito)
```

## このパターンを真似て別のAuthenticatorを作る手順

1. このディレクトリを `keycloak/providers/0X-<your-pattern>/` にコピー
2. `pom.xml` の `<artifactId>` と `<name>` を変更
3. Javaパッケージを `com.example.keycloak.authenticators.<your-pattern>` にリネーム
4. クラス名・`Factory.ID` を変更
5. `META-INF/services/...` の中身をFactoryのFQCNに更新
6. 判定ロジックを書き換え
7. テストを追記
8. `make build-providers && make restart` で動作確認

## 配置上の注意 (フロー設計)

このAuthenticatorは `requiresUser() = true` で、`context.getUser()` が解決済みであることが前提。
**必ず Username Password Form (またはユーザーを特定する任意のステップ) の後段に配置すること**。

## Keycloak管理コンソールでの使い方

1. Authentication → Flows → 既存のbrowserフローを複製 (例: "browser-with-domain-check")
2. ステップ末尾に "Email Domain Allowlist" を追加 (Required)
3. ⚙ 設定 → "許可するドメイン" に `example.com` 等を追加
4. Bindings タブで "Browser Flow" にこの新しいフローを割り当て

## 既知の限界

- SAML/OIDCのブローカリングフロー (外部IdP経由ログイン) でも動作するが、IdPから取得した email が UserModel に反映済みであることが前提
- ワイルドカード (`*.example.com`) は未対応 → 必要なら判定ロジックを拡張

## 設計メモ: Authenticator 失敗時のレスポンス

`context.failure(error, response)` に渡す Response はフロー種別で変える必要がある:

| フロー | 必要なResponse形式 | 渡さないとどうなる |
| --- | --- | --- |
| Direct Grant (OIDC token endpoint) | JSON (`OAuth2ErrorRepresentation`) | `AuthenticationFlowException` がuncaughtで **500** |
| Browser (ログイン画面) | HTMLエラーページ (`context.form().createErrorPage()`) | デフォルトエラーページにフォールバック (500にはならない) |

本Authenticatorは `isDirectGrantFlow()` で `context.getRealm().getDirectGrantFlow()` と現在のexecutionの親フローIDを照合して、フロー種別を検出。両フローで使える「ポータブルなAuthenticator」になっている。

新しいAuthenticatorパターンを書くときは、この `errorResponse()` + `isDirectGrantFlow()` のセットをコピーすると同じ問題で詰まらずに済む。

## 関連リンク

- 親モジュール: [keycloak/providers/pom.xml](../pom.xml)
- SPI開発全般の流儀: [keycloak/providers/CLAUDE.md](../CLAUDE.md)
- パターンレシピ: [docs/specs/patterns/01-email-domain-allowlist.md](../../../docs/specs/patterns/01-email-domain-allowlist.md)
