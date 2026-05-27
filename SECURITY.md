# Security Policy

このリポジトリにおけるセキュリティ方針と運用。

> 雛形リポ向け。顧客リポでは案件固有のセキュリティ要件 (PII取扱・コンプライアンス等) を別途定義する。

---

## 想定する脅威モデル

- **Secrets 漏洩** : `.env` / `.tfvars` / SPI内ハードコードからの認証情報流出
- **依存ライブラリの脆弱性** : Keycloak本体・Java/Node依存・Docker base image
- **設定ミス** : Realm/Client/Flow設定の不備による認可バイパス
- **本番 dev設定混入** : `direct_access_grants_enabled: true` や `ssl_required: none` の本番投入

---

## Secrets管理

### 大原則

**Git にcommitしてはいけないもの** :

- `.env` (.env.example はOK)
- `terraform.tfvars` (terraform.tfvars.example はOK)
- `compose.override.yaml` (`.example` はOK)
- 任意の `*.pem` / `*.key`
- Keycloak realm JSON で client_secret や IdP secret等を含むもの (export時はマスキング)
- Cookie・トークン・パスワード文字列

`.gitignore` で除外済みだが、PR時に再度目視確認すること。

### Secrets混入時の対応

1. **即座にrotateする** (該当secretを無効化・再発行)
2. Git history から除去 (`git filter-repo` または BFG Repo-Cleaner)
3. force pushで履歴を上書き
4. チーム周知 (今後のpullで影響する)
5. インシデント記録に残す

### 本番運用時のSecrets管理

dev環境は `.env` / `.tfvars` のローカル管理で良いが、本番では以下を検討:

- **HashiCorp Vault** : Terraform Provider for Vault と組み合わせ
- **AWS Secrets Manager / Parameter Store** : data source で参照
- **環境変数経由** : Kubernetes Secret / Docker Secret として注入
- **Sealed Secrets / SOPS** : Gitリポに暗号化済みで保管

---

## 依存ライブラリの管理

### Keycloak本体

- 採用バージョン: `26.0.x` 系 (Quarkus版)
- 更新ポリシー: パッチバージョンは **3ヶ月以内** に追従、メジャー/マイナーは半期で検討
- 新バージョンが出たら:
  1. Maven Centralで `org.keycloak:keycloak-core:NEW_VERSION` の存在確認
  2. `keycloak/providers/pom.xml` の `keycloak.version` と `.env` の `KEYCLOAK_VERSION` を同時更新
  3. 全層テスト (`make test-all && make test-e2e`) を通す
  4. CHANGELOGに記録

### Java依存

- Mockito: **5.15+** 必須 (JDK 24/25対応)
- Testcontainers: 1.19+
- AssertJ, JUnit: 5.10+
- 親POM (`keycloak/providers/pom.xml`) で集中管理

### Node.js依存

- `@playwright/test`: latest stable に追従
- `testcontainers` (Node): 10.x系
- `npm audit` で脆弱性を定期確認

### Docker base images

- `quay.io/keycloak/keycloak:26.0` : 上記Keycloak本体方針に従う
- `postgres:16-alpine` : Postgres 16系 latest patch
- `traefik:v3.1` : v3系 latest minor
- `maven:3.9-eclipse-temurin-17` (Dockerfile内): JDK 17 LTS で固定

### CVE追従

- [Keycloak Security Advisories](https://www.keycloak.org/security/) を定期確認
- 重大度Critical/High のCVEは1週間以内に patch versionにアップグレード
- Renovate / Dependabot の導入を推奨 (将来課題)

---

## 設定 (Realm/Terraform) のセキュリティ

詳細チェックリストは [docs/review-checklists/realm-config-review.md](docs/review-checklists/realm-config-review.md) 参照。

### 必ず守る

- 本番Realm の `ssl_required >= external`
- 本番Client の `direct_access_grants_enabled = false` (テスト用以外)
- `valid_redirect_uris` でワイルドカードを濫用しない
- `web_origins` で `*` を使わない
- Client Secret は terraform 自動生成、`output` は `sensitive = true`
- Realm admin の初期パスワードを必ず変更
- ブルートフォース保護 (`bruteForceProtected`) を有効化

### 本番デプロイ前チェック

- [ ] テスト用ユーザー (`testuser`, `testadmin`等) が含まれていない
- [ ] テスト用Client (`testing-only`等) が含まれていない
- [ ] `KC_BOOTSTRAP_ADMIN_PASSWORD` が `.env.example` のデフォルト値ではない
- [ ] 全Client の client_secret が rotate されている (前環境から流用していない)
- [ ] SMTP From アドレスが本番ドメイン

---

## SPI実装のセキュリティ

詳細は [docs/review-checklists/spi-review.md](docs/review-checklists/spi-review.md) 参照。

### 必ず守る

- 外部入力 (フォーム入力、リクエストヘッダ等) を検証なしで信頼しない
- ユーザー入力をログにそのまま出力しない (Log Injection)
- 例外メッセージにシステム内部情報を含めない (Information Disclosure)
- 認証エラー時に「ユーザーが存在しない」「パスワードが間違っている」を区別する応答にしない (Username Enumeration)
- Authenticator で必ず `setRequiredActions` を実装 (`configuredFor=false` 時の挙動を明確化)
- セキュリティ判断のロジックは fail-secure (エラー時は拒否側に倒す)

---

## E2E / IT テストのセキュリティ

- テストrealm JSONに本番相当のsecretsを書かない (テスト用ダミー値)
- Playwright trace ファイルにsecretsが含まれる可能性 → `e2e-tests/test-results/` は `.gitignore` 済み
- CI で trace artifact をアップロードする場合、 retention 期間を短く (1週間程度)

---

## Docker / カスタムイメージ

- `Dockerfile` の base image はバージョン固定 (タグ `latest` 禁止)
- マルチステージビルドで JDK/Maven をランタイムイメージから除外
- 本番イメージは non-root user で動作 (Keycloak公式イメージのデフォルト挙動を維持)
- イメージレジストリへの push 前に `docker scan` / `trivy` 等でスキャン

---

## ローカル開発環境

- 自己署名証明書 (`traefik/certs/local-cert.pem`) は **dev限定** で使う
- `KC_BOOTSTRAP_ADMIN_PASSWORD=admin` は **dev限定**、本番は強パスワード必須
- `make clean` でDB初期化できる前提で運用 (本番DB相当のデータを開発機に置かない)

---

## 脆弱性報告

このリポ (雛形リポ) または案件リポで脆弱性を発見した場合:

- **チーム内Slack** の `#security` チャンネル等の社内エスカレーションに連絡 (外部公開しない)
- 顧客環境への影響がある場合、即座に案件オーナー (熟練者) に通知
- 影響範囲調査 → 対応PR → リリース → 必要なら顧客通知 の手順を踏む

---

## 監査・ロギング

- Keycloak Event Listener で認証イベントを社内SIEMに送信 (案件次第)
- 管理コンソール操作は Admin Event Log に記録
- Terraform apply 履歴は CI ログに残す (誰が・いつ・何を変えたか追跡可能に)

---

## 関連ドキュメント

- [docs/testing.md](docs/testing.md) — テスト方式 + 既知の罠
- [docs/review-checklists/spi-review.md](docs/review-checklists/spi-review.md)
- [docs/review-checklists/realm-config-review.md](docs/review-checklists/realm-config-review.md)
- [Keycloak Security Advisories](https://www.keycloak.org/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
