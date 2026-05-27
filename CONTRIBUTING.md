# Contributing Guide

このリポジトリへ変更を加えるときの規約と手順。
雛形リポ (本リポ) と顧客リポ (派生先) で運用は若干異なるが、基本ルールは共通。

---

## 基本原則

1. **テンプレ・パターンに沿う** — 既存パターンを真似て派生実装するのが基本
2. **変更には必ずテストを伴う** — 3層 (単体 / Java IT / ブラウザE2E) で適切な層を選ぶ
3. **ドキュメントも一緒に更新** — コードを変えたら CLAUDE.md / docs/ の関連箇所も同期
4. **設計判断は熟練者を巻き込む** — パターン新設・命名規則・設計の変更は事前合意

---

## ブランチ戦略

| ブランチ | 用途 | 寿命 |
| --- | --- | --- |
| `main` | 常にデプロイ可能な状態 | 永続 |
| `feature/<name>` | 機能追加 | PR マージで削除 |
| `fix/<name>` | バグ修正 | 同上 |
| `docs/<name>` | ドキュメントのみ | 同上 |
| `refactor/<name>` | 振る舞いを変えないリファクタ | 同上 |
| `chore/<name>` | 依存更新・CI設定等 | 同上 |

ブランチ名は **kebab-case** で具体的に (例: `feature/02-email-domain-blocklist`)。

---

## コミットメッセージ

[Conventional Commits](https://www.conventionalcommits.org/) 準拠を推奨。

形式:
```
<type>(<scope>): <subject>

<body>

<footer>
```

### type

| type | 説明 |
| --- | --- |
| feat | 機能追加 |
| fix | バグ修正 |
| docs | ドキュメントのみ |
| test | テスト追加・修正 |
| refactor | 振る舞いを変えない構造変更 |
| chore | ビルド・依存・CI設定 |
| perf | パフォーマンス改善 |

### scope (任意)

変更箇所を示す: `providers`, `e2e`, `terraform`, `compose`, `docs` 等

### 例

```
feat(providers): add email domain blocklist authenticator pattern

- pattern 02 として keycloak/providers/02-email-domain-blocklist/ を新設
- 単体 / Java IT / ブラウザE2E の3層テスト追加
- docs/specs/patterns/02-email-domain-blocklist.md にレシピ追加

Refs: #123
```

```
fix(keycloak/providers/sample-01-email-domain-allowlist): support Direct Grant 500 error

context.failure(error) 単体呼び出しが Keycloak 26.x で 500 を返すため、
isDirectGrantFlow() でフロー種別を判定して OAuth2 JSON Response を渡すように修正。
ブラウザフローでは HTML エラーページのまま (両立)。
```

---

## Pull Request 作成

### PR description テンプレ

```markdown
## なぜ
(背景・解決したい課題)

## 何を
(変更内容のサマリ)

## どう検証したか
- [ ] make test-providers
- [ ] make test-integration
- [ ] make test-e2e
- [ ] 管理コンソールで手動確認 (該当する場合)

## 関連
- Refs: #issue番号
- Related to: docs/specs/patterns/NN-...

## レビュー観点
- (特に見てほしい箇所、設計判断の理由など)
```

### マージ条件

- [ ] CI (全テスト) green
- [ ] 1名以上の承認 (熟練者によるレビュー)
- [ ] PR description が埋まっている
- [ ] 関連ドキュメントが更新されている (CLAUDE.md / patterns / testing.md 等)

---

## 変更タイプ別の手順

### A. 新しい SPI パターンを追加

1. `keycloak/providers/sample-NN-<pattern-name>/` (汎用) または `case-<client>-<name>/` (案件固有) ディレクトリを既存 `sample-` パターンから複製
2. `pom.xml` の `<artifactId>` `<name>` をリネーム
3. Java パッケージをリネーム (`com.example.keycloak.<spi-type>.<name>`)
4. クラス実装 + 単体テスト
5. `keycloak/providers/integration-tests/src/test/java/.../<Name>IT.java` 追加 + テスト realm JSON 追加
6. (画面UIがあれば) `e2e-tests/tests/<name>-browser.spec.ts` + `e2e-tests/fixtures/test-realm-<name>.json` 追加
7. 親 `keycloak/providers/pom.xml` の `<modules>` に追加
8. `docs/specs/patterns/NN-<name>.md` に **レシピ** (when to use / config / 派生方法 / 既知の限界 / 過去適用案件) を書く
9. `keycloak/providers/CLAUDE.md` のパターン一覧を更新
10. `make build-restart && make test-providers && make test-integration && make test-e2e` で全層検証
11. PR 作成

### B. 既存パターンの改修

1. Issue または PR description で **なぜ・何を・どう** を明示
2. テスト先行で書ければベター
3. 改修後、3層テストが全て green
4. `docs/specs/patterns/NN-...` を必要に応じて更新
5. PR 作成

### C. Terraform モジュール追加

1. `terraform/modules/<name>/` ディレクトリ作成 (main.tf / variables.tf / outputs.tf / README.md)
2. 既存サンプル案件 (`environments/example-customer/`) で1回使ってみる
3. `docs/specs/task-specs/01-admin-console-config-template.md` にこの module の記入欄を追加
4. PR 作成

### D. ドキュメントのみ

1. `docs/` または各 CLAUDE.md を更新
2. リンク切れがないか `grep` で確認
3. PR (テスト省略OK)

---

## レビューの観点

レビュアー (熟練者) が見るポイント。詳細チェックリスト:

- [SPI レビュー観点](docs/review-checklists/spi-review.md)
- [Realm/Terraform 設定レビュー観点](docs/review-checklists/realm-config-review.md)

### 共通観点

1. **テストカバレッジ** — どの層で何をテストしているか、不足はないか
2. **設計判断** — 既存パターン/モジュールを使えるところで新規実装していないか
3. **命名規則** — ケバブケース、`com.example.keycloak.<spi-type>.<name>` 等
4. **ドキュメント同期** — コード変更と CLAUDE.md / patterns / testing.md が乖離していないか
5. **シークレット混入なし** — `.env` / `.tfvars` / 秘匿値が PR に含まれていない
6. **既知の罠を踏んでいないか** — [docs/testing.md](docs/testing.md) "既知の罠" 参照

---

## ドキュメント更新ルール

| 変更タイプ | 更新が必要な docs |
| --- | --- |
| 新パターン追加 | `keycloak/providers/CLAUDE.md` (一覧)、`docs/specs/patterns/NN-...md` (レシピ)、`README.md` (ディレクトリ構成) |
| テスト方式の変更 | `docs/testing.md` |
| Terraform モジュール追加 | `terraform/CLAUDE.md`、`docs/specs/task-specs/01-admin-console-config-template.md` |
| 共通の設計判断変更 | `docs/architecture.md` (ADR追加) |
| 新しいトラブル発見 | `docs/testing.md` "既知の罠"、または該当サブディレクトリ CLAUDE.md |

---

## 雛形リポと顧客リポの関係

このリポは **雛形リポ** として扱う。顧客案件は雛形を clone して派生したリポで進める。

```
雛形リポ (本リポ)
   ├ パターン1
   ├ パターン2
   └ ...
       ↓ clone
顧客リポA (acme-corp-keycloak)
顧客リポB (...)
```

### 雛形 → 顧客リポへの取り込み

雛形に新パターンが追加された場合、顧客リポで取り込むかは案件オーナーの判断:

- 案件で必要なら cherry-pick または手動マージ
- 不要なら無視

### 顧客 → 雛形への逆輸入

顧客案件で生まれた **汎用化可能な** 実装は、雛形リポに PR で逆輸入する:

1. 顧客固有要素 (顧客名、認証情報、ドメイン名等) を除去・汎用化
2. パターン名・命名を雛形流儀に合わせる
3. レシピドキュメントを書く
4. PR 作成 (雛形リポに対して)

判断基準: 「他の案件でも使いそうか」「設計判断として一般化できるか」

---

## 質問・相談

- 技術的な質問: チームSlack
- レビューで悩んだら: 熟練者にメンション
- 設計の大方針: 月次の設計レビュー会
