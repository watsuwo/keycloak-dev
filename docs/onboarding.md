# 新メンバー オンボーディング (1週間プラン)

このリポジトリで Keycloak 開発を始める新メンバー向けの **1週間の手引き** 。
全部きっちりやる必要はなく、自分の知識ベースに合わせて飛ばしてOK。各日にメンターと進捗確認するのがおすすめ。

---

## Day 1 — 環境構築 + 動かす

### ゴール

- Dev Keycloak が手元で動いている
- 管理コンソールにログインできる
- 何が動いているかの全体像を把握

### やること

1. **必要ツールの導入** ([README.md](../README.md#必要なツール))
   - Docker Desktop / Engine
   - Java 17+ / Maven 3.9+
   - Node.js 18+
   - Terraform 1.5+
   - jq
2. **リポジトリ clone**
   ```bash
   git clone <雛形リポ or 案件リポ> ~/dev/keycloak-dev
   cd ~/dev/keycloak-dev
   ```
   WSL2の場合は必ず WSL2 内 (`/mnt/c/` 配下NG)
3. **Dev環境起動**
   ```bash
   make init   # .env と自己署名証明書を生成
   make up
   make ps     # 4サービス全部 healthy/running を確認
   ```
4. **管理コンソールアクセス**
   - https://keycloak.localtest.me/ を開く (証明書警告は「詳細設定→アクセスする」)
   - admin / admin でログイン
   - Realm セレクタ・Clients・Users・Authentication 等を眺める
5. **Mailhog 確認**
   - https://mailhog.localtest.me/ を開く
   - (この時点では空)

### Day 1 終わりに

- [ ] 4コンテナ (keycloak/postgres/traefik/mailhog) が起動している
- [ ] 管理コンソールに admin でログインできた

---

## Day 2 — ドキュメントを通読 + テストを回す

### ゴール

- このリポが何のためのものか・どう構成されているかを把握
- 3層テストを全部実行してグリーンになる

### やること

1. **読むべきドキュメント** (上から順に、各15-30分)
   - [README.md](../README.md) — 全体像
   - [CLAUDE.md](../CLAUDE.md) — 開発作業の流儀全般 (重要)
   - [docs/testing.md](testing.md) — テスト方式の3層構造 (重要)
2. **テスト実行**
   ```bash
   make test-providers       # 単体 (数秒)
   make test-integration     # Java IT (~30秒、Docker pull含めると初回数分)
   make e2e-install          # 初回のみ (npm + Chromium取得、数分)
   make test-e2e             # ブラウザE2E (~30-60秒)
   ```
3. **何をテストしているか確認**
   - 単体テスト: [keycloak/providers/01-email-domain-allowlist/src/test/java/.../EmailDomainAllowlistAuthenticatorTest.java](../keycloak/providers/01-email-domain-allowlist/src/test/java/com/example/keycloak/authenticators/emaildomain/EmailDomainAllowlistAuthenticatorTest.java) を読む
   - Java IT: [keycloak/providers/integration-tests/src/test/java/.../EmailDomainAllowlistIT.java](../keycloak/providers/integration-tests/src/test/java/com/example/keycloak/it/EmailDomainAllowlistIT.java) を読む
   - E2E: [e2e-tests/tests/email-domain-allowlist-browser.spec.ts](../e2e-tests/tests/email-domain-allowlist-browser.spec.ts) を読む
4. **E2E ヘッドフルで実行** (実画面を見る)
   ```bash
   make test-e2e-headed
   ```
   ブラウザでログインフォームが操作されるのを観察。

### Day 2 終わりに

- [ ] 3層テストすべて green
- [ ] 「単体/Java IT/E2E の違いと使い分け」を自分の言葉で説明できる

---

## Day 3 — パターン1を読み解く

### ゴール

- Keycloak SPI Authenticator の仕組みを理解
- パターン1のコードを読み切る

### やること

1. **パターン1の解説を読む**
   - [docs/specs/patterns/01-email-domain-allowlist.md](patterns/01-email-domain-allowlist.md) — レシピ
   - [keycloak/providers/01-email-domain-allowlist/CLAUDE.md](../keycloak/providers/01-email-domain-allowlist/CLAUDE.md) — パターン解説
2. **コードを順に読む**
   - `EmailDomainAllowlistAuthenticatorFactory.java` (SPI登録、設定UI定義)
   - `EmailDomainAllowlistAuthenticator.java` (判定ロジック、フロー検出)
   - `META-INF/services/org.keycloak.authentication.AuthenticatorFactory` (登録ファイル)
3. **管理コンソールで実体験**
   - https://keycloak.localtest.me/ master realm → Authentication → Flows
   - "browser" フローを複製 → ステップ末尾に "Email Domain Allowlist" を追加
   - 許可ドメイン設定 (例: `example.com`)
   - Bindings で Browser Flow を新フローに切替
   - 別ターミナルで `make logs` を流しながらログインしてみる
4. **Keycloak用語の理解 (必要に応じて)**
   - [docs/glossary.md](glossary.md) — 用語集
   - 知らない用語は Keycloak公式ドキュメント https://www.keycloak.org/documentation で深掘り

### Day 3 終わりに

- [ ] パターン1の Authenticator が何をしているか説明できる
- [ ] SPI登録の仕組み (META-INF/services) を理解
- [ ] 設定UIがどう admin console に出てくるか追えた

---

## Day 4 — 小さな改造をやってみる

### ゴール

- 既存パターンを少し改造して、3層テストを通す体験
- 開発フローを体に染み込ませる

### やること (どれか1つ選択)

#### A. パターン1にワイルドカード対応を追加

`*.example.com` のような指定で、サブドメインを全部許可する仕様を加える。

1. `EmailDomainAllowlistAuthenticator.java` の判定ロジックを改造
2. 単体テストにワイルドカードケースを追加 (alice@sub.example.com → 許可)
3. `make test-providers` で確認
4. (任意) Java IT / E2E にもケース追加

#### B. パターン1を「ブロックリスト」化

許可リストではなく「指定ドメインを拒否」する逆動作のパターンを作る。

1. `keycloak/providers/02-email-domain-blocklist/` を `01-email-domain-allowlist/` から複製
2. クラス名・パッケージ・Factory ID をリネーム
3. 判定ロジックを反転 (一致したら拒否)
4. テスト3層すべて追加
5. `make build-restart && make test-providers && make test-integration && make test-e2e`

### 詰まったら

- 各サブディレクトリの `CLAUDE.md` を参照
- [docs/testing.md](testing.md) の「既知の罠」セクション
- メンターに質問

### Day 4 終わりに

- [ ] 改造内容に対する3層テストが green
- [ ] 開発サイクル (実装 → 単体 → IT → E2E → manual確認) を1周経験

---

## Day 5 — レビュー・運用フロー理解

### ゴール

- チームの開発プロセス (PR・レビュー) を把握
- 自分の Day 4 の変更を PR にしてレビューを通す

### やること

1. **チームコントリビューション規約を読む**
   - [CONTRIBUTING.md](../CONTRIBUTING.md) — branch/commit/PR/review規約
2. **レビュー観点を理解**
   - [docs/review-checklists/spi-review.md](review-checklists/spi-review.md) — SPI レビュー観点
   - [docs/review-checklists/realm-config-review.md](review-checklists/realm-config-review.md) — Terraform レビュー観点
3. **PR作成**
   - Day 4 の変更を branch にして PR
   - PR description に「何を・なぜ・どう検証したか」を書く
4. **レビューを受ける**
   - メンターからの指摘を反映
   - レビューでの議論を経験
5. **設計思想を読む (時間があれば)**
   - [docs/architecture.md](architecture.md) — このリポの主要な設計判断 (ADR)
   - [docs/customer-rollout.md](customer-rollout.md) — 新規顧客案件の立ち上げ方

### Day 5 終わりに

- [ ] PR が approved
- [ ] レビュー観点を把握、次回からは self-review でカバーできる
- [ ] 案件開始時に何をすべきかの全体像が見える

---

## 続けて学ぶ (任意)

### より深く

- Keycloak 公式 Server Developer Guide: https://www.keycloak.org/docs/latest/server_development/
- Keycloak Quickstarts: https://github.com/keycloak/keycloak-quickstarts
- Testcontainers ドキュメント: https://testcontainers.com/
- Playwright ドキュメント: https://playwright.dev/

### 関連トピック

- OAuth 2.0 / OIDC の RFC (RFC 6749, RFC 7519, OpenID Connect Core)
- SAML 2.0 (顧客連携で必要になる場合)
- LDAP / Active Directory (User Federation 案件)

---

## メンター向け補足

新メンバーの理解度確認ポイント:

| Day | 確認質問例 |
| --- | --- |
| Day 1 | 「Keycloakが何のためのもので、このDev環境は何を提供している?」 |
| Day 2 | 「単体テストとブラウザE2Eで、検証したい対象はどう違う?」 |
| Day 3 | 「`isDirectGrantFlow()` でフロー種別を判定している理由は?」 |
| Day 4 | 「自分が追加したテストは、どの分岐・どのシナリオをカバーしている?」 |
| Day 5 | 「新規案件が来たら、まず何をする?」 |

---

## 参考

- [README.md](../README.md) — 雛形リポの概要
- [CLAUDE.md](../CLAUDE.md) — 開発作業の詳細リファレンス
- [docs/testing.md](testing.md) — テスト方式ガイド
- [CONTRIBUTING.md](../CONTRIBUTING.md) — コントリビューション規約
- [docs/glossary.md](glossary.md) — Keycloak + プロジェクト用語集
