---
spec_id: TEMPLATE-ADMIN-REALM-SETTINGS
title: Realm 設定テンプレ (デフォルト値付き)
status: template
---

# Realm 設定テンプレ

案件ごとに `*(入力必須)*` 欄を埋め、変えたい行の「デフォルト値」列を上書きしてください。

## 基本情報

| 項目 | 値 |
|------|----|
| 案件名 / 顧客名 | *(入力必須)* |
| Realm 名 (英小文字 kebab-case) | *(入力必須)* (例: acme-corp) |
| Keycloak バージョン | *(入力必須)* (例: 26.0.8) |

## 1. Realm 基本設定

| 項目 | デフォルト値 | 変更する場合の条件 | Terraform 対応キー |
|------|------------|-----------------|------------------|
| 表示名 | *(入力必須)* | — | `display_name` |
| SSL 要件 | `external` | 完全閉域網のみ → `none`、全通信 TLS 必須 → `all` | `ssl_required` |
| ユーザー自己登録 | `false` | 一般公開 B2C サービス → `true` | `registration_allowed` |
| メールでログイン | `true` | — | `login_with_email_allowed` |
| パスワードリセット | `true` | — | `reset_password_allowed` |
| Remember Me | `false` | セキュリティ要件が緩い B2C → `true` | `remember_me` |
| メール検証必須 | `true` | dev 環境 → `false` 可 (本番は `true` 固定) | `verify_email` |
| ブルートフォース保護 | `true` | **変更不可** (セキュリティ必須) | `brute_force_protected` |

## 2. パスワードポリシー

> Terraform では `password_policy` 属性に文字列で渡す。例:
> `"length(12) and upperCase(1) and digits(1) and specialChars(1) and notUsername() and passwordHistory(5)"`

| 項目 | デフォルト値 | 変更する場合の条件 |
|------|------------|-----------------|
| 最小文字長 | `12` | 規制業界 (金融・医療) → `16` 以上推奨 |
| 大文字必須 | `true` | — |
| 数字必須 | `true` | — |
| 特殊文字必須 | `true` | — |
| ユーザー名を含まない | `true` | **変更不可** |
| ハッシュアルゴリズム | `pbkdf2-sha256` | 高セキュリティ要件 → `argon2` (CPU コスト増) |
| パスワード履歴 | `5` (過去5回) | 規制業界 → `10` 以上推奨 |

## 3. セッション / トークン期限

| 項目 | デフォルト値 | 変更する場合の条件 | Terraform 対応キー |
|------|------------|-----------------|------------------|
| Access Token Lifespan | `300` (5分) | B2C 利便性重視 → `900` (15分)、金融/医療 → `60` (1分) | `access_token_lifespan` |
| SSO Session Idle Timeout | `1800` (30分) | — | `sso_session_idle_timeout` |
| SSO Session Max Lifespan | `36000` (10時間) | 金融/医療 → `3600` (1時間) 以下を推奨 | `sso_session_max_lifespan` |
| Offline Session Idle | `2592000` (30日) | セキュリティ要件に応じて短縮 | `offline_session_idle_timeout` |
| Offline Session Max | `5184000` (60日) | — | `offline_session_max_lifespan` |

## 設計判断メモ (案件ごとに記入)

- **SSL 要件の選択**: (例: external を選んだ理由、または変更した場合の理由)
- **パスワードポリシーの強度**: (例: 規制業界要件に合わせて最小長を変更した場合の理由)
- **セッション期限の設定**: (例: UX とセキュリティのバランスで SSO Session Max を変更した場合の理由)
