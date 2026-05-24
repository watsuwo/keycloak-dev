# module: client-confidential

OIDC Confidential Client (サーバーサイドWebアプリ等、`client_secret` を安全に保持できるアプリ向け) を作成する。

## 使い方

```hcl
module "web_app" {
  source = "../../modules/client-confidential"

  realm_id  = keycloak_realm.this.id
  client_id = "web-app"
  name      = "Customer Web App"

  valid_redirect_uris = [
    "https://app.example.com/*",
    "http://localhost:3000/*"  # local dev用
  ]
  web_origins = ["https://app.example.com"]

  standard_flow_enabled        = true
  direct_access_grants_enabled = false  # 本番では基本 false
  service_accounts_enabled     = false
}
```

## 入力 (variables)

| 名前 | 型 | デフォルト | 説明 |
| --- | --- | --- | --- |
| realm_id | string | (必須) | `keycloak_realm.X.id` を渡す |
| client_id | string | (必須) | OIDC client_id (例: "web-app") |
| name | string | null | 表示名 |
| valid_redirect_uris | list(string) | [] | リダイレクトURIリスト |
| web_origins | list(string) | [] | CORS許可Origin |
| standard_flow_enabled | bool | true | Auth Code Flow を許可 |
| direct_access_grants_enabled | bool | false | Password Grant を許可 |
| service_accounts_enabled | bool | false | Client Credentials を許可 |
| client_secret | string | null | 自動生成 (推奨) |

## 出力 (outputs)

| 名前 | 説明 |
| --- | --- |
| client_uuid | Keycloak内部UUID |
| client_id | OIDC client_id |
| client_secret | 発行されたシークレット (sensitive) |

## 関連モジュール (今後追加予定)

- `client-public-spa` : SPA用 public client (PKCE必須)
- `client-service-account` : Client Credentials Grant専用
