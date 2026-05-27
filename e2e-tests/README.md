# e2e-tests

Browser E2E tests for Keycloak SPI/Theme using Playwright + Testcontainers.

詳細は [CLAUDE.md](CLAUDE.md) 参照。

## クイックスタート

```bash
# リポルートから
make e2e-install       # 初回のみ (npm + chromium 取得)
make test-e2e          # SPIビルド → Playwright実行

# UI モードでデバッグ
cd e2e-tests && npm run test:ui

# 失敗時のtrace閲覧
cd e2e-tests && npx playwright show-trace test-results/.../trace.zip
```

## 前提

- Node.js 18+
- Docker daemon が起動中 (testcontainers用)
- リポルートで `make build-providers` が動く状態 (Java 17+ / Maven)
