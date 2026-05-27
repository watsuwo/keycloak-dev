# Keycloak開発環境 操作ターゲット集
# 使い方: make help

SHELL := /bin/bash
DC := docker compose

CERT_DIR  := traefik/certs
CERT_FILE := $(CERT_DIR)/local-cert.pem
KEY_FILE  := $(CERT_DIR)/local-key.pem

.DEFAULT_GOAL := help

.PHONY: help
help: ## 使えるターゲット一覧
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9_-]+:.*?## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# --- セットアップ ---

.env:
	@cp .env.example .env && echo ".env を作成しました"

$(CERT_FILE):
	@bash scripts/generate-certs.sh

.PHONY: init
init: .env certs ## 初回セットアップ (.env生成 + 証明書生成)
	@echo "セットアップ完了。'make up' で起動してください。"

.PHONY: certs
certs: $(CERT_FILE) ## 自己署名証明書を生成 (既存ならスキップ)

.PHONY: certs-regen
certs-regen: ## 証明書を強制再生成 (BASE_DOMAIN変更時)
	@rm -f $(CERT_FILE) $(KEY_FILE)
	@bash scripts/generate-certs.sh
	@echo "Traefik再起動で新証明書が反映されます: make restart-traefik"

# --- 起動・停止 ---

.PHONY: build
build: ## カスタム Keycloak イメージをビルド (providers/themes を組み込み)
	$(DC) build keycloak

.PHONY: up
up: .env certs ## 全サービスを起動 (バックグラウンド)
	$(DC) up -d

.PHONY: down
down: ## 全サービスを停止・削除
	$(DC) down

.PHONY: restart
restart: ## keycloakのみ再起動 (SPI/Theme再読み込み)
	$(DC) restart keycloak

.PHONY: restart-traefik
restart-traefik: ## traefikのみ再起動 (証明書再読み込み)
	$(DC) restart traefik

.PHONY: restart-mock
restart-mock: ## mock-apiのみ再起動 (mappings再読み込み)
	$(DC) restart mock-api

# --- 観察 ---

.PHONY: logs
logs: ## keycloakのログをfollow
	$(DC) logs -f keycloak

.PHONY: logs-traefik
logs-traefik: ## traefikのログをfollow
	$(DC) logs -f traefik

.PHONY: logs-all
logs-all: ## 全サービスのログをfollow
	$(DC) logs -f

.PHONY: logs-mock
logs-mock: ## mock-apiのログをfollow
	$(DC) logs -f mock-api

.PHONY: ps
ps: ## サービス状態を表示
	$(DC) ps

# --- コンテナ内操作 ---

.PHONY: shell
shell: ## keycloakコンテナにbashで入る
	$(DC) exec keycloak /bin/bash

.PHONY: psql
psql: ## PostgreSQLにpsqlで入る
	$(DC) exec postgres psql -U $${POSTGRES_USER:-keycloak} -d $${POSTGRES_DB:-keycloak}

# --- SPI (Java) ビルド ---

.PHONY: build-providers
build-providers: ## SPI (keycloak/providers配下) をビルドしてKeycloakから読める位置にコピー
	cd keycloak/providers && mvn -q package
	@find keycloak/providers -mindepth 2 -maxdepth 4 -name "*.jar" -path "*/target/*" \
	  ! -name "*-sources.jar" ! -name "*-javadoc.jar" \
	  -exec cp -v {} keycloak/providers/ \;
	@echo ""
	@echo "次の手順:"
	@echo "  make restart で Keycloak を再起動 (SPIが読み込まれる)"

.PHONY: build-restart
build-restart: build-providers ## SPIビルド + Keycloak再起動 (反映確認まで)
	$(DC) restart keycloak

.PHONY: clean-providers
clean-providers: ## SPIビルド成果物を削除
	cd keycloak/providers && mvn -q clean
	@find keycloak/providers -maxdepth 1 -name "*.jar" -delete

.PHONY: test-providers
test-providers: ## SPI の単体テストを実行 (Mockito、Docker不要・高速)
	cd keycloak/providers && mvn -B -q test

.PHONY: test-integration
test-integration: ## SPI の統合テストを実行 (Testcontainers + 実Keycloak、Docker必要)
	cd keycloak/providers && mvn -B -pl integration-tests -am verify

.PHONY: test-all
test-all: ## 単体 + 統合テストを全部実行 (E2Eは含まない、make test-e2e別途)
	cd keycloak/providers && mvn -B verify

# --- Spec 検証 (SDD Phase B) ---

.PHONY: spec-validate
spec-validate: ## docs/ 配下の spec frontmatter を検証 (spec_id一意性・impl/test存在等)
	python3 scripts/validate-specs.py

.PHONY: spec-validate-quiet
spec-validate-quiet: ## spec 検証 (エラー/警告時のみ出力、CI用)
	python3 scripts/validate-specs.py --quiet

# --- E2E (Browser, Playwright) ---

.PHONY: e2e-install
e2e-install: ## E2Eテストの初回セットアップ (npm install + Chromium取得)
	cd e2e-tests && npm install && npx playwright install chromium

.PHONY: test-e2e
test-e2e: build-providers ## ブラウザE2Eテスト (Testcontainers + Playwright、要 e2e-install済み)
	cd e2e-tests && npx playwright test

.PHONY: test-e2e-ui
test-e2e-ui: ## Playwright UI モードで起動 (デバッグ用)
	cd e2e-tests && npx playwright test --ui

.PHONY: test-e2e-headed
test-e2e-headed: ## ブラウザ画面を見ながらE2Eテスト実行 (デバッグ用)
	cd e2e-tests && HEADED=true npx playwright test --headed

# --- カスタムイメージ ---

IMAGE_NAME ?= keycloak-custom
IMAGE_TAG  ?= local

.PHONY: image
image: ## カスタムKeycloakイメージをビルド (keycloak/Dockerfile)
	docker build \
	  --build-arg KEYCLOAK_VERSION=$$(grep -E '^KEYCLOAK_VERSION=' .env 2>/dev/null | cut -d= -f2- || echo 26.0) \
	  -t $(IMAGE_NAME):$(IMAGE_TAG) \
	  keycloak/
	@echo ""
	@echo "ビルド完了: $(IMAGE_NAME):$(IMAGE_TAG)"
	@echo "起動確認: make image-run"

.PHONY: image-run
image-run: ## ビルド済みカスタムイメージを単体起動 (動作確認用、dev-file DB)
	docker run --rm -p 8080:8080 \
	  -e KC_BOOTSTRAP_ADMIN_USERNAME=admin \
	  -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin \
	  -e KC_DB=dev-file \
	  -e KC_HOSTNAME_STRICT=false \
	  -e KC_HTTP_ENABLED=true \
	  $(IMAGE_NAME):$(IMAGE_TAG) start-dev

.PHONY: image-inspect
image-inspect: ## カスタムイメージの providers/ 内容を確認
	docker run --rm --entrypoint ls $(IMAGE_NAME):$(IMAGE_TAG) -la /opt/keycloak/providers/

# --- Terraform (管理コンソール設定 as Code) ---

TF_DIR ?= terraform/environments/example-customer

.PHONY: tf-init
tf-init: ## Terraform初期化 (provider取得)
	cd $(TF_DIR) && terraform init

.PHONY: tf-plan
tf-plan: ## Terraform planで差分確認
	cd $(TF_DIR) && terraform plan

.PHONY: tf-apply
tf-apply: ## Terraformで設定を適用 (要 dev Keycloak起動中)
	cd $(TF_DIR) && terraform apply

.PHONY: tf-destroy
tf-destroy: ## Terraform で設定を削除
	cd $(TF_DIR) && terraform destroy

.PHONY: tf-test
tf-test: ## サンプル案件の apply → 検証 → destroy を一気に実行
	bash scripts/test-terraform.sh

# --- モックAPI ---

MOCK_API_PORT ?= 8082

.PHONY: mock-reset
mock-reset: ## mock-api のスタブをファイルベース定義に戻す (実行時追加分をクリア)
	curl -s -X POST http://localhost:$(MOCK_API_PORT)/__admin/mappings/reset | jq .

.PHONY: mock-list
mock-list: ## 現在有効なスタブ一覧を表示
	curl -s http://localhost:$(MOCK_API_PORT)/__admin/mappings | jq '.mappings[] | {id, name: .name, method: .request.method, url: (.request.url // .request.urlPattern // .request.urlPathPattern)}'

# --- メンテナンス ---

.PHONY: clean
clean: ## 全サービス停止 + ボリューム削除 (DBデータも消える)
	$(DC) down -v

.PHONY: pull
pull: ## イメージを最新に更新
	$(DC) pull

# --- テスト (Admin API / OAuth / Spec / Terraform) ---

.PHONY: test
test: test-spec test-tf test-kc test-oauth ## 全テストを実行 (spec → tf → kc → oauth)

.PHONY: test-spec
test-spec: ## Spec markdown の静的検証 (frontmatter・YAMLブロック確認)
	@python3 scripts/test-spec.py

.PHONY: test-tf
test-tf: ## Terraform 構文チェック (全 environment、Keycloak 不要)
	@command -v terraform >/dev/null 2>&1 || { echo "terraform CLI が必要: brew install terraform / apt install terraform"; exit 1; }
	@bash scripts/test-tf-validate.sh

.PHONY: test-kc
test-kc: ## Keycloak設定値を自動検証 — spec と Admin API を突合 (terraform apply後に実行)
	@python3 scripts/test-realm-config.py

.PHONY: test-oauth
test-oauth: ## OAuth フロー動作確認 (OIDC discovery・ROPC拒否・Client Credentials)
	@python3 scripts/test-oauth-flows.py

# --- Realm 入出力 (Phase 3で実装予定) ---

.PHONY: export-realm
export-realm: ## 稼働中のRealmをJSONエクスポート  [Phase 3で実装]
	@echo "TODO: kc.sh export 実行ラッパー"

.PHONY: import-realm
import-realm: ## realms/配下のJSONを再インポート  [Phase 3で実装]
	@echo "TODO: kc.sh import 実行ラッパー"
