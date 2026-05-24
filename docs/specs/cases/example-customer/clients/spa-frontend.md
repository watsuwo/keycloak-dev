---
spec_id: CASE-EXAMPLE-CUSTOMER-CLIENT-SPA-FRONTEND
title: example-customer spa-frontend (public SPA)
status: implemented
implementations:
  - keycloak/realms/example-customer.json
  - terraform/environments/example-customer/dev/main.tf
  - terraform/environments/example-customer/stg/main.tf
  - terraform/environments/example-customer/prod/main.tf
---

# example-customer spa-frontend (Public SPA Client)

## 用途

SPA フロントエンド (React 想定)。ブラウザで直接 token を扱うため PKCE 必須。

## Client 設定値

```yaml
clientId: spa-frontend
name: "Example Customer SPA"
protocol: openid-connect

publicClient: true
bearerOnly: false
serviceAccountsEnabled: false

standardFlowEnabled: true
directAccessGrantsEnabled: false
implicitFlowEnabled: false

redirectUris:
  - http://localhost:3001/*
webOrigins:
  - http://localhost:3001
  - +

defaultClientScopes:
  - openid
  - profile
  - email

attributes:
  pkce.code.challenge.method: S256
  post.logout.redirect.uris: http://localhost:3001
  access.token.lifespan: "300"

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

## 設計判断

- **public**: SPA で client_secret 安全保持不可、PKCE で代替
- **PKCE S256**: 推奨 (plain は非推奨)、attributes で必須化
- **webOrigins に `+`**: redirect URI 各々の origin を自動許可、`*` は使わない
- **directAccessGrants無効**: public で ROPC は危険

## 既知の限界 / 注意点

- 本番ロールアウト時に redirect URI を本番ドメインに切り替え + localhost 削除
- token は LocalStorage より sessionStorage / memory推奨 (XSS耐性)
