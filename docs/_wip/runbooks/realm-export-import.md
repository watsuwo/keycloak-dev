# Realm Export / Import

稼働中のKeycloak Realmを **JSON にエクスポート** 、または別環境に **インポート** する運用手順。

---

## 目的

- 本番Realmのバックアップ・スナップショット取得
- 環境間の設定同期 (staging → production)
- Realm設定の差分確認 (Terraform管理外の手動変更を検出)
- 障害時の復旧用

> **注意**: Terraform化されたRealmは Terraform で管理が正。Realm JSONエクスポートはあくまで **スナップショット参照** 用。
> 手動でJSON編集してインポートし直す運用は競合の元になるので避ける。

---

## 前提条件

- Keycloak が稼働中 (`make up` で dev環境、または対象環境)
- 対象Realmの admin 権限を持つアカウント
- `docker compose exec` 経由でKeycloakコンテナにアクセス可能

---

## エクスポート手順

### 方法A: ファイルにエクスポート (推奨、稼働中でOK)

```bash
# 1. Keycloakコンテナに入って kc.sh export 実行
docker compose exec keycloak /opt/keycloak/bin/kc.sh export \
  --dir /tmp/realm-export \
  --realm <REALM_NAME> \
  --users realm_file

# 2. ホストにコピー
docker compose cp keycloak:/tmp/realm-export ./exports/<REALM_NAME>-$(date +%Y%m%d)

# 3. (秘匿情報をマスキングする場合)
# Client secret、IdP secret、SMTPパスワード等を sed で除去/置換
sed -i.bak 's/"secret": "[^"]*"/"secret": "REDACTED"/g' ./exports/<REALM_NAME>-*/*.json
```

オプション解説:
- `--users realm_file` : ユーザーも含めてエクスポート (`--users skip` でユーザー除外)
- `--users different_files` : ユーザーを別ファイルに分割 (大規模Realm向け)
- `--realm` 省略時は全Realm

### 方法B: Admin REST API 経由

```bash
# 1. admin token取得
ADMIN_TOKEN=$(curl -sk -X POST \
  https://keycloak.localtest.me/realms/master/protocol/openid-connect/token \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=admin" | jq -r .access_token)

# 2. Realm partial export
curl -sk -X POST \
  "https://keycloak.localtest.me/admin/realms/<REALM_NAME>/partial-export?exportClients=true&exportGroupsAndRoles=true" \
  -H "Authorization: Bearer ${ADMIN_TOKEN}" \
  -o "./exports/<REALM_NAME>-partial-$(date +%Y%m%d).json"
```

> ⚠️ Partial Exportは Client Secret 等の秘匿情報を **デフォルトでは含めない** (より安全)

---

## インポート手順

### 方法A: 起動時にimport (推奨、初期構築用)

`keycloak/realms/` ディレクトリにJSONを置いて Keycloak を `start-dev --import-realm` で起動。

```bash
cp ./exports/<REALM_NAME>-20260523/<REALM_NAME>-realm.json ./keycloak/realms/
make restart
```

複数のJSONがあれば全部読み込まれる。

### 方法B: 稼働中Realmに上書き (要注意)

`kc.sh import` または Admin Console UI から実行できるが、 **既存Realm を上書きする操作** なので慎重に。

```bash
# 既存Realm削除 (CAUTION!) → 再インポート
docker compose exec keycloak /opt/keycloak/bin/kc.sh import \
  --file /opt/keycloak/data/import/<REALM_NAME>-realm.json \
  --override true
```

> ⚠️ `--override true` は既存Realmを削除して再作成する。**本番では絶対に使わない** (ユーザーデータが消える)。

---

## 検証

エクスポート後:

- [ ] 生成されたJSONがvalid (`jq . < <file>.json > /dev/null` でエラーなし)
- [ ] ファイルサイズが妥当 (空ではない、極端に小さくない)
- [ ] 主要設定が含まれている (`jq '.clients | length, .users | length, .authenticationFlows | length' < <file>`)

インポート後:

- [ ] 管理コンソールで Realm が見える
- [ ] 主要Clientでログインできる
- [ ] カスタムフローが正しく Bindings に紐づいている
- [ ] テストユーザーで認証フローが期待通り動く

---

## トラブルシューティング

### エクスポートで「Realm not found」

- `--realm` の値が realm 名と完全一致 (大小区別) しているか確認
- `docker compose exec keycloak /opt/keycloak/bin/kcadm.sh get realms --fields realm` で realm一覧取得

### インポート失敗 (Authentication Flow関連)

- 参照しているSPI Authenticator (`email-domain-allowlist-authenticator` 等) のJARが `/opt/keycloak/providers/` に配置されているか
- `make build-restart` で SPI再ビルド + 再起動

### "Account is not fully set up" エラーがimport後に出る

- User の `requiredActions` が空でない (例: VERIFY_EMAIL が自動付与)
- User Profile必須属性 (firstName/lastName) が欠けている
- 詳細は [docs/testing.md](../testing.md#既知の罠--集約リスト) 参照

### 秘匿情報の取扱

- エクスポートしたJSONを **そのままgit commitしない** (Client Secret 等含む場合あり)
- マスキング処理を経由してから保管する (上記 sed 例)
- 本番Realmのエクスポートは **暗号化ストレージ** に保管

---

## ロールバック

エクスポート前のRealmに戻したい場合:

1. 過去のエクスポートJSON (`exports/<REALM_NAME>-YYYYMMDD/`) を用意
2. 現在のRealmを別名でエクスポート (現状の保全)
3. `kc.sh import --override true` で過去版を適用
4. 検証 → 問題があれば 2 のバックアップから再復旧

---

## 自動化案 (将来課題)

- Phase 3で `make export-realm` / `make import-realm` のMake targetを実装予定
- nightly cron で本番Realmを暗号化済みでS3等に自動バックアップ
- Realm JSON diff を CI で検出して「Terraform管理外の手動変更」を通知

## 関連

- [terraform/CLAUDE.md](../../terraform/CLAUDE.md) — 設定as Code の正としての Terraform
- [docs/testing.md](../testing.md) — realm.json の罠
