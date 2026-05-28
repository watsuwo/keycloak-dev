---
spec_id: TEMPLATE-ADMIN-ROLES
title: ロール設定テンプレ (デフォルト値付き)
status: template
---

# ロール設定テンプレ

## Realm Role

| Role 名 | 説明 | 新規ユーザーへの自動付与 | Terraform リソース |
|---------|------|----------------------|------------------|
| `user` | 一般ユーザー | `true` (default role) | `keycloak_role` |
| `admin` | 管理者 | `false` | `keycloak_role` |
| *(追加がある場合はここに列を追加)* | | | |

> **変更条件**: ロール構成は要件に応じて自由に変更可。
> `user` ロールを default role にするのはほとんどの B2B/B2C 案件で有効。
> RBAC が不要な場合はロールを作らなくてよい。

## Client Role (Client ごとに記入、必要な場合のみ)

| Client ID | Role 名 | 説明 |
|-----------|---------|------|
| *(Client ID)* | *(Role 名)* | *(説明)* |

> **変更条件**: Client Role は fine-grained なアクセス制御が必要な場合のみ使用。
> Realm Role だけで要件が満たせる場合は Client Role を作らない (シンプルさを優先)。

## 設計判断メモ (案件ごとに記入)

- **ロール設計の方針**: (例: Realm Role のみで管理、Client Role は不使用)
- **default role の選択**: (例: `user` を default role にした理由)
