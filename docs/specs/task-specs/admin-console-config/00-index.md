---
spec_id: TEMPLATE-ADMIN-INDEX
title: 管理コンソール設定テンプレ — 使い方ガイド
status: template
---

# 管理コンソール設定テンプレ — 使い方ガイド

このディレクトリには Keycloak 管理コンソールの設定カテゴリごとのテンプレが入っています。
各ファイルは **デフォルト値が記入済み** で、案件ごとに変更が必要な箇所だけ上書きして使います。

## 使い方フロー

```
1. 必要なテンプレファイルを docs/specs/task-specs/<案件名>/ にコピー
2. 各ファイルの「*(入力必須)*」欄を埋める
3. デフォルト値を変えたい行の「デフォルト値」列だけを上書きする
4. Claude に渡して Terraform を生成させる
   → writing-keycloak-realm-terraform スキルを使用
```

## テンプレ一覧

| ファイル | spec_id | カバーする設定 |
|---------|---------|-------------|
| [01-realm-settings.md](01-realm-settings.md) | `TEMPLATE-ADMIN-REALM-SETTINGS` | Realm基本・ログイン・パスワードポリシー・セッション/トークン |
| [02-client-confidential.md](02-client-confidential.md) | `TEMPLATE-ADMIN-CLIENT-CONFIDENTIAL` | Confidentialクライアント (Auth Code + Refresh Token) |
| [03-client-public-spa.md](03-client-public-spa.md) | `TEMPLATE-ADMIN-CLIENT-PUBLIC-SPA` | Public SPAクライアント (PKCE) |
| [04-client-service-account.md](04-client-service-account.md) | `TEMPLATE-ADMIN-CLIENT-SERVICE-ACCOUNT` | Service Accountクライアント (Client Credentials) |
| [05-roles.md](05-roles.md) | `TEMPLATE-ADMIN-ROLES` | Realm Role / Client Role |
| [06-groups.md](06-groups.md) | `TEMPLATE-ADMIN-GROUPS` | グループ構造 |
| [07-identity-provider.md](07-identity-provider.md) | `TEMPLATE-ADMIN-IDENTITY-PROVIDER` | 外部IdP (Google / Azure AD / SAML) |
| [08-auth-flow.md](08-auth-flow.md) | `TEMPLATE-ADMIN-AUTH-FLOW` | 認証フローカスタマイズ (SPI パターン参照) |
| [09-smtp.md](09-smtp.md) | `TEMPLATE-ADMIN-SMTP` | メール/SMTP設定 |

## テーブル列の読み方

| 列名 | 説明 |
|------|------|
| 項目 | Keycloak の設定項目名 |
| デフォルト値 | このテンプレが推奨するデフォルト。`*(入力必須)*` は案件ごとに必ず記入 |
| 変更する場合の条件 | デフォルト値を変えるときの根拠・条件。**変更不可** はセキュリティ要件で固定 |
| Terraform 対応キー | `keycloak/keycloak` provider のリソース属性名 |

## 廃止されたテンプレ

旧テンプレ `01-admin-console-config-template.md` は deprecated です。
このディレクトリのファイルを使ってください。
