# Keycloak開発環境 操作ターゲット集
# 使い方: make help

SHELL := /bin/bash
DC := docker compose

CERT_DIR  := certs
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

# --- メンテナンス ---

.PHONY: clean
clean: ## 全サービス停止 + ボリューム削除 (DBデータも消える)
	$(DC) down -v

.PHONY: pull
pull: ## イメージを最新に更新
	$(DC) pull

# --- テスト ---

.PHONY: test
test: test-spec test-tf test-kc test-oauth ## 全テストを実行 (spec → tf → kc → oauth)

.PHONY: test-spec
test-spec: ## Spec markdown の静的検証 (frontmatter・YAMLブロック確認)
	@python3 scripts/test-spec.py

.PHONY: test-tf
test-tf: ## Terraform 構文・型チェック (全 environment)
	@command -v terraform >/dev/null 2>&1 || { echo "terraform CLI が必要: brew install terraform / apt install terraform"; exit 1; }
	@bash scripts/test-terraform.sh

.PHONY: test-kc
test-kc: ## Keycloak設定値を自動検証 — spec と Admin API を突合 (terraform apply後に実行)
	@python3 scripts/test-realm-config.py

.PHONY: test-oauth
test-oauth: ## OAuth フロー動作確認 (OIDC discovery・ROPC拒否・Client Credentials)
	@python3 scripts/test-oauth-flows.py

# --- 以下、Phase 3 で実装予定 ---

.PHONY: build-providers
build-providers: ## SPI (providers配下) をビルド  [Phase 3で実装]
	@echo "TODO: providers/ のMavenビルド + restart"

.PHONY: export-realm
export-realm: ## 稼働中のRealmをJSONエクスポート  [Phase 3で実装]
	@echo "TODO: kc.sh export 実行ラッパー"

.PHONY: import-realm
import-realm: ## realms/配下のJSONを再インポート  [Phase 3で実装]
	@echo "TODO: kc.sh import 実行ラッパー"
