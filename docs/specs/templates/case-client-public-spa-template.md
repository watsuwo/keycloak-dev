---
spec_id: TEMPLATE-CASE-CLIENT-PUBLIC-SPA
title: Client (public SPA / Mobile) — テンプレ
status: template
---

# Public SPA / Mobile Client 設計 — テンプレート

> **使い方**:
> 1. このテンプレを `docs/specs/cases/<案件>/clients/<client_id>.md` にコピー
> 2. frontmatter を書き換え:
>    - `spec_id: CASE-<案件 (UPPER)>-CLIENT-<CLIENT_ID (UPPER-kebab)>`
>    - `status: draft`
> 3. YAML block の値を案件に合わせて埋める
>
> Public client = `client_secret` を安全に保持できないアプリ (SPA, Mobile)。
> **PKCE 必須**。

---

## 用途

(例: SPA フロントエンド。ブラウザで token を扱うため secret 非対応)

## Client 設定値

```yaml
clientId: <client-id (kebab-case)>
name: <表示名>
protocol: openid-connect

# Public のためのフラグ
publicClient: true               # secret なし
bearerOnly: false                # bearer-only にはしない (token発行する側)
serviceAccountsEnabled: false    # public は service account 不可

# フロー設定
standardFlowEnabled: true        # Authorization Code Flow + PKCE
directAccessGrantsEnabled: false # public で ROPC は危険、無効
implicitFlowEnabled: false        # 非推奨

# リダイレクト
redirectUris:
  - https://spa.example.com/*
  - http://localhost:3000/*      # ローカル開発用 (本番では削除)
  - myapp://callback             # Mobile deep link の場合
webOrigins:
  - https://spa.example.com
  - +                            # すべての redirect URI から origin を許可 (+ は Keycloak の特殊値)

# スコープ
defaultClientScopes:
  - openid
  - profile
  - email

# 属性 — PKCE 必須化
attributes:
  pkce.code.challenge.method: S256
  post.logout.redirect.uris: https://spa.example.com
  access.token.lifespan: "300"

# env 別オーバーライド (省略可、dev は base そのまま)
# 配列は完全上書き、scalar/map は env 値が優先
env:
  stg:
    redirectUris:
      - https://stg.<your-spa-domain>/*
    webOrigins:
      - https://stg.<your-spa-domain>
      - +
  prod:
    redirectUris:
      - https://<your-spa-domain>/*
    webOrigins:
      - https://<your-spa-domain>
      - +
```

## 設計判断

- **public を選んだ理由**: SPA/Mobile で client_secret を安全に保管できないため
- **PKCE 必須**: `pkce.code.challenge.method: S256` を attributes に設定。これが無いと CSRF/中間者攻撃の余地
- **directAccessGrants 無効**: public で ROPC は password が漏れた時の影響範囲が大きい
- **webOrigins `+`**: 各 redirect URI のorigin を自動許可。`*` は使わない (任意originを許可してしまう)

## 既知の限界 / 注意点

- **必ず PKCE 有効化** (`pkce.code.challenge.method` 必須)、無いと OAuth2.1 推奨に反する
- Mobile の deep link 形式 (例: `myapp://callback`) を redirectUris に含める場合、 app側で URL scheme 登録要
- Token refresh は短い lifespan が前提 (5-15分程度推奨)
