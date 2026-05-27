# docs/

開発業務に関するドキュメント置き場。コードではなく **業務プロセス・パターン集・ルール** を集約する。

## 構成

```
docs/
├── README.md                        このファイル (docs/ の構成説明)
│
│   ── 利用者向けスターター・全体把握 ──
├── testing.md                       テスト方式ガイド (3層構成、ツール、運用、デバッグ、既知の罠)
├── onboarding.md                    新メンバー1週間オンボーディング (Day 1〜5)
├── customer-rollout.md              新規顧客案件の立ち上げ手順 (clone から本番デプロイまで)
├── architecture.md                  設計判断のADR (Architecture Decision Records)
├── glossary.md                      Keycloak + プロジェクト用語集
│
│   ── spec (仕様書駆動開発) ──
├── specs/                           SDD で扱う spec 一式 (frontmatterで機械検証)
│   ├── README.md                    specs/ 配下の構成
│   ├── specs-guide.md               frontmatterスキーマ + spec_id命名規則
│   ├── case-spec-template.md        TEMPLATE-CASE-SPEC
│   ├── patterns/                    PATTERN-* (再利用パターンカタログ)
│   │   └── 01-email-domain-allowlist.md   PATTERN-AUTH-DOMAIN-ALLOWLIST
│   └── task-specs/                  TEMPLATE-TASK-* (作業タイプ別テンプレ)
│       └── 01-admin-console-config-template.md   TEMPLATE-TASK-ADMIN-CONSOLE
│
│   ── レビューと運用 ──
├── review-checklists/               レビュアー観点チェックリスト
│   ├── spi-review.md
│   └── realm-config-review.md
│
└── runbooks/                        運用手順書
    ├── README.md
    ├── realm-export-import.md
    └── keycloak-upgrade.md
```

## それぞれの位置づけ

### `testing.md`

**テスト方式まとめ** (利用者向け、新メンバー必読)。3層構成 (単体 / Java IT / ブラウザE2E) + 補助の Terraform 検証について、役割分担・利用ツール・実行コマンド・デバッグ手順・既知の罠を集約。

### `onboarding.md`

**新メンバーの最初の1週間** のガイド。Day1=環境構築、Day2=ドキュメント通読+テスト実行、Day3=パターン1読解、Day4=小改造、Day5=PRレビュー体験。

### `customer-rollout.md`

**新規顧客案件を始めるとき** の手順書。雛形リポからclone → リネーム → case-spec埋め → task-spec作成 → 実装 → デプロイ。

### `architecture.md`

**設計判断のADR (Architecture Decision Records)** 集。「なぜ Quarkus版?」「なぜ Terraform?」「なぜ E2E は TypeScript?」等の判断理由を記録。新しい大判断をしたら追記。

### `glossary.md`

**Keycloak + プロジェクト独自用語** の辞書。ジュニアが「これ何?」を即引きできる用に。

### `specs/`

**仕様書駆動開発 (SDD) で扱う spec ファイル一式** 。各ファイルが YAML frontmatter で `spec_id` を持ち、`make spec-validate` で機械検証される。

- `specs/specs-guide.md` — frontmatter スキーマ・spec_id 命名規則・書き方ガイド (SDD リファレンス)
- `specs/case-spec-template.md` — 案件全体の要件入力テンプレ (顧客リポにコピーして使う)
- `specs/patterns/` — SPI/Theme パターンカタログ (動く実例 + レシピ)
- `specs/task-specs/` — 作業タイプ別の入力テンプレ

詳細は [specs/README.md](specs/README.md) 参照。

### `review-checklists/`

**コードレビュー観点のチェックリスト** 。SPI実装・Terraform設定それぞれに分けて整理。レビュアー(熟練者)向けだが、PR著者の自己レビューにも使える。

### `runbooks/`

**定型運用手順** のメモ。Realm export/import、Keycloak upgrade等。新しい運用作業が発生したら追加。

## このリポにdocs/を置く理由

`docs/` の中身は **特定顧客に依存しない、会社共通の資産**。雛形リポに集約することで:

- 全案件から参照可能 (顧客リポからは `git submodule` または手動同期で参照)
- 新パターンが生まれたら雛形リポにPRする運用にできる
- Claudeが案件をまたいでパターン知識を活用できる

## 関連 (リポルート)

| ファイル | 位置 |
| --- | --- |
| [README.md](../README.md) | スターターガイド (最初に読む) |
| [CLAUDE.md](../CLAUDE.md) | 開発作業の詳細リファレンス |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | コントリビューション規約 |
| [SECURITY.md](../SECURITY.md) | セキュリティ方針 |
