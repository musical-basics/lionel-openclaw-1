#!/usr/bin/env python3
import json
import os
import re
import secrets
import signal
import subprocess
import threading
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from uuid import uuid4

BASE_DIR = Path(os.environ.get("HERMES_WORKER_GATEWAY_BASE", "/home/hermes/worker-gateway"))
STATE_DIR = Path(os.environ.get("HERMES_WORKER_GATEWAY_STATE_DIR", str(BASE_DIR / "state")))
STATE_FILE = STATE_DIR / "tasks.json"
PORT = int(os.environ.get("HERMES_WORKER_GATEWAY_PORT", "8788"))
AUTH_TOKEN = os.environ.get("HERMES_WORKER_GATEWAY_TOKEN", "")
EXPLICIT_HOST = os.environ.get("HERMES_WORKER_GATEWAY_HOST", "").strip()
DEFAULT_MAX_TURNS = os.environ.get("HERMES_WORKER_MAX_TURNS", "20")

PROFILE_BIN = {
    "marketing": "/home/hermes/.local/bin/marketing",
    "development": "/home/hermes/.local/bin/development",
    "operations": "/home/hermes/.local/bin/operations",
}
PROFILE_WORKSPACE = {
    name: f"/home/hermes/.hermes/profiles/{name}/workspace" for name in PROFILE_BIN
}

TASK_LOCK = threading.Lock()
TASKS: dict[str, dict[str, Any]] = {}
RUNNING_PROCS: dict[str, subprocess.Popen[str]] = {}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def detect_tailscale_ip() -> str:
    if EXPLICIT_HOST:
        return EXPLICIT_HOST
    try:
        result = subprocess.run(
            ["tailscale", "ip", "-4"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if line:
                return line
    except Exception:
        pass
    return "127.0.0.1"


BIND_HOST = detect_tailscale_ip()


def load_tasks() -> dict[str, dict[str, Any]]:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_tasks() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(TASKS, indent=2, sort_keys=True))
    tmp.replace(STATE_FILE)


def clean_text(text: str) -> str:
    lines = []
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if stripped.startswith("session_id:"):
            continue
        if "⚕ Hermes" in stripped:
            continue
        if all(ch in "╭╮╰╯─│┌┐└┘├┤┬┴┼" for ch in stripped):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


SECTION_MAP = {
    "STATUS": "status",
    "SUMMARY": "summary",
    "WHAT I DID": "whatIDid",
    "ARTIFACTS": "artifacts",
    "EVIDENCE": "evidence",
    "BLOCKERS": "blockers",
    "NEEDS FROM COMMAND": "needsFromCommand",
    "RECOMMENDED NEXT STEP": "recommendedNextStep",
}
SECTION_RE = re.compile(r"^(STATUS|SUMMARY|WHAT I DID|ARTIFACTS|EVIDENCE|BLOCKERS|NEEDS FROM COMMAND|RECOMMENDED NEXT STEP):\s*(.*)$")


def parse_worker_output(text: str) -> dict[str, Any]:
    matches = list(re.finditer(r"(?m)^STATUS:\s*", text))
    if len(matches) > 1:
        text = text[matches[-1].start():].strip()

    result: dict[str, Any] = {
        "status": None,
        "summary": "",
        "whatIDid": [],
        "artifacts": [],
        "evidence": [],
        "blockers": [],
        "needsFromCommand": [],
        "recommendedNextStep": "",
        "rawText": text,
    }
    current: str | None = None
    buckets: dict[str, list[str]] = {k: [] for k in SECTION_MAP.values()}

    for line in text.splitlines():
        match = SECTION_RE.match(line.strip())
        if match:
            current = SECTION_MAP[match.group(1)]
            remainder = match.group(2).strip()
            if remainder:
                buckets[current].append(remainder)
            continue
        if current:
            buckets[current].append(line.rstrip())

    if buckets["status"]:
        status_text = " ".join(buckets["status"]).strip().lower()
        result["status"] = status_text.split()[0]

    def normalize_list(values: list[str]) -> list[str]:
        out = []
        for value in values:
            item = value.strip()
            if not item:
                continue
            item = re.sub(r"^[-*]\s*", "", item)
            if item and item.lower() != "none":
                out.append(item)
        return out

    def normalize_text(values: list[str]) -> str:
        cleaned = [v.strip() for v in values if v.strip()]
        return "\n".join(cleaned).strip()

    result["summary"] = normalize_text(buckets["summary"])
    result["whatIDid"] = normalize_list(buckets["whatIDid"])
    result["artifacts"] = normalize_list(buckets["artifacts"])
    result["evidence"] = normalize_list(buckets["evidence"])
    result["blockers"] = normalize_list(buckets["blockers"])
    result["needsFromCommand"] = normalize_list(buckets["needsFromCommand"])
    result["recommendedNextStep"] = normalize_text(buckets["recommendedNextStep"])

    if not result["summary"]:
        result["summary"] = text[:800].strip()
    if not result["status"]:
        result["status"] = "completed" if result["summary"] else "failed"

    result["artifactsStructured"] = [
        {"type": "note", "label": f"artifact-{i+1}", "value": value}
        for i, value in enumerate(result["artifacts"])
    ]
    return result


def build_prompt(task: dict[str, Any]) -> str:
    request = task["request"]
    context = request.get("context", {})
    assets = request.get("assets", [])
    constraints = request.get("constraints", [])
    success = request.get("successCriteria", [])
    deadline = request.get("deadline") or "none"
    lines = [
        f"You are the Hermes {request['agent']} worker.",
        "Do the work within your domain only.",
        "You are not the final approver, do not send, publish, spend money, change pricing, or touch prohibited systems.",
        "",
        f"OBJECTIVE: {request.get('objective', '').strip()}",
        f"PRIORITY: {request.get('priority', 'medium')}",
        f"DEADLINE: {deadline}",
        "",
        "CONTEXT:",
        context.get("summary", ""),
    ]
    for note in context.get("notes", []) or []:
        lines.append(f"- {note}")
    if context.get("project"):
        lines.append(f"Project: {context['project']}")
    lines.extend(["", "ASSETS:"])
    if assets:
        for asset in assets:
            lines.append(f"- [{asset.get('type', 'note')}] {asset.get('label', 'asset')}: {asset.get('value', '')}")
    else:
        lines.append("- none")
    lines.extend(["", "CONSTRAINTS:"])
    if constraints:
        for item in constraints:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "SUCCESS CRITERIA:"])
    if success:
        for item in success:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "Return exactly these sections and nothing before STATUS:",
            "STATUS: completed | blocked | needs_review | failed",
            "SUMMARY:",
            "WHAT I DID:",
            "- bullet list",
            "ARTIFACTS:",
            "- bullet list",
            "EVIDENCE:",
            "- bullet list",
            "BLOCKERS:",
            "- bullet list or none",
            "NEEDS FROM COMMAND:",
            "- bullet list or none",
            "RECOMMENDED NEXT STEP:",
            "single next action",
            "",
            "If the task cannot proceed because something is missing, use STATUS: blocked.",
            "If the output is ready but should be reviewed before use, use STATUS: needs_review.",
        ]
    )
    return "\n".join(lines).strip()


def callback_payload(task: dict[str, Any], event: str) -> dict[str, Any]:
    return {
        "schemaVersion": "hermes.task.event.v1",
        "event": event,
        "remoteTaskId": task["remoteTaskId"],
        "status": task["status"],
        "agent": task["agent"],
        "currentStep": task.get("currentStep", ""),
        "updatedAt": task["updatedAt"],
        "echo": task["echo"],
        "result": task.get("result"),
        "waiting": task.get("waiting"),
        "error": task.get("error"),
    }


def post_callback(task: dict[str, Any], event: str) -> None:
    callback = task["request"].get("callback") or {}
    url = callback.get("url")
    events = callback.get("events") or []
    if not url or event not in events:
        return
    body = json.dumps(callback_payload(task, event)).encode("utf-8")
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    secret = callback.get("secret")
    if secret:
        req.add_header("X-Hermes-Callback-Secret", secret)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        with TASK_LOCK:
            task.setdefault("callbackLog", []).append({"event": event, "ok": True, "at": now_iso()})
            save_tasks()
    except Exception as exc:
        with TASK_LOCK:
            task.setdefault("callbackLog", []).append({"event": event, "ok": False, "at": now_iso(), "error": str(exc)})
            save_tasks()


def update_task(remote_task_id: str, **changes: Any) -> dict[str, Any]:
    with TASK_LOCK:
        task = TASKS[remote_task_id]
        task.update(changes)
        task["updatedAt"] = now_iso()
        save_tasks()
        return json.loads(json.dumps(task))


def task_status_payload(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": "hermes.task.status.v1",
        "remoteTaskId": task["remoteTaskId"],
        "status": task["status"],
        "agent": task["agent"],
        "currentStep": task.get("currentStep"),
        "progress": task.get("progress"),
        "waiting": task.get("waiting"),
        "blockers": task.get("blockers", []),
        "artifacts": task.get("artifacts", []),
        "result": task.get("result"),
        "error": task.get("error"),
        "updatedAt": task["updatedAt"],
        "echo": task["echo"],
    }


def health_payload() -> dict[str, Any]:
    workers = {}
    for name, path in PROFILE_BIN.items():
        auth_path = Path(f"/home/hermes/.hermes/profiles/{name}/auth.json")
        if Path(path).exists() and auth_path.exists():
            workers[name] = "ready"
        elif Path(path).exists():
            workers[name] = "degraded"
        else:
            workers[name] = "down"
    overall = "ok" if all(v == "ready" for v in workers.values()) else "degraded"
    return {
        "schemaVersion": "hermes.health.v1",
        "status": overall,
        "workers": workers,
        "time": now_iso(),
        "bindHost": BIND_HOST,
        "port": PORT,
    }


def error_payload(code: str, message: str, retryable: bool = False) -> dict[str, Any]:
    return {
        "schemaVersion": "hermes.error.v1",
        "error": {"code": code, "message": message, "retryable": retryable},
    }


def run_task(remote_task_id: str) -> None:
    with TASK_LOCK:
        task = TASKS.get(remote_task_id)
        if not task:
            return
        task["status"] = "running"
        task["currentStep"] = "executing_worker"
        task["updatedAt"] = now_iso()
        save_tasks()
        request = json.loads(json.dumps(task["request"]))
    prompt = build_prompt(task)
    wrapper = PROFILE_BIN[request["agent"]]
    cmd = [wrapper, "chat", "-Q", "--source", "tool", "--max-turns", DEFAULT_MAX_TURNS, "-q", prompt]
    env = os.environ.copy()
    env.update({"NO_COLOR": "1", "TERM": "dumb", "CI": "1"})
    proc: subprocess.Popen[str] | None = None
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=PROFILE_WORKSPACE[request["agent"]],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )
        RUNNING_PROCS[remote_task_id] = proc
        stdout, _ = proc.communicate()
        cleaned = clean_text(stdout)
        parsed = parse_worker_output(cleaned)
        status = parsed["status"]
        if status not in {"completed", "blocked", "needs_review", "failed"}:
            status = "completed" if proc.returncode == 0 else "failed"
        payload = {
            "summary": parsed["summary"],
            "whatIDid": parsed["whatIDid"],
            "artifacts": parsed["artifactsStructured"],
            "evidence": parsed["evidence"],
            "blockers": parsed["blockers"],
            "needsFromCommand": parsed["needsFromCommand"],
            "recommendedNextStep": parsed["recommendedNextStep"],
            "rawText": parsed["rawText"],
        }
        updated = update_task(
            remote_task_id,
            status=status,
            currentStep="done",
            waiting=None,
            blockers=payload["blockers"],
            artifacts=payload["artifacts"],
            result=payload,
            error=None if proc.returncode == 0 else {"code": "WORKER_EXIT_NONZERO", "message": f"worker exited {proc.returncode}", "retryable": False},
        )
        post_callback(updated, status)
    except Exception as exc:
        tb = traceback.format_exc(limit=6)
        updated = update_task(
            remote_task_id,
            status="failed",
            currentStep="failed",
            error={"code": "INTERNAL_ERROR", "message": str(exc), "retryable": False, "trace": tb},
        )
        post_callback(updated, "failed")
    finally:
        RUNNING_PROCS.pop(remote_task_id, None)


class Handler(BaseHTTPRequestHandler):
    server_version = "HermesWorkerGateway/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[{now_iso()}] {self.client_address[0]} {fmt % args}")

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def _authorized(self) -> bool:
        if not AUTH_TOKEN:
            return True
        header = self.headers.get("Authorization", "")
        return header == f"Bearer {AUTH_TOKEN}"

    def do_GET(self) -> None:
        if self.path == "/v1/health":
            self._json(200, health_payload())
            return
        if not self._authorized():
            self._json(401, error_payload("UNAUTHORIZED", "missing or invalid bearer token"))
            return
        match = re.fullmatch(r"/v1/tasks/([^/]+)", self.path)
        if match:
            remote_task_id = match.group(1)
            with TASK_LOCK:
                task = TASKS.get(remote_task_id)
            if not task:
                self._json(404, error_payload("TASK_NOT_FOUND", "task not found"))
                return
            self._json(200, task_status_payload(task))
            return
        self._json(404, error_payload("TASK_NOT_FOUND", "unknown endpoint"))

    def do_POST(self) -> None:
        if not self._authorized():
            self._json(401, error_payload("UNAUTHORIZED", "missing or invalid bearer token"))
            return
        if self.path == "/v1/tasks":
            try:
                payload = self._read_json()
            except Exception:
                self._json(400, error_payload("INVALID_SCHEMA", "request body must be valid JSON"))
                return
            if payload.get("schemaVersion") != "hermes.task.v1":
                self._json(400, error_payload("INVALID_SCHEMA", "schemaVersion must be hermes.task.v1"))
                return
            agent = payload.get("agent")
            if agent not in PROFILE_BIN:
                self._json(400, error_payload("INVALID_AGENT", "agent must be one of marketing, development, operations"))
                return
            command = payload.get("command") or {}
            flow_id = command.get("flowId")
            task_id = command.get("taskId")
            if not flow_id or not task_id:
                self._json(400, error_payload("INVALID_SCHEMA", "command.flowId and command.taskId are required"))
                return
            deduped_task: dict[str, Any] | None = None
            with TASK_LOCK:
                for task in TASKS.values():
                    echo = task.get("echo") or {}
                    if echo.get("flowId") == flow_id and echo.get("taskId") == task_id:
                        deduped_task = task
                        break
                if deduped_task is None:
                    remote_task_id = f"hermes_{uuid4().hex}"
                    created_at = now_iso()
                    task = {
                        "remoteTaskId": remote_task_id,
                        "status": "accepted",
                        "agent": agent,
                        "currentStep": "accepted",
                        "progress": None,
                        "waiting": None,
                        "blockers": [],
                        "artifacts": [],
                        "result": None,
                        "error": None,
                        "createdAt": created_at,
                        "updatedAt": created_at,
                        "echo": {"flowId": flow_id, "taskId": task_id},
                        "request": payload,
                        "callbackLog": [],
                    }
                    TASKS[remote_task_id] = task
                    save_tasks()
                    threading.Thread(target=run_task, args=(remote_task_id,), daemon=True).start()
                    response = {
                        "schemaVersion": "hermes.task.accepted.v1",
                        "remoteTaskId": remote_task_id,
                        "status": "accepted",
                        "agent": agent,
                        "deduped": False,
                        "acceptedAt": created_at,
                        "echo": task["echo"],
                    }
                else:
                    response = {
                        "schemaVersion": "hermes.task.accepted.v1",
                        "remoteTaskId": deduped_task["remoteTaskId"],
                        "status": "accepted",
                        "agent": deduped_task["agent"],
                        "deduped": True,
                        "acceptedAt": deduped_task["createdAt"],
                        "echo": deduped_task["echo"],
                    }
            self._json(202, response)
            return
        match = re.fullmatch(r"/v1/tasks/([^/]+)/cancel", self.path)
        if match:
            remote_task_id = match.group(1)
            with TASK_LOCK:
                task = TASKS.get(remote_task_id)
                if not task:
                    self._json(404, error_payload("TASK_NOT_FOUND", "task not found"))
                    return
                if task["status"] in {"completed", "failed", "cancelled", "blocked", "needs_review"}:
                    self._json(409, error_payload("TASK_ALREADY_FINISHED", "task already finished"))
                    return
                task["status"] = "cancelled"
                task["currentStep"] = "cancelled"
                task["updatedAt"] = now_iso()
                save_tasks()
                proc = RUNNING_PROCS.get(remote_task_id)
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                except Exception:
                    pass
            post_callback(task, "cancelled")
            self._json(
                200,
                {
                    "schemaVersion": "hermes.task.cancel.v1",
                    "remoteTaskId": remote_task_id,
                    "status": "cancelled",
                    "cancelledAt": task["updatedAt"],
                    "echo": task["echo"],
                },
            )
            return
        self._json(404, error_payload("TASK_NOT_FOUND", "unknown endpoint"))


def main() -> None:
    global TASKS
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    TASKS = load_tasks()
    server = ThreadingHTTPServer((BIND_HOST, PORT), Handler)
    print(f"Hermes worker gateway listening on http://{BIND_HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        for proc in list(RUNNING_PROCS.values()):
            if proc.poll() is None:
                try:
                    proc.send_signal(signal.SIGTERM)
                except Exception:
                    pass
        server.server_close()


if __name__ == "__main__":
    main()
