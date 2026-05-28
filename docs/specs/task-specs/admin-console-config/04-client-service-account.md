---
spec_id: TEMPLATE-ADMIN-CLIENT-SERVICE-ACCOUNT
title: Service Account クライアント設定テンプレ (デフォルト値付き)
status: template
---

# Service Account クライアント設定テンプレ

**用途**: バックグラウンドジョブ・バッチ処理・M2M 通信など、ユーザーが介在しないシステム間連携。
Client Credentials Grant (`grant_type=client_credentials`) を使用。

Terraform モジュール: `terraform/modules/client-service-account`

---

## Client 設定

| 項目 | デフォルト値 | 変更する場合の条件 | Terraform 対応キー |
|------|------------|-----------------|------------------|
| Client ID | *(入力必須)* (例: batch-worker) | — | `client_id` |
| 表示名 | *(入力必須)* | — | `name` |
| Client Secret | 自動生成 | **直書き不可** (Vault / Secret Manager から注入) | `client_secret` |
| Public Client | `false` | **変更不可** (Service Account は常に Confidential) | `public_client` |
| Standard Flow | `false` | **変更不可** (ユーザーフローは不要) | `standard_flow_enabled` |
| Implicit Flow | `false` | **変更不可** | `implicit_flow_enabled` |
| Direct Access Grants | `false` | **変更不可** | `direct_access_grants_enabled` |
| Service Account | `true` | **変更不可** | `service_accounts_enabled` |

## Service Account ロール割り当て

| ロール | デフォルト | 変更条件 |
|-------|-----------|--------|
| Realm Role | *(入力必須)* | このクライアントが使うロールを明示 |
| Client Role | *(必要な場合のみ入力)* | — |

## 設計判断メモ (案件ごとに記入)

- **最小権限の原則**: 必要なロールのみ付与、`realm-admin` 等の強力なロールを避ける
- **Secret ローテーション**: Keycloak 管理 UI または `kcadm.sh` で定期ローテーション
- **Token Lifespan**: Service Account の Access Token はデフォルト 5分。長時間バッチの場合は `access_token_lifespan` を延ばすか、Token を都度取り直すロジックにする
