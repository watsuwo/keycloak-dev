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
