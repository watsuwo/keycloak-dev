import { test, expect, TEST_BROWSER_REALM } from '../fixtures/keycloak';

/**
 * Email Domain Allowlist Authenticator のブラウザフロー (Authorization Code Flow) E2E。
 *
 * Direct Grant (Java IT) ではカバーできない:
 *  - 実ログインフォームの操作
 *  - context.form().createErrorPage() で生成される HTML エラーページの表示
 *  - リダイレクト連鎖 (Authorization Code が code= 付きで redirect_uri へ返る)
 * を検証する。
 */

const CLIENT_ID = 'test-browser-client';
const REDIRECT_URI = 'http://localhost:3000/callback';

/**
 * Authorization Code Flow の auth エンドポイントURLを組み立てる。
 */
function buildAuthUrl(kcUrl: string): string {
  const params = new URLSearchParams({
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    response_type: 'code',
    scope: 'openid',
    state: 'e2e-state-' + Date.now(),
  });
  return `${kcUrl}/realms/${TEST_BROWSER_REALM}/protocol/openid-connect/auth?${params}`;
}

test.describe('Email Domain Allowlist — Browser Flow', () => {

  test('許可ドメインのユーザー (alice@example.com) はログインに成功し redirect_uri へ code 付きで戻る', async ({ page, kcUrl }) => {
    await page.goto(buildAuthUrl(kcUrl));

    // Keycloakのログイン画面が表示される
    await expect(page.locator('#username')).toBeVisible();
    await expect(page.locator('#password')).toBeVisible();

    // alice でログイン
    await page.locator('#username').fill('alice');
    await page.locator('#password').fill('password');

    // クリックと同時に redirect_uri へのリクエスト発火を捕捉。
    // localhost:3000 に実サーバが無いのでnavigation自体はchrome-errorに着地するが、
    // リクエスト発生時点では URL に Authorization Code が乗っている。
    const [request] = await Promise.all([
      page.waitForRequest(
        (req) => req.url().startsWith(REDIRECT_URI),
        { timeout: 15_000 }
      ),
      page.locator('#kc-login').click(),
    ]);

    expect(request.url()).toContain(REDIRECT_URI);
    expect(request.url()).toMatch(/code=[^&]+/);
    expect(request.url()).toMatch(/state=e2e-state-/);
  });

  test('拒否ドメインのユーザー (eve@bad.com) はカスタムエラーページに到達する', async ({ page, kcUrl }) => {
    await page.goto(buildAuthUrl(kcUrl));

    await page.locator('#username').fill('eve');
    await page.locator('#password').fill('password');
    await page.locator('#kc-login').click();

    // ブラウザフローでは context.form().createErrorPage() のHTMLが返る
    // Authenticatorに渡したメッセージ "このドメインからのログインは許可されていません" がページ内に出現
    await expect(page.locator('body')).toContainText(
      'このドメインからのログインは許可されていません',
      { timeout: 15_000 }
    );

    // redirect_uri (localhost:3000) には行っていないこと
    expect(page.url()).not.toContain(REDIRECT_URI);
  });

  test('間違ったパスワードでは Keycloak 標準のエラーが表示される (Authenticatorに到達しない)', async ({ page, kcUrl }) => {
    await page.goto(buildAuthUrl(kcUrl));

    await page.locator('#username').fill('alice');
    await page.locator('#password').fill('WRONG_PASSWORD');
    await page.locator('#kc-login').click();

    // ログイン画面に戻り、エラーメッセージが表示される
    await expect(page.locator('#input-error, .kc-feedback-text, .alert-error'))
      .toBeVisible({ timeout: 10_000 });
  });
});
