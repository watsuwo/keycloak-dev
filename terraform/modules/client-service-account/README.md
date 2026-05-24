# client-service-account module

サーバ間通信用 Confidential Client。Client Credentials Grant のみ許可、Browser Flow / Direct Grant は無効。

## 使い方

```hcl
module "batch" {
  source        = "../../../modules/client-service-account"
  realm_id      = keycloak_realm.this.id
  client_id     = "batch-worker"
  name          = "Batch Worker"
  client_secret = var.batch_worker_client_secret
}
```

## MVP の制約

Roles / Permissions 付与は本モジュールには含まない。必要であれば別途 `keycloak_role` + `keycloak_user_roles` を呼び出し側で組む。
