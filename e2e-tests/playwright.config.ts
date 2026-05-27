import { defineConfig } from '@playwright/test';

/**
 * Playwright設定
 *
 * - 並列度1: Testcontainersコンテナ起動コストが高いため、テストワーカー1つで運用
 * - timeout拡張: コンテナ起動+認証フロー実行で時間がかかる
 * - 失敗時はscreenshot/video/traceを残す (ローカル/CIどちらでも有効)
 */
export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  workers: 1,

  timeout: 90_000,
  expect: { timeout: 15_000 },

  reporter: process.env.CI ? [['github'], ['list']] : 'list',

  use: {
    headless: process.env.HEADED !== 'true',
    viewport: { width: 1280, height: 720 },
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
    ignoreHTTPSErrors: true,
  },

  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' },
    },
  ],
});
