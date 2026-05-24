---
spec_id: CASE-EXAMPLE-CUSTOMER-CLIENT-WEB-APP
title: example-customer web-app (confidential)
status: implemented
implementations:
  - keycloak/realms/example-customer.json
  - terraform/environments/example-customer/dev/main.tf
  - terraform/environments/example-customer/stg/main.tf
  - terraform/environments/example-customer/prod/main.tf
---

# example-customer web-app (Confidential Client)

## 用途

顧客向け Web アプリの BFF (Next.js)。Server-side で OAuth Code Flow を完結させ、ブラウザには HttpOnly Cookie でセッション管理。

## Client 設定値

```yaml
clientId: web-app
name: "Example Customer Web App"
protocol: openid-connect

publicClient: false
serviceAccountsEnabled: false

standardFlowEnabled: true
directAccessGrantsEnabled: false
implicitFlowEnabled: false
authorizationServicesEnabled: false

redirectUris:
  - http://localhost:3000/*
webOrigins:
  - http://localhost:3000

defaultClientScopes:
  - openid
  - profile
  - email
optionalClientScopes:
  - offline_access

attributes:
  post.logout.redirect.uris: http://localhost:3000
  access.token.lifespan: "300"

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

## 設計判断

- **confidential**: BFF (Next.js server) で `client_secret` を環境変数として保持可能
- **standardFlow有効**: Authorization Code Flow が標準
- **directAccessGrants無効**: ROPC は本番不要、security baseline で off
- **redirectURI**: ローカル開発用のみ (Phase F MVP)、本番デプロイ時に本番ドメイン追加
- **token lifespan 5分**: short-lived token + refresh で security と UX のバランス

## 既知の限界 / 注意点

- `client_secret` は Keycloak が自動生成、ローカル開発時は admin console で確認 → BFF の env に設定
- 本番ロールアウト時は redirectUris に本番URLを追加 (例: `https://app.example.com/*`)、 localhost は削除
