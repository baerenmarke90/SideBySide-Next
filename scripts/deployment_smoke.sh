#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: bash scripts/deployment_smoke.sh <public-base-url>

Runs the non-destructive HTTP smoke checks required by the SideBySide
Development/Production promotion workflow.

Example:
  bash scripts/deployment_smoke.sh https://dev.sidebyside.example
EOF
}

if [[ $# -ne 1 ]]; then
  usage >&2
  exit 2
fi

base_url=${1%/}
case "$base_url" in
  http://localhost:*|http://127.0.0.1:*) ;;
  https://*) ;;
  *)
    echo "Refusing non-HTTPS non-local base URL: $base_url" >&2
    exit 2
    ;;
esac

curl_flags=(--fail --silent --show-error --location --max-time 20)

echo "[smoke] Web health"
curl "${curl_flags[@]}" "$base_url/healthz" >/dev/null

echo "[smoke] API readiness"
readiness=$(curl "${curl_flags[@]}" "$base_url/api/v1/health/ready")
python3 - "$readiness" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
if payload.get("status") != "ok" or payload.get("database") != "ok":
    raise SystemExit(f"unexpected readiness response: {payload!r}")
PY

echo "[smoke] Web root"
curl "${curl_flags[@]}" "$base_url/" >/dev/null

echo "[smoke] PASS: $base_url"
