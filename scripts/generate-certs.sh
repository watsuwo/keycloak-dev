#!/usr/bin/env bash
# Traefik用の自己署名証明書を生成する
# 既存の証明書がある場合は何もしない (再生成は certs/ を消してから)

set -euo pipefail

cd "$(dirname "$0")/.."

if [ -f .env ]; then
  set -o allexport
  # shellcheck disable=SC1091
  source .env
  set +o allexport
fi

BASE_DOMAIN="${BASE_DOMAIN:-localtest.me}"
CERT_DIR="traefik/certs"
CERT_FILE="${CERT_DIR}/local-cert.pem"
KEY_FILE="${CERT_DIR}/local-key.pem"

mkdir -p "${CERT_DIR}"

if [ -f "${CERT_FILE}" ] && [ -f "${KEY_FILE}" ]; then
  echo "証明書は既に存在します: ${CERT_FILE}"
  echo "再生成する場合は 'make certs-regen' を実行してください"
  exit 0
fi

if ! command -v openssl >/dev/null 2>&1; then
  echo "ERROR: openssl が見つかりません。先にインストールしてください。" >&2
  exit 1
fi

echo "自己署名証明書を生成中... (BASE_DOMAIN=${BASE_DOMAIN})"

openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout "${KEY_FILE}" \
  -out "${CERT_FILE}" \
  -days 365 \
  -subj "/CN=${BASE_DOMAIN}" \
  -addext "subjectAltName=DNS:${BASE_DOMAIN},DNS:*.${BASE_DOMAIN}"

# Keycloakコンテナ等から読み取れるよう権限緩和 (開発用)
chmod 644 "${CERT_FILE}" "${KEY_FILE}"

echo ""
echo "生成完了:"
echo "  証明書: ${CERT_FILE}"
echo "  秘密鍵: ${KEY_FILE}"
echo "  対象  : ${BASE_DOMAIN}, *.${BASE_DOMAIN}"
echo ""
echo "ブラウザでアクセス時の証明書警告は自己署名のため正常です。"
echo "警告を消したい場合は ${CERT_FILE} をOS/ブラウザの信頼ストアに追加してください。"
