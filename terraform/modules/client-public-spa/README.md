# module: client-public-spa

ブラウザ SPA 向け Public Client (PKCE 必須)。secret を持たない。

## 使い方

```hcl
module "spa" {
  source              = "../../modules/client-public-spa"
  realm_id            = keycloak_realm.this.id
  client_id           = "spa-frontend"
  name                = "Example SPA"
  valid_redirect_uris = ["https://app.example.com/*"]
  web_origins         = ["https://app.example.com"]
}
```

## 入力 (variables)

| 名前 | 型 | デフォルト | 説明 |
| --- | --- | --- | --- |
| realm_id | string | (必須) | `keycloak_realm.X.id` を渡す |
| client_id | string | (必須) | OIDC client_id (例: "spa-frontend") |
| name | string | null | 表示名 |
| valid_redirect_uris | list(string) | [] | リダイレクトURIリスト |
| web_origins | list(string) | [] | CORS許可Origin |
| extra_config | map(string) | {} | Client attributes |

## 出力 (outputs)

| 名前 | 説明 |
| --- | --- |
| client_uuid | Keycloak内部UUID |
| client_id | OIDC client_id |

## 特徴

- `access_type = "PUBLIC"` : Client Secret を持たない
- `pkce_code_challenge_method = "S256"` : PKCE 必須 (Security Best Practice)
- `implicit_flow_enabled = false` : Implicit Flow は無効
- `direct_access_grants_enabled = false` : Resource Owner Password は無効
- `service_accounts_enabled = false` : Service Account は無効
