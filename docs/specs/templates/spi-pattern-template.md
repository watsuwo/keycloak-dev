---
spec_id: TEMPLATE-SPI-PATTERN
title: カスタムSPIパターン spec テンプレ
status: template
---

# カスタムSPIパターン spec テンプレート

> **使い方**:
> 1. このテンプレを `docs/specs/patterns/NN-<name>.md` にコピー
> 2. frontmatter を書き換え: `spec_id: PATTERN-<DOMAIN>-<NAME>`, `status: draft`
> 3. `requirements:` YAML ブロックを埋める — **ここだけ埋めれば `writing-keycloak-spi-pattern` スキルが実装を生成できる**
> 4. 熟練者レビュー → `status: approved`
> 5. 実装後 `implementations` / `acceptance_tests` を列挙して `status: implemented`

---

# パターン NN: <名前>

<一行で何をするSPIか書く>

## 適用判断

- **このパターンを使うとき**: (記入)
- **このパターンを使わない方が良いケース**: (記入)

## SPI要件

`writing-keycloak-spi-pattern` スキルがこのブロックを読み込み、Javaコード・テスト・META-INF登録を生成する。
**何が必要か** だけを書く。内部実装はスキルが決定する。

```yaml
requirements:
  spi_type: Authenticator   # Authenticator | EventListener | ProtocolMapper | UserStorage | RequiredAction

  provider_id: *(入力必須 — kebab-case、Keycloak全体で一意)*
  display_name: *(入力必須 — 管理コンソールの「ステップ追加」ドロップダウンに出る名前)*
  reference_category: *(任意 — 同種のAuthenticatorをグループ化する文字列)*
  help_text: *(任意 — 管理コンソールに表示するヘルプ文)*

  requirement_choices: [REQUIRED, DISABLED]   # REQUIRED/OPTIONAL/DISABLED/ALTERNATIVE から選ぶ
  requires_user: true   # Authenticator のみ: 前段でユーザーが解決済みであることを要求するか

  # 管理コンソールの歯車アイコンで設定できるパラメータ (不要なら空リスト [])
  config:
    - key: *(camelCase の設定キー名)*
      label: *(管理コンソール表示ラベル)*
      type: STRING   # STRING | MULTIVALUED_STRING | PASSWORD | BOOLEAN | LIST | ROLE | CLIENT
      help: *(ヘルプテキスト)*
      # default: ""   # 省略可
      # options: []   # LIST type のみ

  # Authenticator を組み込めるフロー種別 (auth-flow spec の patterns[].spec_id 参照時に使う)
  flows:
    browser: true
    direct_grant: false

  # 受け入れ条件 — 単体テストと IT のテストケースを決定する
  acceptance_criteria:
    - id: AC-1
      when: "(条件)"
      then: "(期待結果 — context.success() / context.failure() / context.attempted() 等)"
```

### 各フィールドの説明

| フィールド | 必須 | 説明 |
|---|---|---|
| `spi_type` | ✓ | SPIの種別 |
| `provider_id` | ✓ | Keycloak内でグローバルに一意なID。フロー設定JSONの`authenticator`フィールドの値になる |
| `display_name` | ✓ | 管理コンソールの「ステップ追加」ドロップダウンに表示される名前 |
| `reference_category` | — | 関連するAuthenticatorをグループ化する文字列 (例: `"domain-restriction"`, `"mfa"`) |
| `help_text` | — | 管理コンソールのAuthenticator説明文 |
| `requirement_choices` | — | フロー設定で選べる挙動オプション。省略時は `[REQUIRED, OPTIONAL, DISABLED]` |
| `requires_user` | — | Authenticatorのみ。`true`の場合、前段でユーザーが解決済みであることが前提 |
| `config[].key` | ✓ | 設定値の内部キー名 (camelCase) |
| `config[].type` | ✓ | 設定値の型。`MULTIVALUED_STRING`は複数値を`##`区切りで保存 |
| `flows.browser` | — | ブラウザフローで使えるか |
| `flows.direct_grant` | — | Direct Grantフローで使えるか |
| `acceptance_criteria[].id` | ✓ | テストIDとして使う (AC-1, AC-2, …) |
| `acceptance_criteria[].when` | ✓ | テスト条件 |
| `acceptance_criteria[].then` | ✓ | 期待する結果 |

> **`config`が空の場合**: `isConfigurable() = false` となり、管理コンソールの歯車アイコンが表示されない。

---

## 仕様

(受け入れ条件の補足、エッジケース、設定値の意味など)

## Keycloak管理コンソールでの設定手順

(実装後に記入)

## 実装の場所

(実装後に記入)

## 派生・カスタマイズ

(記入)

## テスト

```bash
cd keycloak/providers/sample-NN-<name>
mvn test

make test-integration
```

## 既知の限界

(記入)

## 過去適用案件

| 案件 | 適用日 | 派生内容 | リポ |
| --- | --- | --- | --- |
| (まだなし) | | | |

## 関連パターン

- (記入)
