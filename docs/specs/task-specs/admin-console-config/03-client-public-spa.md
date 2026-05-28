---
spec_id: TEMPLATE-ADMIN-CLIENT-PUBLIC-SPA
title: Public SPA クライアント設定テンプレ (デフォルト値付き)
status: template
---

# Public SPA クライアント設定テンプレ

**用途**: ブラウザ上で動作する SPA (React / Vue / Angular 等)。
`client_secret` を安全に保持できないため Public Client として設定し PKCE を必須にする。

Terraform モジュール: `terraform/modules/client-public-spa`

---

## Client 設定

| 項目 | デフォルト値 | 変更する場合の条件 | Terraform 対応キー |
|------|------------|-----------------|------------------|
| Client ID | *(入力必須)* (例: spa-frontend) | — | `client_id` |
| 表示名 | *(入力必須)* | — | `name` |
| Public Client | `true` | **変更不可** (SPA は常に Public) | `public_client` |
| PKCE Code Challenge Method | `S256` | **変更不可** (S256 のみ許可) | `pkce_code_challenge_method` |
| Standard Flow (Auth Code) | `true` | **変更不可** | `standard_flow_enabled` |
| Implicit Flow | `false` | **変更不可** (非推奨) | `implicit_flow_enabled` |
| Direct Access Grants | `false` | **変更不可** (SPA では使用不可) | `direct_access_grants_enabled` |
| Service Account | `false` | **変更不可** | `service_accounts_enabled` |
| Valid Redirect URIs | *(入力必須)* (例: `["https://spa.example.com/*"]`) | — | `valid_redirect_uris` |
| Web Origins | *(入力必須)* (例: `["https://spa.example.com"]`) | CORS 対象ドメイン | `web_origins` |
| Post Logout Redirect URI | *(入力必須)* | — | `attributes.post.logout.redirect.uris` |

## スコープ設定

| スコープ | デフォルト | 変更条件 |
|---------|-----------|--------|
| openid | デフォルト追加 | — |
| profile | デフォルト追加 | — |
| email | デフォルト追加 | — |
| offline_access | オプション | Silent Refresh が不要で Refresh Token を使う場合 |

## 設計判断メモ (案件ごとに記入)

- **PKCE 必須**: Authorization Code + PKCE が SPA のセキュリティベースライン (RFC 9700)
- **Redirect URIs**: ローカル開発用 `http://localhost:*` は本番デプロイ前に削除すること
