#!/usr/bin/env python3
"""
L1: spec markdown の静的検証スクリプト。
docs/specs/cases/**/*.md の frontmatter と YAML ブロックを確認する。

使い方:
  python3 scripts/test-spec.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT      = Path(__file__).resolve().parent.parent
SPEC_CASES_DIR = REPO_ROOT / "docs" / "specs" / "cases"

G = "\033[92m"; R = "\033[91m"; B = "\033[1m"; Z = "\033[0m"

REQUIRED_FRONTMATTER = {"spec_id", "title", "status"}
VALID_STATUSES       = {"draft", "review", "implemented", "deprecated"}


# ---------------------------------------------------------------------------
# パーサー
# ---------------------------------------------------------------------------

def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    fm: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm


def has_yaml_block(text: str) -> bool:
    return bool(re.search(r"```yaml\n.*?\n```", text, re.DOTALL))


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

    def fail(self, label: str, detail: str = ""):
        suffix = f": {detail}" if detail else ""
        print(f"  {R}✗{Z} {label}{suffix}")
        self.failed += 1

    @property
    def total(self) -> int:
        return self.passed + self.failed


def check_spec(md_path: Path, results: Results):
    text = md_path.read_text()

    fm = parse_frontmatter(text)
    if not fm:
        results.fail("frontmatter (--- ブロック) が見つからない")
        return

    for field in sorted(REQUIRED_FRONTMATTER):
        if fm.get(field):
            results.ok(f"frontmatter.{field}")
        else:
            results.fail(f"frontmatter.{field} が未設定または空")

    status = fm.get("status", "")
    if status in VALID_STATUSES:
        results.ok(f"status 値が有効 ({status!r})")
    else:
        results.fail(f"status 値が無効 ({status!r})",
                     f"有効値: {', '.join(sorted(VALID_STATUSES))}")

    if has_yaml_block(text):
        results.ok("YAML ブロックあり")
    else:
        results.fail("YAML ブロック (```yaml) が見つからない")


# ---------------------------------------------------------------------------
# エントリポイント
# ---------------------------------------------------------------------------

def main():
    print(f"{B}Spec 静的検証{Z}")
    print(f"対象: {SPEC_CASES_DIR.relative_to(REPO_ROOT)}")
    print("─" * 55)

    if not SPEC_CASES_DIR.exists():
        print(f"{R}spec ディレクトリが見つかりません: {SPEC_CASES_DIR}{Z}")
        sys.exit(1)

    spec_files = sorted(SPEC_CASES_DIR.rglob("*.md"))
    if not spec_files:
        print(f"{R}spec ファイルが見つかりません{Z}")
        sys.exit(1)

    results = Results()
    for md in spec_files:
        print(f"\n{B}{md.relative_to(REPO_ROOT)}{Z}")
        check_spec(md, results)

    print(f"\n{'─' * 55}")
    if results.failed == 0:
        print(f"{G}{B}全 {results.total} 項目 PASSED{Z}")
    else:
        print(f"{R}{B}{results.failed}/{results.total} 項目 FAILED{Z}")
        sys.exit(1)


if __name__ == "__main__":
    main()
