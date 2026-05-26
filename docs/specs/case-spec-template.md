---
spec_id: TEMPLATE-CASE-SPEC
title: 案件全体の要件入力テンプレ
status: template
---

# 案件仕様書 (Case Spec) — テンプレート

> **使い方**: このテンプレを顧客案件リポの `docs/case-spec.md` にコピーし、ヒアリング結果を埋める。
> 埋まらない欄は「未定」と書き、後でヒアリングで埋める。空欄のまま実装には進まない。
> 完成した case-spec は Claude への入力でもある — 曖昧な箇所があるとClaudeの実装も曖昧になる。
>
> **frontmatter** : コピー時に `spec_id: CASE-<案件名 (UPPER-kebab)>` に書き換え、`status: draft` で起票。
> 詳しい命名規則は [docs/specs/specs-guide.md](specs-guide.md) を参照。

---

## 1. 案件基本情報

| 項目 | 内容 |
| --- | --- |
| 顧客名 | (例: ACME株式会社) |
| プロジェクト名 | (例: ACME 認証基盤刷新) |
| 案件マネージャ | |
| 実装担当 | |
| Keycloakバージョン | (例: 26.0.7) |
| 想定リリース日 | YYYY-MM-DD |
| デプロイ先 | (例: AWS ECS / オンプレRHEL9 / ...) |
| 開発リポジトリ | (URL) |

## 2. ユーザー・テナント構成

- 想定ユーザー数: (例: 5万人)
- Realm数: (1テナント = 1Realm / 全社共通1Realm / その他)
- ユーザー種別: (一般会員 / 管理者 / 取引先 / ...)
- マイグレーション元: (既存DB / LDAP / Active Directory / 新規)

## 3. 認証要件

### 3.1 認証方式

- [ ] Username + Password (標準)
- [ ] メールアドレス + Password
- [ ] ソーシャル連携: (Google / GitHub / Microsoft / その他: ___)
- [ ] SAML IdP連携: (IdP名: ___)
- [ ] OIDC IdP連携: (IdP名: ___)
- [ ] パスワードレス (WebAuthn / Magic Link)

### 3.2 MFA

- [ ] 不要
- [ ] TOTP (Google Authenticator等)
- [ ] WebAuthn / FIDO2
- [ ] SMS (要 → 連携先SMS事業者: ___)
- [ ] 条件付きMFA (条件: ___)

### 3.3 アクセス制限

該当する場合は使用するパターンを明記。

- [ ] IPアドレス制限 → パターン: (例: なし、要新規実装)
- [ ] メールドメイン制限 → パターン: [01-email-domain-allowlist](patterns/01-email-domain-allowlist.md)
- [ ] 時間帯制限
- [ ] その他: ___

### 3.4 アカウントポリシー

- パスワードポリシー: (長さ、複雑性、有効期限)
- アカウントロック: (失敗回数、ロック時間)
- セッションタイムアウト: (アクセス / リフレッシュ)

## 4. 画面 (Theme) 要件

### 4.1 ブランディング

- ロゴ画像: (リンク or 添付)
- 主要カラー: (#xxxxxx)
- フォント: ___

### 4.2 カスタマイズする画面

- [ ] ログイン画面 (login.ftl)
- [ ] 登録画面 (register.ftl)
- [ ] パスワード再設定
- [ ] アカウント管理画面
- [ ] エラー画面
- [ ] メールテンプレ (送信メールの文面・デザイン)

各画面の変更点を具体的に列挙すること。

### 4.3 多言語

- 対応言語: (ja / en / ...)
- デフォルト言語: ___

## 5. クライアント (Realm内Client) 構成

各連携アプリごとに記入:

| Client ID | プロトコル | 用途 | リダイレクトURI | 必要スコープ |
| --- | --- | --- | --- | --- |
| (例: web-app) | OIDC | 顧客向けWebアプリ | https://app.example.com/* | openid, profile, email |

## 6. ロール・権限設計

- Realm Role: (例: admin, member, guest)
- Client Role: (各Clientごとに)
- Group: (組織階層を表現するか)
- ロール→属性のマッピング (もしあれば)

## 7. 外部システム連携

### 7.1 ユーザーストレージ (User Storage Provider)

- [ ] 既存DBから読む → 接続先: ___, 認証方式: ___
- [ ] LDAP連携 → URL, BaseDN, 同期方針
- [ ] Active Directory連携

### 7.2 監査・イベント連携 (Event Listener)

- [ ] 標準のJBoss Logging出力のみ
- [ ] Webhook通知 → 送信先URL, イベント種別
- [ ] Kafka/メッセージキュー連携
- [ ] CloudWatch/Datadog等への送信

### 7.3 SMTP

- [ ] 顧客既存SMTPサーバを使う → ホスト・ポート・認証
- [ ] AWS SES等のクラウドメール
- [ ] 開発時はMailhog (このリポ標準)

## 8. セキュリティ要件

- [ ] 監査ログの保管期間: ___
- [ ] 個人情報項目 (PII) の取り扱い: ___
- [ ] パスワードハッシュアルゴリズム指定: (デフォルトPBKDF2 / Argon2 / その他)
- [ ] TLS要件: (TLS 1.2以上 / mTLS等)
- [ ] CORS許可Origin: ___

## 9. テスト要件

- [ ] 単体テスト (SPIに対する)
- [ ] 結合テスト (Realm + Client + フローのE2E)
- [ ] 負荷試験 (目標RPS: ___)
- [ ] 受け入れテストシナリオ (顧客側で実施する項目): ___

## 10. 引き渡し物

- [ ] SPI JAR (provider用)
- [ ] Theme JAR or ディレクトリ
- [ ] Realm export JSON
- [ ] 構築手順書
- [ ] 運用手順書 (バックアップ、復旧、ユーザー追加等)
- [ ] テスト結果報告書

## 11. リスク・前提条件

ヒアリング段階で見えているリスク、保留事項、顧客に確認中の項目をここに残す。

- (例: SSO先のSaaS製品がOIDCのみ対応、SAML不可)
- (例: 既存ユーザーDBのパスワードハッシュ方式が不明 — 確認中)

---

## 仕様書から実装への落とし込み

完成した case-spec を起点に:

1. **設計段階**: 「3.3 アクセス制限」「7. 外部システム連携」等で記載したパターンを `docs/specs/patterns/` から選定。新規パターンが必要な部分を洗い出す
2. **実装段階**: 各パターンを `keycloak/providers/0N-...` に派生実装。Theme・Realmも同様
3. **テスト段階**: 「9. テスト要件」のシナリオを自動化
4. **引き渡し**: 「10. 引き渡し物」リストでチェック

Claudeに実装を任せる場合、この case-spec.md と `docs/specs/patterns/` を入力として渡せば、案件全体の作業を見積もり・着手できる状態になることを目指す。
