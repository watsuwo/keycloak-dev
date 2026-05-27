#!/usr/bin/env bash
# terraform/environments/*/* 全ディレクトリで terraform validate を実行する。
# 前提: terraform CLI がインストールされていること。
set -euo pipefail

G="\033[92m"; R="\033[91m"; B="\033[1m"; Z="\033[0m"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0; FAIL=0

mapfile -t ENV_DIRS < <(find "$REPO_ROOT/terraform/environments" -mindepth 2 -maxdepth 2 -type d | sort)

if [ ${#ENV_DIRS[@]} -eq 0 ]; then
  echo "テスト対象の environment ディレクトリが見つかりません: terraform/environments/*/*"
  exit 1
fi

echo -e "${B}Terraform 構文・型チェック${Z}"
echo -e "対象: ${#ENV_DIRS[@]} environment"
echo "───────────────────────────────────────────────────────"

for dir in "${ENV_DIRS[@]}"; do
  rel="$(realpath --relative-to="$REPO_ROOT" "$dir")"
  printf "  %-50s " "$rel"

  init_log="$(terraform -chdir="$dir" init -backend=false -input=false -no-color 2>&1)" || {
    printf "${R}✗ init 失敗${Z}\n"
    echo "$init_log" | sed 's/^/      /'
    ((FAIL++)); continue
  }

  validate_log="$(terraform -chdir="$dir" validate -no-color 2>&1)" && {
    printf "${G}✓${Z}\n"
    ((PASS++))
  } || {
    printf "${R}✗${Z}\n"
    echo "$validate_log" | sed 's/^/      /'
    ((FAIL++))
  }
done

echo "───────────────────────────────────────────────────────"
if [ "$FAIL" -eq 0 ]; then
  echo -e "${G}${B}全 $((PASS + FAIL)) 環境 PASSED${Z}"
else
  echo -e "${R}${B}${FAIL}/$((PASS + FAIL)) 環境 FAILED${Z}"
  exit 1
fi
