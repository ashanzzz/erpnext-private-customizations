#!/usr/bin/env bash
set -euo pipefail

BUNDLE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_REPO="${1:-}"

if [[ -z "$TARGET_REPO" ]]; then
  echo "Usage: $0 /path/to/ashanzzz-docker" >&2
  exit 2
fi

TARGET_REPO="$(cd "$TARGET_REPO" && pwd)"

if [[ ! -d "$TARGET_REPO/.git" ]]; then
  echo "ERROR: target is not a Git working tree: $TARGET_REPO" >&2
  exit 3
fi

install -D -m 0644 \
  "$BUNDLE_DIR/.github/workflows/erpnext16-single-container-aio.yml" \
  "$TARGET_REPO/.github/workflows/erpnext16-single-container-aio.yml"

install -D -m 0644 \
  "$BUNDLE_DIR/erpnext16/single-aio/Containerfile" \
  "$TARGET_REPO/erpnext16/single-aio/Containerfile"

install -D -m 0755 \
  "$BUNDLE_DIR/erpnext16/scripts/fetch-ashan-custom-app.sh" \
  "$TARGET_REPO/erpnext16/scripts/fetch-ashan-custom-app.sh"

install -D -m 0644 \
  "$BUNDLE_DIR/erpnext16/.dockerignore" \
  "$TARGET_REPO/erpnext16/.dockerignore"

install -D -m 0644 \
  "$BUNDLE_DIR/erpnext16/image/apps.json" \
  "$TARGET_REPO/erpnext16/image/apps.json"

install -D -m 0644 \
  "$BUNDLE_DIR/erpnext16/ERPNEXT_VERSION" \
  "$TARGET_REPO/erpnext16/ERPNEXT_VERSION"

echo "Fixed files installed into: $TARGET_REPO"
echo
git -C "$TARGET_REPO" status --short
echo
echo "Review, then commit:"
echo "  git add .github/workflows/erpnext16-single-container-aio.yml erpnext16"
echo '  git commit -m "fix(erpnext16): avoid second frontend build and track Ashan main"'
echo "  git push"
