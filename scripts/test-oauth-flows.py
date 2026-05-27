#!/usr/bin/env python3
"""
L4: OAuth フロー動作確認スクリプト。
terraform apply 後に実行し、実際の認証フローが spec 通りに動作するか確認する。

テスト内容:
  1. OIDC Discovery エンドポイントが正常応答
  2. spa-frontend: ROPC が拒否される (directAccessGrantsEnabled: false)
  3. batch-worker: Client Credentials でトークン取得 (KC_BATCH_WORKER_SECRET 設定時のみ)

使い方:
  python3 scripts/test-oauth-flows.py
  KC_BATCH_WORKER_SECRET=xxx python3 scripts/test-oauth-flows.py

環境変数:
  KEYCLOAK_URL             デフォルト: https://keycloak.localtest.me
  KEYCLOAK_REALM           デフォルト: example-customer
  KC_INSECURE              1 で TLS 検証スキップ (自己署名証明書用、デフォルト: 1)
  KC_BATCH_WORKER_SECRET   batch-worker の client_secret (省略するとスキップ)
"""

from __future__ import annotations

import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "https://keycloak.localtest.me").rstrip("/")
REALM        = os.getenv("KEYCLOAK_REALM", "example-customer")
INSECURE     = os.getenv("KC_INSECURE", "1") == "1"
BATCH_SECRET = os.getenv("KC_BATCH_WORKER_SECRET", "")

TOKEN_URL     = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"
DISCOVERY_URL = f"{KEYCLOAK_URL}/realms/{REALM}/.well-known/openid-configuration"

G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; B = "\033[1m"; Z = "\033[0m"

# ---------------------------------------------------------------------------
# HTTP ヘルパー
# ---------------------------------------------------------------------------

def _ssl_ctx():
    if INSECURE:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    return None


def http_get_json(url: str) -> dict:
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, context=_ssl_ctx()) as r:
        return json.loads(r.read())


def http_post(url: str, data: dict) -> tuple[int, dict]:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    try:
        with urllib.request.urlopen(req, context=_ssl_ctx()) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


# ---------------------------------------------------------------------------
# テストランナー
# ---------------------------------------------------------------------------

class Results:
    def __init__(self):
        self.passed  = 0
        self.failed  = 0
        self.skipped = 0

    def ok(self, label: str):
        print(f"  {G}✓{Z} {label}")
        self.passed += 1

    def fail(self, label: str, detail: str = ""):
        suffix = f"  ({detail})" if detail else ""
        print(f"  {R}✗{Z} {label}{suffix}")
        self.failed += 1

    def skip(self, label: str, reason: str):
        print(f"  {Y}–{Z} {label}  [{reason}]")
        self.skipped += 1

    @property
    def total(self) -> int:
        return self.passed + self.failed


# ---------------------------------------------------------------------------
# テストケース
# ---------------------------------------------------------------------------

DISCOVERY_REQUIRED_KEYS = [
    "issuer",
    "authorization_endpoint",
    "token_endpoint",
    "jwks_uri",
    "grant_types_supported",
]


def test_discovery(results: Results):
    print(f"\n{B}OIDC Discovery{Z}")
    try:
        doc = http_get_json(DISCOVERY_URL)
    except Exception as e:
        results.fail("discovery エンドポイントへの接続", str(e))
        return

    for key in DISCOVERY_REQUIRED_KEYS:
        if key in doc:
            results.ok(key)
        else:
            results.fail(key, "discovery レスポンスに含まれない")


def test_ropc_rejected(results: Results):
    """directAccessGrantsEnabled: false のクライアントで ROPC が拒否されること。"""
    print(f"\n{B}ROPC 拒否確認 (spa-frontend — directAccessGrantsEnabled: false){Z}")
    status, body = http_post(TOKEN_URL, {
        "grant_type": "password",
        "client_id":  "spa-frontend",
        "username":   "__probe__",
        "password":   "__probe__",
    })
    error = body.get("error", "")
    if error == "unauthorized_client":
        results.ok(f"ROPC 拒否を確認 (error={error!r})")
    elif status == 200:
        results.fail("ROPC が通ってしまった (トークンが返った)")
    else:
        results.fail("期待と異なるエラー", f"status={status} error={error!r}")


def test_client_credentials(results: Results):
    """batch-worker の Client Credentials Grant でトークンが取得できること。"""
    print(f"\n{B}Client Credentials (batch-worker){Z}")
    if not BATCH_SECRET:
        results.skip("Client Credentials Grant", "KC_BATCH_WORKER_SECRET 未設定")
        return

    status, body = http_post(TOKEN_URL, {
        "grant_type":    "client_credentials",
        "client_id":     "batch-worker",
        "client_secret": BATCH_SECRET,
    })
    if status == 200 and "access_token" in body:
        results.ok(
            f"アクセストークン取得成功"
            f" (token_type={body.get('token_type')!r},"
            f" expires_in={body.get('expires_in')}s)"
        )
    else:
        results.fail("トークン取得失敗",
                     f"status={status} error={body.get('error')!r}")


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------

def main():
    print(f"{B}OAuth フロー動作確認{Z}  (realm: {REALM})")
    print(f"URL: {KEYCLOAK_URL}")
    if INSECURE:
        print(f"{Y}TLS検証スキップ中 (KC_INSECURE=1){Z}")
    print("─" * 55)

    results = Results()
    try:
        test_discovery(results)
        test_ropc_rejected(results)
        test_client_credentials(results)
    except Exception as e:
        print(f"{R}接続失敗: {e}{Z}")
        print(f"{Y}Keycloak が起動しているか確認: make ps{Z}")
        sys.exit(1)

    print(f"\n{'─' * 55}")
    skipped_note = f"  ({results.skipped} スキップ)" if results.skipped else ""
    if results.failed == 0:
        print(f"{G}{B}全 {results.total} 項目 PASSED{Z}{skipped_note}")
    else:
        print(f"{R}{B}{results.failed}/{results.total} 項目 FAILED{Z}{skipped_note}")
        sys.exit(1)


if __name__ == "__main__":
    main()
