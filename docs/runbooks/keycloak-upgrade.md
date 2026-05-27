# Keycloak バージョンアップ手順

Keycloak のパッチ/マイナー/メジャーバージョンを上げる作業手順。

---

## 目的

- セキュリティパッチ適用
- 新機能の取り込み
- 将来のEOLバージョンからの移行

---

## バージョンアップの分類

| 種類 | 例 | 影響度 | 頻度 |
| --- | --- | --- | --- |
| Patch | 26.0.7 → 26.0.8 | 低 (SPI API互換、Realm互換) | 月1回程度 |
| Minor | 26.0.x → 26.1.x | 中 (SPI APIに差分の可能性、Realm互換) | 四半期 |
| **Major** | 26.x → 27.x | **高** (SPI/設定/Realm にbreaking changes 可能性) | 半年〜年次 |

判断: **Patch は自動追従、Minor/Major は事前検証必須** 。

---

## 前提条件

- 全テストがgreenな状態 (`make test-all && make test-e2e`)
- リリースノート確認済み ([Keycloak Releases](https://www.keycloak.org/docs/latest/release_notes/))
- ステージング環境がある場合、先にステージングで検証

---

## 手順 (Patch / Minor)

### 1. リリースノートを読む

- https://www.keycloak.org/docs/latest/release_notes/
- 注目点:
  - **Breaking changes** セクション
  - SPI API 変更
  - Realm import schema 変更
  - 依存する Quarkus / Java バージョンの変更

### 2. Maven Centralでバージョン存在確認

```bash
curl -s "https://search.maven.org/solrsearch/select?q=g:org.keycloak+AND+a:keycloak-core&core=gav&rows=10&wt=json" \
  | jq -r '.response.docs[].v' | grep '^26\.' | head -5
```

採用したいバージョンが Maven Central にあることを確認。

### 3. バージョン番号の更新

3箇所を同時に更新:

```bash
# (1) .env.example の KEYCLOAK_VERSION
sed -i.bak 's/^KEYCLOAK_VERSION=.*/KEYCLOAK_VERSION=26.0.NEW/' .env.example

# (2) keycloak/providers/pom.xml の keycloak.version
sed -i.bak 's|<keycloak.version>[^<]*</keycloak.version>|<keycloak.version>26.0.NEW</keycloak.version>|' keycloak/providers/pom.xml

# (3) ローカルの .env も更新 (任意)
sed -i.bak 's/^KEYCLOAK_VERSION=.*/KEYCLOAK_VERSION=26.0.NEW/' .env
```

### 4. テスト用イメージ取得 + 動作確認

```bash
make pull                      # 新イメージを取得
make build-restart             # SPIを新バージョンでビルド + Keycloak再起動
make logs                      # 起動が正常か確認
```

ブラウザで https://keycloak.localtest.me/ にアクセス、管理コンソールに admin ログインできることを確認。

### 5. 全層テスト

```bash
make test-providers            # 単体
make test-integration          # Java IT
make test-e2e                  # ブラウザE2E
make tf-test                   # Terraform設定検証
```

全てgreenを確認。

### 6. ステージング適用 (該当する場合)

```bash
# カスタムイメージビルド
make image IMAGE_TAG=26.0.NEW

# レジストリpush
docker tag keycloak-custom:26.0.NEW registry.example.com/keycloak-custom:26.0.NEW
docker push registry.example.com/keycloak-custom:26.0.NEW

# ステージング k8s/ECS等でイメージタグ更新
# (案件のデプロイ手順に従う)
```

ステージングで実認証フロー (Web Auth Code, Direct Grant, IdP連携等) を **手動で再現テスト**。

### 7. 本番反映

ステージング検証後、同じイメージタグで本番に反映。

> **ロールバック手順**: 古いイメージタグに戻す → DB schema変更があった場合は対応 (通常 minor patch ではない)

### 8. ドキュメント更新

```bash
# docs/architecture.md に「最新バージョン: 26.0.NEW」記録
# SECURITY.md / README.md にもバージョン記述があれば更新
```

CHANGELOG (`docs/CHANGELOG.md` を将来追加予定) または PR description に変更内容を記録。

---

## 手順 (Major)

Patch/Minor の上記手順に加えて:

### 事前準備

1. **公式マイグレーションガイド** を熟読 (例: https://www.keycloak.org/docs/latest/upgrading/)
2. **Breaking changes リスト** を作成し、影響範囲を洗い出す
3. 既存 Realm JSON の互換性確認 (新バージョンで import できるか別環境で試す)
4. SPI コードの修正必要箇所を特定

### 追加手順

- **新規環境で完全テスト** : 新バージョンの空Keycloak に Realm を import + SPI を build → 全テスト → 手動シナリオ確認
- **DB マイグレーション** : Keycloak は起動時に自動マイグレーションするが、大規模Realmでは時間がかかるため事前に **本番相当データで検証**
- **顧客告知** : メジャーバージョンアップは挙動が変わる可能性があるため、案件オーナー経由で顧客通知
- **ロールバック計画** : DBスキーマ変更があるとロールバックが困難なので、 **DB スナップショットを事前取得**

---

## トラブルシューティング

### Keycloak起動失敗

- ログ確認: `make logs`
- 多くは KC_* 環境変数の互換性問題 (新バージョンで非推奨/廃止)
- 公式リリースノートの「Configuration changes」を確認

### SPI ビルド失敗 (compile error)

- SPI API 変更が原因
- 新バージョンの API ドキュメントに合わせて修正
- `EmailDomainAllowlistAuthenticator.java` 等で `realm.getDirectGrantFlow()` 等の signature変更等

### Realm import 失敗

- 新バージョンで非推奨化されたフィールドが原因のことが多い
- 起動時 KC ログを確認 (`make logs | grep -i import`)
- 必要なら Realm JSONを編集 (該当フィールド削除)

### テスト失敗

- testcontainers-keycloak が新Keycloakバージョン未対応の場合あり
- `e2e-tests/package.json` と `keycloak/providers/pom.xml` の testcontainers-keycloak version を上げる

---

## ロールバック

### Patch / Minorの場合

1. `.env.example` / `keycloak/providers/pom.xml` / `.env` を旧バージョンに戻す
2. `make pull && make build-restart`
3. テスト確認

### Majorの場合

1. DB スナップショット復元 (事前取得が前提)
2. 旧イメージタグでデプロイ
3. Realm JSON が破壊的変更を含む場合は import から復旧

---

## 関連

- [Keycloak Releases](https://www.keycloak.org/docs/latest/release_notes/)
- [Keycloak Upgrading Guide](https://www.keycloak.org/docs/latest/upgrading/)
- [SECURITY.md](../../SECURITY.md) — CVE 追従ポリシー
- [docs/architecture.md](../architecture.md) — Keycloak バージョン方針
