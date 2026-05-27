# Admin Console Config テンプレ分割 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `docs/specs/task-specs/admin-console-config/` に Keycloak 管理コンソール設定カテゴリごとのデフォルト値付きテンプレ spec ファイル (10ファイル) を作成し、既存の一枚岩テンプレを deprecated にする。

**Architecture:** デザインドキュメント `docs/superpowers/specs/2026-05-28-admin-console-config-templates-design.md` に基づき、10セクションのテンプレを作成する。各ファイルは YAML frontmatter (`spec_id: TEMPLATE-ADMIN-*` / `status: template`) を持ち、`make spec-validate` で検証できる。

**Tech Stack:** Markdown + YAML frontmatter。コードなし。検証コマンド: `make spec-validate`

---

## File Map

| 操作 | パス |
|------|------|
| **Create** | `docs/specs/task-specs/admin-console-config/00-index.md` |
| **Create** | `docs/specs/task-specs/admin-console-config/01-realm-settings.md` |
| **Create** | `docs/specs/task-specs/admin-console-config/02-client-confidential.md` |
| **Create** | `docs/specs/task-specs/admin-console-config/03-client-public-spa.md` |
| **Create** | `docs/specs/task-specs/admin-console-config/04-client-service-account.md` |
| **Create** | `docs/specs/task-specs/admin-console-config/05-roles.md` |
| **Create** | `docs/specs/task-specs/admin-console-config/06-groups.md` |
| **Create** | `docs/specs/task-specs/admin-console-config/07-identity-provider.md` |
| **Create** | `docs/specs/task-specs/admin-console-config/08-auth-flow.md` |
| **Create** | `docs/specs/task-specs/admin-console-config/09-smtp.md` |
| **Modify** | `docs/specs/task-specs/01-admin-console-config-template.md` (deprecated に変更) |
| **Delete** | `docs/specs/task-specs/admin-conole-config/` (typo ディレクトリを削除) |

---

## Task 1: ディレクトリ作成と 00-index.md

**Files:**
- Create: `docs/specs/task-specs/admin-console-config/00-index.md`
- Delete: `docs/specs/task-specs/admin-conole-config/` (typo)

- [ ] **Step 1: typo ディレクトリを削除して正しいディレクトリを作成**

```bash
rmdir docs/specs/task-specs/admin-conole-config
mkdir -p docs/specs/task-specs/admin-console-config
```

- [ ] **Step 2: 00-index.md を作成**

`docs/specs/task-specs/admin-console-config/00-index.md` に以下を書く:

```markdown
---
spec_id: TEMPLATE-ADMIN-INDEX
title: 管理コンソール設定テンプレ — 使い方ガイド
status: template
---

# 管理コンソール設定テンプレ — 使い方ガイド

このディレクトリには Keycloak 管理コンソールの設定カテゴリごとのテンプレが入っています。
各ファイルは **デフォルト値が記入済み** で、案件ごとに変更が必要な箇所だけ上書きして使います。

## 使い方フロー

```
1. 必要なテンプレファイルを docs/specs/task-specs/<案件名>/ にコピー
2. 各ファイルの「*(入力必須)*」欄を埋める
3. デフォルト値を変えたい行の「デフォルト値」列だけを上書きする
4. Claude に渡して Terraform を生成させる
   → writing-keycloak-realm-terraform スキルを使用
```

## テンプレ一覧

| ファイル | spec_id | カバーする設定 |
|---------|---------|-------------|
| [01-realm-settings.md](01-realm-settings.md) | `TEMPLATE-ADMIN-REALM-SETTINGS` | Realm基本・ログイン・パスワードポリシー・セッション/トークン |
| [02-client-confidential.md](02-client-confidential.md) | `TEMPLATE-ADMIN-CLIENT-CONFIDENTIAL` | Confidentialクライアント (Auth Code + Refresh Token) |
| [03-client-public-spa.md](03-client-public-spa.md) | `TEMPLATE-ADMIN-CLIENT-PUBLIC-SPA` | Public SPAクライアント (PKCE) |
| [04-client-service-account.md](04-client-service-account.md) | `TEMPLATE-ADMIN-CLIENT-SERVICE-ACCOUNT` | Service Accountクライアント (Client Credentials) |
| [05-roles.md](05-roles.md) | `TEMPLATE-ADMIN-ROLES` | Realm Role / Client Role |
| [06-groups.md](06-groups.md) | `TEMPLATE-ADMIN-GROUPS` | グループ構造 |
| [07-identity-provider.md](07-identity-provider.md) | `TEMPLATE-ADMIN-IDENTITY-PROVIDER` | 外部IdP (Google / Azure AD / SAML) |
| [08-auth-flow.md](08-auth-flow.md) | `TEMPLATE-ADMIN-AUTH-FLOW` | 認証フローカスタマイズ (SPI パターン参照) |
| [09-smtp.md](09-smtp.md) | `TEMPLATE-ADMIN-SMTP` | メール/SMTP設定 |

## テーブル列の読み方

| 列名 | 説明 |
|------|------|
| 項目 | Keycloak の設定項目名 |
| デフォルト値 | このテンプレが推奨するデフォルト。`*(入力必須)*` は案件ごとに必ず記入 |
| 変更する場合の条件 | デフォルト値を変えるときの根拠・条件。**変更不可** はセキュリティ要件で固定 |
| Terraform 対応キー | `keycloak/keycloak` provider のリソース属性名 |

## 廃止されたテンプレ

旧テンプレ `01-admin-console-config-template.md` は deprecated です。
このディレクトリのファイルを使ってください。
```

- [ ] **Step 3: spec-validate で frontmatter を確認**

```bash
cd /path/to/keycloak-dev && make spec-validate 2>&1 | grep -E "(TEMPLATE-ADMIN-INDEX|ERROR|WARN)"
```

Expected: `TEMPLATE-ADMIN-INDEX` が listed され ERROR なし

- [ ] **Step 4: コミット**

```bash
git add docs/specs/task-specs/admin-console-config/00-index.md
git rm -r docs/specs/task-specs/admin-conole-config/
git commit -m "feat(spec): admin-console-config テンプレディレクトリを作成 (00-index)"
```

---

## Task 2: 01-realm-settings.md

**Files:**
- Create: `docs/specs/task-specs/admin-console-config/01-realm-settings.md`

- [ ] **Step 1: ファイルを作成**

```markdown
---
spec_id: TEMPLATE-ADMIN-REALM-SETTINGS
title: Realm 設定テンプレ (デフォルト値付き)
status: template
---

# Realm 設定テンプレ

案件ごとに `*(入力必須)*` 欄を埋め、変えたい行の「デフォルト値」列を上書きしてください。

## 基本情報

| 項目 | 値 |
|------|----|
| 案件名 / 顧客名 | *(入力必須)* |
| Realm 名 (英小文字 kebab-case) | *(入力必須)* (例: acme-corp) |
| Keycloak バージョン | *(入力必須)* (例: 26.0.8) |

## 1. Realm 基本設定

| 項目 | デフォルト値 | 変更する場合の条件 | Terraform 対応キー |
|------|------------|-----------------|------------------|
| 表示名 | *(入力必須)* | — | `display_name` |
| SSL 要件 | `external` | 完全閉域網のみ → `none`、全通信 TLS 必須 → `all` | `ssl_required` |
| ユーザー自己登録 | `false` | 一般公開 B2C サービス → `true` | `registration_allowed` |
| メールでログイン | `true` | — | `login_with_email_allowed` |
| パスワードリセット | `true` | — | `reset_password_allowed` |
| Remember Me | `false` | セキュリティ要件が緩い B2C → `true` | `remember_me` |
| メール検証必須 | `true` | dev 環境 → `false` 可 (本番は `true` 固定) | `verify_email` |
| ブルートフォース保護 | `true` | **変更不可** (セキュリティ必須) | `brute_force_protected` |

## 2. パスワードポリシー

> Terraform では `password_policy` を文字列で渡す。例: `"length(12) and upperCase(1) and digits(1) and specialChars(1) and notUsername() and passwordHistory(5)"`

| 項目 | デフォルト値 | 変更する場合の条件 |
|------|------------|-----------------|
| 最小文字長 | `12` | 規制業界 (金融・医療) → `16` 以上推奨 |
| 大文字必須 | `true` | — |
| 数字必須 | `true` | — |
| 特殊文字必須 | `true` | — |
| ユーザー名を含まない | `true` | **変更不可** |
| ハッシュアルゴリズム | `pbkdf2-sha256` | 高セキュリティ要件 → `argon2` (CPU コスト増) |
| パスワード履歴 | `5` (過去5回) | 規制業界 → `10` 以上推奨 |

## 3. セッション / トークン期限

| 項目 | デフォルト値 | 変更する場合の条件 | Terraform 対応キー |
|------|------------|-----------------|------------------|
| Access Token Lifespan | `300` (5分) | B2C 利便性重視 → `900` (15分)、金融/医療 → `60` (1分) | `access_token_lifespan` |
| SSO Session Idle Timeout | `1800` (30分) | — | `sso_session_idle_timeout` |
| SSO Session Max Lifespan | `36000` (10時間) | 金融/医療 → `3600` (1時間) 以下を推奨 | `sso_session_max_lifespan` |
| Offline Session Idle | `2592000` (30日) | セキュリティ要件に応じて短縮 | `offline_session_idle_timeout` |
| Offline Session Max | `5184000` (60日) | — | `offline_session_max_lifespan` |
```

- [ ] **Step 2: コミット**

```bash
git add docs/specs/task-specs/admin-console-config/01-realm-settings.md
git commit -m "feat(spec): TEMPLATE-ADMIN-REALM-SETTINGS を追加"
```

---

## Task 3: 02-client-confidential.md

**Files:**
- Create: `docs/specs/task-specs/admin-console-config/02-client-confidential.md`

- [ ] **Step 1: ファイルを作成**

```markdown
---
spec_id: TEMPLATE-ADMIN-CLIENT-CONFIDENTIAL
title: Confidential クライアント設定テンプレ (デフォルト値付き)
status: template
---

# Confidential クライアント設定テンプレ

**用途**: server-side で `client_secret` を安全に保持できるアプリ。
Web アプリのサーバサイド、BFF、バックエンド API 連携に利用。

Terraform モジュール: `terraform/modules/client-confidential`

クライアントが複数ある場合はこのテンプレを複製して使用。

---

## Client 設定

| 項目 | デフォルト値 | 変更する場合の条件 | Terraform 対応キー |
|------|------------|-----------------|------------------|
| Client ID | *(入力必須)* (例: web-app) | — | `client_id` |
| 表示名 | *(入力必須)* | — | `name` |
| Client Secret | 自動生成 | **直書き不可** (Terraform で `sensitive` 変数) | `client_secret` |
| Standard Flow (Auth Code) | `true` | **変更不可** | `standard_flow_enabled` |
| Implicit Flow | `false` | **変更不可** (非推奨フロー) | `implicit_flow_enabled` |
| Direct Access Grants | `false` | 開発・テスト用途のみ `true` (本番は `false` 必須) | `direct_access_grants_enabled` |
| Service Account | `false` | Confidential + Service Account 兼任が必要な場合 → `true` | `service_accounts_enabled` |
| Valid Redirect URIs | *(入力必須)* (例: `["https://app.example.com/*"]`) | — | `valid_redirect_uris` |
| Web Origins | *(入力必須)* (例: `["https://app.example.com"]`) | — | `web_origins` |
| Post Logout Redirect URI | *(入力必須)* (例: `https://app.example.com`) | — | `attributes.post.logout.redirect.uris` |
| Access Token Lifespan (Override) | Realm デフォルトを継承 | クライアント固有で短縮する場合のみ設定 (秒) | `access_token_lifespan` |

## スコープ設定

| スコープ | デフォルト | 変更条件 |
|---------|-----------|--------|
| openid | デフォルト追加 | — |
| profile | デフォルト追加 | — |
| email | デフォルト追加 | — |
| offline_access | オプション | Refresh Token (長期) が必要な場合はデフォルトへ移動 |
| phone | オプション | 電話番号属性が必要な場合のみ |

## 設計判断メモ (案件ごとに記入)

- **このクライアントを confidential にした理由**: (記入)
- **Direct Access Grants を有効化した場合の理由**: (本番では必ず無効化すること)
- **Redirect URIs の wildcard 方針**: 末尾 `/*` のみ使用、ホスト部分の wildcard は使わない
```

- [ ] **Step 2: コミット**

```bash
git add docs/specs/task-specs/admin-console-config/02-client-confidential.md
git commit -m "feat(spec): TEMPLATE-ADMIN-CLIENT-CONFIDENTIAL を追加"
```

---

## Task 4: 03-client-public-spa.md

**Files:**
- Create: `docs/specs/task-specs/admin-console-config/03-client-public-spa.md`

- [ ] **Step 1: ファイルを作成**

```markdown
---
spec_id: TEMPLATE-ADMIN-CLIENT-PUBLIC-SPA
title: Public SPA クライアント設定テンプレ (デフォルト値付き)
status: template
---

# Public SPA クライアント設定テンプレ

**用途**: ブラウザ上で動作する SPA (React / Vue / Angular 等)。
`client_secret` を安全に保持できないため Public Client として設定し PKCE を必須にする。

Terraform モジュール: `terraform/modules/client-public-spa`

---

## Client 設定

| 項目 | デフォルト値 | 変更する場合の条件 | Terraform 対応キー |
|------|------------|-----------------|------------------|
| Client ID | *(入力必須)* (例: spa-frontend) | — | `client_id` |
| 表示名 | *(入力必須)* | — | `name` |
| Public Client | `true` | **変更不可** (SPA は常に Public) | `public_client` |
| PKCE Code Challenge Method | `S256` | **変更不可** (S256 のみ許可) | `pkce_code_challenge_method` |
| Standard Flow (Auth Code) | `true` | **変更不可** | `standard_flow_enabled` |
| Implicit Flow | `false` | **変更不可** (非推奨) | `implicit_flow_enabled` |
| Direct Access Grants | `false` | **変更不可** (SPA では使用不可) | `direct_access_grants_enabled` |
| Service Account | `false` | **変更不可** | `service_accounts_enabled` |
| Valid Redirect URIs | *(入力必須)* (例: `["https://spa.example.com/*"]`) | — | `valid_redirect_uris` |
| Web Origins | *(入力必須)* (例: `["https://spa.example.com"]`) | CORS 対象ドメイン | `web_origins` |
| Post Logout Redirect URI | *(入力必須)* | — | `attributes.post.logout.redirect.uris` |

## スコープ設定

| スコープ | デフォルト | 変更条件 |
|---------|-----------|--------|
| openid | デフォルト追加 | — |
| profile | デフォルト追加 | — |
| email | デフォルト追加 | — |
| offline_access | オプション | Silent Refresh が不要で Refresh Token を使う場合 |

## 設計判断メモ (案件ごとに記入)

- **PKCE 必須**: Authorization Code + PKCE が SPA のセキュリティベースライン (RFC 9700)
- **Redirect URIs**: ローカル開発用 `http://localhost:*` は本番デプロイ前に削除すること
```

- [ ] **Step 2: コミット**

```bash
git add docs/specs/task-specs/admin-console-config/03-client-public-spa.md
git commit -m "feat(spec): TEMPLATE-ADMIN-CLIENT-PUBLIC-SPA を追加"
```

---

## Task 5: 04-client-service-account.md

**Files:**
- Create: `docs/specs/task-specs/admin-console-config/04-client-service-account.md`

- [ ] **Step 1: ファイルを作成**

```markdown
---
spec_id: TEMPLATE-ADMIN-CLIENT-SERVICE-ACCOUNT
title: Service Account クライアント設定テンプレ (デフォルト値付き)
status: template
---

# Service Account クライアント設定テンプレ

**用途**: バックグラウンドジョブ・バッチ処理・M2M 通信など、ユーザーが介在しないシステム間連携。
Client Credentials Grant (`grant_type=client_credentials`) を使用。

Terraform モジュール: `terraform/modules/client-service-account`

---

## Client 設定

| 項目 | デフォルト値 | 変更する場合の条件 | Terraform 対応キー |
|------|------------|-----------------|------------------|
| Client ID | *(入力必須)* (例: batch-worker) | — | `client_id` |
| 表示名 | *(入力必須)* | — | `name` |
| Client Secret | 自動生成 | **直書き不可** (Vault / Secret Manager から注入) | `client_secret` |
| Public Client | `false` | **変更不可** (Service Account は常に Confidential) | `public_client` |
| Standard Flow | `false` | **変更不可** (ユーザーフローは不要) | `standard_flow_enabled` |
| Implicit Flow | `false` | **変更不可** | `implicit_flow_enabled` |
| Direct Access Grants | `false` | **変更不可** | `direct_access_grants_enabled` |
| Service Account | `true` | **変更不可** | `service_accounts_enabled` |

## Service Account ロール割り当て

| ロール | デフォルト | 変更条件 |
|-------|-----------|--------|
| Realm Role | *(入力必須)* | このクライアントが使うロールを明示 |
| Client Role | *(必要な場合のみ入力)* | — |

## 設計判断メモ (案件ごとに記入)

- **最小権限の原則**: 必要なロールのみ付与、`realm-admin` 等の強力なロールを避ける
- **Secret ローテーション**: Keycloak 管理 UI または `kcadm.sh` で定期ローテーション
- **Token Lifespan**: Service Account の Access Token はデフォルト 5分。長時間バッチの場合は `access_token_lifespan` を延ばすか、Token を都度取り直すロジックにする
```

- [ ] **Step 2: コミット**

```bash
git add docs/specs/task-specs/admin-console-config/04-client-service-account.md
git commit -m "feat(spec): TEMPLATE-ADMIN-CLIENT-SERVICE-ACCOUNT を追加"
```

---

## Task 6: 05-roles.md

**Files:**
- Create: `docs/specs/task-specs/admin-console-config/05-roles.md`

- [ ] **Step 1: ファイルを作成**

```markdown
---
spec_id: TEMPLATE-ADMIN-ROLES
title: ロール設定テンプレ (デフォルト値付き)
status: template
---

# ロール設定テンプレ

## Realm Role

| Role 名 | 説明 | 新規ユーザーへの自動付与 | Terraform リソース |
|---------|------|----------------------|------------------|
| `user` | 一般ユーザー | `true` (default role) | `keycloak_role` |
| `admin` | 管理者 | `false` | `keycloak_role` |
| *(追加がある場合はここに列を追加)* | | | |

> **変更条件**: ロール構成は要件に応じて自由に変更可。
> `user` ロールを default role にするのはほとんどの B2B/B2C 案件で有効。
> RBAC が不要な場合はロールを作らなくてよい。

## Client Role (Client ごとに記入、必要な場合のみ)

| Client ID | Role 名 | 説明 |
|-----------|---------|------|
| *(Client ID)* | *(Role 名)* | *(説明)* |

> **変更条件**: Client Role は fine-grained なアクセス制御が必要な場合のみ使用。
> Realm Role だけで要件が満たせる場合は Client Role を作らない (シンプルさを優先)。

## 設計判断メモ (案件ごとに記入)

- **ロール設計の方針**: (例: Realm Role のみで管理、Client Role は不使用)
- **default role の選択**: (例: `user` を default role にした理由)
```

- [ ] **Step 2: コミット**

```bash
git add docs/specs/task-specs/admin-console-config/05-roles.md
git commit -m "feat(spec): TEMPLATE-ADMIN-ROLES を追加"
```

---

## Task 7: 06-groups.md

**Files:**
- Create: `docs/specs/task-specs/admin-console-config/06-groups.md`

- [ ] **Step 1: ファイルを作成**

```markdown
---
spec_id: TEMPLATE-ADMIN-GROUPS
title: グループ設定テンプレ (デフォルト値付き)
status: template
---

# グループ設定テンプレ

> **使用判断**: ユーザーを組織単位で管理したい場合、または Role 割り当てを一括管理したい場合に使用。
> グループが不要な案件はこのファイルをコピーせず、Claude に「グループなし」と伝えてください。

## グループ構造

| グループ名 | 親グループ | デフォルト付与 Role | 説明 |
|-----------|----------|------------------|------|
| *(入力必須)* | *(なし / 親グループ名)* | *(Role 名 または なし)* | *(説明)* |

> **変更条件**: グループ階層は案件の組織構造に合わせて自由に設計。
> 階層が深い (3 階層以上) 場合は運用コストが上がるため、フラット構造を推奨。

## 設計判断メモ (案件ごとに記入)

- **グループを使う理由**: (例: 部署ごとにアクセス制御が異なるため)
- **Role との関係**: (例: グループに Role を付与してユーザーは Role を直接持たない)
```

- [ ] **Step 2: コミット**

```bash
git add docs/specs/task-specs/admin-console-config/06-groups.md
git commit -m "feat(spec): TEMPLATE-ADMIN-GROUPS を追加"
```

---

## Task 8: 07-identity-provider.md

**Files:**
- Create: `docs/specs/task-specs/admin-console-config/07-identity-provider.md`

- [ ] **Step 1: ファイルを作成**

```markdown
---
spec_id: TEMPLATE-ADMIN-IDENTITY-PROVIDER
title: 外部 IdP 連携設定テンプレ (デフォルト値付き)
status: template
---

# 外部 IdP 連携設定テンプレ

> **使用判断**: Google / Azure AD / 社内 SAML 等の外部 IdP と連携する場合のみこのファイルをコピー。
> 外部 IdP 連携が不要な案件はこのファイルを使わない。

IdP が複数ある場合は「## IdP 設定」セクションを複製してください。

## IdP 設定

| 項目 | デフォルト値 | 変更する場合の条件 | Terraform 対応キー |
|------|------------|-----------------|------------------|
| 種別 | *(入力必須)* (google / oidc / saml / azure-ad) | — | `provider_id` |
| Alias | *(入力必須)* (例: google) | URL の一部になる。変更時はユーザーの紐づけが壊れる | `alias` |
| 表示名 | *(入力必須)* (例: Google でログイン) | — | `display_name` |
| Client ID | *(入力必須)* | — | `extra_config.clientId` |
| Client Secret | **Vault 参照** (tfvars に直書き不可) | — | `extra_config.clientSecret` |
| Issuer URL (OIDC) | *(入力必須。SAML の場合は不要)* | — | `extra_config.issuer` |
| メタデータ URL (SAML) | *(入力必須。OIDC の場合は不要)* | — | `extra_config.metadataDescriptorUrl` |
| 初回ログイン時のフロー | `first broker login` | 既存ユーザーと自動紐づけが必要 → `detect existing broker user` | `first_broker_login_flow_alias` |
| ユーザー自動作成 | `true` | IdP 認証済みユーザーのみ受け入れる → `false` + 手動プロビジョニング | `store_token` |

## 属性マッピング

| IdP 属性 | Keycloak 属性 | デフォルト設定 |
|---------|-------------|------------|
| `email` | `email` | 自動マッピング |
| `name` | `firstName` / `lastName` | 自動マッピング (IdP による) |
| *(追加属性)* | *(Keycloak 属性名)* | *(必要な場合のみ追加)* |

## 設計判断メモ (案件ごとに記入)

- **IdP を選んだ理由**: (例: 顧客が Google Workspace を使っているため)
- **Alias を変えない方針**: Alias はログイン後の内部 ID に影響するため、一度決めたら変更しない
- **Client Secret の管理**: (例: GitHub Actions Secret / Vault / AWS Secrets Manager)
```

- [ ] **Step 2: コミット**

```bash
git add docs/specs/task-specs/admin-console-config/07-identity-provider.md
git commit -m "feat(spec): TEMPLATE-ADMIN-IDENTITY-PROVIDER を追加"
```

---

## Task 9: 08-auth-flow.md

**Files:**
- Create: `docs/specs/task-specs/admin-console-config/08-auth-flow.md`

- [ ] **Step 1: ファイルを作成**

```markdown
---
spec_id: TEMPLATE-ADMIN-AUTH-FLOW
title: 認証フロー設定テンプレ (デフォルト値付き)
status: template
---

# 認証フロー設定テンプレ

> **使用判断**: カスタム認証フロー (SPI Authenticator) が必要な場合のみこのファイルをコピー。
> 標準フロー (Keycloak デフォルト) で要件が満たせる場合は不要。

## フロー設定

| 項目 | デフォルト値 | 変更する場合の条件 | 備考 |
|------|------------|-----------------|------|
| カスタムフロー使用 | `false` | 下記いずれかに該当する場合 → `true` | — |
| 適用先フロー | — | `browser` / `direct-grant` / `reset-credentials` のいずれか | — |

**カスタムフローが必要な典型的ケース:**
- メールドメイン制限 (特定ドメインのみログイン許可)
- TOTP / WebAuthn の独自フロー
- 外部サービスとの連携検証 (IP制限、ライセンス確認など)

## 使用する SPI パターン

| パターン | spec_id | 適用先フロー |
|---------|---------|-----------|
| *(使用するパターンを選択)* | *(例: PATTERN-AUTH-DOMAIN-ALLOWLIST)* | *(例: browser)* |

利用可能なパターン一覧: [docs/specs/patterns/](../patterns/)

> **変更条件**: SPI パターンが既存のものでカバーできない場合は `02-spi-customization` task-spec を別途起票して新パターンを実装する。

## 設計判断メモ (案件ごとに記入)

- **カスタムフローを選んだ理由**: (記入)
- **適用先フローの選定理由**: (例: browser フローのみに適用し direct-grant には適用しない理由)
```

- [ ] **Step 2: コミット**

```bash
git add docs/specs/task-specs/admin-console-config/08-auth-flow.md
git commit -m "feat(spec): TEMPLATE-ADMIN-AUTH-FLOW を追加"
```

---

## Task 10: 09-smtp.md

**Files:**
- Create: `docs/specs/task-specs/admin-console-config/09-smtp.md`

- [ ] **Step 1: ファイルを作成**

```markdown
---
spec_id: TEMPLATE-ADMIN-SMTP
title: SMTP 設定テンプレ (デフォルト値付き)
status: template
---

# SMTP 設定テンプレ

> **使用判断**: Keycloak からメール送信 (パスワードリセット、メール検証等) が必要な場合に使用。
> メール送信不要な案件はこのファイルを使わない。

## SMTP 設定

| 項目 | デフォルト値 | 変更する場合の条件 | Terraform 対応キー |
|------|------------|-----------------|------------------|
| Host | *(入力必須)* (dev: `mailhog`) | — | `host` |
| Port | `587` | dev 環境 (Mailhog) → `1025`、SSL 使用 → `465` | `port` |
| From アドレス | *(入力必須)* (例: noreply@example.com) | — | `from` |
| From 表示名 | *(入力必須)* (例: Example Corp) | — | `from_display_name` |
| 認証有効 | `true` | dev 環境 (Mailhog) → `false` | `auth` |
| STARTTLS | `true` | SSL (port 465) を使う場合 → STARTTLS `false`、SSL `true` | `starttls` |
| SSL | `false` | port 465 使用時 → `true` | `ssl` |
| Username | *(入力必須)* | dev 環境 → 空欄 可 | `user` |
| Password | **Vault 参照** (tfvars に直書き不可) | — | `password` |
| Reply-To | *(省略可)* | サポート窓口への返信が必要な場合に設定 | `reply_to` |

## 環境別設定の例

| 環境 | Host | Port | Auth | STARTTLS |
|------|------|------|------|---------|
| dev (Mailhog) | `mailhog` | `1025` | `false` | `false` |
| staging | *(本番と同じ SMTP サーバを推奨)* | `587` | `true` | `true` |
| production | *(入力必須)* | `587` | `true` | `true` |

## 設計判断メモ (案件ごとに記入)

- **SMTP サービスの選定**: (例: AWS SES / SendGrid / 社内 SMTP)
- **Password 管理**: (例: GitHub Actions Secret / Vault)
```

- [ ] **Step 2: コミット**

```bash
git add docs/specs/task-specs/admin-console-config/09-smtp.md
git commit -m "feat(spec): TEMPLATE-ADMIN-SMTP を追加"
```

---

## Task 11: 既存テンプレを deprecated に更新

**Files:**
- Modify: `docs/specs/task-specs/01-admin-console-config-template.md`

- [ ] **Step 1: frontmatter の status を deprecated に変更し、deprecation notice を追加**

`docs/specs/task-specs/01-admin-console-config-template.md` の先頭を以下に変更:

```markdown
---
spec_id: TEMPLATE-TASK-ADMIN-CONSOLE
title: 管理コンソール設定 task-spec テンプレ (非推奨)
status: deprecated
---

> **⚠️ このファイルは deprecated です。**
> 代わりに [`docs/specs/task-specs/admin-console-config/`](admin-console-config/) のテンプレを使用してください。
> デフォルト値付きでカテゴリごとに分割されています。

---

```

(以降の既存本文はそのまま残す)

- [ ] **Step 2: コミット**

```bash
git add docs/specs/task-specs/01-admin-console-config-template.md
git commit -m "feat(spec): 旧 admin-console-config テンプレを deprecated に変更"
```

---

## Task 12: spec-validate で全体検証

- [ ] **Step 1: spec-validate を実行**

```bash
make spec-validate
```

Expected output (抜粋):
```
TEMPLATE-ADMIN-INDEX           template  OK
TEMPLATE-ADMIN-REALM-SETTINGS  template  OK
TEMPLATE-ADMIN-CLIENT-CONFIDENTIAL template OK
TEMPLATE-ADMIN-CLIENT-PUBLIC-SPA   template OK
TEMPLATE-ADMIN-CLIENT-SERVICE-ACCOUNT template OK
TEMPLATE-ADMIN-ROLES           template  OK
TEMPLATE-ADMIN-GROUPS          template  OK
TEMPLATE-ADMIN-IDENTITY-PROVIDER template OK
TEMPLATE-ADMIN-AUTH-FLOW       template  OK
TEMPLATE-ADMIN-SMTP            template  OK
TEMPLATE-TASK-ADMIN-CONSOLE    deprecated OK
```

ERROR が出た場合: frontmatter の spec_id / status の typo を修正して再実行。

- [ ] **Step 2: 最終コミット (エラー修正があった場合)**

```bash
git add -A
git commit -m "fix(spec): spec-validate エラーを修正"
```
