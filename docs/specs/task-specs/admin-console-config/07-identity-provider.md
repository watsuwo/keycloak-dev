---
spec_id: TEMPLATE-ADMIN-IDENTITY-PROVIDER
title: 外部 IdP 連携設定テンプレ (デフォルト値付き)
status: template
---

# 外部 IdP 連携設定テンプレ

> **使用判断**: Google / Azure AD / 社内 SAML 等の外部 IdP と連携する場合のみこのファイルをコピー。
> 外部 IdP 連携が不要な案件はこのファイルを使わない。

IdP が複数ある場合は「## IdP 設定」セクションを複製してください。

## IdP 設定

| 項目 | デフォルト値 | 変更する場合の条件 | Terraform 対応キー |
|------|------------|-----------------|------------------|
| 種別 | *(入力必須)* (google / oidc / saml / azure-ad) | — | `provider_id` |
| Alias | *(入力必須)* (例: google) | URL の一部になる。変更時はユーザーの紐づけが壊れる | `alias` |
| 表示名 | *(入力必須)* (例: Google でログイン) | — | `display_name` |
| Client ID | *(入力必須)* | — | `extra_config.clientId` |
| Client Secret | **Vault 参照** (tfvars に直書き不可) | — | `extra_config.clientSecret` |
| Issuer URL (OIDC) | *(入力必須。SAML の場合は不要)* | — | `extra_config.issuer` |
| メタデータ URL (SAML) | *(入力必須。OIDC の場合は不要)* | — | `extra_config.metadataDescriptorUrl` |
| 初回ログイン時のフロー | `first broker login` | 既存ユーザーと自動紐づけが必要 → `detect existing broker user` | `first_broker_login_flow_alias` |
| トークン保存 (Store Tokens) | `false` | IdP の Access Token を Keycloak に保存したい場合 → `true` | `store_token` |
| ユーザー自動作成 | `true` (first broker login flow で制御) | 既存ユーザーのみ受け入れる → first broker login flow を変更 | (first_broker_login_flow_alias で制御) |

## 属性マッピング

| IdP 属性 | Keycloak 属性 | デフォルト設定 |
|---------|-------------|------------|
| `email` | `email` | 自動マッピング |
| `name` | `firstName` / `lastName` | 自動マッピング (IdP による) |
| *(追加属性)* | *(Keycloak 属性名)* | *(必要な場合のみ追加)* |

## 設計判断メモ (案件ごとに記入)

- **IdP を選んだ理由**: (例: 顧客が Google Workspace を使っているため)
- **Alias を変えない方針**: Alias はログイン後の内部 ID に影響するため、一度決めたら変更しない
- **Client Secret の管理**: (例: GitHub Actions Secret / Vault / AWS Secrets Manager)
