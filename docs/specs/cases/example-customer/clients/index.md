---
spec_id: CASE-EXAMPLE-CUSTOMER-CLIENTS-INDEX
title: example-customer Client設計
status: implemented
implementations:
  - keycloak/realms/example-customer.json
---

# example-customer Client 設計

## 案件サマリ

- 案件名: Example Customer (雛形リポのサンプル案件)
- realm名: `example-customer`
- 概要: Web + Mobile + バッチワーカーの3アプリ構成。Phase F MVP のサンプル案件

## Realm 共通設定

```yaml
realm: example-customer
enabled: true
sslRequired: none              # devで HTTP 通信可能にする (本番は external)
loginWithEmailAllowed: true
registrationAllowed: false
resetPasswordAllowed: true
verifyEmail: false
duplicateEmailsAllowed: false
bruteForceProtected: true
displayName: "Example Customer"
```

## Client 一覧

| Client ID | 種別 | 用途 | 個別 spec |
| --- | --- | --- | --- |
| web-app | confidential | 顧客向けWebアプリ (Next.js BFF) | [web-app.md](web-app.md) |
| spa-frontend | public-spa | SPA フロントエンド (React) | [spa-frontend.md](spa-frontend.md) |
| batch-worker | service-account | 夜間バッチ・サーバ間通信 | [batch-worker.md](batch-worker.md) |

## 設計判断

- **3 client構成にした理由**: Web (server-side) / SPA (browser) / バッチ (server-to-server) で **保持できる secret の有無** が異なるため、 client を分離して攻撃面を最小化
- **web-app を confidential**: BFF で server-side token交換するので secret 保持可
- **spa-frontend を public**: ブラウザで secret 持てない、PKCE で代替
- **batch-worker を service account**: ユーザー認証なしで API 叩く、Client Credentials Grant 専用
- **同 realm に同居**: 3 アプリは同じ ACME 顧客のものなので 1 realm でまとめる (顧客毎に realm 分離するのが本リポの慣行)

## 関連

- 案件 case-spec: (Phase F MVP のため未作成、サンプル案件は本ファイルが起点)
- Phase F: [docs/architecture.md](../../../../architecture.md) ADR-012
- STG/Prod 向け Terraform: [terraform/environments/example-customer/](../../../../../terraform/environments/example-customer/) (Phase G で本 spec から自動生成予定)
