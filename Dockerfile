# ────────────────────────────────────────────────────────────────────────────
# Stage 1 – builder
# カスタム SPI / テーマを組み込み、Quarkus 最適化ビルド (kc.sh build) を実行する。
# ────────────────────────────────────────────────────────────────────────────
ARG KEYCLOAK_VERSION=26.0
FROM quay.io/keycloak/keycloak:${KEYCLOAK_VERSION} AS builder

WORKDIR /opt/keycloak

# カスタムプロバイダ (SPI 実装 JAR) を配置
# README.md 等の非 JAR ファイルはビルド後に除去する
COPY providers/ /opt/keycloak/providers/
RUN find /opt/keycloak/providers -maxdepth 1 -type f ! -name "*.jar" -delete

# カスタムテーマを配置
# Keycloak はサブディレクトリ単位でテーマを認識するため、
# トップレベルの README.md 等は無視される
COPY themes/ /opt/keycloak/themes/

# Quarkus augmentation (最適化ビルド)
# ここで指定した値はイメージに焼き込まれ、起動時に変更不可になる。
# 変更する場合は docker build をやり直す。
ENV KC_DB=postgres
ENV KC_HTTP_ENABLED=true
ENV KC_PROXY_HEADERS=xforwarded
ENV KC_HEALTH_ENABLED=true

RUN /opt/keycloak/bin/kc.sh build

# ────────────────────────────────────────────────────────────────────────────
# Stage 2 – runtime
# ビルド成果物のみを含む最終イメージ。ビルドツールは残らない。
# ────────────────────────────────────────────────────────────────────────────
FROM quay.io/keycloak/keycloak:${KEYCLOAK_VERSION}

COPY --from=builder /opt/keycloak/ /opt/keycloak/

# 実行時に上書き可能な設定 (DB 接続情報、ホスト名等) は
# compose.yaml / k8s Secret / 環境変数で渡す。
# KC_BOOTSTRAP_ADMIN_* は初回起動時のみ有効。
ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
