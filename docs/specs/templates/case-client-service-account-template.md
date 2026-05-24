---
spec_id: TEMPLATE-CASE-CLIENT-SERVICE-ACCOUNT
title: Client (service account) — テンプレ
status: template
---

# Service Account Client 設計 — テンプレート

> **使い方**:
> 1. このテンプレを `docs/specs/cases/<案件>/clients/<client_id>.md` にコピー
> 2. frontmatter を書き換え:
>    - `spec_id: CASE-<案件 (UPPER)>-CLIENT-<CLIENT_ID (UPPER-kebab)>`
>    - `status: draft`
> 3. YAML block の値を案件に合わせて埋める
>
> Service Account client = サーバ間通信 (Backend ↔ API, バッチ等) で
> ユーザー認証なしに token を取得するための client。
> Client Credentials Grant を使用。

---

## 用途

(例: 夜間バッチ。Keycloak の Admin API を叩いてユーザーデータを集計する)

## Client 設定値

```yaml
clientId: <client-id (kebab-case)>
name: <表示名>
protocol: openid-connect

# Service Account のためのフラグ
publicClient: false              # confidential (secret あり)
serviceAccountsEnabled: true     # ★ 必須: service account 有効化

# フロー設定
standardFlowEnabled: false       # ブラウザフロー不要
directAccessGrantsEnabled: false # ユーザー認証不要
implicitFlowEnabled: false

# リダイレクト不要 (ブラウザ経由しないため空)
redirectUris: []
webOrigins: []

# スコープ
defaultClientScopes:
  - openid
optionalClientScopes: []

# 属性
attributes:
  access.token.lifespan: "600"   # 10分 (バッチ用にやや長め)
```

> Service Account client は通常 redirectUris/webOrigins を持たないため、env: ブロックは省略可。
> Client Secret は env 別に異なる値を `terraform.tfvars` で注入 (spec / realm.json には書かない)。

## 設計判断

- **service account 有効化**: `serviceAccountsEnabled: true` で Client Credentials Grant を許可
- **standardFlow / directAccessGrants 無効**: ブラウザ・ユーザー認証は使わない
- **redirectUris 空**: ブラウザ経由しないので不要
- **必要なロール付与**: Keycloak admin UI で Service Account タブから、API実行に必要な realm/client role を付与する (例: `realm-admin`、`manage-users` 等)

## 既知の限界 / 注意点

- **secret 管理が重要**: service account の secret 漏洩 = API 全権限が露出。Vault 等で厳重に管理
- **Token lifespan は要件次第**: バッチ実行時間より長めに設定 (短すぎると refresh 必要に)
- **権限最小化**: Service Account に付与する role は必要最小限に。`realm-admin` は強すぎるので避ける
- **監査ログ**: Service Account のアクション はEvent Listener で全件記録推奨
