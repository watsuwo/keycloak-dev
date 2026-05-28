---
spec_id: TEMPLATE-ADMIN-AUTH-FLOW
title: 認証フロー設定テンプレ (デフォルト値付き)
status: template
---

# 認証フロー設定テンプレ

> **使用判断**: カスタム認証フロー (SPI Authenticator) が必要な場合のみこのファイルをコピー。
> 標準フロー (Keycloak デフォルト) で要件が満たせる場合は不要。

**カスタムフローが必要な典型的ケース:**
- メールドメイン制限 (特定ドメインのみログイン許可)
- TOTP / WebAuthn の独自フロー
- 外部サービスとの連携検証 (IP制限、ライセンス確認など)

## 認証フロー要件

`writing-keycloak-auth-flow` スキルがこのブロックを読み込み、フロー構造を設計して Realm JSON と Terraform を生成する。
フローの内部構造 (サブフロー・ステップ順序・priority 等) はスキルが決定するため、ここには **何が必要か** だけを書く。

```yaml
realm: *(入力必須)*

# カスタマイズ対象フロー (不要な行は削除)
customize:
  browser: true
  direct_grant: true

browser:
  # 使用する SPI パターン (複数可、不要なら空リスト [])
  patterns:
    - spec_id: PATTERN-AUTH-DOMAIN-ALLOWLIST
      config:
        allowedDomains: [example.com]   # 許可ドメイン (複数可)
  # MFA
  otp: optional          # required / optional / disabled
  webauthn: disabled     # required / optional / disabled
  # ソーシャルログイン / 外部 IdP (不要なら false)
  social_login: false

direct_grant:            # 不要ならブロックごと削除
  patterns:
    - spec_id: PATTERN-AUTH-DOMAIN-ALLOWLIST
      config:
        allowedDomains: [example.com]
  otp: disabled
```

### 各フィールドの説明

| フィールド | 意味 |
|---|---|
| `customize.browser` | Keycloak デフォルトの browser フローをカスタムフローで置き換える |
| `customize.direct_grant` | direct grant フロー (ROPC) をカスタムフローで置き換える |
| `patterns[].spec_id` | 使用する SPI パターンの spec_id。パターン一覧: [docs/specs/patterns/](../patterns/) |
| `patterns[].config` | パターンに渡す設定値 (キーはパターン spec を参照) |
| `otp` | OTP (TOTP) の要否。`required` / `optional` / `disabled` |
| `webauthn` | WebAuthn (パスキー) の要否。`required` / `optional` / `disabled` |
| `social_login` | Google 等の外部 IdP ボタンを表示するか |

> **変更条件**: 必要な SPI パターンが一覧にない場合は別途パターン spec を起票して実装する。

## 設計判断メモ (案件ごとに記入)

- **カスタムフローを選んだ理由**: (記入)
- **browser / direct_grant どちらに適用するかの判断**: (記入)
