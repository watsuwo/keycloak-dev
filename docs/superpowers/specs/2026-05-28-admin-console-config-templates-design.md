# デザイン: Keycloak 管理コンソール設定テンプレ (admin-console-config)

**日付:** 2026-05-28  
**ステータス:** 承認済み  
**対象ディレクトリ:** `docs/specs/task-specs/admin-console-config/`

---

## 背景・目的

既存の `01-admin-console-config-template.md` は全設定を1ファイルに詰め込んだ記入テンプレだが、
以下の問題がある:

- デフォルト値が明示されていない (空欄を埋めるだけ)
- 変更すべき理由・条件が書かれていない
- 全セクションが混在しているためClaudeへの部分的な渡し方が難しい

新しいテンプレ群は**設定カテゴリごとに分割**し、**デフォルト値付き**にすることで、
案件ごとの差分入力だけでTerraform生成ができるようにする。

---

## ディレクトリ構造

```
docs/specs/task-specs/admin-console-config/
  00-index.md                    ← 使い方ガイド
  01-realm-settings.md           ← Realm基本+ログイン+パスワードポリシー+セッション/トークン
  02-client-confidential.md      ← Confidentialクライアント (Auth Code + Refresh Token)
  03-client-public-spa.md        ← Public SPAクライアント (PKCE)
  04-client-service-account.md   ← Service Accountクライアント (Client Credentials)
  05-roles.md                    ← Realm Role / Client Role
  06-groups.md                   ← グループ構造
  07-identity-provider.md        ← 外部IdP (Google / Azure AD / SAML)
  08-auth-flow.md                ← 認証フローカスタマイズ (SPI pattern参照)
  09-smtp.md                     ← メール/SMTP設定
```

---

## spec_id 命名規則

形式: `TEMPLATE-ADMIN-<NAME>`

| ファイル | spec_id |
|---------|---------|
| 00-index.md | `TEMPLATE-ADMIN-INDEX` |
| 01-realm-settings.md | `TEMPLATE-ADMIN-REALM-SETTINGS` |
| 02-client-confidential.md | `TEMPLATE-ADMIN-CLIENT-CONFIDENTIAL` |
| 03-client-public-spa.md | `TEMPLATE-ADMIN-CLIENT-PUBLIC-SPA` |
| 04-client-service-account.md | `TEMPLATE-ADMIN-CLIENT-SERVICE-ACCOUNT` |
| 05-roles.md | `TEMPLATE-ADMIN-ROLES` |
| 06-groups.md | `TEMPLATE-ADMIN-GROUPS` |
| 07-identity-provider.md | `TEMPLATE-ADMIN-IDENTITY-PROVIDER` |
| 08-auth-flow.md | `TEMPLATE-ADMIN-AUTH-FLOW` |
| 09-smtp.md | `TEMPLATE-ADMIN-SMTP` |

---

## テーブルフォーマット

各設定ファイルは以下の4列テーブルで設定を記述する:

| 項目 | デフォルト値 | 変更する場合の条件 | Terraform 対応キー |
|------|------------|-----------------|------------------|
| SSL 要件 | `external` | 閉域網のみ → `none`、全暗号化必須 → `all` | `ssl_required` |

**表記ルール:**
- `*(入力必須)*` = 案件ごとに必ず埋める空白値
- **変更不可** = セキュリティ要件で固定の項目
- Keycloak 26.x のデフォルト値と異なる場合は理由を変更条件列に明記

---

## 使い方フロー

```
1. 必要な spec ファイルを docs/specs/task-specs/<案件名>/ にコピー
2. 各ファイルの「*(入力必須)*」欄を埋める
3. デフォルト値を変えたい行だけ「デフォルト値」列を上書き
4. Claude に渡して Terraform を生成させる (writing-keycloak-realm-terraform スキル)
```

---

## 既存ファイルの処置

`docs/specs/task-specs/01-admin-console-config-template.md` を `status: deprecated` に変更し、
本体を新ディレクトリへのリンクで置き換える。

---

## 実装スコープ (writing-plans への引き渡し)

1. `docs/specs/task-specs/admin-console-config/` ディレクトリを作成
2. 各ファイルを作成 (00-index から 09-smtp まで)
3. 既存 `01-admin-console-config-template.md` を deprecated に更新
4. `make spec-validate` が green になることを確認
