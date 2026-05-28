---
spec_id: TEMPLATE-ADMIN-SMTP
title: SMTP 設定テンプレ (デフォルト値付き)
status: template
---

# SMTP 設定テンプレ

> **使用判断**: Keycloak からメール送信 (パスワードリセット、メール検証等) が必要な場合に使用。
> メール送信不要な案件はこのファイルを使わない。

## SMTP 設定

| 項目 | デフォルト値 | 変更する場合の条件 | Terraform 対応キー |
|------|------------|-----------------|------------------|
| Host | *(入力必須)* (dev: `mailhog`) | — | `host` |
| Port | `587` | dev 環境 (Mailhog) → `1025`、SSL 使用 → `465` | `port` |
| From アドレス | *(入力必須)* (例: noreply@example.com) | — | `from` |
| From 表示名 | *(入力必須)* (例: Example Corp) | — | `from_display_name` |
| 認証有効 | `true` | dev 環境 (Mailhog) → `false` | `auth` |
| STARTTLS | `true` | SSL (port 465) を使う場合 → STARTTLS `false`、SSL `true` | `starttls` |
| SSL | `false` | port 465 使用時 → `true` | `ssl` |
| Username | *(入力必須)* | dev 環境 → 空欄 可 | `user` |
| Password | **Vault 参照** (tfvars に直書き不可) | — | `password` |
| Reply-To | *(省略可)* | サポート窓口への返信が必要な場合に設定 | `reply_to` |

## 環境別設定の例

| 環境 | Host | Port | Auth | STARTTLS |
|------|------|------|------|---------|
| dev (Mailhog) | `mailhog` | `1025` | `false` | `false` |
| staging | *(本番と同じ SMTP サーバを推奨)* | `587` | `true` | `true` |
| production | *(入力必須)* | `587` | `true` | `true` |

## 設計判断メモ (案件ごとに記入)

- **SMTP サービスの選定**: (例: AWS SES / SendGrid / 社内 SMTP)
- **Password 管理**: (例: GitHub Actions Secret / Vault)
