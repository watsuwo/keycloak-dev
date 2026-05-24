---
spec_id: CASE-EXAMPLE-CUSTOMER-CLIENT-BATCH-WORKER
title: example-customer batch-worker (service account)
status: implemented
implementations:
  - keycloak/realms/example-customer.json
  - terraform/environments/example-customer/dev/main.tf
  - terraform/environments/example-customer/stg/main.tf
  - terraform/environments/example-customer/prod/main.tf
---

# example-customer batch-worker (Service Account Client)

## 用途

夜間バッチ。Keycloak Admin API でユーザー集計、定期的なデータエクスポート等を実行。

## Client 設定値

```yaml
clientId: batch-worker
name: "Example Customer Batch Worker"
protocol: openid-connect

publicClient: false
serviceAccountsEnabled: true

standardFlowEnabled: false
directAccessGrantsEnabled: false
implicitFlowEnabled: false

redirectUris: []
webOrigins: []

defaultClientScopes:
  - openid

attributes:
  access.token.lifespan: "600"
```

## 設計判断

- **service account 有効化** + **standardFlow 無効**: バッチはユーザー認証なし、Client Credentials Grant のみ
- **redirectURIs 空**: ブラウザを介さない
- **token lifespan 10分**: バッチ1回の実行時間 (典型) より長め

## 既知の限界 / 注意点

- `client_secret` 漏洩 = API 全権限露出 → Vault 等で厳重管理 (本番)
- Service Account に付与する role は本番運用時に **最小権限** で設定 (admin console の Service Account タブ)
- 監査ログ: Event Listener で全アクション記録推奨
