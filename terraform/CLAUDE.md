# terraform/ — 管理コンソール設定の Infrastructure as Code

Keycloak の Realm/Client/Role/IdP 等の設定を **Terraform Provider for Keycloak** (`keycloak/keycloak`) で宣言的に管理する。

## なぜ Terraform 化したいか

- 手動GUI操作 → 案件毎に再現不能、ジュニアでもできる定型作業に熟練者の時間が取られる
- Realm JSON export/import → 全体像が1ファイルで diff 読みにくい、部分更新しづらい
- **Terraform** → HCLで宣言的、`plan` で diff レビュー、Git管理、案件間でモジュール再利用、Claudeにとって生成しやすい

## ディレクトリ構成

```
terraform/
├── CLAUDE.md                              このファイル
├── modules/                               再利用モジュール (案件横断)
│   ├── client-confidential/               OIDC confidential client
│   ├── client-public-spa/                 OIDC public client (PKCE 必須)
│   └── client-service-account/            Client Credentials Grant 専用
└── environments/                          案件別 (各案件で複製)
    └── example-customer/                  ★サンプル案件
        ├── README.md                      env 別構造の案内
        ├── dev/                           ローカル開発環境
        │   ├── main.tf                    provider + realm + module 呼出し
        │   ├── variables.tf
        │   ├── terraform.tfvars.example   パラメータひな型 (実体はgit管理外)
        │   └── README.md
        ├── stg/                           Staging 環境
        └── prod/                          Production 環境
```

各 env は独立 state で管理される (`terraform init && apply` が env 単位)。

## 開発フロー (Phase G 以降)

```
docs/specs/cases/<案件>/clients/*.md   (case-spec、SoT)
       ↓ env: ブロックで環境差分を表現
       ↓ writing-keycloak-realm-terraform skill (env 引数指定)
terraform/environments/<案件>/{dev,stg,prod}/main.tf
       ↓ terraform init && terraform plan (差分確認)
       ↓ terraform apply
Keycloak 設定適用
```

**SoT は case-spec**。HCL を直接編集すると次回 skill 実行で上書きされる。spec を先に更新してから skill を再実行する。

## よく使うコマンド

```bash
# dev 環境への apply (example-customer)
cd terraform/environments/example-customer/dev
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply

# validate のみ (CI 用)
terraform init -backend=false && terraform validate

# 別 env
cd terraform/environments/example-customer/stg
terraform init && terraform plan
```

## モジュール一覧

| モジュール | 用途 | 主な変数 |
|---|---|---|
| `client-confidential` | Authorization Code Flow (server-side) | `client_id`, `valid_redirect_uris`, `client_secret`, `extra_config` |
| `client-public-spa` | SPA / Mobile (PKCE 必須、secret なし) | `client_id`, `valid_redirect_uris`, `web_origins`, `extra_config` |
| `client-service-account` | Client Credentials Grant (M2M) | `client_id`, `client_secret`, `extra_config` |

## 前提ツール

- **Terraform CLI 1.5以上** : `brew install terraform` / WSL2 `sudo apt install terraform`
- **dev Keycloak が起動中** (`make up`)、または別環境のKeycloakが accessible

## TLS とシークレットの扱い

- dev 環境は自己署名証明書だが provider の `initial_login = false` で接続チェックをスキップ
- 本番/ステージングは正規証明書、`tls_insecure_skip_verify` は使わない
- `terraform.tfvars` および `terraform.tfstate*` は **gitignore対象** (secrets含む)
- 本番運用時は remote backend (S3 + DynamoDB等) を検討

## 新しいモジュールを追加する手順

1. 「複数案件で再利用しそうか」を判断 — 1案件限定ならenvironments側にinlineで書く
2. `terraform/modules/<name>/` ディレクトリを作成 (main.tf / variables.tf / outputs.tf / README.md)
3. example-customer のいずれかの env で使って `terraform validate` が green になることを確認

## 命名規則

- モジュール名: ケバブケース、用途を表す (`client-confidential`、`role-set`、`idp-google`、`flow-mfa-totp`)
- リソース名 (HCL内): スネークケース、`this` を多用 (モジュール内なら主リソースは `this`)
- 環境ディレクトリ: 顧客名のケバブケース (`acme-corp`、`example-customer`)
- module ラベル: clientId をスネークケース化 (`web-app` → `web_app`)

## 参考

- Provider Registry: https://registry.terraform.io/providers/keycloak/keycloak/latest/docs
- 動く実例: `terraform/environments/example-customer/dev/`
- 設計レビュー観点 (将来作成): `docs/review-checklists/realm-config-review.md`
