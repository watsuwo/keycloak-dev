---
spec_id: TEMPLATE-CASE-CLIENT-CONFIDENTIAL
title: Client (confidential) — テンプレ
status: template
---

# Confidential Client 設計 — テンプレート

> **使い方**:
> 1. このテンプレを `docs/specs/cases/<案件>/clients/<client_id>.md` にコピー
> 2. frontmatter を書き換え:
>    - `spec_id: CASE-<案件 (UPPER)>-CLIENT-<CLIENT_ID (UPPER-kebab)>`
>    - `status: draft`
> 3. YAML block の値を案件に合わせて埋める
> 4. 設計判断セクションで「なぜこの設定にしたか」を残す
>
> Confidential client = server-side で `client_secret` を安全に保持できるアプリ。
> Webアプリのサーバサイド・バックエンドAPI連携 (BFF含む) で利用。

---

## 用途

(例: 顧客向け Web アプリ。Next.js BFF が server-side で token交換を行う)

## Client 設定値

```yaml
clientId: <client-id (kebab-case)>
name: <表示名>
protocol: openid-connect

# Confidential のためのフラグ
publicClient: false
serviceAccountsEnabled: false   # service account を兼任しないなら false

# フロー設定
standardFlowEnabled: true       # Authorization Code Flow
directAccessGrantsEnabled: false # 本番は基本 false (テスト用にのみ true)
implicitFlowEnabled: false       # 非推奨フロー
authorizationServicesEnabled: false

# リダイレクト
redirectUris:
  - https://app.example.com/*
  - http://localhost:3000/*    # ローカル開発用 (本番では削除)
webOrigins:
  - https://app.example.com

# スコープ
defaultClientScopes:
  - openid
  - profile
  - email
optionalClientScopes:
  - offline_access
  - phone

# 属性
attributes:
  post.logout.redirect.uris: https://app.example.com
  access.token.lifespan: "300"      # 5分 (秒指定)

# env 別オーバーライド (省略可、dev は base そのまま)
# 配列は完全上書き、scalar/map は env 値が優先
env:
  stg:
    redirectUris:
      - https://stg.<your-domain>/*
    webOrigins:
      - https://stg.<your-domain>
  prod:
    redirectUris:
      - https://<your-domain>/*
    webOrigins:
      - https://<your-domain>
```

## 設計判断

- **confidential を選んだ理由**: (例: server-side で secret 保管できるため)
- **standardFlow有効**: Authorization Code Flow を使う標準形
- **directAccessGrants無効**: 本番では ROPC を使う理由が無い、無効化が security baseline
- **redirectUris の wildcard**: 末尾 `/*` のみ (中間や host の wildcard は使わない)
- **localhost redirect**: ローカル開発用、本番デプロイ前に削除する必要あり

## 既知の限界 / 注意点

- `secret` 値は spec に書かない (Keycloak 自動生成、runtime で別途取得)
- ローテーション時は Keycloak admin UI または `kcadm.sh` で実施
