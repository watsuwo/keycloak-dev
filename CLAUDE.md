# Keycloak 開発基盤 — 作業者向け詳細ガイド

チーム共通のKeycloakカスタマイズ開発リポジトリ。SPI拡張・Themes・Realm設定・外部システム連携の4領域を扱う。

> **はじめて読む方は [README.md](README.md) から** — このリポジトリの目的・全体像・最初に読むべきドキュメントの誘導があります。
> このファイル (CLAUDE.md) はそれを踏まえた **作業中の参照用** (Claude含む全員が常時参照する詳細仕様)。

## バージョン

- Keycloak: **26.x (Quarkus版)** — `quay.io/keycloak/keycloak`
- PostgreSQL: 16-alpine
- Traefik: v3.x — リバースプロキシ + TLS終端
- Mailhog: 開発用SMTPサーバ

具体的なバージョン固定は `.env` の各 `*_VERSION` で行う。

## クイックスタート

```bash
make init   # .env を生成 + 自己署名証明書を生成
make up     # 全サービスを起動
make logs   # Keycloakログを追う
```

起動後 (デフォルト設定の場合):

| URL | 用途 |
| --- | --- |
| https://keycloak.localtest.me/ | Keycloak 管理コンソール (admin / admin) |
| https://mailhog.localtest.me/ | Mailhog Web UI |
| http://localhost:9000/health/ready | Keycloak 健康チェック (直接) |
| http://localhost:8081/dashboard/ | Traefik ダッシュボード |

> 初回アクセス時、ブラウザに自己署名証明書の警告が出ます。これは正常です。「詳細設定」→「アクセスする」で進めるか、`traefik/certs/local-cert.pem` をOS/ブラウザの信頼ストアに追加すれば警告を消せます。

停止:

```bash
make down       # 停止 (DBは保持)
make clean      # 停止 + DBボリューム削除 (完全クリーン)
```

その他のターゲットは `make help` を参照。

## アクセス用ホスト名 (`BASE_DOMAIN`)

`.env` の `BASE_DOMAIN` で Traefik のルーティングホスト名のベースを決める。サービスは `<service>.${BASE_DOMAIN}` でルーティングされる:

- `keycloak.${BASE_DOMAIN}` → Keycloak
- `mailhog.${BASE_DOMAIN}` → Mailhog Web UI

デフォルトは `localtest.me`。`*.localtest.me` は公開DNSで `127.0.0.1` に自動解決されるため `/etc/hosts` の編集は不要。

### 独自ドメインを使う場合

例えば `dev.example.local` をベースにしたい場合:

1. `.env` を以下のように変更
   ```
   BASE_DOMAIN=dev.example.local
   KC_HOSTNAME=https://keycloak.dev.example.local
   ```
2. `/etc/hosts` (WSL2の場合は `/etc/hosts` と Windowsの `C:\Windows\System32\drivers\etc\hosts` の両方) に追記
   ```
   127.0.0.1 keycloak.dev.example.local mailhog.dev.example.local
   ```
3. 証明書を再生成
   ```bash
   make certs-regen
   make restart-traefik
   ```

## ディレクトリ構造

```
keycloak-dev/
├── compose.yaml                 # Docker Compose定義 (Traefik + Keycloak + Postgres + Mailhog)
├── .env.example                 # 環境変数テンプレ
├── compose.override.yaml.example  # 個人override用テンプレ
├── Makefile                     # よく使う操作のラッパー
├── CLAUDE.md                    # このファイル
├── .claude/settings.json        # Claude Code チーム共通設定
├── traefik/                     # Traefik 設定 (静的 + 動的)
├── traefik/certs/                       # 自己署名証明書 (gitignore対象 / make certs で生成)
├── scripts/                     # 運用ヘルパー
├── keycloak/providers/                   # SPI実装 (Java / Maven multi-module)
│   ├── pom.xml                  # 親POM
│   ├── CLAUDE.md                # SPI開発の流儀
│   ├── sample-NN-<pattern>/     # 汎用パターン (Authenticator/EventListener/etc.)
│   └── case-<client>-<name>/   # 案件固有実装
├── keycloak/themes/                      # FreeMarker/CSS/JS — Phase 2.x で本格整備
├── keycloak/realms/                      # Realm JSON (起動時にimport) — Phase 2.x で本格整備
├── docs/                        # 業務プロセスドキュメント
│   ├── case-spec-template.md    # 案件要件の入力テンプレ (顧客リポにコピーして使う)
│   ├── task-specs/              # 作業タイプ別の入力テンプレ (ジュニア記入 → 熟練者レビュー)
│   │   └── 01-admin-console-config-template.md
│   └── patterns/                # SPI/Themeパターンのカタログ (動く実例 + レシピ)
│       └── 01-email-domain-allowlist.md
├── terraform/                   # 管理コンソール設定 as Code (keycloak/keycloak provider)
│   ├── modules/                 # 案件横断の再利用モジュール (client-confidential 等)
│   └── environments/            # 案件別のサンプル/実体
│       └── example-customer/
└── e2e-tests/                   # ブラウザE2E (TypeScript + Playwright + testcontainers)
    ├── fixtures/                # KeycloakContainer fixture + test realm JSON
    └── tests/                   # *.spec.ts (Browser Flow / UI / Themes 検証)
```

## テスト3層構成

| 層 | ディレクトリ | 守備範囲 | コマンド |
| --- | --- | --- | --- |
| 単体テスト | `keycloak/providers/sample-*/src/test/` `case-*/src/test/` | ロジック分岐 (Mockito) | `make test-providers` |
| Java IT | `keycloak/providers/integration-tests/` | Direct Grant等API挙動 | `make test-integration` |
| ブラウザE2E | `e2e-tests/` | ブラウザ画面・Auth Code Flow・Themes | `make test-e2e` |

詳細・運用・デバッグ手順・既知の罠は [docs/testing.md](docs/testing.md) を参照。

### 雛形リポとしての位置づけ

このリポジトリは単なる開発環境ではなく **「全顧客案件の出発点となる雛形 + 全社共通のパターン集」** として育てる方針。

- 新案件: このリポを `git clone` → 顧客名でリネーム → `docs/specs/case-spec-template.md` を埋めて要件確定 → 必要なパターンを `keycloak/providers/` から派生実装
- 新パターン: 案件で生まれた汎用化可能な実装は、この雛形リポに逆輸入する

## 開発フロー (現時点)

| やりたいこと | 操作 |
| --- | --- |
| 初回起動 | `make init && make up` |
| Keycloakだけ再起動 | `make restart` |
| Traefik再起動 (証明書再読込) | `make restart-traefik` |
| ログ確認 | `make logs` / `make logs-traefik` / `make logs-all` |
| DBに直接入る | `make psql` |
| コンテナ内で操作 | `make shell` |
| 証明書再生成 (BASE_DOMAIN変更時) | `make certs-regen && make restart-traefik` |
| SPIビルド + Keycloak反映 | `make build-restart` |
| SPI単体テスト | `make test-providers` |
| SPIビルド成果物の削除 | `make clean-providers` |
| バージョンアップ | `.env` のバージョン変更 → `make pull && make up` |

### テスト

| やりたいこと | 操作 | Keycloak 要否 |
| --- | --- | --- |
| Spec markdown の静的検証 | `make test-spec` | 不要 |
| Terraform 構文・型チェック | `make test-tf` | 不要 |
| Keycloak 設定値の検証 | `make test-kc` | 必要 |
| OAuth フロー動作確認 | `make test-oauth` | 必要 |
| 全テストまとめて実行 | `make test` | 必要 |

`make test-kc` / `make test-oauth` は `make up && terraform apply` 後に実行する。  
`KEYCLOAK_ENV=stg make test-kc` で stg 環境の設定値を検証できる。  
batch-worker の Client Credentials テストは `KC_BATCH_WORKER_SECRET=xxx make test-oauth` で有効化。

## TLS / 証明書

- `make certs` で `traefik/certs/local-cert.pem` と `traefik/certs/local-key.pem` を生成 (`make init` / `make up` から自動呼出)。
- SANに `${BASE_DOMAIN}` と `*.${BASE_DOMAIN}` を含むので、その配下のサブドメインを全部カバー。
- 有効期限は365日。期限切れになったら `make certs-regen`。
- `traefik/certs/` 配下はgit管理外。各環境で個別に生成する。

## 環境別の注意

### Windows (WSL2)

- このリポジトリは必ず WSL2 内 (例: `~/dev/keycloak-dev`) にcloneすること。`/mnt/c/` 配下だとvolume mountが極端に遅い。
- 改行コードは `.gitattributes` でLF統一済み。Git for Windowsを使う場合は `git config --global core.autocrlf false` を推奨。
- `BASE_DOMAIN` に `localtest.me` 以外を使う場合、Windows側の `hosts` ファイルにも追記が必要 (ブラウザはWindows側のDNSを見るため)。

### Mac

- Apple Silicon: 全イメージとも arm64 対応済み。追加設定不要。

## SMTP設定 (Realm内設定)

Mailhogを使う場合、Realm > Email設定で:
- Host: `mailhog` (Docker内DNSで解決)
- Port: `1025`
- 認証なし、SSL/TLS無効

送信されたメールは https://mailhog.localtest.me/ で確認できる。

## カスタムイメージのビルド (ステージング・本番向け)

[keycloak/Dockerfile](keycloak/Dockerfile) で SPI/Themes/Realms を焼き込んだKeycloakイメージをビルドできる。Build context は `keycloak/` ディレクトリ。3段構成:

1. **spi-builder** : Maven公式イメージで `keycloak/providers/` をビルド (host にJDK/Maven不要)
2. **kc-builder** : Keycloak公式イメージに JAR + Themes + Realms を取り込み、`kc.sh build` で Quarkus augmentation
3. **runtime** : 最適化済みの `/opt/keycloak/` だけを持つ最終イメージ。デフォルトCMDは `start --optimized`

開発時 (`compose.yaml`) との使い分け:

| 用途 | 推奨 |
| --- | --- |
| ローカル開発 (SPI修正→即確認) | 既存の compose.yaml (volume mount + `start-dev`) |
| 配布・ステージング・本番 | カスタムイメージ (`make image`) を build & push |
| CIで「実イメージで動くか」検証 | カスタムイメージで `make image-run` |

### よく使うコマンド

```bash
make image          # カスタムイメージをビルド (KEYCLOAK_VERSION は .env から)
make image-run      # ビルドしたイメージを単体起動 (dev-file DB、SPI動作確認用)
make image-inspect  # イメージ内の /opt/keycloak/providers/ を確認
```

### .dockerignore の方針

dev用ファイル (compose.yaml / traefik/certs/ / traefik/ / Makefile / docs/ / CLAUDE.md等) はイメージに含めない。`keycloak/providers/**/target/` や `keycloak/providers/*.jar` も除外して、必ずクリーンな状態からビルドする (host側で `make build-providers` した結果はイメージに混入しない)。

### 本番向け設定の注入

ランタイム設定 (DB接続情報、`KC_HOSTNAME`、admin初期パスワード等) は **イメージに焼き込まず、起動時の環境変数で注入** する。例:

```bash
docker run --rm -p 8080:8080 \
  -e KC_DB_URL=jdbc:postgresql://db:5432/keycloak \
  -e KC_DB_USERNAME=keycloak \
  -e KC_DB_PASSWORD=secret \
  -e KC_HOSTNAME=https://auth.example.com \
  -e KC_PROXY_HEADERS=xforwarded \
  -e KC_HTTP_ENABLED=true \
  -e KC_BOOTSTRAP_ADMIN_USERNAME=admin \
  -e KC_BOOTSTRAP_ADMIN_PASSWORD=$(openssl rand -base64 32) \
  keycloak-custom:local
```

`KC_DB=postgres` だけは build 時に確定するため Dockerfile 内に書いている (`start --optimized` 時はDB種別の変更不可)。別DBに切り替える場合は Dockerfile を編集して再ビルド。

## 個人カスタマイズ

`.env` / `compose.override.yaml` / `traefik/certs/` はgit管理外。

- 個人の環境変数オーバーライド → `.env`
- 個人のcompose追加設定 (デバッグポート、追加マウント等) → `compose.override.yaml` (`.example`をコピーして使う)
- 個人のClaude Code設定 → `.claude/settings.local.json`

## Phaseロードマップ

- [x] **Phase 1** : 最小で動くdocker-compose基盤
- [x] **Phase 1.5** : Traefik + 自己署名証明書でHTTPSアクセス
- [x] **Phase 2.0** : パターン1個目 (Authenticator) + 要件テンプレ整備
- [ ] **Phase 2.x** : パターンを順次拡充 (Authenticator追加 / EventListener / Theme / Realm JSON)
- [ ] **Phase 3** : 自動テスト基盤 (Keycloak Testcontainers) + デプロイスクリプト
- [ ] **Phase 4** : 雛形リポからのclone手順 + 案件レビュー観点リスト + 実案件適用
- [x] **Phase G** : テスト自動化 (L1 spec検証・L2 terraform validate・L3 Admin API検証・L4 OAuthフロー確認)

## トラブルシューティング

- **Keycloakが起動しない** → `make logs` でログ確認。多くはDB接続失敗 (`postgres` の起動待ち) なので少し待ってリトライ。
- **HTTPSアクセスで `ERR_CONNECTION_REFUSED`** → Traefikが起動しているか `make ps` で確認。ポート443が他プロセスに使われていないか (Mac: `sudo lsof -i:443`、Win: `netstat -ano | findstr :443`)。
- **証明書エラーで進めない** → 自己署名なので警告は正常。回避するか、`traefik/certs/local-cert.pem` を信頼ストアに追加。
- **Keycloakで `Invalid parameter: redirect_uri`** → `KC_HOSTNAME` と実際のアクセスURLが一致しているか確認。HTTPS_PORTを変えたら `KC_HOSTNAME` にも `:ポート番号` を含める必要あり。
- **ポート競合 (80/443)** → `.env` で `HTTP_PORT=8080 HTTPS_PORT=8443` 等に変更し、`KC_HOSTNAME` も合わせて変更。
- **DBスキーマ破損** → `make clean` でボリュームごと削除して再起動。
