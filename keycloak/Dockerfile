# syntax=docker/dockerfile:1.7
#
# カスタマイズ済みKeycloakイメージ
# 構成: SPI(Java)ビルド → Keycloak最適化build (kc.sh build) → ランタイム
#
# Build context は **このファイルがある keycloak/ ディレクトリ**。
#   make image                       # 推奨
#   docker build --build-arg KEYCLOAK_VERSION=26.0 -t keycloak-custom:local keycloak/
#
# 実行方法:
#   make image-run                          # スタンドアロン (dev-file DB) で起動確認
#   docker run --rm -p 8080:8080 \
#     -e KC_BOOTSTRAP_ADMIN_USERNAME=admin \
#     -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin \
#     -e KC_DB=dev-file \
#     -e KC_HOSTNAME_STRICT=false \
#     keycloak-custom:local start-dev

ARG KEYCLOAK_VERSION=26.0
ARG MAVEN_IMAGE=maven:3.9-eclipse-temurin-17

# ====================================================================
# Stage 1: SPI (Java) のビルド
# ====================================================================
FROM ${MAVEN_IMAGE} AS spi-builder

WORKDIR /workspace
COPY providers/ ./providers/

# テストはCI側で実行する想定 (イメージビルドは速度優先で skip)
RUN cd providers \
 && mvn -B -q package -DskipTests \
 && mkdir -p /spi-output \
 && find /workspace/providers -mindepth 2 -maxdepth 4 -name "*.jar" -path "*/target/*" \
      ! -name "*-sources.jar" ! -name "*-javadoc.jar" \
      -exec cp -v {} /spi-output/ \; \
 && ls -la /spi-output/

# ====================================================================
# Stage 2: Keycloak の最適化ビルド (Quarkus augmentation)
# ====================================================================
FROM quay.io/keycloak/keycloak:${KEYCLOAK_VERSION} AS kc-builder

# プロビルドに含めたい構成 — ランタイム時の上書きより優先される静的設定
# (DB種別だけは build 時に確定させる必要がある)
ENV KC_DB=postgres
ENV KC_HEALTH_ENABLED=true
ENV KC_METRICS_ENABLED=true

# SPI JAR を取り込み
COPY --from=spi-builder /spi-output/ /opt/keycloak/providers/

# Themes を取り込み (空の場合は何も起きない)
COPY themes/ /opt/keycloak/themes/

# Realms (--import-realm 用) — README.md 等が混ざらないよう .json のみ抽出
# /tmp/realms-raw は中間stage 内なので最終イメージには含まれない (rmで掃除しなくてもサイズに影響なし)
COPY realms/ /tmp/realms-raw/
RUN mkdir -p /opt/keycloak/data/import \
 && find /tmp/realms-raw -maxdepth 1 -name "*.json" -exec cp -v {} /opt/keycloak/data/import/ \;

# Quarkus augmentation: providers/themes 込みで Keycloak を最適化
RUN /opt/keycloak/bin/kc.sh build

# ====================================================================
# Stage 3: ランタイム
# ====================================================================
FROM quay.io/keycloak/keycloak:${KEYCLOAK_VERSION}

LABEL org.opencontainers.image.title="keycloak-custom" \
      org.opencontainers.image.description="Customized Keycloak with SPI/Themes/Realms baked in" \
      org.opencontainers.image.source="https://github.com/<your-org>/keycloak-dev"

COPY --from=kc-builder /opt/keycloak/ /opt/keycloak/

# 既定は本番モード (最適化ビルド済み)
# 開発確認したい場合は CMD を "start-dev" で上書きする
ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
CMD ["start", "--optimized"]
