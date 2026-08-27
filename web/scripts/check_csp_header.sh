#!/bin/sh

set -eu

sbs_url=${1:?Aufruf: check_csp_header.sh URL [zusaetzliche-connect-origins]}
sbs_extra_origins=${2:-}
sbs_headers=$(mktemp)
sbs_body=$(mktemp)
trap 'rm -f "$sbs_headers" "$sbs_body"' EXIT HUP INT TERM

curl --fail --silent --show-error --dump-header "$sbs_headers" \
    --output "$sbs_body" "$sbs_url"

sbs_header_count=$(grep -ic '^Content-Security-Policy:' "$sbs_headers" || true)
if [ "$sbs_header_count" -ne 1 ]; then
    echo "Erwartet genau einen Content-Security-Policy-Header, gefunden: $sbs_header_count" >&2
    exit 1
fi

sbs_actual=$(grep -i '^Content-Security-Policy:' "$sbs_headers" \
    | tr -d '\r' \
    | sed 's/^[^:]*:[[:space:]]*//')
sbs_connect="'self'"
if [ -n "$sbs_extra_origins" ]; then
    sbs_connect="$sbs_connect $sbs_extra_origins"
fi
sbs_expected="default-src 'none'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; frame-src 'none'; form-action 'self'; script-src 'self'; script-src-attr 'none'; style-src 'self'; style-src-attr 'none'; img-src 'self' blob:; font-src 'self'; connect-src $sbs_connect; media-src 'none'; manifest-src 'none'; worker-src 'none'"

if [ "$sbs_actual" != "$sbs_expected" ]; then
    echo "Unerwartete Content-Security-Policy:" >&2
    echo "$sbs_actual" >&2
    exit 1
fi

echo "Content-Security-Policy: restriktiver Header vorhanden"
