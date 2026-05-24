---
spec_id: TEMPLATE-CASE-CLIENTS-INDEX
title: 案件Client設計 index — テンプレ
status: template
---

# 案件Client設計 — テンプレート

> **使い方**:
> 1. このテンプレを `docs/specs/cases/<案件>/clients/index.md` にコピー
> 2. frontmatter を書き換え:
>    - `spec_id: CASE-<案件名 (UPPER-kebab)>-CLIENTS-INDEX`
>    - `status: draft`
> 3. 本文の Client 一覧表と Realm 共通設定 を埋める
> 4. 個別 client は `clients/<client_id>.md` を別途作成 ([case-client-confidential-template.md](case-client-confidential-template.md) 等を参照)
> 5. 熟練者レビュー → `status: approved`
> 6. Claude に `writing-keycloak-realm-json` skill を起動 → `keycloak/realms/<案件>.json` 生成

---

## 案件サマリ

- 案件名: (例: ACME Corporation)
- realm名 (Keycloak 内部識別子): (例: `acme-corp`)
- 概要: (顧客の認証要件を1-2文)

## Realm 共通設定

```yaml
realm: <案件のrealm名>
enabled: true
sslRequired: external          # 本番想定: external (HTTPSのみ)、dev: none
loginWithEmailAllowed: true
registrationAllowed: false
resetPasswordAllowed: true
verifyEmail: false
duplicateEmailsAllowed: false
bruteForceProtected: true
# 必要に応じて追加: passwordPolicy, accessTokenLifespan, ssoSessionIdleTimeout 等
```

## Client 一覧

| Client ID | 種別 | 用途 | 個別 spec |
| --- | --- | --- | --- |
| (例: web-app) | confidential | 顧客向けWebアプリ | [web-app.md](web-app.md) |
| (例: mobile-app) | public-spa | iOS/Android アプリ | [mobile-app.md](mobile-app.md) |
| (例: api-worker) | service-account | バッチ・サーバ間通信 | [api-worker.md](api-worker.md) |

## 設計判断 (なぜ)

- (例: Web は confidential client、 server-side で secret 保持できるため)
- (例: Mobile は PKCE 必須の public client、 device secret流出リスク回避)
- (例: バッチは service account のみ、 ユーザー認証不要のため Direct Grant も不要)

## 関連

- 案件 case-spec: [../case-spec.md](../case-spec.md) (案件全体要件)
- 使うパターン: [docs/specs/patterns/](../../../patterns/) (該当パターンへリンク)
- STG/Prod 向け Terraform: [terraform/environments/<案件>/](../../../../../terraform/environments/) (Phase G で対応)
