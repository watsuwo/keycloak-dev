# example-customer / prod

Prod 環境への terraform apply。

## 前提

- Prod Keycloak が稼働済 (URL は `terraform.tfvars` で指定)
- 実 secret を `terraform.tfvars` に注入 (gitignore)
- `example-customer` realm が存在しないか、本 terraform state で管理開始する状態

## apply

```bash
cp terraform.tfvars.example terraform.tfvars
# 実 secret を編集 (本番アクセス権が必要)
terraform init
terraform plan
terraform apply
```

## 手動編集ポイント

MVP は Realm policy / SMTP / IdP / Roles / Groups を含まない。必要に応じて `main.tf` の `keycloak_realm.this` ブロックに `smtp_server`, `password_policy` などを追記。
