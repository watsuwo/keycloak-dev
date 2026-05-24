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
- public-spa の PKCE は module 側で自動設定 (extra_config への `pkce.code.challenge.method` 追記不要)
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
