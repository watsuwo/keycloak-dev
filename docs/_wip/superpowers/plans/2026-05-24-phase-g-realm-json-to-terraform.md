# Phase G Implementation Plan — case-spec → Terraform HCL

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** case-spec を SoT として `terraform/environments/<案件>/{dev,stg,prod}/` の HCL を生成できるようにする (skill 化 + 例実装 + 旧構成廃止)。

**Architecture:** 既存 `writing-keycloak-realm-terraform` skill を case-spec ベースに書き換え。client spec に `env:` ブロックを追加し env 差分を表現。`terraform/modules/` に public-spa / service-account モジュールを新設し、`terraform/environments/example-customer/{dev,stg,prod}/` を生成して `terraform validate` で検証。

**Tech Stack:** Terraform 1.x, keycloak/keycloak provider ~> 5.0, Markdown + YAML spec, Docker Compose (Keycloak 26)

---

## File Structure

**新規 / 変更ファイル**:

| パス | 操作 | 責務 |
|---|---|---|
| `docs/specs/templates/case-client-confidential-template.md` | Modify | `env:` ブロック例を追記 |
| `docs/specs/templates/case-client-public-spa-template.md` | Modify | `env:` ブロック例を追記 |
| `docs/specs/templates/case-client-service-account-template.md` | Modify | `env:` ブロック例 (空想定) を追記 |
| `docs/specs/cases/example-customer/clients/web-app.md` | Modify | `env: stg/prod` 追加 + `implementations:` に HCL 3パス追記 |
| `docs/specs/cases/example-customer/clients/spa-frontend.md` | Modify | 同上 |
| `docs/specs/cases/example-customer/clients/batch-worker.md` | Modify | `implementations:` に HCL 3パス追記 (env 差分なし) |
| `terraform/modules/client-confidential/main.tf` | Modify | `extra_config` (=attributes) variable サポート追加 |
| `terraform/modules/client-confidential/variables.tf` | Modify | 同上 |
| `terraform/modules/client-public-spa/{main.tf,variables.tf,outputs.tf,README.md}` | Create | public client (PKCE 前提) module |
| `terraform/modules/client-service-account/{main.tf,variables.tf,outputs.tf,README.md}` | Create | service account client module |
| `terraform/environments/example-customer/main.tf` | Delete | 旧 task-spec 構造 |
| `terraform/environments/example-customer/variables.tf` | Delete | 同上 |
| `terraform/environments/example-customer/outputs.tf` | Delete | 同上 |
| `terraform/environments/example-customer/terraform.tfvars.example` | Delete | 同上 |
| `terraform/environments/example-customer/README.md` | Replace | env 別構造の案内 |
| `terraform/environments/example-customer/dev/{main.tf,variables.tf,terraform.tfvars.example,README.md}` | Create | dev env HCL |
| `terraform/environments/example-customer/stg/{main.tf,variables.tf,terraform.tfvars.example,README.md}` | Create | stg env HCL |
| `terraform/environments/example-customer/prod/{main.tf,variables.tf,terraform.tfvars.example,README.md}` | Create | prod env HCL |
| `.claude/skills/writing-keycloak-realm-terraform/SKILL.md` | Replace | case-spec + env 引数 ベース新仕様 |
| `terraform/CLAUDE.md` | Modify | env 別ディレクトリ構造への変更を反映 |
| `memory/project_phase_f_realm_json.md` (Claude memory) | Modify | Phase G 完了を記録 |

---

## Task 1: client-confidential module に extra_config (attributes) サポート追加

**Files:**
- Modify: `terraform/modules/client-confidential/main.tf`
- Modify: `terraform/modules/client-confidential/variables.tf`

- [ ] **Step 1: variables.tf に extra_config 変数追加**

`terraform/modules/client-confidential/variables.tf` の末尾に追記:

```hcl
variable "extra_config" {
  type        = map(string)
  description = "Client attributes (例: post.logout.redirect.uris, access.token.lifespan)。Keycloak の Attributes に対応"
  default     = {}
}
```

- [ ] **Step 2: main.tf で extra_config を渡す**

`terraform/modules/client-confidential/main.tf` の `resource "keycloak_openid_client" "this"` ブロック内、`client_secret` 行の直後に追記:

```hcl
  extra_config = var.extra_config
```

- [ ] **Step 3: モジュール単体で validate**

```bash
cd terraform/modules/client-confidential && terraform init -backend=false && terraform validate
cd -
```
Expected: `Success! The configuration is valid.`

- [ ] **Step 4: Commit**

```bash
git add terraform/modules/client-confidential/
git commit -m "feat(terraform): add extra_config var to client-confidential module"
```

---

## Task 2: client-public-spa module 新設

**Files:**
- Create: `terraform/modules/client-public-spa/main.tf`
- Create: `terraform/modules/client-public-spa/variables.tf`
- Create: `terraform/modules/client-public-spa/outputs.tf`
- Create: `terraform/modules/client-public-spa/README.md`

- [ ] **Step 1: variables.tf 作成**

```hcl
variable "realm_id" {
  type        = string
  description = "Realm の ID (keycloak_realm.<name>.id を渡す)"
}

variable "client_id" {
  type        = string
  description = "OIDC client_id (例: \"spa-frontend\")"
}

variable "name" {
  type        = string
  description = "Client の表示名"
  default     = null
}

variable "valid_redirect_uris" {
  type        = list(string)
  description = "許可するリダイレクトURI"
  default     = []
}

variable "web_origins" {
  type        = list(string)
  description = "CORS許可Origin"
  default     = []
}

variable "extra_config" {
  type        = map(string)
  description = "Client attributes"
  default     = {}
}
```

- [ ] **Step 2: main.tf 作成**

```hcl
terraform {
  required_providers {
    keycloak = {
      source  = "keycloak/keycloak"
      version = "~> 5.0"
    }
  }
}

resource "keycloak_openid_client" "this" {
  realm_id    = var.realm_id
  client_id   = var.client_id
  name        = var.name
  enabled     = true
  access_type = "PUBLIC"

  standard_flow_enabled        = true
  direct_access_grants_enabled = false
  service_accounts_enabled     = false
  implicit_flow_enabled        = false

  valid_redirect_uris = var.valid_redirect_uris
  web_origins         = var.web_origins

  extra_config = var.extra_config

  # PKCE 必須 (public client の security baseline)
  pkce_code_challenge_method = "S256"
}
```

- [ ] **Step 3: outputs.tf 作成**

```hcl
output "client_uuid" {
  description = "Keycloak内部UUID"
  value       = keycloak_openid_client.this.id
}

output "client_id" {
  description = "OIDC client_id"
  value       = keycloak_openid_client.this.client_id
}
```

- [ ] **Step 4: README.md 作成**

```markdown
# client-public-spa module

ブラウザ SPA 向け Public Client (PKCE 必須)。secret を持たない。

## 使い方

\`\`\`hcl
module "spa" {
  source              = "../../../modules/client-public-spa"
  realm_id            = keycloak_realm.this.id
  client_id           = "spa-frontend"
  name                = "Example SPA"
  valid_redirect_uris = ["https://app.example.com/*"]
  web_origins         = ["https://app.example.com"]
}
\`\`\`
```

- [ ] **Step 5: モジュール validate**

```bash
cd terraform/modules/client-public-spa && terraform init -backend=false && terraform validate
cd -
```
Expected: `Success! The configuration is valid.`

- [ ] **Step 6: Commit**

```bash
git add terraform/modules/client-public-spa/
git commit -m "feat(terraform): add client-public-spa module"
```

---

## Task 3: client-service-account module 新設

**Files:**
- Create: `terraform/modules/client-service-account/main.tf`
- Create: `terraform/modules/client-service-account/variables.tf`
- Create: `terraform/modules/client-service-account/outputs.tf`
- Create: `terraform/modules/client-service-account/README.md`

- [ ] **Step 1: variables.tf 作成**

```hcl
variable "realm_id" {
  type        = string
  description = "Realm の ID"
}

variable "client_id" {
  type        = string
  description = "OIDC client_id (例: \"batch-worker\")"
}

variable "name" {
  type        = string
  description = "Client の表示名"
  default     = null
}

variable "client_secret" {
  type        = string
  description = "Client Secret (null で Keycloak 自動生成 — 推奨)"
  default     = null
  sensitive   = true
}

variable "extra_config" {
  type        = map(string)
  description = "Client attributes"
  default     = {}
}
```

- [ ] **Step 2: main.tf 作成**

```hcl
terraform {
  required_providers {
    keycloak = {
      source  = "keycloak/keycloak"
      version = "~> 5.0"
    }
  }
}

resource "keycloak_openid_client" "this" {
  realm_id    = var.realm_id
  client_id   = var.client_id
  name        = var.name
  enabled     = true
  access_type = "CONFIDENTIAL"

  standard_flow_enabled        = false
  direct_access_grants_enabled = false
  service_accounts_enabled     = true
  implicit_flow_enabled        = false

  valid_redirect_uris = []
  web_origins         = []

  client_secret = var.client_secret
  extra_config  = var.extra_config
}
```

- [ ] **Step 3: outputs.tf 作成**

```hcl
output "client_uuid" {
  description = "Keycloak内部UUID"
  value       = keycloak_openid_client.this.id
}

output "client_id" {
  description = "OIDC client_id"
  value       = keycloak_openid_client.this.client_id
}

output "service_account_user_id" {
  description = "Service Account の Keycloak User UUID (Role 付与等で参照)"
  value       = keycloak_openid_client.this.service_account_user_id
}

output "client_secret" {
  description = "Client Secret (sensitive)"
  value       = keycloak_openid_client.this.client_secret
  sensitive   = true
}
```

- [ ] **Step 4: README.md 作成**

```markdown
# client-service-account module

サーバ間通信用 Confidential Client。Client Credentials Grant のみ許可、Browser Flow / Direct Grant は無効。

## 使い方

\`\`\`hcl
module "batch" {
  source        = "../../../modules/client-service-account"
  realm_id      = keycloak_realm.this.id
  client_id     = "batch-worker"
  name          = "Batch Worker"
  client_secret = var.batch_worker_client_secret
}
\`\`\`

## MVP の制約

Roles / Permissions 付与は本モジュールには含まない。必要であれば別途 `keycloak_role` + `keycloak_user_roles` を呼び出し側で組む。
```

- [ ] **Step 5: モジュール validate**

```bash
cd terraform/modules/client-service-account && terraform init -backend=false && terraform validate
cd -
```
Expected: `Success! The configuration is valid.`

- [ ] **Step 6: Commit**

```bash
git add terraform/modules/client-service-account/
git commit -m "feat(terraform): add client-service-account module"
```

---

## Task 4: example-customer client spec に env ブロック追加

**Files:**
- Modify: `docs/specs/cases/example-customer/clients/web-app.md`
- Modify: `docs/specs/cases/example-customer/clients/spa-frontend.md`
- Modify: `docs/specs/cases/example-customer/clients/batch-worker.md`

- [ ] **Step 1: web-app.md に env ブロックと implementations 追記**

[docs/specs/cases/example-customer/clients/web-app.md](docs/specs/cases/example-customer/clients/web-app.md) の frontmatter `implementations:` を以下に置換:

```yaml
implementations:
  - keycloak/realms/example-customer.json
  - terraform/environments/example-customer/dev/main.tf
  - terraform/environments/example-customer/stg/main.tf
  - terraform/environments/example-customer/prod/main.tf
```

`## Client 設定値` の YAML ブロック末尾 (`access.token.lifespan: "300"` の直後の閉じ ``` の前) に env: ブロック追記:

```yaml
env:
  stg:
    redirectUris:
      - https://stg.app.example.com/*
    webOrigins:
      - https://stg.app.example.com
    attributes:
      post.logout.redirect.uris: https://stg.app.example.com
  prod:
    redirectUris:
      - https://app.example.com/*
    webOrigins:
      - https://app.example.com
    attributes:
      post.logout.redirect.uris: https://app.example.com
```

- [ ] **Step 2: spa-frontend.md に env ブロックと implementations 追記**

[docs/specs/cases/example-customer/clients/spa-frontend.md](docs/specs/cases/example-customer/clients/spa-frontend.md) の frontmatter `implementations:` を以下に置換:

```yaml
implementations:
  - keycloak/realms/example-customer.json
  - terraform/environments/example-customer/dev/main.tf
  - terraform/environments/example-customer/stg/main.tf
  - terraform/environments/example-customer/prod/main.tf
```

`## Client 設定値` の YAML ブロック末尾 (`access.token.lifespan: "300"` の直後の閉じ ``` の前) に env: ブロック追記:

```yaml
env:
  stg:
    redirectUris:
      - https://stg.spa.example.com/*
    webOrigins:
      - https://stg.spa.example.com
      - +
    attributes:
      post.logout.redirect.uris: https://stg.spa.example.com
  prod:
    redirectUris:
      - https://spa.example.com/*
    webOrigins:
      - https://spa.example.com
      - +
    attributes:
      post.logout.redirect.uris: https://spa.example.com
```

(`pkce.code.challenge.method: S256` は base にあり全 env 共通なので env ブロックでは省略)

- [ ] **Step 3: batch-worker.md に implementations 追記**

[docs/specs/cases/example-customer/clients/batch-worker.md](docs/specs/cases/example-customer/clients/batch-worker.md) の frontmatter `implementations:` を 4パス (json + dev/stg/prod main.tf) に拡張。env ブロックは省略 (redirect 不要)。

- [ ] **Step 4: spec-validate green 確認**

```bash
make spec-validate
```
Expected: `✓ 12 spec(s) checked, 0 error(s), 0 warning(s)` (件数は同じ、内容は更新)

- [ ] **Step 5: Commit**

```bash
git add docs/specs/cases/example-customer/clients/
git commit -m "feat(spec): add env blocks + HCL implementations to example-customer clients"
```

---

## Task 5: spec templates に env ブロック例を追記

**Files:**
- Modify: `docs/specs/templates/case-client-confidential-template.md`
- Modify: `docs/specs/templates/case-client-public-spa-template.md`
- Modify: `docs/specs/templates/case-client-service-account-template.md`

- [ ] **Step 1: confidential template に env ブロック例追加**

[docs/specs/templates/case-client-confidential-template.md](docs/specs/templates/case-client-confidential-template.md) の `## Client 設定値` セクションの YAML ブロック末尾に追記:

```yaml
# env 別オーバーライド (省略可、dev は base そのまま)
# 配列は完全上書き、scalar/map は env 値が優先
env:
  stg:
    redirectUris:
      - https://stg.<your-domain>/*
    webOrigins:
      - https://stg.<your-domain>
  prod:
    redirectUris:
      - https://<your-domain>/*
    webOrigins:
      - https://<your-domain>
```

- [ ] **Step 2: public-spa template に同様の追記**

[docs/specs/templates/case-client-public-spa-template.md](docs/specs/templates/case-client-public-spa-template.md) にも同じ env ブロック例を追記 (URL は SPA 用に調整)。

- [ ] **Step 3: service-account template に注記追加**

[docs/specs/templates/case-client-service-account-template.md](docs/specs/templates/case-client-service-account-template.md) の `## Client 設定値` 末尾に注記:

```markdown
> Service Account client は通常 redirectUris/webOrigins を持たないため、env: ブロックは省略可。
> Client Secret は env 別に異なる値を `terraform.tfvars` で注入 (spec / realm.json には書かない)。
```

- [ ] **Step 4: spec-validate**

```bash
make spec-validate
```
Expected: green (件数同じ)

- [ ] **Step 5: Commit**

```bash
git add docs/specs/templates/
git commit -m "docs(spec): add env block examples to client templates"
```

---

## Task 6: 旧 example-customer terraform 構成を削除

**Files:**
- Delete: `terraform/environments/example-customer/main.tf`
- Delete: `terraform/environments/example-customer/variables.tf`
- Delete: `terraform/environments/example-customer/outputs.tf`
- Delete: `terraform/environments/example-customer/terraform.tfvars.example`

- [ ] **Step 1: 旧ファイル削除**

```bash
git rm terraform/environments/example-customer/main.tf \
       terraform/environments/example-customer/variables.tf \
       terraform/environments/example-customer/outputs.tf \
       terraform/environments/example-customer/terraform.tfvars.example
```

(README.md は次タスクで置換するので残す)

- [ ] **Step 2: Commit**

```bash
git commit -m "refactor(terraform): remove old example-customer flat structure"
```

---

## Task 7: example-customer/dev/ HCL 生成

**Files:**
- Create: `terraform/environments/example-customer/dev/main.tf`
- Create: `terraform/environments/example-customer/dev/variables.tf`
- Create: `terraform/environments/example-customer/dev/terraform.tfvars.example`
- Create: `terraform/environments/example-customer/dev/README.md`

- [ ] **Step 1: main.tf 作成**

```hcl
terraform {
  required_version = ">= 1.5"
  required_providers {
    keycloak = {
      source  = "keycloak/keycloak"
      version = "~> 5.0"
    }
  }
}

provider "keycloak" {
  client_id     = "admin-cli"
  username      = "admin"
  password      = var.keycloak_admin_password
  url           = var.keycloak_url
  initial_login = false
}

resource "keycloak_realm" "this" {
  realm                    = "example-customer"
  enabled                  = true
  display_name             = "Example Customer"
  ssl_required             = "external"
  registration_allowed     = false
  login_with_email_allowed = true
  verify_email             = false
  reset_password_allowed   = true
  duplicate_emails_allowed = false
  brute_force_protected    = true
}

module "web_app" {
  source              = "../../../modules/client-confidential"
  realm_id            = keycloak_realm.this.id
  client_id           = "web-app"
  name                = "Example Customer Web App"
  valid_redirect_uris = ["http://localhost:3000/*"]
  web_origins         = ["http://localhost:3000"]
  client_secret       = var.web_app_client_secret
  extra_config = {
    "post.logout.redirect.uris" = "http://localhost:3000"
    "access.token.lifespan"     = "300"
  }
}

module "spa_frontend" {
  source              = "../../../modules/client-public-spa"
  realm_id            = keycloak_realm.this.id
  client_id           = "spa-frontend"
  name                = "Example Customer SPA"
  valid_redirect_uris = ["http://localhost:3001/*"]
  web_origins         = ["http://localhost:3001", "+"]
  extra_config = {
    "pkce.code.challenge.method" = "S256"
    "post.logout.redirect.uris"  = "http://localhost:3001"
    "access.token.lifespan"      = "300"
  }
}

module "batch_worker" {
  source        = "../../../modules/client-service-account"
  realm_id      = keycloak_realm.this.id
  client_id     = "batch-worker"
  name          = "Example Customer Batch Worker"
  client_secret = var.batch_worker_client_secret
}
```

> 実装時に spec の現在値で `redirectUris` / `webOrigins` / `extra_config` を再確認すること。

- [ ] **Step 2: variables.tf 作成**

```hcl
variable "keycloak_url" {
  type        = string
  description = "Keycloak の base URL (例: https://keycloak.localtest.me)"
}

variable "keycloak_admin_password" {
  type        = string
  description = "master realm の admin パスワード"
  sensitive   = true
}

variable "web_app_client_secret" {
  type        = string
  description = "web-app client_secret"
  sensitive   = true
}

variable "batch_worker_client_secret" {
  type        = string
  description = "batch-worker client_secret"
  sensitive   = true
}
```

- [ ] **Step 3: terraform.tfvars.example 作成**

```hcl
keycloak_url               = "https://keycloak.localtest.me"
keycloak_admin_password    = "admin"
web_app_client_secret      = "dev-dummy-secret-web-app"
batch_worker_client_secret = "dev-dummy-secret-batch-worker"
```

- [ ] **Step 4: README.md 作成**

```markdown
# example-customer / dev

ローカル開発用 Keycloak への terraform apply。`--import-realm` 経由とは排他 (どちらか一方で realm を作る)。

## 前提

- `make up` で Keycloak が `https://keycloak.localtest.me` で起動済
- `example-customer` realm が **存在しない** 状態 (`compose.override.yaml` で `--import-realm` を外すか、admin console で削除済)

## apply

\`\`\`bash
cp terraform.tfvars.example terraform.tfvars
# 必要なら secret を編集 (dev はダミーで OK)
terraform init
terraform apply
\`\`\`

## 手動編集ポイント

このディレクトリの `main.tf` は MVP では Realm policy / SMTP / IdP / Roles / Groups を含まない。必要に応じて `keycloak_realm.this` ブロックに `smtp_server`, `password_policy` などを追記、または `keycloak_role` / `keycloak_oidc_identity_provider` 等のリソースを別ファイルで追加。
```

- [ ] **Step 5: dev/ で validate**

```bash
cd terraform/environments/example-customer/dev && terraform init -backend=false && terraform validate && terraform fmt -check
cd -
```
Expected: `Success! The configuration is valid.` and `terraform fmt -check` exit 0

- [ ] **Step 6: Commit**

```bash
git add terraform/environments/example-customer/dev/
git commit -m "feat(terraform): add example-customer/dev env"
```

---

## Task 8: example-customer/stg/ HCL 生成

**Files:**
- Create: `terraform/environments/example-customer/stg/main.tf`
- Create: `terraform/environments/example-customer/stg/variables.tf`
- Create: `terraform/environments/example-customer/stg/terraform.tfvars.example`
- Create: `terraform/environments/example-customer/stg/README.md`

- [ ] **Step 1: main.tf 作成 (dev からの差分 = stg env マージ適用後の値)**

dev の main.tf を完全複製した上で、各 module ブロックを以下に差し替え:

```hcl
module "web_app" {
  source              = "../../../modules/client-confidential"
  realm_id            = keycloak_realm.this.id
  client_id           = "web-app"
  name                = "Example Customer Web App"
  valid_redirect_uris = ["https://stg.app.example.com/*"]
  web_origins         = ["https://stg.app.example.com"]
  client_secret       = var.web_app_client_secret
  extra_config = {
    "post.logout.redirect.uris" = "https://stg.app.example.com"
    "access.token.lifespan"     = "300"
  }
}

module "spa_frontend" {
  source              = "../../../modules/client-public-spa"
  realm_id            = keycloak_realm.this.id
  client_id           = "spa-frontend"
  name                = "Example Customer SPA"
  valid_redirect_uris = ["https://stg.spa.example.com/*"]
  web_origins         = ["https://stg.spa.example.com", "+"]
  extra_config = {
    "pkce.code.challenge.method" = "S256"
    "post.logout.redirect.uris"  = "https://stg.spa.example.com"
    "access.token.lifespan"      = "300"
  }
}

module "batch_worker" {
  source        = "../../../modules/client-service-account"
  realm_id      = keycloak_realm.this.id
  client_id     = "batch-worker"
  name          = "Example Customer Batch Worker"
  client_secret = var.batch_worker_client_secret
}
```

`terraform { ... }`, `provider { ... }`, `resource "keycloak_realm" "this"` ブロックは dev と同一。

- [ ] **Step 2: variables.tf 作成 (dev と同一)**

dev/variables.tf をそのままコピー (各 var の description は同じ、stg 用に微調整しない)

- [ ] **Step 3: terraform.tfvars.example 作成**

```hcl
keycloak_url               = "https://keycloak.stg.example.com"
keycloak_admin_password    = "REPLACE_ME_BEFORE_APPLY"
web_app_client_secret      = "REPLACE_ME_BEFORE_APPLY"
batch_worker_client_secret = "REPLACE_ME_BEFORE_APPLY"
```

- [ ] **Step 4: README.md 作成**

```markdown
# example-customer / stg

STG 環境への terraform apply。

## 前提

- STG Keycloak が稼働済 (URL は `terraform.tfvars` で指定)
- 実 secret を `terraform.tfvars` に注入 (gitignore)
- `example-customer` realm が存在しないか、本 terraform state で管理開始する状態

## apply

\`\`\`bash
cp terraform.tfvars.example terraform.tfvars
# 実 secret を編集 (本番アクセス権が必要)
terraform init
terraform plan
terraform apply
\`\`\`

## 手動編集ポイント

dev/README.md と同じ。MVP は Realm policy / SMTP / IdP / Roles / Groups を含まない。
```

- [ ] **Step 5: stg/ で validate**

```bash
cd terraform/environments/example-customer/stg && terraform init -backend=false && terraform validate && terraform fmt -check
cd -
```
Expected: validate OK, fmt -check exit 0

- [ ] **Step 6: Commit**

```bash
git add terraform/environments/example-customer/stg/
git commit -m "feat(terraform): add example-customer/stg env"
```

---

## Task 9: example-customer/prod/ HCL 生成

**Files:**
- Create: `terraform/environments/example-customer/prod/main.tf`
- Create: `terraform/environments/example-customer/prod/variables.tf`
- Create: `terraform/environments/example-customer/prod/terraform.tfvars.example`
- Create: `terraform/environments/example-customer/prod/README.md`

- [ ] **Step 1: main.tf 作成 (stg と同形、URL は prod 値)**

stg/main.tf を複製し、各 module ブロックを以下に差し替え:

```hcl
module "web_app" {
  source              = "../../../modules/client-confidential"
  realm_id            = keycloak_realm.this.id
  client_id           = "web-app"
  name                = "Example Customer Web App"
  valid_redirect_uris = ["https://app.example.com/*"]
  web_origins         = ["https://app.example.com"]
  client_secret       = var.web_app_client_secret
  extra_config = {
    "post.logout.redirect.uris" = "https://app.example.com"
    "access.token.lifespan"     = "300"
  }
}

module "spa_frontend" {
  source              = "../../../modules/client-public-spa"
  realm_id            = keycloak_realm.this.id
  client_id           = "spa-frontend"
  name                = "Example Customer SPA"
  valid_redirect_uris = ["https://spa.example.com/*"]
  web_origins         = ["https://spa.example.com", "+"]
  extra_config = {
    "pkce.code.challenge.method" = "S256"
    "post.logout.redirect.uris"  = "https://spa.example.com"
    "access.token.lifespan"      = "300"
  }
}

module "batch_worker" {
  source        = "../../../modules/client-service-account"
  realm_id      = keycloak_realm.this.id
  client_id     = "batch-worker"
  name          = "Example Customer Batch Worker"
  client_secret = var.batch_worker_client_secret
}
```

`terraform`/`provider`/`keycloak_realm.this` ブロックは dev/stg と同一。

- [ ] **Step 2: variables.tf 作成 (stg と同一)**

stg/variables.tf をコピー

- [ ] **Step 3: terraform.tfvars.example 作成**

```hcl
keycloak_url               = "https://keycloak.example.com"
keycloak_admin_password    = "REPLACE_ME_BEFORE_APPLY"
web_app_client_secret      = "REPLACE_ME_BEFORE_APPLY"
batch_worker_client_secret = "REPLACE_ME_BEFORE_APPLY"
```

- [ ] **Step 4: README.md 作成**

stg/README.md をコピーし、"STG 環境" を "Prod 環境" に置換。

- [ ] **Step 5: prod/ で validate**

```bash
cd terraform/environments/example-customer/prod && terraform init -backend=false && terraform validate && terraform fmt -check
cd -
```
Expected: validate OK, fmt -check exit 0

- [ ] **Step 6: Commit**

```bash
git add terraform/environments/example-customer/prod/
git commit -m "feat(terraform): add example-customer/prod env"
```

---

## Task 10: example-customer/README.md (案件全体) を新内容に置換

**Files:**
- Modify: `terraform/environments/example-customer/README.md`

- [ ] **Step 1: 全置換**

```markdown
# example-customer

サンプル案件の Terraform 構成。3 env (dev / stg / prod) を独立 state で管理。

## ディレクトリ

- `dev/` — ローカル開発 Keycloak (https://keycloak.localtest.me) 向け
- `stg/` — Staging 環境
- `prod/` — Production 環境

各 env はそれぞれ `terraform init && apply` で独立に管理される。state 共有なし。

## SoT

このディレクトリの HCL は `docs/specs/cases/example-customer/clients/*.md` から `writing-keycloak-realm-terraform` skill で生成されたもの。**spec を直接編集 → skill 再実行** が正しい更新フロー。HCL を直接編集すると次回 skill 実行で上書きされる。

## apply 順 (新規環境セットアップ時)

1. `dev/` で動作確認 (`terraform apply`)
2. `stg/` の手動編集ポイント (Realm policy / SMTP / IdP 等) を spec 外で追記
3. `stg/` で `terraform plan` → 内容確認 → `apply`
4. `prod/` で同様

## 注意

- dev 環境は `--import-realm` (`keycloak/realms/example-customer.json`) でも構築できるが、**terraform apply と排他** (同じ realm を両経路で作らない)。
- secret は `terraform.tfvars` に注入し、リポジトリにコミットしない (`.gitignore` 済)。
```

- [ ] **Step 2: Commit**

```bash
git add terraform/environments/example-customer/README.md
git commit -m "docs(terraform): replace example-customer README for env-split structure"
```

---

## Task 11: `.gitignore` に terraform.tfvars 追加 (未追加なら)

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: 現状確認**

```bash
grep -n "terraform.tfvars\|\.tfstate\|\.terraform/" .gitignore
```

- [ ] **Step 2: 不足分を追記**

`.gitignore` に以下が無ければ追記:

```
terraform/**/terraform.tfvars
terraform/**/.terraform/
terraform/**/.terraform.lock.hcl
terraform/**/*.tfstate
terraform/**/*.tfstate.*
```

(既存パターンを壊さないよう、現状 grep の結果を見て不足分のみ追記)

- [ ] **Step 3: Commit (差分があれば)**

```bash
git add .gitignore
git commit -m "chore: gitignore terraform.tfvars and state under per-env dirs"
```

---

## Task 12: `writing-keycloak-realm-terraform` SKILL.md を全置換

**Files:**
- Replace: `.claude/skills/writing-keycloak-realm-terraform/SKILL.md`

- [ ] **Step 1: SKILL.md 全置換**

[.claude/skills/writing-keycloak-realm-terraform/SKILL.md](.claude/skills/writing-keycloak-realm-terraform/SKILL.md) を以下に完全置換:

````markdown
---
name: writing-keycloak-realm-terraform
description: Use when generating or updating Terraform HCL for Keycloak admin console configuration from case specs (CASE-<CASE>-CLIENT-* specs) in this project. Translates case-spec + env (dev/stg/prod) into terraform/environments/<case>/<env>/ HCL using the keycloak/keycloak provider ~> 5.0.
---

# Writing Keycloak Terraform HCL from case specs

case-spec を SoT として 1 env 分の HCL を `terraform/environments/<案件>/<env>/` に生成する skill。`writing-keycloak-realm-json` skill (realm.json 生成) の **双子**。両方とも同じ spec を入力に、出力先と出力形式が違うだけ。

## When to Use

- 新案件の terraform/environments/<案件>/{dev,stg,prod}/ を最初に生成する
- 既存 case の client spec を変更した後、HCL を再生成する
- 新規 client spec を追加した後、HCL の `module "..."` を追加・更新する

## When NOT to Use

- ローカル開発用 realm.json 生成 (それは `writing-keycloak-realm-json` skill)
- SPI 実装 (それは `writing-keycloak-spi-pattern` skill)
- spec 自体を起票する (それは `writing-spec` skill — 必ず先に走らせる)
- Roles / Groups / IdP / Auth Flow / SMTP の HCL 化 (Phase G MVP スコープ外。`keycloak_realm` リソースに手動追記)

## Prerequisites

- [ ] `docs/specs/cases/<案件>/clients/index.md` (status: approved)
- [ ] `docs/specs/cases/<案件>/clients/<client_id>.md` が1つ以上 (status: approved)
- [ ] 各 client spec の YAML ブロックに `clientId`, `publicClient`, `standardFlowEnabled`, `redirectUris`, `webOrigins`, (任意) `env: { stg: ..., prod: ... }` が記載済
- [ ] `terraform/modules/client-confidential/`, `client-public-spa/`, `client-service-account/` が存在
- [ ] env 引数 (`dev` | `stg` | `prod`) がユーザーから提供されている

## Reference

- [docs/specs/specs-guide.md](../../../docs/specs/specs-guide.md)
- [docs/specs/templates/case-client-confidential-template.md](../../../docs/specs/templates/case-client-confidential-template.md)
- [terraform/modules/client-confidential/](../../../terraform/modules/client-confidential/)
- [terraform/modules/client-public-spa/](../../../terraform/modules/client-public-spa/)
- [terraform/modules/client-service-account/](../../../terraform/modules/client-service-account/)
- [terraform/environments/example-customer/dev/](../../../terraform/environments/example-customer/dev/) — 動く実例
- [keycloak/keycloak provider v5](https://registry.terraform.io/providers/keycloak/keycloak/latest/docs)

## Workflow

### Step 1: 入力収集

ユーザーから案件名 (例: `acme-corp`) と env (`dev`|`stg`|`prod`) を受け取る。

```
docs/specs/cases/<案件>/clients/index.md   ← Realm 設定 (案件名・displayName 等)
docs/specs/cases/<案件>/clients/*.md       ← 個別 client spec (index.md 以外)
```

各 client spec の YAML ブロックを抽出。

### Step 2: env マージ

各 client spec の YAML について:

- `base` = top-level フィールド (ただし `env:` を除く)
- `env_overlay` = `env.<指定env>` (無ければ空)
- 有効値 = `base` ∪ `env_overlay` (同キーは env が勝つ、配列は完全上書き)
- `env:` ブロック自体は出力に含めない

### Step 3: client タイプ判定 → module 選択

| YAML フラグ | module |
|---|---|
| `publicClient: true` | `client-public-spa` |
| `serviceAccountsEnabled: true` (かつ `publicClient: false`) | `client-service-account` |
| 上記以外 (confidential + standard flow) | `client-confidential` |

### Step 4: HCL 出力

`terraform/environments/<案件>/<env>/` に4ファイル生成:

#### main.tf

```hcl
terraform {
  required_version = ">= 1.5"
  required_providers {
    keycloak = {
      source  = "keycloak/keycloak"
      version = "~> 5.0"
    }
  }
}

provider "keycloak" {
  client_id     = "admin-cli"
  username      = "admin"
  password      = var.keycloak_admin_password
  url           = var.keycloak_url
  initial_login = false
}

resource "keycloak_realm" "this" {
  realm                    = "<案件名 from index.md>"
  enabled                  = true
  display_name             = "<displayName from index.md>"
  ssl_required             = "external"
  registration_allowed     = false
  login_with_email_allowed = true
  verify_email             = false
  reset_password_allowed   = true
  duplicate_emails_allowed = false
  brute_force_protected    = true
}

# 各 client spec ごとに module ブロック
module "<terraform名 = clientId をスネークケース化>" {
  source              = "../../../modules/<選択 module>"
  realm_id            = keycloak_realm.this.id
  client_id           = "<clientId>"
  name                = "<name>"
  valid_redirect_uris = <マージ後 redirectUris>
  web_origins         = <マージ後 webOrigins>
  client_secret       = var.<terraform名>_client_secret   # confidential / service-account のみ
  extra_config        = <マージ後 attributes>             # 空ならフィールドごと省略可
}
```

**重要 attribute 対応**:

- spec の `attributes` は HCL の `extra_config` (map(string)) に渡す
- public-spa は client_secret を持たない
- service-account は redirectUris/webOrigins 持たない (空配列で渡す or省略)

#### variables.tf

```hcl
variable "keycloak_url" {
  type        = string
  description = "Keycloak の base URL"
}

variable "keycloak_admin_password" {
  type        = string
  description = "master realm の admin パスワード"
  sensitive   = true
}

# 各 confidential / service-account client ごとに1つ
variable "<terraform名>_client_secret" {
  type        = string
  description = "<clientId> の client_secret"
  sensitive   = true
}
```

#### terraform.tfvars.example

```hcl
keycloak_url               = "https://keycloak.<env>.example.com"
keycloak_admin_password    = "REPLACE_ME_BEFORE_APPLY"   # dev は "admin"
<terraform名>_client_secret = "REPLACE_ME_BEFORE_APPLY"   # dev は "dev-dummy-secret-<clientId>"
```

#### README.md

```markdown
# <案件> / <env>

<env 説明 (dev=ローカル開発、stg=Staging、prod=Production)>

## apply

\`\`\`bash
cp terraform.tfvars.example terraform.tfvars
# 実 secret 編集
terraform init
terraform plan
terraform apply
\`\`\`

## 手動編集ポイント

MVP は Realm policy / SMTP / IdP / Roles / Groups を含まない。必要に応じて `main.tf` の `keycloak_realm.this` ブロックに `smtp_server`, `password_policy` などを追記。
```

### Step 5: 検証

```bash
cd terraform/environments/<案件>/<env>
terraform init -backend=false
terraform validate
terraform fmt -check
```

3つすべて成功すること。失敗したらエラーを spec 読み直しから直す。

### Step 6: spec の implementations 更新

各 client spec の frontmatter `implementations:` に当該 env のパスを追記:

```yaml
implementations:
  - keycloak/realms/<案件>.json
  - terraform/environments/<案件>/dev/main.tf
  - terraform/environments/<案件>/stg/main.tf
  - terraform/environments/<案件>/prod/main.tf
```

(同 spec から3 env 分作るので3行すべて追加 — 1 env だけ実装した直後はその1行のみ追加)

最後に `make spec-validate` で green 確認。

## Known Limitations (MVP)

- Realm 全体設定 (SMTP, password policy, IdP, Roles, Groups) は HCL に含まれない。手動編集が必要。
- env 別オーバーライドは **完全上書き** のみ。配列の差分マージは未対応 (将来必要なら拡張)。
- `default_client_scopes` / `optional_client_scopes` の module variable 化は未対応 (現状 module 内デフォルト)。
````

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/writing-keycloak-realm-terraform/SKILL.md
git commit -m "feat(skill): rewrite writing-keycloak-realm-terraform for case-spec + env"
```

---

## Task 13: `terraform/CLAUDE.md` を新フローに合わせて更新

**Files:**
- Modify: `terraform/CLAUDE.md`

- [ ] **Step 1: 現状確認**

```bash
grep -n "task-spec\|env\|environments" terraform/CLAUDE.md | head -20
```

- [ ] **Step 2: 該当箇所を編集**

旧 task-spec 言及部分を削除し、case-spec + env 別ディレクトリ構造の説明に置換。少なくとも以下を含める:

- ディレクトリ構造: `environments/<案件>/{dev,stg,prod}/` が各 env 独立 state
- SoT は `docs/specs/cases/<案件>/clients/*.md` (env: ブロック付き)
- 生成は `writing-keycloak-realm-terraform` skill (env 引数指定で1 env ずつ)
- 旧 `task-spec` ベース skill は廃止済
- example-customer がリファレンス実装

(具体的な編集差分は現ファイルの内容を読んで該当部分のみ置換。全置換ではなく targeted edits)

- [ ] **Step 3: Commit**

```bash
git add terraform/CLAUDE.md
git commit -m "docs(terraform): update CLAUDE.md for env-split structure"
```

---

## Task 14: 統合 verify — spec ↔ HCL 整合 + validate 全 env

**Files:** (検証のみ、変更なし)

- [ ] **Step 1: spec-validate green**

```bash
make spec-validate
```
Expected: green (件数同じ、内容は spec 追記後)

- [ ] **Step 2: 3 env すべてで validate**

```bash
for env in dev stg prod; do
  echo "=== $env ==="
  (cd terraform/environments/example-customer/$env && terraform init -backend=false && terraform validate && terraform fmt -check)
done
```
Expected: 3 env すべて `Success!` + fmt exit 0

- [ ] **Step 3: 全 module で validate**

```bash
for m in client-confidential client-public-spa client-service-account; do
  echo "=== $m ==="
  (cd terraform/modules/$m && terraform init -backend=false && terraform validate)
done
```
Expected: 3 module すべて `Success!`

- [ ] **Step 4: spec の implementations: 整合性 (目視)**

```bash
grep -A 6 "implementations:" docs/specs/cases/example-customer/clients/*.md
```
Expected: 各 client spec に json + dev/stg/prod main.tf の4パス

このタスクで失敗した場合はその場で対応する task に戻って修正。

---

## Task 15: dev 実 apply 動作確認 (任意だが推奨)

**Files:** (実環境検証、変更なし)

- [ ] **Step 1: realm 未存在状態に**

`compose.override.yaml` が無ければ `compose.override.yaml.example` をコピーし、keycloak サービスの `command` から `--import-realm` を除外。

または、admin console で `example-customer` realm を手動削除。

確認:

```bash
curl -sk https://keycloak.localtest.me/realms/example-customer/.well-known/openid-configuration
```
Expected: `{"error":"Realm does not exist"}`

- [ ] **Step 2: terraform apply**

```bash
cd terraform/environments/example-customer/dev
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform apply -auto-approve
cd -
```
Expected: `Apply complete! Resources: 4 added` (realm + 3 clients)

- [ ] **Step 3: clients 検証**

```bash
TOKEN=$(curl -sk -X POST https://keycloak.localtest.me/realms/master/protocol/openid-connect/token \
  -d "username=admin" -d "password=admin" -d "grant_type=password" -d "client_id=admin-cli" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl -sk -H "Authorization: Bearer $TOKEN" \
  "https://keycloak.localtest.me/admin/realms/example-customer/clients" \
  | python3 -c "import sys,json; cs=json.load(sys.stdin); [print(c['clientId'], c['publicClient'], c.get('serviceAccountsEnabled')) for c in cs if c['clientId'] in ('web-app','spa-frontend','batch-worker')]"
```
Expected: 3 clients が realm.json import 時と同じ設定で並ぶ

- [ ] **Step 4: 後始末**

検証完了後、apply した realm を削除して `--import-realm` を元に戻す:

```bash
cd terraform/environments/example-customer/dev && terraform destroy -auto-approve && cd -
```

`compose.override.yaml` の `--import-realm` 復活 (or override 削除)。

`make restart` で realm を realm.json から再 import。

このタスクで失敗した場合、HCL またはモジュールに実環境バグあり → 対応タスクに戻る。

---

## Task 16: メモリ更新 + Phase F memory に Phase G 完了を記録

**Files:**
- Modify: Claude メモリ `project_phase_f_realm_json.md` (Phase F + G の状態を統合)

- [ ] **Step 1: メモリ更新 (Claude 実行)**

`/Users/wataru/.claude/projects/-Users-wataru-dev-keycloak-dev/memory/project_phase_f_realm_json.md` に Phase G 完了セクションを追記、または別ファイル `project_phase_g_terraform.md` を新設して `MEMORY.md` に登録。判断は Claude が memory 系の文脈で行う。

最低限以下を記録:

- Phase G 完了 (日付)
- 新 skill 仕様 (case-spec + env → HCL)
- 旧 task-spec skill 廃止済
- 次の候補フェーズ: Roles / IdP / Flow / SMTP 等の HCL/JSON 対応、Phase H (Excel パラメータシート)

- [ ] **Step 2: (commit 不要 — memory はリポ外)**

---

## Self-Review チェック

実装完了後、以下を確認:

- [ ] `make spec-validate` green
- [ ] 3 env + 3 module すべて `terraform validate` green
- [ ] 旧 `terraform/environments/example-customer/{main,variables,outputs,terraform.tfvars.example}.tf` が削除済
- [ ] `writing-keycloak-realm-terraform/SKILL.md` から旧 task-spec 言及が完全消去
- [ ] 各 client spec の `implementations:` に4パス
- [ ] `.gitignore` で `terraform.tfvars` / state が除外
- [ ] (任意) dev 実 apply で 3 client 作成確認

## 後続フェーズ候補 (Phase G スコープ外)

- Realm 全体設定 (SMTP, password policy, IdP, Roles, Groups) の HCL 化
- Phase H: spec / HCL → Excel パラメータシート (顧客提出物)
- CI で `terraform validate` 自動化
