#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

CONFIG_PATH = Path('/home/openclaw/.openclaw/openclaw.json')
MAIN_WORKSPACE = Path('/home/openclaw/.openclaw/workspace')
REFERENCE_DIR = Path('/home/openclaw/.openclaw/workspace/skills/hermes-local-dispatch/references')
SCHEMA_PATH = REFERENCE_DIR / 'worker-brief.schema.json'
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
ROLE_DEFAULTS = {
    'marketing': {
        'focus': 'Optimize for clarity, differentiation, and conversion. Return concrete copy or positioning, not vague theory.',
        'defaultConstraints': [
            'Do not invent pricing, customer proof, or product facts.',
            'Prefer concise, premium language over hype or fluff.',
        ],
        'defaultSuccessCriteria': [
            'Tie the recommendation to the likely business outcome.',
            'Return usable draft language when the task is copy-related.',
        ],
        'defaultRequiredOutput': [
            'Lead with the recommended angle or option first.',
            'Make the commercial logic easy for Command to judge quickly.',
        ],
    },
    'development': {
        'focus': 'Optimize for correctness, root-cause clarity, and the smallest safe fix. Verify before claiming success.',
        'defaultConstraints': [
            'Prefer the smallest safe direct fix first.',
            'Do not claim something is fixed without evidence.',
        ],
        'defaultSuccessCriteria': [
            'State root cause clearly if one is found.',
            'Return verification evidence or the strongest practical check run.',
        ],
        'defaultRequiredOutput': [
            'List files touched or inspected when relevant.',
            'Make the recommended next technical step explicit.',
        ],
    },
    'operations': {
        'focus': 'Optimize for execution clarity, sequencing, and blocker visibility. Make the next action obvious.',
        'defaultConstraints': [
            'Keep the plan concise and operational, not bloated.',
            'Surface blockers early instead of hiding uncertainty.',
        ],
        'defaultSuccessCriteria': [
            'Make priorities and dependencies clear.',
            'Return a next action that Command can use immediately.',
        ],
        'defaultRequiredOutput': [
            'Put the next immediate action near the top.',
            'Separate blockers from routine follow-up items.',
        ],
    },
}
ROLE_TEMPLATES = {
    'marketing': {
        'agent': 'marketing',
        'objective': 'Write 3 concise hero hooks for the masterclass waitlist page.',
        'deliverable': 'Three hook options plus one recommended CTA.',
        'priority': 'high',
        'businessContext': 'Masterclass revenue matters more than extra polish right now.',
        'context': {
            'summary': 'Keep it premium, direct, and non-fluffy.',
            'project': 'ultimate-pianist-masterclass',
            'background': 'Lionel prefers short, practical messaging work.',
            'decisionContext': 'Prioritize conversion clarity over cleverness.',
            'notes': ['Do not invent pricing.', 'A $1 VIP waitlist exists.'],
        },
        'files': [],
        'assets': [],
        'constraints': ['Draft only.', 'No fake proof or invented scarcity.'],
        'successCriteria': ['3 distinct options.', 'Each hook is short enough for a hero section.'],
        'nonGoals': ['No long-form sales page rewrite.'],
        'requiredOutput': ['Lead with the recommended option first.'],
        'questionsToAnswer': ['Which angle is strongest for conversion?'],
    },
    'development': {
        'agent': 'development',
        'objective': 'Fix the checkout bug on mobile Safari.',
        'deliverable': 'Verified patch plus root-cause summary and file list.',
        'priority': 'high',
        'businessContext': 'Checkout breakage directly hurts revenue, so conversion protection matters more than polish.',
        'context': {
            'summary': 'Users can reach checkout, but final submit fails on iPhone Safari.',
            'project': 'dreamplay-shop-2',
            'background': 'Lionel prefers the smallest safe fix first.',
            'decisionContext': 'Do not redesign checkout unless the root cause truly requires it.',
            'notes': ['DreamPlay One and DreamPlay Pro must stay clearly distinct.', 'Gold is Pro-only.'],
        },
        'files': ['dreamplay-shop-2/app/checkout/page.tsx'],
        'assets': [],
        'constraints': ['Smallest safe fix first.', 'Do not change product tier logic.'],
        'successCriteria': ['Root cause identified.', 'Patch applied.', 'Evidence returned.'],
        'nonGoals': ['No unrelated refactor.', 'No visual redesign.'],
        'requiredOutput': ['State root cause clearly.', 'List files touched.', 'Include verification evidence.'],
        'questionsToAnswer': ['What exactly caused the break?', 'What is the smallest safe fix?'],
    },
    'operations': {
        'agent': 'operations',
        'objective': 'Turn the launch into a prioritized execution checklist.',
        'deliverable': 'Ordered checklist with blockers and next action.',
        'priority': 'high',
        'businessContext': 'Execution clarity matters because launch timing and cash pressure matter right now.',
        'context': {
            'summary': 'One concrete next step at a time.',
            'project': 'ultimate-pianist-masterclass',
            'background': 'Lionel prefers concise status summaries over verbose planning.',
            'decisionContext': 'Focus on sequence and execution, not brainstorming.',
            'notes': [],
        },
        'files': [],
        'assets': [],
        'constraints': ['Keep it concise.', 'Prioritize execution over brainstorming.'],
        'successCriteria': ['Checklist is prioritized.', 'Dependencies are clear.'],
        'nonGoals': ['No generic productivity advice.'],
        'requiredOutput': ['Put the next immediate action first.'],
        'questionsToAnswer': ['What should happen next?', 'What is blocked?'],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Local same-VPS Hermes worker client via OpenClaw agents')
    sub = parser.add_subparsers(dest='command', required=True)

    sub.add_parser('list', help='List configured local worker agents')
    sub.add_parser('schema', help='Print the machine-readable worker brief schema')

    template_parser = sub.add_parser('template', help='Print a starter JSON worker brief template')
    template_parser.add_argument('agent', choices=VALID_AGENTS)

    run_parser = sub.add_parser('run', help='Run a worker task from JSON on stdin')
    run_parser.add_argument('--timeout-seconds', type=int, default=None)

    return parser.parse_args()


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def normalize_text(value) -> str:
    if value is None:
        return ''
    return str(value).strip()


def normalize_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        raise SystemExit('list-like fields must be a string or array of strings')
    result = []
    for item in value:
        text = normalize_text(item)
        if text and text not in result:
            result.append(text)
    return result


def merge_unique(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    for group in groups:
        for item in group:
            if item not in merged:
                merged.append(item)
    return merged


def normalize_request(request: dict) -> dict:
    if not isinstance(request, dict):
        raise SystemExit('request must be a JSON object')
    agent = normalize_text(request.get('agent'))
    if agent not in VALID_AGENTS:
        raise SystemExit(f'agent must be one of: {", ".join(VALID_AGENTS)}')
    objective = normalize_text(request.get('objective'))
    if not objective:
        raise SystemExit('objective is required')
    priority = normalize_text(request.get('priority') or 'normal').lower()
    if priority not in {'low', 'normal', 'high', 'urgent'}:
        raise SystemExit('priority must be one of: low, normal, high, urgent')

    context = request.get('context') or {}
    if not isinstance(context, dict):
        raise SystemExit('context must be an object when provided')

    normalized_context = {
        'summary': normalize_text(context.get('summary')),
        'project': normalize_text(context.get('project')),
        'background': normalize_text(context.get('background')),
        'decisionContext': normalize_text(context.get('decisionContext')),
        'notes': normalize_list(context.get('notes')),
    }

    return {
        'agent': agent,
        'objective': objective,
        'deliverable': normalize_text(request.get('deliverable')),
        'priority': priority,
        'businessContext': normalize_text(request.get('businessContext')),
        'context': normalized_context,
        'files': normalize_list(request.get('files')),
        'assets': normalize_list(request.get('assets')),
        'constraints': normalize_list(request.get('constraints')),
        'successCriteria': normalize_list(request.get('successCriteria')),
        'nonGoals': normalize_list(request.get('nonGoals')),
        'requiredOutput': normalize_list(request.get('requiredOutput')),
        'questionsToAnswer': normalize_list(request.get('questionsToAnswer')),
    }


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


def command_schema() -> int:
    print(json.dumps(load_schema(), indent=2))
    return 0


def command_template(agent: str) -> int:
    print(json.dumps(deepcopy(ROLE_TEMPLATES[agent]), indent=2))
    return 0


def build_prompt(request: dict) -> str:
    request = normalize_request(request)
    agent = request['agent']
    defaults = ROLE_DEFAULTS[agent]
    context = request['context']
    constraints = merge_unique(request['constraints'], defaults['defaultConstraints'])
    success = merge_unique(request['successCriteria'], defaults['defaultSuccessCriteria'])
    required_output = merge_unique(request['requiredOutput'], defaults['defaultRequiredOutput'])

    lines = [
        'You are receiving a delegated task from Command.',
        f'Work as the {agent} worker.',
        f'Role focus: {defaults["focus"]}',
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
        'If critical information is missing, say so under BLOCKERS and NEEDS FROM COMMAND instead of guessing.',
        '',
        'TASK',
        f'Objective: {request["objective"]}',
        f'Priority: {request["priority"]}',
    ]

    if request['deliverable']:
        lines.extend(['', f'Deliverable: {request["deliverable"]}'])
    if request['businessContext']:
        lines.extend(['', 'Business context:', request['businessContext']])
    if context['summary']:
        lines.extend(['', 'Context summary:', context['summary']])
    if context['project']:
        lines.extend(['', f'Project: {context["project"]}'])
    if context['background']:
        lines.extend(['', 'Background:', context['background']])
    if context['decisionContext']:
        lines.extend(['', 'Decision context:', context['decisionContext']])
    if context['notes']:
        lines.append('')
        lines.append('Notes:')
        lines.extend(f'- {item}' for item in context['notes'])
    if request['files']:
        lines.append('')
        lines.append('Relevant files to inspect first:')
        lines.extend(f'- {item}' for item in request['files'])
    if request['assets']:
        lines.append('')
        lines.append('Related assets or references:')
        lines.extend(f'- {item}' for item in request['assets'])
    if constraints:
        lines.append('')
        lines.append('Constraints and guardrails:')
        lines.extend(f'- {item}' for item in constraints)
    if success:
        lines.append('')
        lines.append('Success criteria:')
        lines.extend(f'- {item}' for item in success)
    if request['nonGoals']:
        lines.append('')
        lines.append('Non-goals:')
        lines.extend(f'- {item}' for item in request['nonGoals'])
    if request['questionsToAnswer']:
        lines.append('')
        lines.append('Questions to answer if possible:')
        lines.extend(f'- {item}' for item in request['questionsToAnswer'])
    if required_output:
        lines.append('')
        lines.append('Output emphasis for Command:')
        lines.extend(f'- {item}' for item in required_output)

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
    normalized = normalize_request(request)
    prompt = build_prompt(normalized)
    cmd = ['openclaw', 'agent', '--agent', normalized['agent'], '--message', prompt, '--json']
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
        'workerAgentId': normalized['agent'],
        'status': normalize_status(parsed, payload),
        'summary': parsed.get('summary') or payload.get('summary'),
        'parsed': parsed,
        'rawText': text,
        'runId': payload.get('runId'),
        'sessionId': (((payload.get('result') or {}).get('meta') or {}).get('agentMeta') or {}).get('sessionId'),
        'request': normalized,
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
    if args.command == 'schema':
        return command_schema()
    if args.command == 'template':
        return command_template(args.agent)
    if args.command == 'run':
        return command_run(args.timeout_seconds)
    raise SystemExit(f'unknown command: {args.command}')


if __name__ == '__main__':
    sys.exit(main())
