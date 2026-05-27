#!/usr/bin/env python3
"""
spec frontmatter の検証スクリプト (Phase B).

検証内容 (forward check: spec → impl):
  1. spec_id の存在・形式 (PATTERN-/TEMPLATE-/CASE-/TASK- で始まる)
  2. spec_id の一意性
  3. status の値が有効か (draft/approved/implemented/deprecated/template/ready)
  4. implementations: で列挙されたパスが実在するか
  5. acceptance_tests: で列挙されたパスが実在するか
  6. status: implemented なのに implementations が空でないか (warning)

依存: Python 3.8+ stdlib のみ (PyYAML不要、簡易YAMLパーサ内蔵)

使い方:
    python3 scripts/validate-specs.py            # docs/ 配下を検証
    python3 scripts/validate-specs.py --quiet    # エラー時のみ出力 (CI用)
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_DIRS = ["docs/specs"]
VALID_STATUSES = {"draft", "approved", "implemented", "deprecated", "template", "ready"}
VALID_PREFIXES = ("PATTERN-", "TEMPLATE-", "CASE-", "TASK-")


# ANSIカラー (出力先がtty以外なら無効化)
def _color(code: str) -> str:
    return code if sys.stdout.isatty() else ""


RED = _color("\033[31m")
YELLOW = _color("\033[33m")
GREEN = _color("\033[32m")
DIM = _color("\033[2m")
RESET = _color("\033[0m")


# ---------- 簡易YAMLパーサ (frontmatter専用、最小機能) ----------

def parse_frontmatter(text: str) -> dict[str, Any] | None:
    """``---`` で囲まれた YAML frontmatter を dict に変換。

    対応: scalar (key: value), list (key: ... + ``  - item`` 行)。
    nested map / inline list / 引用符 / multiline は未対応 (現状の用途では不要)。
    """
    m = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", text, re.DOTALL)
    if not m:
        return None

    body = m.group(1)
    result: dict[str, Any] = {}
    current_key: str | None = None
    for raw in body.split("\n"):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        # リスト要素: "  - value"
        if line.startswith("  - ") and current_key is not None:
            value = line[4:].strip()
            existing = result.get(current_key)
            if isinstance(existing, list):
                existing.append(value)
            else:
                result[current_key] = [value]
            continue
        # key: value or key:
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            if value:
                result[key] = value
                current_key = key
            else:
                result[key] = []
                current_key = key
    return result


# ---------- 検証 ----------

@dataclass
class Issue:
    level: str  # "error" or "warn"
    msg: str


@dataclass
class SpecRecord:
    path: Path
    spec_id: str
    status: str
    issues: list[Issue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.level == "error" for i in self.issues)


def find_spec_files() -> list[Path]:
    files: list[Path] = []
    for d in SPEC_DIRS:
        base = REPO_ROOT / d
        if not base.is_dir():
            continue
        files.extend(sorted(base.rglob("*.md")))
    return files


def validate_one(path: Path, fm: dict[str, Any]) -> SpecRecord:
    spec_id = str(fm.get("spec_id", "")).strip()
    status = str(fm.get("status", "")).strip()
    rec = SpecRecord(path=path, spec_id=spec_id or "?", status=status or "?")

    if not spec_id:
        rec.issues.append(Issue("error", "missing required field: spec_id"))
    elif not spec_id.startswith(VALID_PREFIXES):
        rec.issues.append(
            Issue("error", f"spec_id '{spec_id}' must start with one of: {', '.join(VALID_PREFIXES)}")
        )

    if not status:
        rec.issues.append(Issue("error", "missing required field: status"))
    elif status not in VALID_STATUSES:
        rec.issues.append(
            Issue("error", f"invalid status '{status}', must be one of: {', '.join(sorted(VALID_STATUSES))}")
        )

    impls = fm.get("implementations", []) or []
    if isinstance(impls, str):
        impls = [impls]
    for impl in impls:
        p = REPO_ROOT / impl
        if not p.exists():
            rec.issues.append(Issue("error", f"implementations path not found: {impl}"))

    tests = fm.get("acceptance_tests", []) or []
    if isinstance(tests, str):
        tests = [tests]
    for t in tests:
        p = REPO_ROOT / t
        if not p.exists():
            rec.issues.append(Issue("error", f"acceptance_tests path not found: {t}"))

    if status == "implemented" and not impls:
        rec.issues.append(Issue("warn", "status is 'implemented' but no implementations listed"))

    return rec


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate spec frontmatter (Phase B forward check)")
    parser.add_argument("--quiet", action="store_true", help="エラー/警告がある場合のみ出力")
    args = parser.parse_args()

    files = find_spec_files()
    records: list[SpecRecord] = []
    seen_ids: dict[str, Path] = {}
    skipped: list[Path] = []

    for f in files:
        text = f.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if fm is None:
            skipped.append(f)
            continue
        rec = validate_one(f, fm)

        # 一意性チェック
        if rec.spec_id != "?" and rec.spec_id in seen_ids:
            other = seen_ids[rec.spec_id].relative_to(REPO_ROOT)
            rec.issues.append(Issue("error", f"duplicate spec_id (also defined in {other})"))
        else:
            seen_ids[rec.spec_id] = f
        records.append(rec)

    total_errors = sum(1 for r in records for i in r.issues if i.level == "error")
    total_warns = sum(1 for r in records for i in r.issues if i.level == "warn")

    # 出力
    if not args.quiet or total_errors or total_warns:
        print(f"Validating specs under {SPEC_DIRS}/ (REPO_ROOT={REPO_ROOT})\n")
        for rec in records:
            rel = rec.path.relative_to(REPO_ROOT)
            if rec.has_errors:
                head = f"{RED}✗{RESET}"
            elif any(i.level == "warn" for i in rec.issues):
                head = f"{YELLOW}!{RESET}"
            else:
                head = f"{GREEN}✓{RESET}"
            line = f"  {head} {rec.spec_id} ({rec.status}) {DIM}{rel}{RESET}"
            if args.quiet and not rec.issues:
                continue
            print(line)
            for issue in rec.issues:
                tag = f"{RED}ERROR{RESET}" if issue.level == "error" else f"{YELLOW}WARN {RESET}"
                print(f"      {tag} {issue.msg}")

        if not args.quiet and skipped:
            print(f"\n{DIM}Skipped (no frontmatter): {len(skipped)} file(s){RESET}")
            for s in skipped:
                print(f"  - {s.relative_to(REPO_ROOT)}")

    # サマリ
    print()
    summary = f"{len(records)} spec(s) checked, {total_errors} error(s), {total_warns} warning(s)"
    if total_errors:
        print(f"{RED}✗ {summary}{RESET}")
        return 1
    elif total_warns:
        print(f"{YELLOW}! {summary}{RESET}")
        return 0
    else:
        print(f"{GREEN}✓ {summary}{RESET}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
