---
spec_id: DESIGN-PHASE-G-REALM-JSON-TO-TERRAFORM
title: Phase G — case-spec から Terraform HCL を生成する (realm.json と双子出力)
status: approved
date: 2026-05-24
implementations:
  - .claude/skills/writing-keycloak-realm-terraform/SKILL.md
  - terraform/modules/client-public-spa/
  - terraform/modules/client-service-account/
  - terraform/environments/example-customer/dev/
  - terraform/environments/example-customer/stg/
  - terraform/environments/example-customer/prod/
---

# Phase G Design — case-spec → Terraform HCL (STG/Prod 配備)

## 背景

Phase F (完了) で `case-spec → keycloak/realms/<案件>.json` の経路ができ、ローカル開発で `--import-realm` による realm 構築が動作した。残るは **STG/Prod 環境への配備経路** で、これを Terraform HCL で表現する。

調査の結果、`GoogleCloudPlatform/terraformer` は 2026-03 に archived となり Keycloak provider 対応も最小限だったため、reverse-engineering 方式は採らない。代わりに **case-spec を SoT として HCL を Claude skill で生成** する。

既存 skill `writing-keycloak-realm-terraform` は当初 task-spec を入力としていたが、case-spec への一本化に伴い廃止 (=同名 skill の中身を入れ替え) する。

## 採用方針

### 1. Source of Truth: case-spec 一本

```
[case-spec (clients/*.md, env ブロック付き)]
   │
   ├─ writing-keycloak-realm-json skill (既存) → keycloak/realms/<案件>.json (dev のみ)
   │
   └─ writing-keycloak-realm-terraform skill (中身差し替え) → terraform/environments/<案件>/{dev,stg,prod}/
```

- realm.json と HCL は **同じ spec から派生する双子出力**
- realm.json は dev での `--import-realm` 専用、HCL は全 env (dev/stg/prod) の `terraform apply` 用
- dev は両経路 (import-realm と terraform) どちらでも構築可能だが、**同時実行は禁止** (memo の運用方針通り)

### 2. スコープ (MVP: clients のみ)

Phase F.4 (Realm 全体への spec 拡張) はスキップした方針に合わせ、Phase G の MVP も **clients のみ** をカバー:

- 対象リソース: confidential / public-spa / service-account の3パターン
- 対象外: Roles / Groups / Users / IdP / Auth Flow / SMTP / その他 realm policy
- 対象外項目は HCL 中で `keycloak_realm` リソースの **固定デフォルト** として出力され、必要に応じて手動編集する。各 env の README に手動編集ポイントを列記。

### 3. env 差分の表現 (spec 内 env ブロック)

各 client spec の YAML ブロックに `env:` セクションを追加:

```yaml
clientId: web-app
publicClient: false
standardFlowEnabled: true
redirectUris:
  - http://localhost:3000/*
webOrigins:
  - http://localhost:3000
attributes:
  post.logout.redirect.uris: http://localhost:3000

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

**マージルール**:
- 各 env の有効値 = `base` (`env:` を除く top-level フィールド) ∪ `env.<name>`
- 同キーは env が勝つ、配列は **完全上書き** で連結しない
- `env:` ブロックが無い env (dev など) は base そのまま

### 4. secret 管理

- spec / realm.json には secret 値を一切書かない
- HCL では confidential / service-account client の `client_secret` を `var.<clientId>_client_secret` として外出し
- 実値は `terraform.tfvars` (gitignore) で env 別に注入
- `terraform.tfvars.example` には **形だけ** (ダミー値) を示す

### 5. ssl_required

`keycloak_realm.this.ssl_required` は **全 env で `"external"` 固定**。dev も Traefik 経由 HTTPS なので問題なし。

### 6. terraform ディレクトリ構造

```
terraform/
├── modules/
│   ├── client-confidential/         # 既存
│   ├── client-public-spa/           # 新規 (Phase G)
│   └── client-service-account/      # 新規 (Phase G)
└── environments/
    └── <案件>/
        ├── README.md                # 案件全体の説明・apply 順
        ├── dev/
        │   ├── main.tf
        │   ├── variables.tf
        │   ├── terraform.tfvars.example
        │   └── README.md
        ├── stg/  (同上)
        └── prod/ (同上)
```

各 env は **独立 state**。env 間共有なし、shared module は `terraform/modules/` を参照。

### 7. 既存 skill 廃止

`writing-keycloak-realm-terraform/SKILL.md` の旧 task-spec ベース説明は完全に消去し、case-spec + env 引数ベースの新仕様で書き換える。

既存 `terraform/environments/example-customer/{main.tf,variables.tf,outputs.tf,terraform.tfvars.example}` は削除し env 別構造で置き換える。Phase F での realm import 切替時点で既に使われていない (memo の「Realm 未存在・state なし」確認済)。

## skill 仕様 (`writing-keycloak-realm-terraform` 新版)

### 入力

- 引数: 案件名 (例: `example-customer`)、env (`dev` | `stg` | `prod`)
- 参照: `docs/specs/cases/<案件>/clients/index.md` + `clients/*.md`

### 出力

`terraform/environments/<案件>/<env>/` 配下に:

- `main.tf` — `provider "keycloak"` + `keycloak_realm.this` + 各 client の module 呼び出し
- `variables.tf` — `keycloak_url`, `keycloak_admin_password`, `<clientId>_client_secret` (confidential/service-account のみ)
- `terraform.tfvars.example` — 各 var の形 (ダミー)
- `README.md` — apply 手順、手動編集ポイント、secret 注入手順

### main.tf 構造例

```hcl
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
  source        = "../../../modules/client-confidential"
  realm_id      = keycloak_realm.this.id
  client_id     = "web-app"
  name          = "Example Customer Web App"
  redirect_uris = ["https://app.example.com/*"]   # env 適用後の値
  web_origins   = ["https://app.example.com"]
  client_secret = var.web_app_client_secret
}
```

### 前提モジュール

| Module | 状態 | 主要 variables |
|---|---|---|
| `client-confidential` | 既存 | realm_id, client_id, name, redirect_uris, web_origins, client_secret, attributes |
| `client-public-spa` | **新規** | realm_id, client_id, name, root_url, redirect_uris, web_origins, default/optional client_scopes |
| `client-service-account` | **新規** | realm_id, client_id, name, client_secret (roles/perms は後回し) |

## サンプル拡張 (example-customer)

### spec 更新

- `clients/web-app.md` に `env: { stg, prod }` ブロック追加
- `clients/spa-frontend.md` に同上
- `clients/batch-worker.md` は env 差分なし想定で `env:` 省略 (spec 内 secret 説明だけ追記)

### 成果物

```
terraform/environments/example-customer/
├── README.md   ← 新内容に置換
├── dev/   (main.tf, variables.tf, terraform.tfvars.example, README.md)
├── stg/   (同上)
└── prod/  (同上)
```

### 旧ファイル削除

`terraform/environments/example-customer/{main.tf,variables.tf,outputs.tf,terraform.tfvars.example}` を削除。

## 受け入れ基準

1. **skill 動作**
   - `example-customer` + env 引数で起動 → 3 env 分の HCL 生成
   - `terraform fmt` でフォーマット整合
   - `terraform init && terraform validate` が 3 env すべて green

2. **dev 実 apply 検証** (最低限ここまで)
   - `make clean && make up` で realm 未存在状態に
   - `--import-realm` を **無効化** (`compose.override.yaml` で `command` から外す) して空 realm で起動
   - `cd terraform/environments/example-customer/dev && terraform init && terraform apply`
   - Admin API で 3 client が期待通りの設定で作成されていることを確認

3. **STG/Prod は plan まで**
   - `terraform init && terraform validate` レベルで OK
   - 実 apply は実案件で別途

4. **spec ↔ HCL 整合**
   - `make spec-validate` が引き続き green
   - 各 client spec の `implementations:` に新 HCL パス3つを追記

5. **既存 skill 廃止の後始末**
   - 旧 task-spec 説明が `SKILL.md` から完全消去、新 case-spec ベースに置換
   - 旧 `terraform/environments/example-customer/{main.tf,variables.tf,outputs.tf,terraform.tfvars.example}` が削除済

6. **ドキュメント**
   - `terraform/environments/example-customer/README.md` 新内容に置換
   - 各 env の README に手動編集ポイント列記
   - `terraform/CLAUDE.md` を新フローに合わせて更新

### テストの省略事項 (YAGNI)

- JSON↔HCL の自動往復テストは作らない (手動 verify でカバー)
- skill のユニットテストは作らない (LLM 駆動)
- `terraform apply` の CI 自動化は Phase G スコープ外

## 関連

- 前フェーズ: Phase F (case-spec → realm.json) — `memory/project_phase_f_realm_json.md`
- 関連 ADR: `docs/architecture.md` ADR-012 (SDD + superpowers)
- 上書き対象 skill: `.claude/skills/writing-keycloak-realm-terraform/SKILL.md`
