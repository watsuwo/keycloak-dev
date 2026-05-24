#!/usr/bin/env python3
"""
Keycloak 設定値の自動検証スクリプト (spec ドリブン版)

docs/specs/cases/<realm>/clients/ 配下の spec markdown を読み込み、
Keycloak Admin REST API の実際の設定値と突合する。

使い方:
  python3 scripts/test-realm-config.py                   # dev 環境
  KEYCLOAK_ENV=stg python3 scripts/test-realm-config.py  # stg 環境

環境変数:
  KEYCLOAK_URL       デフォルト: https://keycloak.localtest.me
  KC_ADMIN_USERNAME  デフォルト: admin
  KC_ADMIN_PASSWORD  デフォルト: admin
  KEYCLOAK_REALM     デフォルト: example-customer
  KEYCLOAK_ENV       dev / stg / prod  デフォルト: dev
  KC_INSECURE        1 で TLS 検証スキップ (自己署名証明書用、デフォルト: 1)

依存:
  pip install pyyaml
"""

from __future__ import annotations

import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError:
    print("pyyaml が必要です: pip install pyyaml")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 設定
# ---------------------------------------------------------------------------

KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "https://keycloak.localtest.me").rstrip("/")
ADMIN_USER   = os.getenv("KC_ADMIN_USERNAME", "admin")
ADMIN_PASS   = os.getenv("KC_ADMIN_PASSWORD", "admin")
REALM        = os.getenv("KEYCLOAK_REALM", "example-customer")
ENV          = os.getenv("KEYCLOAK_ENV", "dev")
INSECURE     = os.getenv("KC_INSECURE", "1") == "1"

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_DIR  = REPO_ROOT / "docs" / "specs" / "cases" / REALM / "clients"

G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; B = "\033[1m"; Z = "\033[0m"

# ---------------------------------------------------------------------------
# Spec パーサー
# ---------------------------------------------------------------------------

def _extract_yaml_block(text: str, path: Path) -> dict:
    """markdown 内の最初の ```yaml ブロックを解析して返す。"""
    match = re.search(r"```yaml\n(.*?)\n```", text, re.DOTALL)
    if not match:
        raise ValueError(f"YAML ブロックが見つかりません: {path}")
    return yaml.safe_load(match.group(1))


def _deep_merge(base: dict, override: dict) -> dict:
    """override を base に再帰的にマージ。dict は深くマージ、それ以外は上書き。"""
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


# Keycloak Admin API と対応する spec フィールド
_CLIENT_BOOL_FIELDS = {
    "publicClient",
    "serviceAccountsEnabled",
    "standardFlowEnabled",
    "directAccessGrantsEnabled",
    "implicitFlowEnabled",
}
_CLIENT_LIST_FIELDS = {"redirectUris", "webOrigins"}

_REALM_BOOL_FIELDS = {
    "enabled",
    "registrationAllowed",
    "loginWithEmailAllowed",
    "resetPasswordAllowed",
    "verifyEmail",
    "duplicateEmailsAllowed",
    "bruteForceProtected",
}
_REALM_STR_FIELDS = {"sslRequired", "displayName"}


def parse_client_spec(md_path: Path, env: str = "dev") -> tuple[str, dict]:
    """
    クライアント spec markdown から (clientId, 期待値dict) を返す。
    env: ブロックのオーバーライドを適用する。
    """
    raw = _extract_yaml_block(md_path.read_text(), md_path)

    env_overrides = raw.get("env", {}).get(env, {})
    merged = _deep_merge(raw, env_overrides)
    merged.pop("env", None)

    client_id = merged["clientId"]
    expected: dict = {}

    for field in _CLIENT_BOOL_FIELDS:
        if field in merged:
            expected[field] = bool(merged[field])
    for field in _CLIENT_LIST_FIELDS:
        expected[field] = list(merged.get(field) or [])
    if "attributes" in merged:
        # attributes の値は Keycloak API がすべて文字列で返す
        expected["attributes"] = {k: str(v) for k, v in merged["attributes"].items()}

    return client_id, expected


def parse_realm_spec(index_md: Path) -> dict:
    """
    index.md の YAML ブロックから realm 期待値 dict を返す。
    realm spec は env オーバーライドを持たないため env 引数は不要。
    """
    raw = _extract_yaml_block(index_md.read_text(), index_md)

    expected: dict = {}
    for field in _REALM_BOOL_FIELDS:
        if field in raw:
            expected[field] = bool(raw[field])
    for field in _REALM_STR_FIELDS:
        if field in raw:
            expected[field] = str(raw[field])
    return expected


def load_client_specs(spec_dir: Path, env: str) -> dict[str, dict]:
    """spec_dir 内の *.md (index.md 除く) を解析して {clientId: 期待値} を返す。"""
    specs: dict[str, dict] = {}
    for md in sorted(spec_dir.glob("*.md")):
        if md.name == "index.md":
            continue
        try:
            client_id, expected = parse_client_spec(md, env)
            specs[client_id] = expected
        except (ValueError, KeyError) as e:
            print(f"{Y}警告: {md.name} をスキップ — {e}{Z}")
    return specs


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


def http_post(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req, context=_ssl_ctx()) as r:
        return json.loads(r.read())


def http_get(url: str, token: str) -> dict | list:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, context=_ssl_ctx()) as r:
        return json.loads(r.read())


def get_token() -> str:
    return http_post(
        f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
        {"grant_type": "password", "client_id": "admin-cli",
         "username": ADMIN_USER, "password": ADMIN_PASS},
    )["access_token"]


# ---------------------------------------------------------------------------
# テストランナー
# ---------------------------------------------------------------------------

class Results:
    def __init__(self):
        self.passed = 0
        self.failed = 0

    def ok(self, label: str):
        print(f"  {G}✓{Z} {label}")
        self.passed += 1

    def fail(self, label: str, expected, actual):
        print(f"  {R}✗{Z} {label}")
        print(f"      expected : {expected!r}")
        print(f"      actual   : {actual!r}")
        self.failed += 1

    @property
    def total(self) -> int:
        return self.passed + self.failed


def assert_eq(results: Results, label: str, actual, expected):
    if isinstance(expected, list):
        match = sorted(str(x) for x in (actual or [])) == sorted(str(x) for x in expected)
    else:
        match = actual == expected
    if match:
        results.ok(label)
    else:
        results.fail(label, expected, actual)


def check_realm(token: str, realm_expected: dict, results: Results):
    print(f"\n{B}Realm: {REALM}{Z}")
    data = http_get(f"{KEYCLOAK_URL}/admin/realms/{REALM}", token)
    for key, expected in realm_expected.items():
        assert_eq(results, key, data.get(key), expected)


def check_clients(token: str, client_specs: dict, results: Results):
    all_clients = http_get(
        f"{KEYCLOAK_URL}/admin/realms/{REALM}/clients?max=200", token
    )
    by_client_id = {c["clientId"]: c for c in all_clients}

    for client_id, expected in client_specs.items():
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
    print(f"{B}Keycloak 設定値検証{Z}  (realm: {REALM} / env: {ENV})")
    print(f"URL: {KEYCLOAK_URL}")
    print(f"Spec: {SPEC_DIR.relative_to(REPO_ROOT)}")
    if INSECURE:
        print(f"{Y}TLS検証スキップ中 (KC_INSECURE=1 — 自己署名証明書用){Z}")
    print("─" * 55)

    if not SPEC_DIR.exists():
        print(f"{R}Spec ディレクトリが見つかりません: {SPEC_DIR}{Z}")
        sys.exit(1)

    index_md = SPEC_DIR / "index.md"
    realm_expected: dict = {}
    if index_md.exists():
        try:
            realm_expected = parse_realm_spec(index_md)
        except (ValueError, KeyError) as e:
            print(f"{Y}警告: realm spec (index.md) をスキップ — {e}{Z}")

    client_specs = load_client_specs(SPEC_DIR, ENV)
    if not client_specs:
        print(f"{R}テスト対象の client spec が見つかりません: {SPEC_DIR}/*.md{Z}")
        sys.exit(1)

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
        if realm_expected:
            check_realm(token, realm_expected, results)
        check_clients(token, client_specs, results)
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
