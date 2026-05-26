---
spec_id: PATTERN-AUTH-DOMAIN-ALLOWLIST
title: Email Domain Allowlist Authenticator
status: implemented
implementations:
  - keycloak/providers/01-email-domain-allowlist/
acceptance_tests:
  - keycloak/providers/01-email-domain-allowlist/src/test/java/com/example/keycloak/authenticators/emaildomain/EmailDomainAllowlistAuthenticatorTest.java
  - keycloak/providers/integration-tests/src/test/java/com/example/keycloak/it/EmailDomainAllowlistIT.java
  - e2e-tests/tests/email-domain-allowlist-browser.spec.ts
---

# パターン 01: Email Domain Allowlist Authenticator

特定のメールドメインを持つユーザーのみログインを許可する Keycloak Authenticator。

## 適用判断

このパターンを使うのはこんなとき:

- **B2B SaaS** で「契約顧客の社内ドメインを持つユーザーのみ」許可したい
- **社内システム** で「会社のメールアドレスを持つユーザーのみ」許可したい
- 既存のソーシャルログイン (Google/Microsoft) を活かしつつ、ドメインで弾きたい

**このパターンを使わない方が良いケース**:

- IPアドレスでの制限が要件 → 別パターン (IP Allowlist) を作る
- ユーザー属性 (department等) での制限 → ProtocolMapper + Conditional Authenticator パターン
- ワイルドカード `*.example.com` で網羅したい → 本パターンを拡張する

## 仕様

- 設定: `allowedDomains` (複数指定可、`##` 区切り保存)
- 動作: ユーザーのメールアドレスのドメイン部分 (大小無視、trim済) が `allowedDomains` のいずれかに完全一致 → 許可
- 設定が空 → 制限なし (常に許可)
- ユーザーが未解決 (前段で特定されていない) → `attempted()` で判定スキップ
- メールアドレスが空・不正形式 → `INVALID_USER` で失敗

## Keycloak管理コンソールでの設定手順

1. **Authentication → Flows** で既存のbrowserフローを複製
   - 例: "browser" を複製して "browser-with-domain-check" に
2. 複製したフローのステップ末尾に **Email Domain Allowlist** を追加
   - Requirement: **REQUIRED**
3. ⚙ (歯車) アイコン → 設定で **許可するドメイン** に追加
   - 例: `example.com`, `corp.example`
4. **Authentication → Bindings** タブで **Browser Flow** を `browser-with-domain-check` に切替

## 実装の場所

- ソース: [keycloak/providers/01-email-domain-allowlist/](../../../keycloak/providers/01-email-domain-allowlist/)
- Authenticator: [EmailDomainAllowlistAuthenticator.java](../../../keycloak/providers/01-email-domain-allowlist/src/main/java/com/example/keycloak/authenticators/emaildomain/EmailDomainAllowlistAuthenticator.java)
- Factory: [EmailDomainAllowlistAuthenticatorFactory.java](../../../keycloak/providers/01-email-domain-allowlist/src/main/java/com/example/keycloak/authenticators/emaildomain/EmailDomainAllowlistAuthenticatorFactory.java)
- テスト: [EmailDomainAllowlistAuthenticatorTest.java](../../../keycloak/providers/01-email-domain-allowlist/src/test/java/com/example/keycloak/authenticators/emaildomain/EmailDomainAllowlistAuthenticatorTest.java)

## 派生・カスタマイズ

このパターンから派生させやすい改造:

| 派生 | 変更点 |
| --- | --- |
| ワイルドカード対応 | `readAllowedDomains()` で `*.example.com` 形式をサフィックスマッチに変換 |
| 拒否リスト (Blocklist) 化 | 判定ロジックを反転 (一致したら拒否) + Factory.getDisplayType() 変更 |
| 属性ベース制限 | `user.getEmail()` を `user.getFirstAttribute("department")` 等に置換 |
| ドメインごとに別フローへ分岐 | `Authenticator` を `ConditionalAuthenticator` に変更してフロー側で条件分岐 |

## テスト

単体テストは Mockito で `AuthenticationFlowContext` をモックして判定ロジックを検証 (パターン1個目のお手本)。

```bash
cd keycloak/providers/01-email-domain-allowlist
mvn test
```

結合テスト (Phase 3で整備予定) では Keycloak Testcontainers でRealm作成 + フロー設定 + 実際のログインで挙動を検証する。

## 既知の限界

- Email属性が未設定のユーザーは弾かれる → 案件によってはユーザー登録時にemail必須化が必要
- SAML/OIDC ブローカリングで初回ログインの場合、UserModelに反映されているemailを評価する。IdP側マッピング設定が必要
- 国際化ドメイン (IDN) の正規化は未対応

## 過去適用案件

| 案件 | 適用日 | 派生内容 | リポ |
| --- | --- | --- | --- |
| (まだなし) | | | |

> 案件で使ったら、ここに1行追加する運用にする。派生実装したコードへのリンクを残す。

## 関連パターン

- (将来) パターン02: IP Allowlist Authenticator
- (将来) パターン03: 属性ベース Conditional Authenticator
