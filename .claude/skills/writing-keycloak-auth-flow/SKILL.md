---
name: writing-keycloak-auth-flow
description: Use when generating or updating Keycloak authentication flow configuration from an auth-flow spec (TEMPLATE-ADMIN-AUTH-FLOW pattern) in this project. Reads the requirements YAML block, designs the flow structure, and produces the authenticationFlows section in Realm JSON and/or Terraform HCL.
---

# Writing Keycloak Authentication Flow from spec

auth-flow spec の要件 YAML を読み込み、フロー構造を設計して Realm JSON と Terraform を生成する skill。
spec には「何が必要か」だけを書き、フローの内部構造はこの skill が決定する。

## When to Use

- auth-flow spec の要件 YAML を書いた後、Realm JSON に `authenticationFlows` を反映する
- auth-flow spec を更新した後、Realm JSON / Terraform を再生成する
- 新しい SPI パターンを既存フローに追加する

## When NOT to Use

- クライアント設定の生成 → `writing-keycloak-realm-json` skill
- フローに使う SPI 実装 → `writing-keycloak-spi-pattern` skill
- spec 自体の起票 → `writing-spec` skill

## Prerequisites

- [ ] auth-flow spec に要件 YAML ブロックが記述されている (`realm`, `customize`, 各フロー要件)
- [ ] `patterns[].spec_id` で参照しているパターン spec が `docs/specs/patterns/` に存在する
- [ ] 対象案件の Realm JSON (`keycloak/realms/<案件>.json`) が既存 or 新規作成する準備ができている

## Reference Documents

- [docs/specs/task-specs/admin-console-config/08-auth-flow.md](../../../docs/specs/task-specs/admin-console-config/08-auth-flow.md) — spec テンプレ (要件 YAML スキーマの正典)
- [docs/specs/patterns/](../../../docs/specs/patterns/) — SPI パターン一覧 (authenticator ID 確認用)
- [Keycloak AuthenticationFlowRepresentation](https://www.keycloak.org/docs-api/latest/rest-api/index.html#AuthenticationFlowRepresentation) — JSON フィールドの正典

## Workflow

### Step 1: spec 読み込み

auth-flow spec ファイルを読む。要件 YAML の `realm`, `customize`, 各フローブロックを把握する。
`patterns[].spec_id` が参照するパターン spec も読み、各パターンの `authenticator ID` と `config キー` を確認する。

### Step 2: フロー構造の設計

要件からフローの内部構造を決定する。以下が標準的な構造テンプレート。

**browser フローの標準構造:**

```
<案件> browser  (topLevel: true)
  ├─ auth-cookie                      ALTERNATIVE   ← Cookie SSO (常に含める)
  ├─ identity-provider-redirector     ALTERNATIVE   ← social_login: true のときのみ
  └─ <案件> browser forms             ALTERNATIVE   (サブフロー)
       ├─ auth-username-password-form REQUIRED
       ├─ <SPI patterns 順に>         REQUIRED      ← patterns に列挙した順
       ├─ auth-otp-form               OPTIONAL/REQUIRED  ← otp の値に応じて
       └─ webauthn-authenticator      OPTIONAL/REQUIRED  ← webauthn の値に応じて
```

**direct_grant フローの標準構造:**

```
<案件> direct grant  (topLevel: true)
  ├─ direct-grant-validate-username   REQUIRED
  ├─ direct-grant-validate-password   REQUIRED
  ├─ <SPI patterns 順に>              REQUIRED      ← patterns に列挙した順
  └─ direct-grant-validate-otp        OPTIONAL/REQUIRED  ← otp の値に応じて
```

`otp: disabled` / `webauthn: disabled` のステップは構造に含めない。
`social_login: false` のとき `identity-provider-redirector` は含めない。

### Step 3: Realm JSON 生成

設計したフロー構造を Keycloak の JSON 表現に変換する。

**Keycloak JSON の主要ルール:**
- サブフロー参照は `flowAlias` + `autheticatorFlow: true` (typo だが仕様)
- authenticator 参照は `authenticator` + `autheticatorFlow: false`
- priority は steps の順序に従い 10 刻みで付番 (10, 20, 30, …)
- config を持つ execution は `authenticatorConfig` フィールドに alias を設定し、`authenticatorConfig[]` 配列にエントリを追加する
- `builtIn: false`, `topLevel` はフロー階層に応じて設定

**出力例 (ドメイン制限 + OTP optional):**

```json
{
  "browserFlow": "<案件> browser",
  "authenticationFlows": [
    {
      "alias": "<案件> browser",
      "providerId": "basic-flow",
      "topLevel": true,
      "builtIn": false,
      "authenticationExecutions": [
        { "authenticator": "auth-cookie",                   "requirement": "ALTERNATIVE", "priority": 10, "autheticatorFlow": false },
        { "flowAlias":    "<案件> browser forms",           "requirement": "ALTERNATIVE", "priority": 20, "autheticatorFlow": true  }
      ]
    },
    {
      "alias": "<案件> browser forms",
      "providerId": "basic-flow",
      "topLevel": false,
      "builtIn": false,
      "authenticationExecutions": [
        { "authenticator": "auth-username-password-form",          "requirement": "REQUIRED",  "priority": 10, "autheticatorFlow": false },
        { "authenticator": "email-domain-allowlist-authenticator", "requirement": "REQUIRED",  "priority": 20, "autheticatorFlow": false, "authenticatorConfig": "<alias>" },
        { "authenticator": "auth-otp-form",                       "requirement": "OPTIONAL",  "priority": 30, "autheticatorFlow": false }
      ]
    }
  ],
  "authenticatorConfig": [
    {
      "alias": "<alias>",
      "config": { "allowedDomains": "example.com##example.org" }
    }
  ]
}
```

`keycloak/realms/<案件>.json` の更新方針:
- `authenticationFlows` の `builtIn: false` エントリは完全置換 (spec が SoT)
- `authenticationFlows` の `builtIn: true` エントリは保持
- `authenticatorConfig` は alias が重複するものを置換、それ以外は保持
- `browserFlow` / `directGrantFlow` 等のバインディングフィールドを更新
- clients / roles / users 等その他フィールドは変更しない

### Step 4: Terraform 生成 (オプション)

`terraform/environments/<案件>/<env>/auth_flows.tf` を生成する。

**Terraform リソース対応:**

| フロー要素 | Terraform リソース |
|---|---|
| トップレベルフロー | `keycloak_authentication_flow` |
| サブフロー | `keycloak_authentication_subflow` |
| authenticator ステップ | `keycloak_authentication_execution` |
| SPI config | `keycloak_authentication_execution_config` |
| フロー バインディング | `keycloak_realm.this` の `browser_flow` 等 |

`depends_on` で execution 間の順序を保証する (Terraform は並列実行するため順序指定が必要)。

### Step 5: 動作確認 (Realm JSON の場合)

```bash
jq . keycloak/realms/<案件>.json > /dev/null   # JSON valid チェック
make restart                                    # import-realm 再実行
make logs                                       # エラーなしを確認
```

### Step 6: spec frontmatter 更新

```yaml
implementations:
  - keycloak/realms/<案件>.json
  - terraform/environments/<案件>/dev/auth_flows.tf   # Terraform 生成済みなら追加
```

### Step 7: spec-validate

```bash
make spec-validate
```

## Common Pitfalls

| アンチパターン | 正しいやり方 |
|---|---|
| `autheticatorFlow` を修正してしまう | Keycloak の typo のまま `autheticatorFlow` が正しい |
| サブフローの `topLevel` を `true` にする | トップレベルフローのみ `true` |
| `authenticatorConfig` の alias と execution の参照が不一致 | alias は完全一致させる |
| Terraform で `depends_on` を省略 | priority 順序が保証されなくなる |
| `builtIn: true` のフローを削除してしまう | 更新時に保持する |
| `allowedDomains` を配列で書く | Keycloak の config 値はすべて文字列。複数値は `##` 区切り (`"a.com##b.com"`) |

## See Also

- [writing-spec](../writing-spec/SKILL.md) — spec 起票・更新
- [writing-keycloak-realm-json](../writing-keycloak-realm-json/SKILL.md) — クライアント設定の Realm JSON 生成
- [writing-keycloak-realm-terraform](../writing-keycloak-realm-terraform/SKILL.md) — STG/Prod Terraform 生成
- [writing-keycloak-spi-pattern](../writing-keycloak-spi-pattern/SKILL.md) — フローに組み込む SPI 実装
