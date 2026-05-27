# keycloak/realms/

Keycloakの **Realm設定JSON** を配置する。`compose.yaml` で `/opt/keycloak/data/import/` にマウントされ、起動時に `--import-realm` で自動インポートされる。

## ファイル命名

- `<realm-name>-realm.json` — Realm本体
- `<realm-name>-users-0.json` — ユーザー (オプション、分割可)

## エクスポート

稼働中のRealmから設定をJSONに書き出す方法はPhase 3で `make export-realm` ターゲットとして整備予定。

## 注意

- 秘匿情報 (clientSecret、SMTPパスワード、IdPシークレット) はJSONに含めないようマスキングする運用にする。具体的なルールはPhase 3で定義。
- インポートは起動時のみ。実行中の設定変更は管理コンソール経由で行い、定期的にexportしてコミットする。

> 詳細はPhase 2で本ディレクトリ内に専用CLAUDE.mdを追加予定。
