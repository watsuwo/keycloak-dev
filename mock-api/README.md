# モックAPIサーバ (WireMock)

外部APIのモックを定義するディレクトリ。[WireMock](https://wiremock.org/) を使用。

## アクセスURL

| URL | 用途 |
| --- | --- |
| `https://mock-api.localtest.me/<path>` | モックエンドポイント (Traefik経由・HTTPS) |
| `http://localhost:8082/<path>` | モックエンドポイント (直接・HTTP) |
| `http://localhost:8082/__admin/` | 管理API (スタブ追加・リセット等) |

## ディレクトリ構成

```
mock-api/
├── mappings/              # スタブ定義 (1ファイル = 1スタブ)
│   ├── example-get.json
│   ├── example-post.json
│   ├── example-template.json
│   └── example-file-body.json
└── __files/               # bodyFileName で参照する静的レスポンスボディ
    └── catalog.json
```

## スタブの追加方法

### A. ファイルで定義 (推奨・永続)

`mappings/` に `.json` ファイルを追加し、コンテナを再起動:

```bash
make restart-mock
```

### B. 管理APIで追加 (実行時・一時)

```bash
curl -s -X POST http://localhost:8082/__admin/mappings \
  -H "Content-Type: application/json" \
  -d '{
    "request": { "method": "GET", "url": "/api/token/verify" },
    "response": { "status": 200, "jsonBody": { "valid": true } }
  }'
```

コンテナ再起動 or `make mock-reset` でファイル定義に戻る。

## スタブ定義リファレンス

### 基本形

```json
{
  "name": "スタブの説明 (任意)",
  "request": {
    "method": "GET",
    "url": "/api/path"
  },
  "response": {
    "status": 200,
    "headers": { "Content-Type": "application/json" },
    "jsonBody": { "key": "value" }
  }
}
```

### リクエストマッチング

```json
"request": {
  "method": "POST",
  "urlPattern": "/api/users/[0-9]+",      // 正規表現
  "urlPathPattern": "/api/users/([^/]+)", // パスのみ正規表現
  "headers": {
    "Authorization": { "matches": "Bearer .+" }
  },
  "bodyPatterns": [
    { "matchesJsonPath": "$.username" },
    { "equalToJson": { "role": "admin" } }
  ]
}
```

### レスポンステンプレート

`--global-response-templating` 有効済みのため、全スタブで使用可能:

```json
"response": {
  "body": "{ \"id\": \"{{request.pathSegments.[2]}}\", \"query\": \"{{request.query.q}}\" }"
}
```

主なテンプレート変数:

| 変数 | 内容 |
| --- | --- |
| `{{request.pathSegments.[N]}}` | パスセグメント (0始まり) |
| `{{request.query.KEY}}` | クエリパラメータ |
| `{{request.headers.KEY}}` | リクエストヘッダ |
| `{{jsonPath request.body '$.field'}}` | リクエストボディのJSONフィールド |
| `{{randomValue length=10 type='ALPHANUMERIC'}}` | ランダム文字列 |

### ファイルからレスポンス

```json
"response": {
  "bodyFileName": "my-response.json"
}
```

`__files/my-response.json` が返される。

### シナリオ (ステートフル)

同じエンドポイントで呼び出し順に応じてレスポンスを変えたい場合:

```json
[
  {
    "scenarioName": "Token Expiry",
    "requiredScenarioState": "Started",
    "newScenarioState": "Expired",
    "request": { "method": "GET", "url": "/api/token" },
    "response": { "status": 200, "jsonBody": { "valid": true } }
  },
  {
    "scenarioName": "Token Expiry",
    "requiredScenarioState": "Expired",
    "request": { "method": "GET", "url": "/api/token" },
    "response": { "status": 401, "jsonBody": { "error": "token_expired" } }
  }
]
```

## よく使う make コマンド

```bash
make restart-mock   # mappings再読み込み
make mock-reset     # 実行時追加スタブをクリア (ファイル定義に戻す)
make mock-list      # 有効スタブ一覧
make logs-mock      # ログ確認
```

## Keycloak SPI からの利用

コンテナ内DNS名は `mock-api`。SPI の設定値 (外部APIのURLなど) に以下を指定:

```
http://mock-api:8080/api/your-endpoint
```

`.env` に環境変数として定義し、Keycloak の SPI 設定へ渡すのを推奨:

```env
EXTERNAL_USER_API_URL=http://mock-api:8080/api/users
```
