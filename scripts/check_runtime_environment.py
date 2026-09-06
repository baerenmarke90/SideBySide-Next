#!/usr/bin/env python3
"""Verify critical SideBySide runtime environment before and after Compose recreation."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

CRITICAL_RUNTIME_KEYS = (
    "SBS_ACCOUNT_DELETION_INSTANCE_ID",
    "SBS_ENVIRONMENT",
    "SBS_DEPLOYMENT",
    "SBS_PUBLIC_BASE_URL",
    "SBS_CURSOR_SIGNING_KEY",
)
DOTENV_AUTHORITATIVE_KEYS = (
    "SBS_ACCOUNT_DELETION_INSTANCE_ID",
    "SBS_ENVIRONMENT",
    "SBS_PUBLIC_BASE_URL",
    "SBS_CURSOR_SIGNING_KEY",
)
PROFILE_RUNTIME_SERVICES = {
    "self-hosted": frozenset({"api", "worker", "demo-init"}),
    "cloud": frozenset({"cloud-api", "cloud-worker"}),
}


class RuntimeEnvironmentError(RuntimeError):
    """The intended, rendered, or running runtime configuration is inconsistent."""


def parse_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise RuntimeEnvironmentError(f"could not read env file: {path}") from exc

    for lineno, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise RuntimeEnvironmentError(f"{path}:{lineno}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            raise RuntimeEnvironmentError(f"{path}:{lineno}: empty variable name")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def service_environment(service: dict[str, Any]) -> dict[str, str]:
    environment = service.get("environment") or {}
    if isinstance(environment, dict):
        return {str(key): "" if value is None else str(value) for key, value in environment.items()}
    if isinstance(environment, list):
        values: dict[str, str] = {}
        for item in environment:
            if not isinstance(item, str):
                continue
            key, separator, value = item.partition("=")
            values[key] = value if separator else ""
        return values
    raise RuntimeEnvironmentError("Compose rendered an unsupported service environment shape")


def rendered_runtime_environments(
    config: dict[str, Any], service_names: frozenset[str] | None = None
) -> dict[str, dict[str, str]]:
    services = config.get("services")
    if not isinstance(services, dict):
        raise RuntimeEnvironmentError("Compose config does not contain a services object")

    rendered: dict[str, dict[str, str]] = {}
    for name, service in services.items():
        if not isinstance(name, str) or not isinstance(service, dict):
            continue
        if service_names is not None and name not in service_names:
            continue
        environment = service_environment(service)
        if any(key in environment for key in CRITICAL_RUNTIME_KEYS):
            rendered[name] = environment
    return rendered


def check_dotenv_to_rendered(
    dotenv: dict[str, str], rendered: dict[str, dict[str, str]]
) -> list[str]:
    problems: list[str] = []

    dotenv_is_production = dotenv.get("SBS_ENVIRONMENT") == "production"
    rendered_is_production = any(
        environment.get("SBS_ENVIRONMENT") == "production" for environment in rendered.values()
    )
    if dotenv_is_production and not dotenv.get("SBS_ACCOUNT_DELETION_INSTANCE_ID"):
        problems.append(
            "production env file must set non-empty SBS_ACCOUNT_DELETION_INSTANCE_ID"
        )
    if rendered_is_production and any(
        not environment.get("SBS_ACCOUNT_DELETION_INSTANCE_ID")
        for environment in rendered.values()
        if environment.get("SBS_ENVIRONMENT") == "production"
    ):
        problems.append(
            "rendered Production runtime must set non-empty SBS_ACCOUNT_DELETION_INSTANCE_ID"
        )

    for key in DOTENV_AUTHORITATIVE_KEYS:
        intended = dotenv.get(key)
        if not intended:
            continue
        consumers = [name for name, environment in rendered.items() if key in environment]
        if not consumers:
            problems.append(f"no rendered service consumes {key}")
            continue
        for service_name in consumers:
            if rendered[service_name].get(key) != intended:
                problems.append(
                    f"rendered service {service_name} differs from env file for {key}"
                )

    return problems


def parse_container_environment(values: list[str]) -> dict[str, str]:
    environment: dict[str, str] = {}
    for item in values:
        key, separator, value = item.partition("=")
        environment[key] = value if separator else ""
    return environment


def check_rendered_to_running(
    rendered: dict[str, dict[str, str]],
    running: dict[str, dict[str, str] | None],
) -> list[str]:
    problems: list[str] = []
    for service_name, expected_environment in rendered.items():
        actual_environment = running.get(service_name)
        if actual_environment is None:
            problems.append(f"service {service_name} has no inspectable Compose container")
            continue
        for key in CRITICAL_RUNTIME_KEYS:
            if key not in expected_environment:
                continue
            if actual_environment.get(key) != expected_environment.get(key):
                problems.append(f"running service {service_name} differs from rendered Compose for {key}")
    return problems


def run_command(command: list[str]) -> str:
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True)
    except OSError as exc:
        raise RuntimeEnvironmentError(f"could not execute {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or "command failed"
        raise RuntimeEnvironmentError(f"{' '.join(command[:3])} failed: {detail}") from exc
    return completed.stdout


def compose_prefix(args: argparse.Namespace) -> list[str]:
    command = ["docker", "compose"]
    if args.project_name:
        command.extend(["--project-name", args.project_name])
    if args.profile:
        command.extend(["--profile", args.profile])
    command.extend(["--env-file", str(args.env_file)])
    if args.compose_file:
        command.extend(["--file", str(args.compose_file)])
    return command


def load_rendered_config(args: argparse.Namespace) -> dict[str, Any]:
    output = run_command([*compose_prefix(args), "config", "--format", "json"])
    try:
        config = json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeEnvironmentError("docker compose config did not return valid JSON") from exc
    if not isinstance(config, dict):
        raise RuntimeEnvironmentError("docker compose config returned an unexpected JSON value")
    return config


def inspect_running_services(
    args: argparse.Namespace, rendered: dict[str, dict[str, str]]
) -> dict[str, dict[str, str] | None]:
    running: dict[str, dict[str, str] | None] = {}
    prefix = compose_prefix(args)
    for service_name in rendered:
        container_ids = [
            value.strip()
            for value in run_command([*prefix, "ps", "-aq", service_name]).splitlines()
            if value.strip()
        ]
        if len(container_ids) != 1:
            running[service_name] = None
            continue
        output = run_command(
            ["docker", "inspect", "--format", "{{json .Config.Env}}", container_ids[0]]
        )
        try:
            values = json.loads(output)
        except json.JSONDecodeError as exc:
            raise RuntimeEnvironmentError(
                f"docker inspect returned invalid environment JSON for {service_name}"
            ) from exc
        if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
            raise RuntimeEnvironmentError(
                f"docker inspect returned an unexpected environment for {service_name}"
            )
        running[service_name] = parse_container_environment(values)
    return running


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--compose-file", type=Path)
    parser.add_argument("--profile", default="self-hosted")
    parser.add_argument("--project-name")
    parser.add_argument(
        "--check-running",
        action="store_true",
        help="also compare rendered critical settings with existing Compose containers",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        dotenv = parse_dotenv(args.env_file)
        selected_services = PROFILE_RUNTIME_SERVICES.get(args.profile)
        rendered = rendered_runtime_environments(
            load_rendered_config(args), service_names=selected_services
        )
        problems = check_dotenv_to_rendered(dotenv, rendered)
        if args.check_running:
            running = inspect_running_services(args, rendered)
            problems.extend(check_rendered_to_running(rendered, running))
    except RuntimeEnvironmentError as exc:
        print(f"runtime environment check failed: {exc}", file=sys.stderr)
        return 2

    if problems:
        print("runtime environment check failed:", file=sys.stderr)
        for problem in problems:
            print(f"- {problem}", file=sys.stderr)
        return 1

    scope = "rendered and running" if args.check_running else "rendered"
    print(f"runtime environment check passed ({scope} configuration)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
