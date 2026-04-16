#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CONFIG_PATH = Path('/home/openclaw/.openclaw/openclaw.json')
MAIN_WORKSPACE = Path('/home/openclaw/.openclaw/workspace')
VALID_AGENTS = ('marketing', 'development', 'operations')
SECTION_KEYS = [
    ('status', 'STATUS'),
    ('summary', 'SUMMARY'),
    ('whatIDid', 'WHAT I DID'),
    ('artifacts', 'ARTIFACTS'),
    ('evidence', 'EVIDENCE'),
    ('blockers', 'BLOCKERS'),
    ('needsFromCommand', 'NEEDS FROM COMMAND'),
    ('recommendedNextStep', 'RECOMMENDED NEXT STEP'),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Local same-VPS Hermes worker client via OpenClaw agents')
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('list', help='List configured local worker agents')

    run_parser = sub.add_parser('run', help='Run a worker task from JSON on stdin')
    run_parser.add_argument('--timeout-seconds', type=int, default=None)

    return parser.parse_args()


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def command_list() -> int:
    cfg = load_config()
    agents = {entry.get('id'): entry for entry in cfg.get('agents', {}).get('list', [])}
    payload = []
    for agent_id in VALID_AGENTS:
        entry = agents.get(agent_id, {})
        payload.append({
            'agentId': agent_id,
            'configured': bool(entry),
            'workspace': entry.get('workspace'),
            'agentDir': entry.get('agentDir'),
        })
    print(json.dumps({'workers': payload}, indent=2))
    return 0


def build_prompt(request: dict) -> str:
    agent = request['agent']
    objective = request['objective'].strip()
    priority = request.get('priority', 'normal')
    context = request.get('context') or {}
    assets = request.get('assets') or []
    constraints = request.get('constraints') or []
    success = request.get('successCriteria') or []

    lines = [
        'You are receiving a delegated task from Command.',
        f'Work as the {agent} worker.',
        'Return plain text with exactly these headings:',
        'STATUS:',
        'SUMMARY:',
        'WHAT I DID:',
        'ARTIFACTS:',
        'EVIDENCE:',
        'BLOCKERS:',
        'NEEDS FROM COMMAND:',
        'RECOMMENDED NEXT STEP:',
        '',
        'Use one of these STATUS values when possible: completed, needs_review, blocked, failed, cancelled.',
        '',
        'TASK',
        f'Objective: {objective}',
        f'Priority: {priority}',
    ]

    summary = context.get('summary')
    project = context.get('project')
    notes = context.get('notes') or []

    if summary:
        lines.extend(['', 'Context summary:', str(summary)])
    if project:
        lines.extend(['', f'Project: {project}'])
    if notes:
        lines.append('')
        lines.append('Notes:')
        lines.extend(f'- {item}' for item in notes)
    if assets:
        lines.append('')
        lines.append('Assets:')
        lines.extend(f'- {item}' for item in assets)
    if constraints:
        lines.append('')
        lines.append('Constraints:')
        lines.extend(f'- {item}' for item in constraints)
    if success:
        lines.append('')
        lines.append('Success criteria:')
        lines.extend(f'- {item}' for item in success)

    lines.extend([
        '',
        f'Use the shared project workspace at {MAIN_WORKSPACE} when the task needs real project files, unless the request explicitly says otherwise.',
    ])
    return '\n'.join(lines)


def extract_json_blob(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find('{')
        end = text.rfind('}')
        if start == -1 or end == -1 or end <= start:
            raise
        return json.loads(text[start:end + 1])


def strip_reply_tag(text: str) -> str:
    return re.sub(r'^\s*\[\[[^\]]+\]\]\s*', '', text, count=1)


def extract_text(payload: dict) -> str:
    result = payload.get('result') or {}
    payloads = result.get('payloads') or []
    for item in payloads:
        text = item.get('text')
        if text:
            return strip_reply_tag(text).strip()
    meta_text = (result.get('meta') or {}).get('finalAssistantVisibleText')
    if meta_text:
        return strip_reply_tag(meta_text).strip()
    raise RuntimeError('No text payload returned by worker')


def parse_sections(text: str) -> dict:
    matches = []
    for key, heading in SECTION_KEYS:
        pattern = re.compile(rf'(?mi)^\s*{re.escape(heading)}\s*:\s*')
        match = pattern.search(text)
        if match:
            matches.append((match.start(), match.end(), key))
    matches.sort()
    parsed = {key: '' for key, _heading in SECTION_KEYS}
    if not matches:
        parsed['summary'] = text.strip()
        return parsed
    for index, (start, end, key) in enumerate(matches):
        next_start = matches[index + 1][0] if index + 1 < len(matches) else len(text)
        parsed[key] = text[end:next_start].strip()
    return parsed


def normalize_status(parsed: dict, payload: dict) -> str:
    raw = (parsed.get('status') or payload.get('summary') or '').strip().lower()
    raw = raw.replace(' ', '_')
    if raw in {'completed', 'needs_review', 'blocked', 'failed', 'cancelled'}:
        return raw
    if raw == 'ok':
        return 'completed'
    return raw or 'unknown'


def run_worker(request: dict, timeout_seconds: int | None) -> dict:
    agent = request.get('agent')
    if agent not in VALID_AGENTS:
        raise SystemExit(f'agent must be one of: {", ".join(VALID_AGENTS)}')
    if not (request.get('objective') or '').strip():
        raise SystemExit('objective is required')

    prompt = build_prompt(request)
    cmd = ['openclaw', 'agent', '--agent', agent, '--message', prompt, '--json']
    if timeout_seconds:
        cmd.extend(['--timeout', str(timeout_seconds)])

    proc = subprocess.run(cmd, cwd=str(MAIN_WORKSPACE), capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'openclaw agent failed')

    payload = extract_json_blob(proc.stdout)
    text = extract_text(payload)
    parsed = parse_sections(text)
    return {
        'transport': 'openclaw-local',
        'workerAgentId': agent,
        'status': normalize_status(parsed, payload),
        'summary': parsed.get('summary') or payload.get('summary'),
        'parsed': parsed,
        'rawText': text,
        'runId': payload.get('runId'),
        'sessionId': (((payload.get('result') or {}).get('meta') or {}).get('agentMeta') or {}).get('sessionId'),
    }


def command_run(timeout_seconds: int | None) -> int:
    request = json.loads(sys.stdin.read())
    result = run_worker(request, timeout_seconds=timeout_seconds)
    print(json.dumps(result, indent=2))
    return 0


def main() -> int:
    args = parse_args()
    if args.command == 'list':
        return command_list()
    if args.command == 'run':
        return command_run(args.timeout_seconds)
    raise SystemExit(f'unknown command: {args.command}')


if __name__ == '__main__':
    sys.exit(main())
