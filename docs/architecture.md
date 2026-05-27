# Architecture Decision Records (ADR)

このリポジトリの主要な設計判断とその理由をまとめる。
新しい大きな判断をするときは、ここに ADR を追加する (1ファイル/ADR の形式ではなく、本ファイルに追記)。

> 形式は ADR の簡易版: **Context → Decision → Consequence**。
> 全ADRはこのファイルに集約 (リポが小規模なため)。多くなれば `docs/adr/0NNN-*.md` に分割する。

---

## ADR-001: Keycloak Quarkus版 (26.x) を採用

**Context** :
Keycloak には旧Wildfly版と Quarkus版がある。Wildfly版は EOL 済み (Keycloak 17 が最後)。

**Decision** :
**Quarkus版 26.x系** を採用。`quay.io/keycloak/keycloak:26.0` イメージを基準。

**Consequence** :
- 起動が高速化 (`start --optimized` で数秒)
- 設定方法が `KC_*` 環境変数や CLI フラグに統一
- `kc.sh build` でカスタムプロバイダ込みの最適化ビルドが可能
- Wildfly時代の `standalone.xml` や `cli` ベースの設定は使えない (移行ガイド参照)
- SPI APIにも一部変更あり

---

## ADR-002: SPI = Maven multi-module 構成

**Context** :
SPIを案件ごとに増やしていく。1つの巨大JARに全部入れるか、機能単位でJAR分割するか。

**Decision** :
**Maven multi-module** で1パターン=1モジュール構成。親POMで依存・プラグインのバージョンを集中管理。

**Consequence** :
- パターンごとに独立したJAR (例: `email-domain-allowlist-1.0.0-SNAPSHOT.jar`)
- 案件で必要なパターンだけ選んでデプロイできる
- ビルド順序は Maven reactor が依存解決で決定
- 案件横断で再利用しやすい

---

## ADR-003: Realm-as-code は Terraform Provider for Keycloak

**Context** :
管理コンソール設定 (Realm/Client/Role/Flow等) を、手動GUI操作からコード化したい。選択肢:
- (a) Realm JSON エクスポート/インポート
- (b) kcadm.sh スクリプト
- (c) Terraform Provider for Keycloak
- (d) Pulumi / Ansible / その他

**Decision** :
**Terraform Provider for Keycloak (`keycloak/keycloak` 公式)** を採用。

**Consequence** :
- HCL で宣言的に書ける、`terraform plan` で diff レビューが容易
- module化して案件横断の再利用 (`terraform/modules/client-confidential` 等)
- state管理が必要 (dev は local state、本番は remote backend 推奨)
- Realm JSON exportは「現状把握・スナップショット」用途で併用
- `kcadm.sh` は ad-hoc 操作用に残す

---

## ADR-004: ブラウザE2E は TypeScript + Playwright + testcontainers Node

**Context** :
ブラウザ操作するE2Eテストの選択肢:
- (a) Java + Playwright for Java
- (b) Java + Selenium
- (c) TypeScript + Playwright (公式推奨)
- (d) Cypress

**Decision** :
**TypeScript + @playwright/test + testcontainers (Node.js port)** を採用。SPI開発の Java とは別スタック。

**Consequence** :
- Playwright公式ツーリング (Inspector / codegen / trace viewer) が最も成熟
- TypeScriptの型情報で記述が安定
- SPI開発のJava と分離 (E2E担当が変わっても理解しやすい)
- Node.js を新たに必要とする (チーム全員がJavaのみ、ではなくなる)
- Java IT (Direct Grant) と E2E (Browser Flow) で言語が違うが、検証対象も違うため許容

---

## ADR-005: 案件は雛形リポからの clone (per-customer repo)

**Context** :
複数顧客の案件をどうリポジトリ管理するか:
- (a) 1リポ・モノレポで顧客別ディレクトリ
- (b) 顧客別に独立したリポ (clone from template)
- (c) 共通ライブラリ + 顧客リポが依存

**Decision** :
**(b) 顧客別リポ、雛形リポから派生** を採用。

**Consequence** :
- 案件は独立進化し、顧客固有のカスタマイズと汎用部分が混ざらない
- 雛形リポはパターンカタログ + 共通基盤として育つ
- 案件で生まれた汎用化可能な実装は雛形に逆輸入する運用
- 案件横断のリファクタは個別取り込みが必要 (cherry-pick / subtreeマージ)
- 顧客環境への影響範囲が明確 (顧客リポ内に閉じる)

---

## ADR-006: Java IT は dasniko/testcontainers-keycloak

**Context** :
Java側で実Keycloakを起動するテストツール:
- (a) Testcontainers の GenericContainer で自前ラップ
- (b) dasniko/testcontainers-keycloak (community-maintained wrapper)

**Decision** :
**dasniko/testcontainers-keycloak (3.4+)** を採用。

**Consequence** :
- Keycloak固有のメソッド (`withProviderLibsFrom`, `withRealmImportFile` 等) で記述が短い
- Quarkus版26.xに対応
- community-maintained のため Keycloak新バージョン対応にラグが出る可能性
- 不足する操作は GenericContainer のメソッドで補える (継承関係)

---

## ADR-007: テストは3層構成 (単体 / Java IT / ブラウザE2E)

**Context** :
SPI開発でどの粒度のテストを書くか:
- 全部 Mockito で済ます → 実環境の挙動見えない
- 全部 E2E で → 遅い、CI で時間がかかる
- 階層化する

**Decision** :
**3層構成** :
1. 単体 (Mockito + JUnit5): ロジック分岐
2. Java IT (Testcontainers + HTTP): API挙動
3. ブラウザE2E (Playwright): 画面・OAuth Code Flow

各層は **検証対象が異なる** ため互いに代替不能。新パターン追加時は3層すべて書くのが原則。

**Consequence** :
- カバレッジが多角的になる
- 単体は高速 (Docker不要)、IT/E2E は Docker必要
- 開発時の繰り返し速度を保ちつつ、本番相当の挙動も検証可能
- 新パターン追加コストは増える (3層ぶんのテスト)。だが「テストがあるから安心して改造できる」効果が上回ると判断

---

## ADR-008: Mockito 5.18+ (JDK 24/25 対応)

**Context** :
Mockito 5.11 では JDK 24/25 で `Could not modify all classes` エラーが出てモック生成に失敗する。

**Decision** :
**parent pom の mockito.version を 5.18.0 (またはそれ以上)** に固定。

**Consequence** :
- 開発機の JDK バージョンが新しくても動く
- Mockito の inline-mock-maker は将来 JDK で agent モードへの移行が必要 (将来対応事項)

---

## ADR-009: Authenticator の Response はフロー検出して JSON/HTML出し分け

**Context** :
カスタム Authenticator で `context.failure(error)` (Response無し) を Direct Grant flow で呼ぶと、Keycloak が `AuthenticationFlowException` をハンドルできず HTTP 500 を返す。
一方で Browser flow なら Response なしでも標準エラーページが出る。

**Decision** :
**Authenticator は `isDirectGrantFlow()` ヘルパーでフロー種別を判定し、Direct Grantなら OAuth2 JSON Response、Browser なら HTML エラーページを返す** という二段構えにする。

**Consequence** :
- 両フローで使える「ポータブル Authenticator」になる
- 検出ロジックを再利用 (今後のパターンでもコピペ可)
- Keycloak内部のフロー判定APIに依存 (`realm.getDirectGrantFlow()`)
- 別のフロー (reset-credentials等) で動かす場合は判定ロジック拡張が必要

実装: [keycloak/providers/sample-01-email-domain-allowlist/src/main/java/.../EmailDomainAllowlistAuthenticator.java](../keycloak/providers/sample-01-email-domain-allowlist/src/main/java/com/example/keycloak/authenticators/emaildomain/EmailDomainAllowlistAuthenticator.java) `isDirectGrantFlow()` メソッド

---

## ADR-010: ブラウザE2E の OAuth redirect 検証は waitForRequest

**Context** :
Authorization Code Flow のE2Eで、認可成功時に `redirect_uri` (例: `http://localhost:3000/callback`) に `code=` 付きでブラウザがリダイレクトされる。
実サーバを立てないと localhost:3000 への navigation が `ERR_CONNECTION_REFUSED` → Chrome が `chrome-error://chromewebdata/` に着地。
`page.waitForURL()` も `page.route()` interception も期待通り動かない。

**Decision** :
**`page.waitForRequest(req => req.url().startsWith(REDIRECT_URI))` でリクエスト発火時点を捕捉する**。

**Consequence** :
- リクエストURLに `code=...&state=...` が乗っているので、レスポンスが返らなくても検証可能
- 実サーバを立てる必要なし
- 同様のパターンが他のOAuth E2Eでも使える (ADRと同時に [docs/testing.md](testing.md) 既知の罠に記録)

---

## ADR-011: docs/ 配下に業務プロセス文書を集約

**Context** :
パターンレシピ・テスト方式・案件入力テンプレ・運用手順をどこに置くか:
- (a) 各サブディレクトリの CLAUDE.md に分散
- (b) `docs/` 配下に集約
- (c) Wiki / Notion等の外部システム

**Decision** :
**業務プロセス系は `docs/` 配下に集約**、技術仕様 (SPI/Theme/Realm等の実装規約) は **各サブディレクトリの CLAUDE.md** に分散。

**Consequence** :
- 案件横断で再利用したい文書 (case-spec / task-specs / patterns / testing / runbooks) は docs/ 一箇所
- 実装に近い流儀 (SPI開発・Java IT・E2E等) はコードと隣接した CLAUDE.md
- 外部システム (Notion等) には依存せず、Git管理で版管理
- Claude Code が CLAUDE.md を自動で読む特性も活かせる

---

## ADR-012: 仕様書駆動開発 (SDD) + obra/superpowers の採用

**Context** :
仕様 (case-spec、task-spec、patterns) と実装 (providers/, terraform/, etc.) の対応関係が暗黙的で、以下が問題:
- どの実装がどの仕様を満たすのか追跡できない
- 仕様変更時に影響範囲を機械的に検出できない
- Claude/AIに仕様を渡しても自由文markdown だと曖昧さが残る
- 完了判定が人手依存

**Decision** :
**全 spec ファイルに YAML frontmatter を付与し、それを Source of Truth とする** 。
具体的には:
- `spec_id` (一意ID、`PATTERN- / TEMPLATE- / CASE- / TASK-` の4タイプ接頭辞)
- `status` (draft / approved / implemented / deprecated / template / ready)
- `implementations` (この spec が導出する成果物のパス)
- `acceptance_tests` (この spec を verify するテスト)

実装workflowは [obra/superpowers](https://github.com/obra/superpowers) (Claude Code 用 agentic skills framework) と組み合わせ、
spec frontmatter を superpowers の `writing-plans` / `executing-plans` / `test-driven-development` 等が消費する設計。

**Consequence** :
- spec と impl/test の双方向リンクが追跡可能になる
- CI で「spec_id → impl」「impl → spec_id」のマッピング検証が将来可能 (Phase B)
- AI/superpowers が完了条件 (acceptance_tests) を機械的に判定できる
- spec ファイルの記述コストが増える (frontmatter編集の手間)
- superpowers なしでも spec は単独で読める (YAML frontmatter は普通の Markdown 慣行)

詳細: [docs/specs/specs-guide.md](specs/specs-guide.md)

Phase展開:
- Phase A (完了): 既存 spec に frontmatter 付与
- Phase B (完了): `make spec-validate` で spec ↔ impl マッピングを CI 検証
- Phase C (完了): `docs/specs/` へ spec 系を集約
- Phase D (完了): Keycloak固有 skill を `.claude/skills/` に4つ追加 (writing-spec / writing-keycloak-spi-pattern / writing-keycloak-realm-terraform / writing-keycloak-acceptance-tests)、superpowers の workflow に統合
- Phase B.1 (将来): 逆参照検証 (impl ファイル側の `// spec: SPEC-ID` コメント ↔ spec frontmatter の双方向チェック)

---

## 将来検討事項 (未決定)

| 項目 | 検討状況 |
| --- | --- |
| CI/CD パイプライン (GitHub Actions等) | 未着手。`make test-providers / integration / e2e / tf-test` の組合せで実現可能 |
| 本番 Terraform state の remote backend | dev は local stateで運用中。本番運用前に S3 + DynamoDB等への移行 |
| Secret管理 (Vault連携) | 現状 `.env` / `.tfvars` のローカル管理。本番運用前にVault/SSM等の検討必要 |
| Theme開発のホットリロード自動化 | `KC_SPI_THEME_CACHE_*=false` で手動リロード可だがWatchベースでない |
| Keycloak バージョン自動更新通知 | Renovate / Dependabot の導入検討 |
| パターンの単独配布 (社内 Maven リポジトリ) | 現状はソース共有。複雑化したらバイナリ配布へ |

---

## ADRの追加方法

新たな大きな設計判断をしたときは、本ファイルに追記:

```markdown
## ADR-0NN: <タイトル>

**Context** : (背景・選択肢)

**Decision** : (採用したアプローチ)

**Consequence** : (得られるもの・失うもの・将来課題)
```

判断が後から覆る可能性があるので、ADRは **削除せず追記・補足** する運用。
覆った場合は新ADRで「ADR-XXを置き換える」と明記する。
