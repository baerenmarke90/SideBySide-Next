#!/bin/sh

set -eu

sbs_validator=${1:-docker-entrypoint.d/19-validate-csp-connect-src.envsh}

sbs_run_validator() {
    SBS_WEB_CSP_CONNECT_ORIGINS=$1 sh -c \
        '. "$1"; printf "%s" "$SBS_WEB_CSP_CONNECT_ORIGINS"' \
        sh "$sbs_validator"
}

sbs_assert_accepts() {
    sbs_input=$1
    sbs_expected=$2
    sbs_actual=$(sbs_run_validator "$sbs_input")
    if [ "$sbs_actual" != "$sbs_expected" ]; then
        echo "CSP origin was normalized incorrectly." >&2
        exit 1
    fi
}

sbs_assert_rejects() {
    if sbs_run_validator "$1" >/dev/null 2>&1; then
        echo "Unsafe CSP source was accepted." >&2
        exit 1
    fi
}

sbs_assert_accepts '' ''
sbs_assert_accepts 'https://api.example.test' ' https://api.example.test'
sbs_assert_accepts \
    '  https://api.example.test   https://s3.example.test:9443  ' \
    ' https://api.example.test https://s3.example.test:9443'
sbs_assert_accepts 'http://localhost:9000 https://[::1]:9443' \
    ' http://localhost:9000 https://[::1]:9443'
sbs_assert_accepts 'https://example.test:65535' ' https://example.test:65535'

sbs_assert_rejects 'https:'
sbs_assert_rejects 'https://*.example.test'
sbs_assert_rejects 'https://user@example.test'
sbs_assert_rejects 'https://example.test/path'
sbs_assert_rejects 'https://example.test:65536'
sbs_assert_rejects "'unsafe-inline'"
sbs_assert_rejects "https://example.test; add_header X-Injected true"

echo "CSP origin validation: successful"
