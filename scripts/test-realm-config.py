#!/usr/bin/env python3
"""
Keycloak 設定値の自動検証スクリプト。
terraform apply 後に実行し、Admin REST API 経由で期待値と突合する。

使い方:
  python3 scripts/test-realm-config.py

環境変数 (すべて省略可):
  KEYCLOAK_URL       デフォルト: https://keycloak.localtest.me
  KC_ADMIN_USERNAME  デフォルト: admin
  KC_ADMIN_PASSWORD  デフォルト: admin
  KEYCLOAK_REALM     デフォルト: example-customer
  KC_INSECURE        1 にすると TLS 検証スキップ (自己署名証明書用、デフォルト: 1)
"""

import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "https://keycloak.localtest.me").rstrip("/")
ADMIN_USER   = os.getenv("KC_ADMIN_USERNAME", "admin")
ADMIN_PASS   = os.getenv("KC_ADMIN_PASSWORD", "admin")
REALM        = os.getenv("KEYCLOAK_REALM", "example-customer")
INSECURE     = os.getenv("KC_INSECURE", "1") == "1"

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


def http_post(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, context=_ssl_ctx()) as r:
        return json.loads(r.read())


def http_get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, context=_ssl_ctx()) as r:
        return json.loads(r.read())


def get_token():
    return http_post(
        f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
        {"grant_type": "password", "client_id": "admin-cli",
         "username": ADMIN_USER, "password": ADMIN_PASS},
    )["access_token"]


# ---------------------------------------------------------------------------
# 期待値定義
# SoT は docs/specs/cases/example-customer/clients/*.md
# 環境: dev (terraform/environments/example-customer/dev/)
# ---------------------------------------------------------------------------

EXPECTED_REALM = {
    "realm":                  "example-customer",
    "enabled":                True,
    "registrationAllowed":    False,
    "loginWithEmailAllowed":  True,
    "sslRequired":            "external",
    "resetPasswordAllowed":   True,
    "duplicateEmailsAllowed": False,
}

EXPECTED_CLIENTS = {
    # clients/web-app.md
    "web-app": {
        "publicClient":              False,
        "standardFlowEnabled":       True,
        "directAccessGrantsEnabled": False,
        "serviceAccountsEnabled":    False,
        "implicitFlowEnabled":       False,
        "redirectUris":              ["http://localhost:3000/*"],
        "webOrigins":                ["http://localhost:3000"],
        "attributes": {
            "post.logout.redirect.uris": "http://localhost:3000",
            "access.token.lifespan":     "300",
        },
    },
    # clients/spa-frontend.md
    "spa-frontend": {
        "publicClient":              True,
        "standardFlowEnabled":       True,
        "directAccessGrantsEnabled": False,
        "serviceAccountsEnabled":    False,
        "implicitFlowEnabled":       False,
        "redirectUris":              ["http://localhost:3001/*"],
        "webOrigins":                ["http://localhost:3001", "+"],
        "attributes": {
            "pkce.code.challenge.method":  "S256",
            "post.logout.redirect.uris":   "http://localhost:3001",
            "access.token.lifespan":       "300",
        },
    },
    # clients/batch-worker.md
    "batch-worker": {
        "publicClient":              False,
        "standardFlowEnabled":       False,
        "directAccessGrantsEnabled": False,
        "serviceAccountsEnabled":    True,
        "implicitFlowEnabled":       False,
        "redirectUris":              [],
        "webOrigins":                [],
        "attributes": {
            "access.token.lifespan": "600",
        },
    },
}


# ---------------------------------------------------------------------------
# テストランナー
# ---------------------------------------------------------------------------

class Results:
    def __init__(self):
        self.passed = 0
        self.failed = 0

    def ok(self, label):
        print(f"  {G}✓{Z} {label}")
        self.passed += 1

    def fail(self, label, expected, actual):
        print(f"  {R}✗{Z} {label}")
        print(f"      expected : {expected!r}")
        print(f"      actual   : {actual!r}")
        self.failed += 1

    @property
    def total(self):
        return self.passed + self.failed


def assert_eq(results, label, actual, expected):
    if isinstance(expected, list):
        match = sorted(str(x) for x in (actual or [])) == sorted(str(x) for x in expected)
    else:
        match = actual == expected
    if match:
        results.ok(label)
    else:
        results.fail(label, expected, actual)


def check_realm(token, results):
    print(f"\n{B}Realm: {REALM}{Z}")
    data = http_get(f"{KEYCLOAK_URL}/admin/realms/{REALM}", token)
    for key, expected in EXPECTED_REALM.items():
        assert_eq(results, key, data.get(key), expected)


def check_clients(token, results):
    all_clients = http_get(
        f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients?max=200", token
    )
    by_client_id = {c["clientId"]: c for c in all_clients}

    for client_id, expected in EXPECTED_CLIENTS.items():
        print(f"\n{B}Client: {client_id}{Z}")
        if client_id not in by_client_id:
            print(f"  {R}✗{Z} Realm にクライアントが存在しない")
            results.failed += 1
            continue

        c = by_client_id[client_id]
        for key, val in expected.items():
            if key == "attributes":
                attrs = c.get("attributes", {})
                for attr_key, attr_val in val.items():
                    assert_eq(results, f"attributes.{attr_key}", attrs.get(attr_key), attr_val)
            else:
                assert_eq(results, key, c.get(key), val)


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------

def main():
    print(f"{B}Keycloak 設定値検証{Z}  (env: dev / realm: {REALM})")
    print(f"URL: {KEYCLOAK_URL}")
    if INSECURE:
        print(f"{Y}TLS検証スキップ中 (KC_INSECURE=1 — 自己署名証明書用){Z}")
    print("─" * 55)

    try:
        token = get_token()
    except urllib.error.HTTPError as e:
        print(f"{R}認証失敗: HTTP {e.code} — ユーザー名/パスワードを確認{Z}")
        sys.exit(1)
    except Exception as e:
        print(f"{R}接続失敗: {e}{Z}")
        print(f"{Y}Keycloak が起動しているか確認: make ps{Z}")
        sys.exit(1)

    results = Results()
    try:
        check_realm(token, results)
        check_clients(token, results)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"{R}API エラー: HTTP {e.code} — {body[:300]}{Z}")
        sys.exit(1)

    print(f"\n{'─' * 55}")
    if results.failed == 0:
        print(f"{G}{B}全 {results.total} 項目 PASSED{Z}")
    else:
        print(f"{R}{B}{results.failed}/{results.total} 項目 FAILED{Z}")
        sys.exit(1)


if __name__ == "__main__":
    main()
