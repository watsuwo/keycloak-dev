# 新規顧客案件の立ち上げ手順

このリポジトリを **雛形** として新規顧客案件を始めるときの手順書。

> 想定読者: 案件マネージャ / 熟練エンジニア (新案件の初動を担当)
> 所要時間: 環境構築まで30分、初回要件ヒアリング次第で半日〜数日

---

## 概要 — 全体の流れ

```
[案件発生]
    ↓
[1. 雛形リポを clone して顧客リポを作る]
    ↓
[2. 顧客名でリネーム + 初期設定]
    ↓
[3. case-spec.md でヒアリング結果を構造化]
    ↓
[4. task-spec を作業タイプ別に作成 (ジュニア → 熟練者レビュー)]
    ↓
[5. Claude にtask-spec を渡して実装ドラフト生成]
    ↓
[6. terraform plan/apply + 3層テスト で検証]
    ↓
[7. ステージング → 本番デプロイ]
```

---

## 1. 雛形リポからの clone

```bash
# 命名規則: <顧客名のケバブケース>-keycloak または <顧客名>-auth など、社内ルールに従う
# 例: ACME 株式会社 → acme-corp-keycloak
git clone <雛形リポURL> acme-corp-keycloak
cd acme-corp-keycloak

# 雛形リポとのリンクを切る (案件は独立進化させる)
git remote remove origin

# 顧客リポを新規作成して push
git remote add origin <顧客リポURL>
git branch -M main
git push -u origin main
```

> **雛形リポと顧客リポの関係**: 案件は雛形から派生して独立進化する。
> 雛形側で生まれた新パターンを取り込みたい場合は、cherry-pick または subtree マージで個別取り込み (運用は熟練者判断)。
> 逆に、案件側で生まれた汎用化可能な実装は雛形リポに PR で逆輸入する。

---

## 2. 案件用にリネーム + 初期設定

### 2.1 識別子の決定

| 項目 | 雛形での値 | 案件での例 | 用途 |
| --- | --- | --- | --- |
| 案件コード | `example-customer` | `acme-corp` | Realm名、tfディレクトリ名等 |
| 顧客表示名 | "Example Customer" | "ACME株式会社" | 管理コンソールの表示名 |
| Maven groupId | `com.example.keycloak` | `com.acme.keycloak` | SPI Java パッケージ |
| Docker image名 | `keycloak-custom` | `keycloak-acme` | カスタムイメージタグ |

### 2.2 ファイル書き換え (機械的)

雛形では `example-customer` / `com.example` で固定しているので置換する。

```bash
# Realm名・Terraform環境名・Java package を一括置換 (確認しながら)
grep -rl "example-customer" --include="*.tf" --include="*.json" --include="*.md" \
  | xargs sed -i '' 's/example-customer/acme-corp/g'

# Java package
find providers -name "*.java" -o -name "pom.xml" \
  | xargs grep -l "com.example.keycloak" \
  | xargs sed -i '' 's/com.example.keycloak/com.acme.keycloak/g'

# ディレクトリリネーム
mv keycloak/providers/sample-01-email-domain-allowlist/src/main/java/com/example keycloak/providers/sample-01-email-domain-allowlist/src/main/java/com/acme
mv keycloak/providers/sample-01-email-domain-allowlist/src/test/java/com/example keycloak/providers/sample-01-email-domain-allowlist/src/test/java/com/acme
# (テストも同様、IntelliJ等のリファクタ機能の方が安全)
```

> ⚠️ パッケージ名は IDE のリファクタ機能でやる方が import/参照ずれが少ない。sed は最終確認用。

### 2.3 Terraform 環境の準備

```bash
cp -r terraform/environments/example-customer terraform/environments/acme-corp
# terraform/environments/acme-corp/main.tf の realm_name, client_id 等を案件用に修正
cp terraform/environments/acme-corp/terraform.tfvars.example terraform/environments/acme-corp/terraform.tfvars
# .tfvars を実環境値で埋める (本番URL、admin認証等)
```

サンプル `example-customer` は不要なら削除しても良いが、参考実装として残しておく方が新メンバーに親切。

### 2.4 動作確認

```bash
make init
make up
make build-restart    # SPI ビルド + KC再起動
make test-providers   # 単体テスト
make test-integration # Java IT (Docker要)
make test-e2e         # ブラウザE2E (要 make e2e-install)
```

すべてグリーンになることを確認。雛形の動作を案件リポでも再現できている = 起点が正常。

---

## 3. case-spec.md でヒアリング結果を構造化

顧客との初回ヒアリングが終わったら、`docs/specs/case-spec-template.md` を起点に案件の要件を文書化する。

```bash
cp docs/specs/case-spec-template.md docs/case-spec.md
# 11セクションを埋める
```

埋めるタイミングと粒度:

| タイミング | 埋める範囲 | 状態 |
| --- | --- | --- |
| 初回ヒアリング後 | 1.基本情報、2.ユーザー構成、3.認証要件 (大枠) | 70%下書き |
| 2回目以降のヒアリング | 4.Theme、5.Client構成、6.Role、7.外部連携 | 90%確定 |
| 設計完了時 | 8.セキュリティ、9.テスト、10.引き渡し、11.リスク | 100%確定 |

不明な点は **「未確認」と書いて空欄にしない**。次回ヒアリングで何を確認するかが明示される。

### case-spec の役割

- 顧客との対話の **型** (これを埋めようとすると質問項目が自然に出てくる)
- Claude/AI への **入力フォーマット** (これが曖昧だと実装も曖昧になる)
- 案件レビュー時の **チェックリスト** (実装が要件をカバーしているか)

---

## 4. task-spec を作業タイプ別に作成

`case-spec.md` (案件全体) を **作業タイプ別の task-spec** に分解する。これがClaude/ジュニア向けの実装インプット。

```bash
mkdir -p docs/specs/task-specs
cp /path/to/雛形/docs/specs/task-specs/01-admin-console-config-template.md docs/specs/task-specs/acme-admin-console.md
# (将来は 02-spi-customization-template.md, 03-themes-template.md 等も追加予定)
```

役割分担:

| 役割 | 担当 |
| --- | --- |
| task-spec ドラフト | ジュニア (顧客ヒアリングで得た情報を構造化) |
| task-spec レビュー | 熟練者 (設計判断・パターン選定・命名規則の確定) |
| 実装ドラフト | Claude + ジュニア |
| 実装レビュー | 熟練者 |

---

## 5. Claude による実装ドラフト生成

レビュー済み task-spec を Claude に渡して、Terraform HCL や SPI コード を生成させる。

### 管理コンソール設定 (Terraform) の生成パターン

```
Claudeへの指示例:
「docs/specs/task-specs/acme-admin-console.md に基づいて、
terraform/environments/acme-corp/main.tf を生成してください。
terraform/modules/ から該当モジュールを選んで組合せてください。」
```

Claude は:
- task-spec から Realm / Client / Role / Flow を読み取る
- `terraform/modules/` の `client-confidential` 等を参照
- main.tf を生成 (resource 構造を整える、Secrets は変数に切る)
- 必要なら module 不足を指摘 (新規 module 作成タスクを別途切る)

### SPI カスタマイズの生成パターン

```
Claudeへの指示例:
「docs/case-spec.md の "3.3 アクセス制限" にあるドメイン制限要件について、
docs/specs/patterns/01-email-domain-allowlist.md のパターンを派生させて
keycloak/providers/02-acme-domain-policy/ を作ってください。
ドメインリストはAcme固有のXXXルールに従って判定するよう改造してください。」
```

Claude は:
- パターン1を雛形にディレクトリ複製
- Java実装を案件固有ロジックに書き換え
- 単体テスト・Java IT・(必要なら) ブラウザE2E のテストもセットで生成

---

## 6. 検証

```bash
# Terraform: dev環境でapply → 検証 → destroy のローテーション
make tf-test TF_DIR=terraform/environments/acme-corp

# SPI: 3層テスト
make test-providers
make test-integration
make test-e2e
```

熟練者は:
- `terraform plan` の diff をレビュー (期待する設定変更になっているか)
- SPI コードレビュー ([review-checklists/](review-checklists/) 参照)
- 自動テストでカバーされていない観点を案件用受け入れテストとして手動実施

---

## 7. ステージング → 本番デプロイ

```bash
# カスタムKCイメージをビルド (SPI + Theme + 必要なら Realm import 同梱)
make image IMAGE_NAME=keycloak-acme IMAGE_TAG=$(git rev-parse --short HEAD)

# ステージング環境のレジストリに push
docker tag keycloak-acme:$(git rev-parse --short HEAD) registry.example.com/keycloak-acme:$(git rev-parse --short HEAD)
docker push registry.example.com/keycloak-acme:$(git rev-parse --short HEAD)

# ステージングのKubernetes/ECS等で新イメージにロールアウト
# Terraform は同じ HCL を staging環境向け .tfvars で apply
cd terraform/environments/acme-corp
terraform workspace select staging  # workspaceで環境切替する場合
terraform apply -var-file=staging.tfvars
```

本番反映は熟練者承認を経て同様のフローで実施。`docs/runbooks/` の運用手順を順守。

---

## チェックリスト — 案件立ち上げ完了の判断基準

- [ ] 顧客リポが GitHub等に作成され、雛形リポからのコピーが完了
- [ ] `make up && make test-providers && make test-integration && make test-e2e` がグリーン
- [ ] `docs/case-spec.md` の主要セクションが「未確認」ゼロで埋まっている
- [ ] `docs/specs/task-specs/` に作業タイプごとの task-spec がドラフト〜レビュー完了の状態である
- [ ] `terraform/environments/<案件>/` が dev環境で apply できる
- [ ] チーム内で案件オーナー (熟練者) と作業担当 (ジュニア) が決まっている
- [ ] 顧客向けに必要な追加合意事項 (NDA、CI/CDアクセス権、本番アクセス権等) を確認

---

## 参考

- [README.md](../README.md) — 雛形リポの概要
- [docs/specs/case-spec-template.md](case-spec-template.md) — 案件全体の入力テンプレ
- [docs/specs/task-specs/](task-specs/) — 作業タイプ別の入力テンプレ
- [docs/specs/patterns/](patterns/) — SPI パターンカタログ
- [terraform/CLAUDE.md](../terraform/CLAUDE.md) — Terraform化の流儀
- [docs/testing.md](testing.md) — テスト方式
- [docs/onboarding.md](onboarding.md) — 新メンバーのオンボーディング
