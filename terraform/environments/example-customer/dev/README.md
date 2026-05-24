# example-customer / dev

ローカル開発用 Keycloak への terraform apply。`--import-realm` 経由とは排他 (どちらか一方で realm を作る)。

## 前提

- `make up` で Keycloak が `https://keycloak.localtest.me` で起動済
- `example-customer` realm が **存在しない** 状態 (`compose.override.yaml` で `--import-realm` を外すか、admin console で削除済)

## apply

```bash
cp terraform.tfvars.example terraform.tfvars
# 必要なら secret を編集 (dev はダミーで OK)
terraform init
terraform apply
```

## 手動編集ポイント

このディレクトリの `main.tf` は MVP では Realm policy / SMTP / IdP / Roles / Groups を含まない。必要に応じて `keycloak_realm.this` ブロックに `smtp_server`, `password_policy` などを追記、または `keycloak_role` / `keycloak_oidc_identity_provider` 等のリソースを別ファイルで追加。
