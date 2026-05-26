#!/usr/bin/env bash
# サンプル案件の Terraform を apply → 検証 → destroy のローテーション
# 前提: dev Keycloak が起動中 (make up)

set -euo pipefail

cd "$(dirname "$0")/.."

TF_DIR="terraform/environments/example-customer"

# --- 前提チェック ---

if ! command -v terraform >/dev/null 2>&1; then
  echo "ERROR: terraform コマンドが見つかりません" >&2
  echo "  WSL2/Ubuntu: sudo apt install terraform" >&2
  echo "  macOS      : brew install terraform" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq コマンドが見つかりません (検証結果のパースに必要)" >&2
  exit 1
fi

KEYCLOAK_URL="${TF_VAR_keycloak_url:-https://keycloak.localtest.me}"
if ! curl -sk -o /dev/null -w "%{http_code}" "${KEYCLOAK_URL}/realms/master/.well-known/openid-configuration" | grep -q "200"; then
  echo "ERROR: ${KEYCLOAK_URL} に到達できません" >&2
  echo "  事前に 'make up' で dev Keycloak を起動してください" >&2
  exit 1
fi

cd "${TF_DIR}"

if [ ! -f terraform.tfvars ]; then
  echo "terraform.tfvars を生成します"
  cp terraform.tfvars.example terraform.tfvars
fi

trap 'echo "=== cleanup: terraform destroy ===" && terraform destroy -auto-approve >/dev/null 2>&1 || true' EXIT

# --- apply ---

echo "=== terraform init ==="
terraform init -upgrade -no-color | tail -5

echo ""
echo "=== terraform apply ==="
terraform apply -auto-approve -no-color | tail -10

# --- validate: トークン取得 ---

echo ""
echo "=== validation: Direct Grant でトークン取得 ==="

REALM=$(terraform output -raw realm_name)
CLIENT_ID=$(terraform output -raw web_app_client_id)
CLIENT_SECRET=$(terraform output -raw web_app_client_secret)
USERNAME=$(terraform output -raw test_user_username)

RESPONSE=$(curl -sk -X POST \
  "${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token" \
  -d "grant_type=password" \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "username=${USERNAME}" \
  -d "password=testpassword")

if echo "${RESPONSE}" | jq -e '.access_token' >/dev/null 2>&1; then
  echo "✓ Token issued for ${USERNAME}@${REALM}/${CLIENT_ID}"
else
  echo "✗ Token request FAILED" >&2
  echo "${RESPONSE}" | jq . >&2 || echo "${RESPONSE}" >&2
  exit 1
fi

# --- validate: wrong-password で失敗確認 ---

echo ""
echo "=== validation: 間違ったパスワードで拒否されることを確認 ==="

BAD_RESPONSE=$(curl -sk -X POST \
  "${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token" \
  -d "grant_type=password" \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "username=${USERNAME}" \
  -d "password=WRONG_PASSWORD")

if echo "${BAD_RESPONSE}" | jq -e '.error == "invalid_grant"' >/dev/null 2>&1; then
  echo "✓ Wrong password correctly rejected (invalid_grant)"
else
  echo "✗ Expected invalid_grant for wrong password, got:" >&2
  echo "${BAD_RESPONSE}" | jq . >&2 || echo "${BAD_RESPONSE}" >&2
  exit 1
fi

echo ""
echo "=== ALL VALIDATIONS PASSED ==="
echo "destroy は trap で自動実行されます"
