---
spec_id: TEMPLATE-TASK-ADMIN-CONSOLE
title: 管理コンソール設定 task-spec テンプレ (非推奨)
status: deprecated
---

> **⚠️ このファイルは deprecated です。**
> 代わりに [`docs/specs/task-specs/admin-console-config/`](admin-console-config/) のテンプレを使用してください。
> デフォルト値付きでカテゴリごとに分割されています。

---

# Task Spec: 管理コンソール設定 — テンプレート

> **使い方**:
> 1. このテンプレを `docs/specs/task-specs/<案件名>-admin-console.md` (顧客リポ側) にコピー
> 2. **frontmatter を書き換え** : `spec_id: TASK-<案件名 (UPPER-kebab)>-ADMIN-CONSOLE`、`status: draft`
> 3. ジュニアが顧客ヒアリングを元に空欄を埋める (不明欄は「未確認」と書いて顧客に確認)
> 4. 熟練者がレビュー → パターン選定や設計判断を確定 → `status: approved`
> 5. 完成した task-spec を Claude に渡し、`terraform/environments/<案件名>/` を生成させる
> 6. `terraform plan` の diff を熟練者レビュー → apply → 自動検証 → `status: implemented`
>
> spec_id 命名規則の詳細は [docs/specs/specs-guide.md](../specs-guide.md) を参照。

---

## 0. 基本情報

| 項目 | 値 |
| --- | --- |
| 案件名 / 顧客名 | (例: ACME株式会社) |
| Realm名 (英小文字ケバブケース) | (例: acme-corp) |
| Keycloakバージョン | (例: 26.0.8) |
| デプロイ先 (環境) | dev / staging / production |
| ドラフト担当 (ジュニア) | |
| レビュー担当 (熟練者) | |
| 期日 | YYYY-MM-DD |

## 1. Realm 設定

| 項目 | 値 | 備考 |
| --- | --- | --- |
| Realm名 | | |
| 表示名 | | ログイン画面に出る |
| SSL要件 | all / external / none | 本番は external 以上 |
| ユーザー自己登録 | yes / no | |
| メールでログイン許可 | yes / no | |
| パスワード再設定 | yes / no | |
| Remember Me | yes / no | |
| メール検証必須 | yes / no | |
| ブルートフォース保護 | yes / no | |

### パスワードポリシー

| 項目 | 値 |
| --- | --- |
| 最小長 | (例: 12) |
| 大文字含む | yes / no |
| 数字含む | yes / no |
| 特殊文字含む | yes / no |
| ハッシュアルゴリズム | pbkdf2-sha256 (default) / argon2 |
| パスワード履歴 | (例: 過去5回) |

### セッション・トークン期限

| 項目 | 値 |
| --- | --- |
| Access Token Lifespan | (例: 5分) |
| Refresh Token Lifespan | (例: 30分) |
| SSO Session Idle | (例: 30分) |
| SSO Session Max | (例: 10時間) |

## 2. Clients (連携アプリごとに記入)

### Client A

| 項目 | 値 |
| --- | --- |
| Client ID | (例: web-app) |
| 種別 | confidential / public-spa / service-account |
| 表示名 | |
| Standard Flow (Auth Code) | yes / no |
| Direct Access Grants | yes / no (本番は基本no) |
| Service Account | yes / no |
| Implicit Flow | no (基本no) |
| Valid Redirect URIs | (例: https://app.example.com/*) |
| Web Origins | (例: https://app.example.com) |
| 必要なScope | (例: openid, profile, email) |
| 利用モジュール | `terraform/modules/client-confidential` 等 |

(Client が複数ある場合は上記表を複製)

## 3. Roles

### Realm Role

| Role名 | 説明 | 自動付与 (default) |
| --- | --- | --- |
| (例: user) | 一般ユーザー | yes |
| (例: admin) | 管理者 | no |

### Client Role (該当する場合、Client毎に)

| Client | Role名 | 説明 |
| --- | --- | --- |
| | | |

## 4. Groups (該当する場合)

| Group名 | 親 | デフォルトRole |
| --- | --- | --- |
| | | |

## 5. Identity Provider 連携 (外部SSOがあれば)

| 項目 | 値 |
| --- | --- |
| 種別 | google / azure-ad / saml / oidc-generic |
| Alias | (例: google) |
| Client ID | |
| Client Secret | (Vault等から注入、tfvarsに直書きしない) |
| Issuer URL (OIDC) | |
| メタデータURL (SAML) | |
| 自動ユーザー紐づけ | first broker login flow / always |
| 属性マッピング | (例: email → email, name → fullName) |

## 6. Authentication Flow カスタマイズ (該当する場合)

| 項目 | 値 |
| --- | --- |
| カスタムフロー必要 | yes / no |
| 使用パターン | (例: docs/specs/patterns/01-email-domain-allowlist) |
| 適用先フロー | browser / direct-grant / reset-credentials |

カスタムフローが必要な場合は別途 `02-spi-customization` task-spec を作る。

## 7. SMTP 設定 (メール送信が必要なら)

| 項目 | 値 |
| --- | --- |
| Host | (例: smtp.example.com / dev: mailhog) |
| Port | (例: 587 / dev: 1025) |
| 認証 | yes / no |
| TLS / STARTTLS | |
| From アドレス | |
| From 表示名 | |

## 8. テスト用ユーザー (検証用、本番には作らない)

| Username | Email | Roles | 用途 |
| --- | --- | --- | --- |
| testuser | testuser@example.com | user | 一般ユーザーフロー確認 |
| testadmin | testadmin@example.com | admin | 管理者フロー確認 |

## 9. 受け入れ条件 (自動検証で確認する項目)

- [ ] `terraform apply` が成功する
- [ ] 各 Client で指定の認証フローでトークン取得できる
- [ ] Direct Grant が無効なクライアントで Direct Grant が拒否される
- [ ] 各 Role が想定通り付与される
- [ ] (IdP連携あれば) リダイレクトが正しく発生する
- [ ] (カスタムフローあれば) 該当パターンの IT が通る

## 10. 備考・特記事項

- (顧客固有の制約、未確定事項、過去案件との差分など)
- (例: 既存顧客DBからのユーザーマイグレーション要否)

---

## Claude への引き渡し時のチェックリスト

このtask-specを Claude に渡す前に:

- [ ] 0-9 のうち、N/A 以外の欄に「未確認」が残っていない
- [ ] Client種別が `terraform/modules/` に存在するモジュールに対応している、または新規モジュール作成タスクを別途切っている
- [ ] Secrets (Client Secret等) は値を書かず「Vault参照」または「自動生成」と明記
- [ ] 受け入れ条件 (9) が具体的にテスト可能な形になっている
