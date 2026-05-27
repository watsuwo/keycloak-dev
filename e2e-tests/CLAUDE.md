# e2e-tests/ — ブラウザE2Eテスト (TypeScript + Playwright + Testcontainers)

実Keycloakコンテナをブラウザで操作して認証フロー全体をE2E検証する。
Java IT (`keycloak/providers/integration-tests/`) はAPIレベル (Direct Grant等) で、こちらは **UI/ブラウザ操作** を検証する。

## 2層テスト戦略

| 層 | 場所 | 守備範囲 | 言語 |
| --- | --- | --- | --- |
| 単体テスト | `keycloak/providers/0N-*/src/test/` | ロジックの分岐網羅 | Java + Mockito |
| Java IT | `keycloak/providers/integration-tests/src/test/` | Direct Grant等 APIレベルの挙動 | Java + Testcontainers |
| **ブラウザE2E (このディレクトリ)** | `e2e-tests/tests/` | **Browser Flow、ログイン画面、エラーページ、Themes、Auth Code Flow、IdP redirect** | TypeScript + Playwright + testcontainers |

各層は **検証対象が異なる** ため互いに代替不能。すべて維持する。

## ディレクトリ構造

```
e2e-tests/
├── package.json
├── tsconfig.json
├── playwright.config.ts                テスト設定 (workers/timeout/reporter)
├── CLAUDE.md                           このファイル
├── README.md                           ユーザー向けクイックスタート
├── fixtures/
│   ├── keycloak.ts                     KeycloakContainer fixture (worker-scope)
│   └── test-realm-browser.json         テスト用 realm (alice/eve + Browser Flow + 我々のSPI)
└── tests/
    └── email-domain-allowlist-browser.spec.ts   パターン1のブラウザE2E (3ケース)
```

## 実行

```bash
# 初回のみ: 依存とブラウザバイナリを取得
make e2e-install

# 全テスト実行 (SPI再ビルド → Playwright)
make test-e2e

# UI モード (Playwright Inspector でデバッグ)
cd e2e-tests && npm run test:ui

# ヘッドレスを切る (ブラウザ画面が見える)
cd e2e-tests && npm run test:headed
```

## 仕組み

1. `make build-providers` で `keycloak/providers/*/target/*.jar` を生成 (前提条件)
2. Playwright が `keycloak.ts` fixture を起動 — Worker開始時に1回
3. testcontainers が Keycloak コンテナを起動:
   - JAR を bind mount で `/opt/keycloak/providers/` に投入
   - `test-realm-browser.json` を `/opt/keycloak/data/import/` に投入
   - `start-dev --import-realm` で起動 (SPI読み込み + realm import)
4. `Wait.forHttp` で realm の well-known が 200 を返すまで待機
5. テストごとに Playwright が ChromiumのコンテキストとPage を新規発行
6. Page が Keycloak の認可エンドポイントに navigate して認証フローを進める
7. Worker終了時にコンテナ停止

## fixture の scope

- **worker scope**: 同一の `*.spec.ts` 群を実行する間、Keycloakコンテナは共有される
- **テスト間の独立性**: テストごとに Playwright がブラウザ状態をリセット (cookie/storage)
- **realm を変えたい場合**: 別の spec file に分けて別 fixture を作る (将来のパターン用)

## テスト realm を新規パターン用に追加する手順

1. `fixtures/test-realm-<pattern>.json` を作る
   - SPIを含む auth flow を定義
   - テスト用ユーザーを定義
   - **必ず `firstName`/`lastName`/`emailVerified: true`/`requiredActions: []` を user に設定**
     (User Profile必須属性問題でDirect Grantが詰む既知の罠)
2. fixture を派生 (`fixtures/keycloak-<pattern>.ts`)
   - realm path を別ファイルに
3. `tests/<pattern>-browser.spec.ts` を書く

## 落とし穴とデバッグ

- **Docker daemon必須**: testcontainers が Docker Engine 経由でコンテナ起動
- **SPI JAR が無い**: fixture が `make build-providers` をしろ、と例外を投げる
- **realm import失敗**: コンテナログを見る (`docker logs <container_id>`)。多くは realm.json のSPI名typo
- **テストがhangする**: Playwright trace を確認 (`npm run trace test-results/...`)
- **存在しない redirect_uri (例: `http://localhost:3000/callback`) への遷移**:
  - `page.waitForURL(/code=/)` は `chrome-error://chromewebdata/` に着地してTimeoutする (`waitUntil: 'commit'` でも回避不可、page.route の interceptもtop-level navigationでは効きにくい)
  - **正解**: `page.waitForRequest(req => req.url().startsWith(REDIRECT_URI))` でリクエスト発火時点を捕捉。URLにAuthorization Codeが乗っているので、レスポンスが返らなくてもOK
  - パターン:
    ```typescript
    const [request] = await Promise.all([
      page.waitForRequest(req => req.url().startsWith(REDIRECT_URI), { timeout: 15_000 }),
      page.locator('#kc-login').click(),
    ]);
    expect(request.url()).toMatch(/code=[^&]+/);
    ```

## CI連携 (将来)

```yaml
# GitHub Actions 例
- run: make build-providers
- run: make e2e-install
- run: make test-e2e
- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: playwright-report
    path: e2e-tests/playwright-report
```

## 関連

- Java IT (Direct Grant): [keycloak/providers/integration-tests/CLAUDE.md](../keycloak/providers/integration-tests/CLAUDE.md)
- Authenticator実装: [keycloak/providers/sample-01-email-domain-allowlist/CLAUDE.md](../keycloak/providers/sample-01-email-domain-allowlist/CLAUDE.md)
- パターンレシピ: [docs/specs/patterns/01-email-domain-allowlist.md](../docs/specs/patterns/01-email-domain-allowlist.md)
