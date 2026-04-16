#!/usr/bin/env python3
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

SCRIPT_PATH = Path(__file__).resolve()
WORKSPACE_DIR = SCRIPT_PATH.parents[3]
DEFAULT_ENV_PATHS = [
    os.environ.get("HERMES_GATEWAY_ENV_FILE", "").strip(),
    str(WORKSPACE_DIR / ".env.hermes-gateway"),
    str(Path.home() / ".openclaw" / "hermes-gateway.env"),
]
TERMINAL_STATUSES = {"completed", "needs_review", "blocked", "failed", "cancelled"}


class ConfigError(RuntimeError):
    pass


class HttpError(RuntimeError):
    pass


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def load_env_file(path: str) -> dict[str, str]:
    result: dict[str, str] = {}
    if not path:
        return result
    env_path = Path(path).expanduser()
    if not env_path.exists():
        return result
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = strip_quotes(value.strip())
    return result


def load_config(require_token: bool = True) -> dict[str, str]:
    data: dict[str, str] = {}
    for candidate in DEFAULT_ENV_PATHS:
        data.update(load_env_file(candidate))
    for key in [
        "HERMES_GATEWAY_URL",
        "HERMES_GATEWAY_TOKEN",
        "HERMES_GATEWAY_POLL_SECONDS",
        "HERMES_GATEWAY_TIMEOUT_SECONDS",
        "HERMES_COMMAND_REQUESTER_AGENT",
        "HERMES_COMMAND_REQUESTER_USER",
        "HERMES_COMMAND_SESSION_KEY",
    ]:
        value = os.environ.get(key)
        if value:
            data[key] = value
    if not data.get("HERMES_GATEWAY_URL"):
        raise ConfigError(
            "Missing Hermes gateway URL. Expected HERMES_GATEWAY_URL in env or in "
            f"{WORKSPACE_DIR / '.env.hermes-gateway'}"
        )
    if require_token and not data.get("HERMES_GATEWAY_TOKEN"):
        raise ConfigError(
            "Missing Hermes gateway token. Expected HERMES_GATEWAY_TOKEN in env or in "
            f"{WORKSPACE_DIR / '.env.hermes-gateway'}"
        )
    data.setdefault("HERMES_GATEWAY_POLL_SECONDS", "5")
    data.setdefault("HERMES_GATEWAY_TIMEOUT_SECONDS", "1800")
    data.setdefault("HERMES_COMMAND_REQUESTER_AGENT", "command")
    return data


def normalize_url(url: str) -> str:
    return url.rstrip("/")


def request_json(config: dict[str, str], method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None
    headers = {
        "Accept": "application/json",
    }
    if config.get("HERMES_GATEWAY_TOKEN"):
        headers["Authorization"] = f"Bearer {config['HERMES_GATEWAY_TOKEN']}"
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(normalize_url(config["HERMES_GATEWAY_URL"]) + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"status": exc.code, "body": raw}
        raise HttpError(json.dumps(parsed, indent=2)) from exc
    except urllib.error.URLError as exc:
        raise HttpError(str(exc.reason)) from exc


def read_json_input(path: str | None) -> dict[str, Any]:
    if not path or path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path).read_text()
    if not raw.strip():
        raise ValueError("request JSON is empty")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("request JSON must be an object")
    return parsed


def enrich_request(payload: dict[str, Any], config: dict[str, str]) -> dict[str, Any]:
    request = deepcopy(payload)
    request.setdefault("schemaVersion", "hermes.task.v1")
    if request.get("schemaVersion") != "hermes.task.v1":
        raise ValueError("schemaVersion must be hermes.task.v1")
    agent = request.get("agent")
    if agent not in {"marketing", "development", "operations"}:
        raise ValueError("agent must be marketing, development, or operations")
    objective = str(request.get("objective", "")).strip()
    if not objective:
        raise ValueError("objective is required")
    request["objective"] = objective
    command = request.setdefault("command", {})
    command.setdefault("flowId", make_id("flow"))
    command.setdefault("taskId", make_id("task"))
    command.setdefault("requestedAt", now_iso())
    requester = command.setdefault("requester", {})
    requester.setdefault("agent", config.get("HERMES_COMMAND_REQUESTER_AGENT", "command"))
    if config.get("HERMES_COMMAND_REQUESTER_USER"):
        requester.setdefault("user", config["HERMES_COMMAND_REQUESTER_USER"])
    if config.get("HERMES_COMMAND_SESSION_KEY"):
        requester.setdefault("sessionKey", config["HERMES_COMMAND_SESSION_KEY"])
    request.setdefault("priority", "medium")
    request.setdefault("context", {"summary": ""})
    request.setdefault("assets", [])
    request.setdefault("constraints", [])
    request.setdefault("successCriteria", [])
    request.setdefault("approval", {"required": False, "kind": None})
    return request


def print_json(payload: dict[str, Any], pretty: bool) -> None:
    if pretty:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False))


def submit_request(config: dict[str, str], request_payload: dict[str, Any]) -> dict[str, Any]:
    request_payload = enrich_request(request_payload, config)
    return request_json(config, "POST", "/v1/tasks", request_payload)


def get_status(config: dict[str, str], remote_task_id: str) -> dict[str, Any]:
    return request_json(config, "GET", f"/v1/tasks/{remote_task_id}")


def wait_for_task(config: dict[str, str], remote_task_id: str, poll_seconds: float, timeout_seconds: float) -> dict[str, Any]:
    started = time.time()
    latest = get_status(config, remote_task_id)
    while latest.get("status") not in TERMINAL_STATUSES:
        if time.time() - started > timeout_seconds:
            raise TimeoutError(f"Timed out waiting for task {remote_task_id}")
        time.sleep(poll_seconds)
        latest = get_status(config, remote_task_id)
    return latest


def handle_submit(args: argparse.Namespace, config: dict[str, str]) -> int:
    request_payload = read_json_input(args.request)
    response = submit_request(config, request_payload)
    print_json(response, args.pretty)
    return 0


def handle_run(args: argparse.Namespace, config: dict[str, str]) -> int:
    request_payload = read_json_input(args.request)
    accepted = submit_request(config, request_payload)
    remote_task_id = accepted["remoteTaskId"]
    if not args.wait:
        print_json(accepted, args.pretty)
        return 0
    final = wait_for_task(config, remote_task_id, args.poll_seconds, args.timeout_seconds)
    if args.include_accepted:
        print_json({"accepted": accepted, "final": final}, args.pretty)
    else:
        print_json(final, args.pretty)
    return 0


def handle_status(args: argparse.Namespace, config: dict[str, str]) -> int:
    print_json(get_status(config, args.remote_task_id), args.pretty)
    return 0


def handle_wait(args: argparse.Namespace, config: dict[str, str]) -> int:
    final = wait_for_task(config, args.remote_task_id, args.poll_seconds, args.timeout_seconds)
    print_json(final, args.pretty)
    return 0


def handle_cancel(args: argparse.Namespace, config: dict[str, str]) -> int:
    result = request_json(config, "POST", f"/v1/tasks/{args.remote_task_id}/cancel")
    print_json(result, args.pretty)
    return 0


def handle_health(args: argparse.Namespace, config: dict[str, str]) -> int:
    result = request_json(config, "GET", "/v1/health")
    print_json(result, args.pretty)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Hermes worker gateway client")
    parser.set_defaults(pretty=True)
    parser.add_argument("--compact", action="store_true", help="print compact JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    submit_p = subparsers.add_parser("submit", help="submit a task request")
    submit_p.add_argument("request", nargs="?", help="path to request JSON, or read stdin if omitted")
    submit_p.set_defaults(func=handle_submit)

    run_p = subparsers.add_parser("run", help="submit a task and optionally wait")
    run_p.add_argument("request", nargs="?", help="path to request JSON, or read stdin if omitted")
    run_p.add_argument("--wait", action="store_true", help="wait for terminal status")
    run_p.add_argument("--include-accepted", action="store_true", help="include accepted response along with final status")
    run_p.add_argument("--poll-seconds", type=float, default=None, help="poll interval while waiting")
    run_p.add_argument("--timeout-seconds", type=float, default=None, help="max wait time")
    run_p.set_defaults(func=handle_run)

    status_p = subparsers.add_parser("status", help="fetch task status")
    status_p.add_argument("remote_task_id")
    status_p.set_defaults(func=handle_status)

    wait_p = subparsers.add_parser("wait", help="wait for a task to finish")
    wait_p.add_argument("remote_task_id")
    wait_p.add_argument("--poll-seconds", type=float, default=None, help="poll interval while waiting")
    wait_p.add_argument("--timeout-seconds", type=float, default=None, help="max wait time")
    wait_p.set_defaults(func=handle_wait)

    cancel_p = subparsers.add_parser("cancel", help="cancel a running task")
    cancel_p.add_argument("remote_task_id")
    cancel_p.set_defaults(func=handle_cancel)

    health_p = subparsers.add_parser("health", help="check gateway health")
    health_p.set_defaults(func=handle_health)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    args.pretty = not args.compact
    try:
        config = load_config(require_token=args.command != "health")
        default_poll = float(config.get("HERMES_GATEWAY_POLL_SECONDS", "5"))
        default_timeout = float(config.get("HERMES_GATEWAY_TIMEOUT_SECONDS", "1800"))
        if hasattr(args, "poll_seconds") and args.poll_seconds is None:
            args.poll_seconds = default_poll
        if hasattr(args, "timeout_seconds") and args.timeout_seconds is None:
            args.timeout_seconds = default_timeout
        return args.func(args, config)
    except (ConfigError, HttpError, ValueError, TimeoutError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
