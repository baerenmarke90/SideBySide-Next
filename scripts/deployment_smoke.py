#!/usr/bin/env python3
"""Non-destructive smoke checks for a deployed SideBySide revision."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass

REVISION_HEADER = "X-SideBySide-Revision"
TIMEOUT_SECONDS = 20


@dataclass(frozen=True)
class HttpResult:
    status: int
    body: bytes
    revision: str | None


def request(
    url: str,
    *,
    method: str = "GET",
    payload: dict[str, object] | None = None,
    bearer: str | None = None,
) -> HttpResult:
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if bearer is not None:
        headers["Authorization"] = f"Bearer {bearer}"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as response:
            return HttpResult(
                status=response.status,
                body=response.read(),
                revision=response.headers.get(REVISION_HEADER),
            )
    except urllib.error.HTTPError as exc:
        body = exc.read()
        raise RuntimeError(f"{method} {url} returned HTTP {exc.code}: {body[:200]!r}") from None
    except OSError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc}") from exc


def expect_json(result: HttpResult, *, url: str) -> object:
    try:
        return json.loads(result.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{url} did not return valid JSON") from exc


def expect_text(result: HttpResult, *, url: str) -> str:
    try:
        return result.body.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise RuntimeError(f"{url} did not return UTF-8 text") from exc


def check(base_url: str, expected_revision: str) -> None:
    origin = base_url.rstrip("/")

    web_url = f"{origin}/healthz"
    web = request(web_url)
    if web.status != 200:
        raise RuntimeError(f"Web health returned HTTP {web.status}")
    print("ok: Web /healthz")

    web_revision_url = f"{origin}/.well-known/sidebyside-revision"
    web_revision = expect_text(request(web_revision_url), url=web_revision_url)
    if web_revision != expected_revision:
        raise RuntimeError(
            f"Web revision mismatch: expected {expected_revision!r}, got {web_revision!r}"
        )
    print(f"ok: Web revision {expected_revision}")

    ready_url = f"{origin}/api/v1/health/ready"
    ready = request(ready_url)
    ready_body = expect_json(ready, url=ready_url)
    if not isinstance(ready_body, dict) or ready_body.get("status") != "ok" or ready_body.get("database") != "ok":
        raise RuntimeError(f"API readiness is not healthy: {ready_body!r}")
    if ready.revision != expected_revision:
        raise RuntimeError(
            f"API revision mismatch: expected {expected_revision!r}, got {ready.revision!r}"
        )
    print(f"ok: API ready, revision {expected_revision}")

    email = os.environ.get("SBS_SMOKE_EMAIL", "")
    password = os.environ.get("SBS_SMOKE_PASSWORD", "")
    if bool(email) != bool(password):
        raise RuntimeError("Set both SBS_SMOKE_EMAIL and SBS_SMOKE_PASSWORD, or neither.")
    if not email:
        print("skip: authenticated smoke (no SBS_SMOKE_EMAIL/SBS_SMOKE_PASSWORD)")
        return

    sign_in_url = f"{origin}/api/v1/auth/sign-in"
    signed_in = request(
        sign_in_url,
        method="POST",
        payload={
            "email": email,
            "password": password,
            "deviceName": "SideBySide deployment smoke",
            "platform": "ops-smoke",
        },
    )
    session = expect_json(signed_in, url=sign_in_url)
    if not isinstance(session, dict):
        raise RuntimeError("Sign-in response is not an object")
    tokens = session.get("tokens")
    if not isinstance(tokens, dict) or not isinstance(tokens.get("accessToken"), str):
        raise RuntimeError("Sign-in response contains no access token")
    access_token = tokens["accessToken"]
    print("ok: password sign-in")

    memberships_url = f"{origin}/api/v1/auth/memberships"
    memberships = request(memberships_url, bearer=access_token)
    expect_json(memberships, url=memberships_url)
    print("ok: authenticated memberships read")

    sign_out_url = f"{origin}/api/v1/auth/sign-out"
    sign_out = request(sign_out_url, method="POST", bearer=access_token)
    if sign_out.status < 200 or sign_out.status >= 300:
        raise RuntimeError(f"Sign-out returned HTTP {sign_out.status}")
    print("ok: smoke session signed out")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="Public SideBySide origin")
    parser.add_argument(
        "--expected-revision",
        required=True,
        help="Exact revision expected from both Web and API deployment identities",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        check(args.base_url, args.expected_revision)
    except RuntimeError as exc:
        print(f"deployment smoke failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
