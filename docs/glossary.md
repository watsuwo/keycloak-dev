# 用語集 — Keycloak + プロジェクト用語

このリポジトリで頻出する Keycloak 標準用語 + 本プロジェクト独自用語をまとめる。
ジュニアの「これ何?」を即引きできるように。

---

## Keycloak 標準用語

### コア概念

| 用語 | 意味 |
| --- | --- |
| **Realm** | テナント境界の単位。ユーザー・ロール・クライアント・認証フロー等のグループ。1社=1Realmが多いが、要件次第 |
| **Master Realm** | 管理者用Realm。他のRealmを管理する権限を持つ。本番では `master` の admin user パスワードを必ず変更 |
| **Client** | Realmに登録する「連携アプリ」。Webアプリ・モバイルアプリ・APIサーバ等。OIDCの client_id に対応 |
| **User** | Realm内のエンドユーザー |
| **Role** | 権限の単位。Realm Role (Realm全体) と Client Role (特定Client内) の2階層 |
| **Group** | 複数Userをまとめる単位。Roleの一括付与に使う |
| **Identity Provider (IdP)** | 外部認証プロバイダ。Google/Microsoft/SAML/OIDC等。Keycloakを「ブローカー」として使う場合に登場 |
| **User Federation** | LDAP / Active Directory 等の外部ユーザーストアを Keycloak Realm と同期する仕組み |

### 認証フロー関連

| 用語 | 意味 |
| --- | --- |
| **Authentication Flow** | 認証ステップの一連の流れ。「ログイン画面表示 → Username/Password → 2FA」など |
| **Authenticator** | フロー内の1ステップを実装するSPI。本リポの主要なSPIカテゴリ |
| **Required Action** | ログイン後に強制実行されるアクション (パスワード更新、メール検証等) |
| **Browser Flow** | ブラウザ経由のログイン用 flow。Authorization Code Flow 等 |
| **Direct Grant Flow** | Resource Owner Password Credentials Grant (API直接認証) 用 flow |
| **Reset Credentials Flow** | パスワードリセット用 flow |
| **First Broker Login Flow** | 外部IdP経由で初めてログインしたユーザーの紐づけ flow |
| **Conditional Authenticator** | 条件によって実行/スキップを切替えられる Authenticator |

### OIDC / OAuth 関連

| 用語 | 意味 |
| --- | --- |
| **Authorization Code Flow** | ブラウザリダイレクトでcodeを取得し、サーバ側でtokenに交換する標準フロー。Public/Confidential両対応 |
| **Direct Grant (ROPC)** | Resource Owner Password Credentials。username/passwordを直接送ってtoken取得。テスト・レガシー連携で使う |
| **Client Credentials Grant** | Service Account用。client_id/secretだけでtoken取得 |
| **Implicit Flow** | ブラウザに直接tokenを返す古い方式。現在は非推奨 |
| **PKCE** | Public Client (SPA, モバイル) のセキュリティ強化機構。Authorization Code Flow にcode_verifier/challengeを追加 |
| **Access Token** | リソースアクセス用の短命token。JWTで実装されることが多い |
| **Refresh Token** | Access Tokenを再発行するためのlong-livedトークン |
| **ID Token** | OIDCで発行される、ユーザー identity を含むJWT |
| **Scope** | tokenに含める情報の範囲指定 (openid, profile, email 等) |
| **Protocol Mapper** | tokenに含めるclaim (属性) を制御するSPI |

### SPI (Service Provider Interface)

| 用語 | 意味 |
| --- | --- |
| **SPI** | Keycloakの拡張点。Authenticator / EventListener / UserStorage / Mapper 等 |
| **Provider** | SPIの実装インスタンス |
| **Factory** | Providerを生成するクラス。設定UIや ID も定義する |
| **META-INF/services** | Java ServiceLoaderの仕組み。FactoryクラスのFQCNをここに書くと Keycloak が読み込む |
| **kc.sh build** | Keycloak Quarkus版の最適化ビルドコマンド。keycloak/providers/themes取り込み + Quarkus augmentation |

### Theme

| 用語 | 意味 |
| --- | --- |
| **Theme** | Keycloakの画面・メールの見た目をカスタマイズする仕組み。FreeMarkerテンプレート + CSS/JS |
| **theme.properties** | テーマの設定ファイル (継承元、対応する type 等を指定) |
| **base / keycloak テーマ** | 標準提供の基本テーマ。独自テーマで継承して使う |
| **FreeMarker (FTL)** | Keycloakが使うサーバサイドテンプレートエンジン |

---

## プロジェクト独自用語

### ドキュメント・設計

| 用語 | 意味 | 場所 |
| --- | --- | --- |
| **雛形リポ** | このリポ自身。全顧客案件の出発点 | [README.md](../README.md) |
| **顧客リポ** | 雛形リポから派生した案件別リポ | [docs/customer-rollout.md](customer-rollout.md) |
| **case-spec** | 案件全体の要件を構造化した文書 | [docs/specs/case-spec-template.md](case-spec-template.md) |
| **task-spec** | 作業タイプ別の入力テンプレ (管理コンソール設定・SPI実装等) | [docs/specs/task-specs/](task-specs/) |
| **pattern (パターン)** | 再利用可能なSPI/Themeの実装単位。動くコード+解説+テスト+レシピが一式 | [docs/specs/patterns/](patterns/) |
| **パターンレシピ** | パターンの使い方・適用判断・派生方法を書いた文書 | [docs/specs/patterns/0N-...md](patterns/) |
| **Layer 1/2/3 context** | Claudeへの入力の3階層 (常時 / 案件単位 / タスク単位) | (内部設計概念) |

### テスト関連

| 用語 | 意味 | 場所 |
| --- | --- | --- |
| **単体テスト** | Mockitoでロジック分岐を検証 | `keycloak/providers/0N-*/src/test/` |
| **Java IT (結合テスト APIレベル)** | Testcontainers + HTTPで実Keycloakを起動して検証 | `keycloak/providers/integration-tests/` |
| **ブラウザE2E (結合テスト UIレベル)** | Playwright + testcontainers Nodeで実ブラウザ経由検証 | `e2e-tests/` |
| **3層テスト** | 上記3つの総称。本プロジェクトの基本テスト構成 | [docs/testing.md](testing.md) |
| **Terraform設定検証** | terraform apply の結果を curl で検証する補助テスト | `scripts/test-terraform.sh` |

### 開発フロー

| 用語 | 意味 |
| --- | --- |
| **3-layer build (Dockerfile)** | SPI build → Keycloak optimize (kc.sh build) → runtime の3ステージ |
| **build-providers** | SPI Maven build + JAR を keycloak/providers/ ルートにコピーする処理 |
| **逆輸入** | 顧客リポで生まれた汎用化可能な実装を雛形リポに PR で取り込むこと |

### 既知の罠で出てくる用語

| 用語 | 意味 | 詳細 |
| --- | --- | --- |
| **MDEP-187** | Maven dependency-plugin で reactor内 sibling JAR が package 前に参照できない既知問題 | [docs/testing.md](testing.md) "既知の罠" |
| **User Profile 必須属性問題** | Keycloak 26.x で firstName/lastName が必須化されており、無いと Direct Grant が "Account is not fully set up" で詰む | 同上 |
| **chrome-error 着地** | E2Eで存在しない URL (localhost:3000 等) への redirect で Chrome がエラーページに着地する現象 | 同上 |
| **isDirectGrantFlow** | Authenticator が Direct Grant か Browser かを判別するヘルパー (フロー別Response出し分け用) | `keycloak/providers/sample-01-email-domain-allowlist/src/main/java/.../EmailDomainAllowlistAuthenticator.java` |

---

## 略語

| 略語 | 展開 |
| --- | --- |
| KC | Keycloak |
| SPI | Service Provider Interface |
| IdP | Identity Provider |
| OIDC | OpenID Connect |
| RP | Relying Party (OIDC) |
| OP | OpenID Provider (= Keycloak側) |
| JWT | JSON Web Token |
| JWS / JWE | JSON Web Signature / Encryption |
| ROPC | Resource Owner Password Credentials |
| MFA / 2FA | Multi-Factor Authentication / Two-Factor |
| TOTP | Time-based One-Time Password (Google Authenticator等) |
| SSO | Single Sign-On |
| LDAP | Lightweight Directory Access Protocol |
| AD | Active Directory |
| SAML | Security Assertion Markup Language |
| FTL | FreeMarker Template Language |
| HCL | HashiCorp Configuration Language (Terraform) |
| IT | Integration Test |
| E2E | End-to-End test |
| MVP | Minimum Viable Product |
| ADR | Architecture Decision Record |

---

## さらに学ぶ

- Keycloak Server Administration Guide: https://www.keycloak.org/docs/latest/server_admin/
- Keycloak Server Developer Guide: https://www.keycloak.org/docs/latest/server_development/
- OpenID Connect Core 1.0: https://openid.net/specs/openid-connect-core-1_0.html
- OAuth 2.0 RFC 6749: https://datatracker.ietf.org/doc/html/rfc6749
- OAuth 2.1 Draft: https://oauth.net/2.1/
