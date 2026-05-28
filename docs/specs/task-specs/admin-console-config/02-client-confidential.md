---
spec_id: TEMPLATE-ADMIN-CLIENT-CONFIDENTIAL
title: Confidential クライアント設定テンプレ (デフォルト値付き)
status: template
---

# Confidential クライアント設定テンプレ

**用途**: server-side で `client_secret` を安全に保持できるアプリ。
Web アプリのサーバサイド、BFF、バックエンド API 連携に利用。

Terraform モジュール: `terraform/modules/client-confidential`

クライアントが複数ある場合はこのテンプレを複製して使用。

---

## Client 設定

| 項目 | デフォルト値 | 変更する場合の条件 | Terraform 対応キー |
|------|------------|-----------------|------------------|
| Client ID | *(入力必須)* (例: web-app) | — | `client_id` |
| 表示名 | *(入力必須)* | — | `name` |
| Client Secret | 自動生成 | **直書き不可** (Terraform で `sensitive` 変数) | `client_secret` |
| Standard Flow (Auth Code) | `true` | **変更不可** | `standard_flow_enabled` |
| Implicit Flow | `false` | **変更不可** (非推奨フロー) | `implicit_flow_enabled` |
| Direct Access Grants | `false` | 開発・テスト用途のみ `true` (本番は `false` 必須) | `direct_access_grants_enabled` |
| Service Account | `false` | Confidential + Service Account 兼任が必要な場合 → `true` | `service_accounts_enabled` |
| Valid Redirect URIs | *(入力必須)* (例: `["https://app.example.com/*"]`) | — | `valid_redirect_uris` |
| Web Origins | *(入力必須)* (例: `["https://app.example.com"]`) | — | `web_origins` |
| Post Logout Redirect URI | *(入力必須)* (例: `https://app.example.com`) | — | `attributes.post.logout.redirect.uris` |
| Access Token Lifespan (Override) | Realm デフォルトを継承 | クライアント固有で短縮する場合のみ設定 (秒) | `access_token_lifespan` |

## スコープ設定

| スコープ | デフォルト | 変更条件 |
|---------|-----------|--------|
| openid | デフォルト追加 | — |
| profile | デフォルト追加 | — |
| email | デフォルト追加 | — |
| offline_access | オプション | Refresh Token (長期) が必要な場合はデフォルトへ移動 |
| phone | オプション | 電話番号属性が必要な場合のみ |

## 設計判断メモ (案件ごとに記入)

- **このクライアントを confidential にした理由**: (記入)
- **Direct Access Grants を有効化した場合の理由**: (本番では必ず無効化すること)
- **Redirect URIs の wildcard 方針**: 末尾 `/*` のみ使用、ホスト部分の wildcard は使わない
