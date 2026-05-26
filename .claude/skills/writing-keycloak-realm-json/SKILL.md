---
name: writing-keycloak-realm-json
description: Use when generating or updating a Keycloak Realm JSON file (keycloak/realms/<case>.json) from case specs (CASE-<CASE>-CLIENTS-INDEX and CASE-<CASE>-CLIENT-* specs) in this project. Reads YAML blocks from the spec markdown files and assembles them into Keycloak Realm Representation JSON suitable for --import-realm.
---

# Writing a Keycloak Realm JSON from case specs

ローカル開発用 Keycloak Realm JSON を、案件の spec ファイル群から生成・更新する skill。
spec が SoT、Realm JSON は派生物。Admin UI で試行して変更した場合は逆方向 (export → spec 更新) を行う。

## When to Use

- 新案件で `docs/specs/cases/<案件>/clients/` に spec を書いた後、初めて `keycloak/realms/<案件>.json` を生成する
- 既存 case の spec を更新した後、Realm JSON を再生成する
- 個別 client spec を追加した後、対応する client を Realm JSON の `clients[]` に反映する

## When NOT to Use

- STG/Prod 向けの Terraform 生成 (それは `writing-keycloak-realm-terraform` skill)
- SPI 実装 (それは `writing-keycloak-spi-pattern` skill)
- spec 自体を起票する (それは `writing-spec` skill — 必ず先に走らせる)

## Prerequisites

開始前に必ず満たすこと:

- [ ] case spec が `docs/specs/cases/<案件>/clients/index.md` (status: approved) に存在
- [ ] 個別 client spec が `docs/specs/cases/<案件>/clients/<client_id>.md` (status: approved) に1つ以上存在
- [ ] 各 client spec に YAML block で Client 設定値が記述されている
- [ ] 各 spec の `spec_id` が `CASE-<CASE>-CLIENT(S)-...` 形式に従っている

満たさない場合は `writing-spec` skill を先に実行 (status: draft → approved まで持っていく)。

## Reference Documents

- [docs/specs/specs-guide.md](../../../docs/specs/specs-guide.md) — spec_id命名・frontmatterスキーマ
- [docs/specs/templates/case-clients-index-template.md](../../../docs/specs/templates/case-clients-index-template.md) — index spec 雛形
- [docs/specs/templates/case-client-confidential-template.md](../../../docs/specs/templates/case-client-confidential-template.md) — Confidential Client spec 雛形
- [Keycloak Server REST API ClientRepresentation](https://www.keycloak.org/docs-api/latest/rest-api/index.html#ClientRepresentation) — JSON フィールドの正典
- [既存サンプル: example-customer](../../../docs/specs/cases/example-customer/clients/) — 動く実例

## Workflow

### Step 1: 案件特定 + spec 走査

ユーザーから案件名 (例: `acme-corp`) を受け取る。次のファイルを読む:

```
docs/specs/cases/<案件>/clients/index.md     ← Realm共通設定 + Client一覧 (案件で必要なRealm属性も含む)
docs/specs/cases/<案件>/clients/*.md         ← 個別 client spec (index.md 以外、全件)
```

`*.md` の各ファイルの YAML block (```yaml ... ```) を抽出。

### Step 2: index.md から Realm-level 設定を取得

index.md の本文 (YAML blockまたは表) から以下を取得:

- realm名 (省略時は案件名と同一)
- `sslRequired`, `loginWithEmailAllowed`, `registrationAllowed` 等 Realm レベル属性
- (将来) パスワードポリシー、ブルートフォース保護等

無ければデフォルト:
```yaml
realm: <案件名>
enabled: true
sslRequired: external
loginWithEmailAllowed: true
registrationAllowed: false
```

### Step 3: 個別 client spec から ClientRepresentation 配列を構築

各 client spec の YAML block を抽出。すべて連結して `clients[]` 配列にする。

YAML フィールドは Keycloak ClientRepresentation スキーマと一致する想定:
```yaml
clientId: web-app                # 必須
protocol: openid-connect         # 通常固定
publicClient: false              # confidential なら false
standardFlowEnabled: true
directAccessGrantsEnabled: false
serviceAccountsEnabled: false
implicitFlowEnabled: false
redirectUris:
  - https://app.example.com/*
webOrigins:
  - https://app.example.com
attributes:                       # 必要に応じて
  post.logout.redirect.uris: https://app.example.com
```

**注意点 (既知の罠):**
- `secret` フィールドは spec に書かない (Keycloak 側で自動生成 or runtime secret管理)
- `publicClient: true` のときは `secret` 不可、`bearerOnly` も false
- redirect URI のワイルドカードは末尾のみ (`https://*` は不可、`https://example.com/*` はOK)

### Step 4: Realm JSON への組み立て

`keycloak/realms/<案件>.json` を以下構造で出力:

```json
{
  "realm": "<案件名>",
  "enabled": true,
  "sslRequired": "external",
  ...Realm-level fields from Step 2...,
  "clients": [
    ...各 client spec の YAML block を JSON 化した配列...
  ]
}
```

### Step 5: 既存ファイルがある場合の差し替え戦略

`keycloak/realms/<案件>.json` が既存:
- **clients[] 配列は完全置換** (spec が SoT のため、spec に無いものは削除)
- **clients以外のフィールド (users, roles, authenticationFlows等) は維持** (Phase F.x で順次 spec 管理に移行)

新規の場合: Step 4 の構造をそのまま出力。

### Step 6: 動作確認

```bash
# JSON が valid か
jq . keycloak/realms/<案件>.json > /dev/null

# Keycloak に import して読めるか
make restart        # コンテナ起動中なら restart で import-realm 再実行
make logs           # KCログで import 成功 or エラーを確認
```

エラー (例: "Realm already exists") が出る場合は `make clean && make up` で初期化してから再 import。

### Step 7: spec frontmatter を更新

各 client spec (および index.md) の frontmatter を更新:

```yaml
---
spec_id: CASE-<CASE>-CLIENT-<CLIENT_ID>
title: ...
status: implemented             # ← 更新
implementations:                # ← 追加 (新規時) or 既存維持
  - keycloak/realms/<案件>.json
acceptance_tests: []            # client 単独テストがあれば追記
---
```

### Step 8: spec-validate

```bash
make spec-validate
```

green を確認したら作業完了。

## Acceptance Criteria for This Skill

- [ ] `keycloak/realms/<案件>.json` が valid JSON で生成された
- [ ] 各 client spec の YAML block が `clients[]` 配列に1対1で対応している
- [ ] `make restart` で import-realm が成功 (KCログにエラー無し)
- [ ] 管理コンソール (https://keycloak.localtest.me/) で対象 realm が見える + 全 client が想定通りの設定で登録されている
- [ ] 各 spec の `status: implemented` + `implementations` に realm JSON パスが入っている
- [ ] `make spec-validate` green

## Common Pitfalls

| アンチパターン | 正しいやり方 |
| --- | --- |
| Realm JSON を手で編集 (spec と乖離) | 必ず spec 側を更新 → skill で再生成 |
| spec に `secret` を書く | secret は Keycloak 自動生成 or runtime 注入、spec に置かない |
| `redirectUris` に `https://*` | 必ず host 指定 + 末尾ワイルドカード (`https://example.com/*`) |
| 同じ `clientId` を複数 spec に重複 | spec_id 一意性 + clientId 一意性の両方を担保 |
| users / roles を spec で管理せず JSON 直編集 | Phase F.x で順次 spec 管理に移行、それまでは JSON 編集箇所をコメント記録 |
| `publicClient: true` で `secret` を書く | publicClient は secret 持てない、spec から secret 行を除去 |

## Integration with superpowers

- `brainstorming` → spec を refine (client 設計判断、redirect URI 等)
- `writing-plans` → 「N個のclient spec を生成 → realm.json生成 → 動作確認」を 2-5分タスクに分解
- `executing-plans` → 本 skill の Step 1〜8 を順次実行
- `verification-before-completion` → Step 6 の `make restart` + admin console確認を必ず実施

## See Also

- [writing-spec](../writing-spec/SKILL.md) — spec を書く・更新するときの汎用 skill
- [writing-keycloak-realm-terraform](../writing-keycloak-realm-terraform/SKILL.md) — STG/Prod 向け Terraform 生成 (Realm JSON が固まった後)
