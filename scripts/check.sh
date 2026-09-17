#!/usr/bin/env bash
# One command to lint + test everything that doesn't need Docker running:
# the web app and all three Python services (identity/city-core use an
# in-memory SQLite database for their unit tests, so no Postgres needed).
#
# Usage (from the repo root, Git Bash / any POSIX shell):
#   bash scripts/check.sh

set -uo pipefail
cd "$(dirname "$0")/.."

PY=".venv/Scripts/python.exe"
[ -x "$PY" ] || PY=".venv/bin/python"

NAMES=()
RESULTS=()

run_step() {
  local name="$1"; shift
  echo
  echo "=== $name ==="
  if "$@"; then
    RESULTS+=("PASS")
  else
    RESULTS+=("FAIL")
  fi
  NAMES+=("$name")
}

run_step "web: lint" npm run lint:web
run_step "web: typecheck" npm run typecheck:web
run_step "web: test" npm run test:web

for service in api-gateway identity city-core; do
  dir="services/$service"
  run_step "$service: install" "$PY" -m pip install -q -e "$dir[dev]"
  pushd "$dir" >/dev/null
  run_step "$service: lint" "../../$PY" -m ruff check .
  run_step "$service: test" "../../$PY" -m pytest -q
  popd >/dev/null
done

echo
echo "=== Summary ==="
fail=0
for i in "${!NAMES[@]}"; do
  printf "%-25s %s\n" "${NAMES[$i]}" "${RESULTS[$i]}"
  [ "${RESULTS[$i]}" = "FAIL" ] && fail=1
done

echo
if [ "$fail" = "1" ]; then
  echo "Some checks failed."
  exit 1
else
  echo "All checks passed."
  exit 0
fi
