#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WF="$ROOT/.github/workflows/erpnext16-single-container-aio.yml"
CF="$ROOT/erpnext16/single-aio/Containerfile"
FS="$ROOT/erpnext16/scripts/fetch-ashan-custom-app.sh"

echo "[validate] shell syntax"
bash -n "$FS"

echo "[validate] custom app branch"
grep -q 'ASHAN_REPO_REF: main' "$WF"
grep -q 'ASHAN_REPO_REF:=main' "$FS"

echo "[validate] failed build path removed"
if grep -Fq 'bench build --app ashan_cn_procurement' "$CF"; then
  echo "ERROR: second Ashan bench build is still present" >&2
  exit 1
fi

echo "[validate] static assets are linked"
grep -q 'APP_PUBLIC=' "$CF"
grep -q 'sites/assets/ashan_cn_procurement' "$CF"
grep -q 'ln -s "${APP_PUBLIC}" "${ASSET_LINK}"' "$CF"

echo "[validate] custom app context remains included"
grep -q '!custom-apps/ashan_cn_procurement/\*\*' "$ROOT/erpnext16/.dockerignore"

echo "[validate] workflow structure"
python3 - "$WF" <<'PY'
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text()
required = [
    "name: Build ERPNext16 AIO image (single container)",
    "docker/build-push-action@v6",
    "ghcr.io/${{ github.repository_owner }}/erpnext16:latest",
    "com.ashan.erpnext.custom-app.revision=",
]
for item in required:
    if item not in text:
        raise SystemExit(f"missing workflow marker: {item}")
print("workflow markers OK")
PY

echo "[validate] PASS"
