# keycloak/providers/ — Keycloak SPI 開発

このディレクトリはKeycloakのカスタムProvider (SPI実装) をMaven multi-moduleとして管理する。

## ディレクトリ構造

```
keycloak/providers/
├── pom.xml                          親POM (依存・プラグインバージョン管理)
├── CLAUDE.md                        このファイル (SPI開発の流儀)
├── 01-email-domain-allowlist/       パターン1: Authenticator (見本)
├── 0N-...                           パターンを増やすときは番号付けで並列に配置
├── integration-tests/                Java IT (実Keycloak起動でAPI検証)
└── *.jar                            ビルド成果物 (make build-providers でコピーされる、gitignore対象)
```

各サブモジュールは独立したJARとしてビルドされ、`make build-providers` で `keycloak/providers/` 直下にコピーされる。Keycloakは `/opt/keycloak/providers/*.jar` を起動時に読み込む。

## 開発の基本フロー

```bash
make build-providers   # 全モジュールを mvn package + JARを keycloak/providers/ にコピー
make restart           # Keycloakを再起動 (SPIが読み込まれる)
# または
make build-restart     # 上記2つを一気に
```

`start-dev` モードのKeycloakは起動時にSPIを自動buildする (`kc.sh build` 相当が暗黙実行)。`start` モードで動かすときは明示的なbuildが必要。

## 前提ツール

- **JDK 17以上** (Keycloak 26.x のSPIはJava 17でビルド可)
- **Maven 3.9以上**
- WSL2の場合は `sudo apt install openjdk-17-jdk maven` 等で導入

## SPIの種類とExtension Point

このリポで扱うSPIは主に以下:

| SPI種別 | 用途 | Factoryインタフェース |
| --- | --- | --- |
| Authenticator | 認証フローのステップ | `org.keycloak.authentication.AuthenticatorFactory` |
| Required Action | アカウント初期設定フロー | `org.keycloak.authentication.RequiredActionFactory` |
| Event Listener | 監査・通知 | `org.keycloak.events.EventListenerProviderFactory` |
| User Storage | 外部DB連携 | `org.keycloak.storage.UserStorageProviderFactory` |
| Protocol Mapper | JWTクレーム生成 | `org.keycloak.protocol.oidc.mappers.OIDCProtocolMapper` (継承) |
| Theme | 画面/メール (これは別ディレクトリ `keycloak/themes/` で扱う) | — |

それぞれ `META-INF/services/<Factoryインタフェースの完全名>` に実装クラスを登録する。

## 新しいパターンを追加する手順

1. `keycloak/providers/0N-<pattern-name>/` ディレクトリを作る (既存パターンを丸ごとコピーするのが早い)
2. `pom.xml` の `<artifactId>` `<name>` を変更
3. Javaパッケージ名を変更 (`com.example.keycloak.<spi-type>.<name>`)
4. 親POMの `<modules>` に追加
5. クラス実装 → テスト → CLAUDE.md (パターン解説) を整備
6. `docs/specs/patterns/0N-<pattern-name>.md` にレシピを書く (パターンカタログ用)
7. `make build-restart` で動作確認

## バージョン整合

`pom.xml` の `keycloak.version` は、`.env` の `KEYCLOAK_VERSION` と同じ系列 (例: 26.0.x) に揃える。マイナーバージョンが上がる (26.0→26.1) ときはSPI APIに破壊的変更が入る可能性があるため、ビルドと動作確認をやり直すこと。

## テスト方針

2層構成。フェーズと実行ターゲットを分離している。

| 層 | 場所 | 仕組み | フェーズ | Docker | 実行コマンド |
| --- | --- | --- | --- | --- | --- |
| 単体テスト | 各SPIモジュール `src/test/` | Mockito + JUnit5 で `AuthenticationFlowContext` 等をモック | Surefire (`test`) | 不要 | `make test-providers` |
| 統合テスト | `integration-tests/src/test/` | Testcontainers で実Keycloakを起動、Realm import + Direct Grant 等で検証 | Failsafe (`verify`) | 必要 | `make test-integration` |

- 単体テストはCIで毎コミット実行 (高速、Docker不要)
- 統合テストは PR マージ前 / ナイトリーで実行 (Keycloak pullで初回数分)
- パターンを追加するときは **両方** を書く: 単体でロジック、統合で実Keycloak挙動

詳細: [keycloak/providers/integration-tests/CLAUDE.md](integration-tests/CLAUDE.md)

## 命名規則

- パッケージ: `com.example.keycloak.<spi-type>.<pattern-name>` (顧客リポでは `com.example` を会社/顧客のドメインに置換)
- artifactId: ケバブケース (`email-domain-allowlist`)
- ディレクトリ: `0N-<artifactId>` (Nは2桁の連番)

## 参考

- Keycloak Server Developer Guide: https://www.keycloak.org/docs/latest/server_development/
- Keycloak Quickstarts (公式サンプル): https://github.com/keycloak/keycloak-quickstarts
