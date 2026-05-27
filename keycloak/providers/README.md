# keycloak/providers/

Keycloakの **SPI拡張** (カスタムプロバイダー) を配置する。`compose.yaml` で `/opt/keycloak/providers/` にマウントされる。

## 含まれるもの (Phase 2以降)

- カスタム Authenticator (多要素認証、独自認証フロー)
- UserStorage Provider (外部DB/LDAPからのユーザー取得)
- Event Listener (監査ログ、外部通知)
- Required Action、Mapper など

## ビルド成果物

JARをこのディレクトリに配置する。サブディレクトリでMavenマルチモジュールにする予定 (Phase 2)。

## デプロイの流れ

1. Mavenでビルドして `target/*.jar` を `providers/` 配下にコピー (またはシンボリックリンク)
2. `make restart` でKeycloakを再起動 — `start-dev` モードでは起動時に provider のbuildが自動実行される

> 詳細はPhase 2 / Phase 3 で本ディレクトリ内に専用CLAUDE.mdを追加予定。
