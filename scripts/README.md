# scripts/

運用補助スクリプトの置き場 (Phase 3 で整備)。

## 予定しているスクリプト

- `export-realm.sh` — 稼働中Realmを `realms/` 配下にJSONエクスポート (秘匿情報マスキング込み)
- `build-providers.sh` — `providers/` 配下のMavenモジュールを一括ビルド
- `wait-for-keycloak.sh` — Keycloakのhealth/readyを待機 (CI用)
- `dev-reset.sh` — 開発DB初期化 + 最小Realm再投入

> このディレクトリは Phase 3 で本格的に内容が入る。
