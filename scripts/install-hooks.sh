#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/.." && pwd)"

cp "$repo_root/.githooks/pre-push" "$repo_root/.git/hooks/pre-push"
chmod +x "$repo_root/.git/hooks/pre-push"

if test -x "$repo_root/.git/hooks/pre-push"; then
  echo "Git hooks installed."
else
  echo "Hook installation failed." >&2
  exit 1
fi
