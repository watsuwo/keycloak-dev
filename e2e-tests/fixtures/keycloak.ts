import { test as base } from '@playwright/test';
import { GenericContainer, StartedTestContainer, Wait } from 'testcontainers';
import { globSync } from 'glob';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';

// Docker Desktop on Mac ではsocketパスが ~/.docker/run/docker.sock になる。
// testcontainers が自動検出に失敗するケースに備えて明示的にセット。
if (!process.env.DOCKER_HOST) {
  const candidates = [
    path.join(os.homedir(), '.docker/run/docker.sock'),
    '/var/run/docker.sock',
  ];
  for (const candidate of candidates) {
    try {
      if (fs.existsSync(candidate)) {
        process.env.DOCKER_HOST = `unix://${candidate}`;
        break;
      }
    } catch {
      // ignore
    }
  }
}

/**
 * Keycloak fixture for Playwright tests.
 *
 * Worker-scope: 同一workerの全テストで1つのKeycloakコンテナを共有 (起動コスト圧縮)。
 * Realm/SPI/設定は fixture作成時に固定されるため、テスト間で realm 設定を変えたい場合は
 * 別の spec file に分けて別 worker で動かす運用にする。
 */

export type KeycloakFixtures = {
  kcUrl: string;
};

type WorkerFixtures = {
  _container: StartedTestContainer;
};

const KEYCLOAK_IMAGE = process.env.KC_IMAGE ?? 'quay.io/keycloak/keycloak:26.0';
const KEYCLOAK_INTERNAL_PORT = 8080;
const TEST_REALM = 'test-browser';

const repoRoot = path.resolve(__dirname, '../..');
const providersDir = path.join(repoRoot, 'keycloak/providers');
const realmJsonPath = path.resolve(__dirname, 'test-realm-browser.json');

export const test = base.extend<KeycloakFixtures, WorkerFixtures>({
  _container: [async ({}, use) => {
    const spiJars = findSpiJars();
    if (spiJars.length === 0) {
      throw new Error(
        `SPI JAR が見つかりません。先に 'make build-providers' を実行してください。\n探索パス: ${providersDir}/*/target/*.jar`
      );
    }
    // glob は providersDir 内の <module>/target/*.jar を探すパターンを変えずに使う
    if (!fs.existsSync(realmJsonPath)) {
      throw new Error(`test realm JSON が見つかりません: ${realmJsonPath}`);
    }

    const bindMounts = [
      {
        source: realmJsonPath,
        target: '/opt/keycloak/data/import/test-realm.json',
        mode: 'ro' as const,
      },
      ...spiJars.map((jar) => ({
        source: jar,
        target: `/opt/keycloak/providers/${path.basename(jar)}`,
        mode: 'ro' as const,
      })),
    ];

    console.log(`[keycloak fixture] Starting Keycloak container with:`);
    console.log(`  Image: ${KEYCLOAK_IMAGE}`);
    console.log(`  SPI JARs: ${spiJars.length}`);
    spiJars.forEach((j) => console.log(`    - ${path.basename(j)}`));
    console.log(`  Realm import: ${path.basename(realmJsonPath)}`);

    const container = await new GenericContainer(KEYCLOAK_IMAGE)
      .withCommand(['start-dev', '--import-realm'])
      .withEnvironment({
        KC_BOOTSTRAP_ADMIN_USERNAME: 'admin',
        KC_BOOTSTRAP_ADMIN_PASSWORD: 'admin',
        KC_HTTP_ENABLED: 'true',
        KC_HOSTNAME_STRICT: 'false',
        KC_LOG_LEVEL: 'INFO',
      })
      .withBindMounts(bindMounts)
      .withExposedPorts(KEYCLOAK_INTERNAL_PORT)
      .withWaitStrategy(
        Wait.forHttp(
          `/realms/${TEST_REALM}/.well-known/openid-configuration`,
          KEYCLOAK_INTERNAL_PORT
        )
          .forStatusCode(200)
          .withStartupTimeout(180_000)
      )
      .start();

    const url = `http://${container.getHost()}:${container.getMappedPort(KEYCLOAK_INTERNAL_PORT)}`;
    console.log(`[keycloak fixture] Keycloak ready at ${url}`);

    await use(container);

    console.log('[keycloak fixture] Stopping Keycloak container...');
    await container.stop();
  }, { scope: 'worker', timeout: 240_000 }],

  kcUrl: async ({ _container }, use) => {
    const url = `http://${_container.getHost()}:${_container.getMappedPort(KEYCLOAK_INTERNAL_PORT)}`;
    await use(url);
  },
});

export { expect } from '@playwright/test';

/**
 * providers/<module>/target/*.jar を再帰検索 (テストモジュールやsources/javadocは除外)
 */
function findSpiJars(): string[] {
  const matches = globSync('*/target/*.jar', {
    cwd: providersDir,
    ignore: [
      'integration-tests/**',
      '**/*-sources.jar',
      '**/*-javadoc.jar',
      '**/original-*.jar',
    ],
  });
  return matches.map((m) => path.join(providersDir, m));
}

export const TEST_BROWSER_REALM = TEST_REALM;
