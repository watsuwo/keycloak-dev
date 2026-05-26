# Keycloak 開発雛形リポジトリ

Keycloak (Quarkus版 26.x) のカスタマイズ開発を **チーム全体で効率化** するための共通基盤。
新規顧客案件はこのリポジトリを clone して始めることで、環境構築・パターン適用・テストが標準化される。

## このリポジトリにあるもの

- **動く開発環境** — Docker Compose で Keycloak + PostgreSQL + Traefik(HTTPS) + Mailhog
- **SPIパターンカタログ** — Authenticator等の動くサンプル + レシピ (派生して案件に適用)
- **管理コンソール設定 as Code** — Terraform Provider for Keycloak (`keycloak/keycloak`)
- **3層テスト基盤** — 単体 (Mockito) / Java IT (Testcontainers) / ブラウザE2E (Playwright)
- **業務プロセス文書** — 案件入力テンプレ、タスク別仕様テンプレ、テスト方式ガイド

---

## クイックスタート

```bash
make init               # .env と自己署名証明書を生成
make up                 # Dev Keycloak起動 (Traefik + PostgreSQL + Mailhog 同梱)
make build-restart      # SPI ビルド + Keycloak 再起動 (パターン1が読み込まれる)
```

起動後にアクセス:

| URL | 用途 | 認証 |
| --- | --- | --- |
| https://keycloak.localtest.me/ | Keycloak 管理コンソール | admin / admin |
| https://mailhog.localtest.me/ | Mailhog Web UI | なし |
| http://localhost:8081/dashboard/ | Traefik ダッシュボード | なし |

ブラウザの自己署名証明書警告は「詳細設定 → アクセスする」で進む。

詳細・他コマンドは `make help` および [CLAUDE.md](CLAUDE.md) を参照。

---

## 最初に読むべきドキュメント — 目的別ガイド

| やりたいこと | 最初に読むファイル |
| --- | --- |
| **全体把握・基本操作** | [CLAUDE.md](CLAUDE.md) — 環境構築・ディレクトリ役割・運用フロー |
| **新メンバー (1週間のオンボーディング)** | [docs/onboarding.md](docs/onboarding.md) — Day1〜5の手引き |
| **テスト方式の理解 (必読)** | [docs/testing.md](docs/testing.md) — 3層構造、ツール、デバッグ、既知の罠 |
| **仕様書駆動開発 (SDD) を理解する** | [docs/specs/specs-guide.md](docs/specs/specs-guide.md) — frontmatter スキーマ + spec_id 命名規則 + `make spec-validate` で機械検証 |
| **Claude/superpowers 用のプロジェクト固有 skill** | [.claude/skills/README.md](.claude/skills/README.md) — writing-spec / writing-keycloak-spi-pattern / writing-keycloak-realm-terraform / writing-keycloak-acceptance-tests |
| **新規顧客案件を開始する** | [docs/customer-rollout.md](docs/customer-rollout.md) — clone から本番デプロイまでの全体手順 |
| 案件要件を構造化する | [docs/specs/case-spec-template.md](docs/specs/case-spec-template.md) — 顧客リポに複製して埋める |
| 管理コンソール設定を Terraform化 | [terraform/CLAUDE.md](terraform/CLAUDE.md) + [docs/specs/task-specs/01-admin-console-config-template.md](docs/specs/task-specs/01-admin-console-config-template.md) |
| 新しい SPI パターンを追加 | [keycloak/providers/CLAUDE.md](keycloak/providers/CLAUDE.md) + 参考パターン [docs/specs/patterns/01-email-domain-allowlist.md](docs/specs/patterns/01-email-domain-allowlist.md) |
| Java IT を書く / 詰まる | [keycloak/providers/integration-tests/CLAUDE.md](keycloak/providers/integration-tests/CLAUDE.md) |
| ブラウザE2E を書く / 詰まる | [e2e-tests/CLAUDE.md](e2e-tests/CLAUDE.md) |
| カスタム Keycloakイメージを作る | [CLAUDE.md](CLAUDE.md) "カスタムイメージのビルド" セクション |
| **コードレビューする (チェックリスト)** | [docs/review-checklists/spi-review.md](docs/review-checklists/spi-review.md) + [docs/review-checklists/realm-config-review.md](docs/review-checklists/realm-config-review.md) |
| **PR/ブランチ規約** | [CONTRIBUTING.md](CONTRIBUTING.md) — branch/commit/PR規約 + 変更タイプ別手順 |
| **設計判断の背景** | [docs/architecture.md](docs/architecture.md) — ADR (Architecture Decision Records) |
| **用語が分からない** | [docs/glossary.md](docs/glossary.md) — Keycloak + プロジェクト用語集 |
| **セキュリティ方針** | [SECURITY.md](SECURITY.md) — secrets管理、依存、CVE方針 |
| **運用作業 (export/upgrade等)** | [docs/runbooks/](docs/runbooks/) — Realm export/import、Keycloak upgrade等 |

---

## ディレクトリ構成

```
keycloak-dev/
├── README.md                            ★このファイル (利用者向けスターター、最初に読む)
├── CLAUDE.md                            開発作業の流儀全般 (Claude含む全員が常時参照)
├── CONTRIBUTING.md                      コントリビューション規約 (branch / commit / PR / レビュー)
├── SECURITY.md                          セキュリティ方針 (secrets / 依存 / CVE)
│
│   ── インフラ・環境 ──
├── compose.yaml                         Dev環境定義 (Keycloak + Postgres + Traefik + Mailhog)
├── compose.override.yaml.example        個人override用ひな型 (gitignore対象にコピーして使う)
├── .env.example                         環境変数テンプレ (コピーして .env)
├── Makefile                             全操作の入口。`make help` で一覧
│
│   ── サービス毎の設定・成果物 ──
├── traefik/                             リバースプロキシ (HTTPS終端) 関連一式
│   ├── traefik.yml                      静的設定
│   ├── dynamic/                         動的設定 (証明書・ミドルウェア等)
│   └── certs/                           自己署名証明書 (gitignore、make certs で生成)
├── keycloak/                            Keycloak 関連一式
│   ├── Dockerfile                       カスタムイメージビルド (3-stage: SPI→optimize→runtime)
│   ├── .dockerignore                    build context (= keycloak/) 内の除外パターン
│   ├── providers/                       SPI (Java / Maven multi-module)
│   │   ├── CLAUDE.md                    SPI開発の流儀
│   │   ├── pom.xml                      親POM (依存・プラグイン管理)
│   │   ├── 01-email-domain-allowlist/   ★パターン1: Authenticator サンプル
│   │   └── integration-tests/           Java IT モジュール (Testcontainers + HTTP)
│   ├── themes/                          FreeMarkerテンプレ + CSS/JS (Phase 2.x で本格整備)
│   └── realms/                          起動時 import 用 Realm JSON (Phase 2.x で本格整備)
│
│   ── テスト ──
├── e2e-tests/                           ブラウザE2E (TypeScript + Playwright + testcontainers Node)
│   ├── CLAUDE.md
│   ├── playwright.config.ts
│   ├── fixtures/                        KeycloakContainer fixture + 各パターン用テスト realm JSON
│   └── tests/                           *.spec.ts
│
│   ── 管理コンソール設定 as Code ──
├── terraform/                           Terraform Provider for Keycloak (`keycloak/keycloak`)
│   ├── modules/                         再利用モジュール (client-confidential 等、案件横断)
│   └── environments/                    案件別の設定 (example-customer がサンプル)
│
│   ── 運用ヘルパー ──
├── scripts/                             証明書生成、Terraform検証 等
│
│   ── 業務プロセス・ドキュメント ──
├── docs/                                業務プロセス文書 (チーム横断ナレッジ)
│   ├── README.md                        docs/ 配下の構成
│   ├── testing.md                       ★テスト方式ガイド (新メンバー必読)
│   ├── onboarding.md                    新メンバー1週間オンボーディング (Day1〜5)
│   ├── customer-rollout.md              新規顧客案件の立ち上げ手順
│   ├── specs-guide.md                   仕様書frontmatterスキーマ + spec_id命名 (SDD)
│   ├── architecture.md                  設計判断のADR (Architecture Decision Records)
│   ├── glossary.md                      Keycloak + プロジェクト用語集
│   ├── case-spec-template.md            案件全体の要件入力テンプレ
│   ├── task-specs/                      作業タイプ別の入力テンプレ
│   ├── patterns/                        SPI パターンカタログ (動く実例 + レシピ)
│   ├── review-checklists/               レビュー観点チェックリスト
│   └── runbooks/                        運用手順書 (realm-export-import / keycloak-upgrade)
│
└── .claude/
    └── settings.json                    Claude Code チーム共通設定 (権限許可リスト)
```

---

## 必要なツール

利用者の手元に必要なものをまとめておきます。

| ツール | 用途 | 導入例 |
| --- | --- | --- |
| Docker Desktop / Engine | Dev環境 + Testcontainers | https://docs.docker.com/desktop/ |
| GNU Make | Make ターゲット実行 | macOS/Linux 標準。WSL2: `sudo apt install make` |
| Java 17+ | SPIビルド (Mockitoの関係でJDK 24-25にも対応) | macOS: `brew install openjdk@17`。WSL2: `sudo apt install openjdk-17-jdk` |
| Maven 3.9+ | SPIビルド | macOS: `brew install maven`。WSL2: `sudo apt install maven` |
| Node.js 18+ | E2Eテスト (Playwright) | macOS: `brew install node`。WSL2: `nvm` 推奨 |
| Terraform 1.5+ | 管理コンソール設定 | macOS: `brew install terraform`。WSL2: 公式手順 |
| jq | テストスクリプト内のJSON解析 | macOS: `brew install jq`。WSL2: `sudo apt install jq` |

### 環境別の注意

- **WSL2**: 必ず WSL2内 (例: `~/dev/keycloak-dev`) に clone する。`/mnt/c/` 配下だと volume mount が極端に遅い。改行コードは `.gitattributes` で LF 統一済み
- **macOS (Apple Silicon)**: 全イメージ arm64 対応済み、追加設定不要
- **Docker Desktop on Mac**: testcontainers が `~/.docker/run/docker.sock` を自動検出 (失敗時は手動で `DOCKER_HOST` 指定)

---

## 設計思想 — このリポジトリの位置づけ

**「単なる Dev 環境」ではなく「全顧客案件の出発点となる雛形 + 全社共通のパターン集」** として育てる方針。

```
[新案件開始]
    ↓ clone
keycloak-dev → 顧客名にリネーム → 顧客リポへ
    ↓
docs/case-spec.md を埋める (要件)
    ↓
必要パターンを keycloak/providers/ から派生実装
管理コンソール設定を terraform/environments/<案件>/ で記述
    ↓
3層テストで検証 → デプロイ
    ↓
案件で生まれた汎用化可能なパターンは雛形リポに PR で逆輸入
```

これにより:
- 全案件で構造が統一される → 新メンバーが迷わず作業に入れる
- パターン・知識が雛形リポに集約される → Claude/AI を活用しやすい
- 熟練者の暗黙知が「動くパターン+レシピ」に明文化される → 属人化解消

---

## 主要な作業フロー

### A. Dev環境を起動して触りたい

```bash
make init && make up
# → https://keycloak.localtest.me/ にブラウザでアクセス
```

### B. SPIパターンを追加する

1. `keycloak/providers/0N-<name>/` を既存パターンから複製
2. ロジック実装 + 単体テスト
3. `keycloak/providers/integration-tests/` に `*IT.java` + テスト realm JSON 追加
4. (画面UIあれば) `e2e-tests/tests/` に `*.spec.ts` 追加
5. `docs/specs/patterns/0N-<name>.md` にレシピを書く
6. `make test-providers && make test-integration && make test-e2e` で全層検証

詳細手順は [keycloak/providers/CLAUDE.md](keycloak/providers/CLAUDE.md)、テストの書き分けは [docs/testing.md](docs/testing.md)。

### C. 管理コンソール設定を案件に適用する

1. `docs/specs/task-specs/01-admin-console-config-template.md` を顧客リポにコピーして埋める
2. ジュニアが Claude に渡す → `terraform/environments/<案件>/main.tf` を生成
3. `terraform plan` の diff を熟練者がレビュー
4. `terraform apply` で本番反映、`make tf-test` で動作検証

詳細は [terraform/CLAUDE.md](terraform/CLAUDE.md)。

### D. 全テストを回す

```bash
make test-providers       # 単体 (Mockito、Docker不要)
make test-integration     # Java IT (Testcontainers + HTTP、Docker必要)
make test-e2e             # ブラウザE2E (Playwright、Docker必要、初回は make e2e-install)
```

各層の責務は [docs/testing.md](docs/testing.md) に詳細記載。

---

## ヘルプ・トラブルシューティング

- `make help` — 全コマンド一覧
- 各サブディレクトリの `CLAUDE.md` が詳細な流儀・規約
- [docs/testing.md](docs/testing.md) の "既知の罠" セクションに開発中に踏んだ落とし穴を集約
- ログを見る:
  - Keycloak (dev): `make logs`
  - Java IT: `keycloak/providers/integration-tests/target/failsafe-reports/`
  - E2E: `e2e-tests/test-results/<test>/` の screenshot/video/trace
- E2E trace 閲覧: `npx playwright show-trace e2e-tests/test-results/<...>/trace.zip`
- Maven 詳細: `mvn ... -X`

## ライセンス / コントリビューション

(社内利用想定。雛形リポへの改善提案は PR で受付)
