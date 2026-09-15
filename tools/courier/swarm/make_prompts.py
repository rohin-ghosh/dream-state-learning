#!/usr/bin/env python3
"""Generate the Fable parent prompt files that gpu/orch_r110_claude_broker.py consumes.

Contract (from the broker): tools/courier/swarm/prompts/<branch>.md must be EXACTLY the fixed parent template
extracted from PARENTING_BATTLE_PLAN_v4 (the '> You are the parent of a young model.' block) with the four fields
[GAME], [STYLE], [NUDGING], [FOCUS] substituted; <branch>.fields.json carries schema ORCH_R114_HEAD_FIELDS_V1 with
prompt_sha256 = sha256 of the .md bytes and fields incl. REFLECTION {mode, max_new_tokens}. The head parent may
change only STYLE, FOCUS, REFLECTION and optional NEXT_GUIDANCE; GAME and NUDGING
are fixed for the life. NEXT_GUIDANCE is metadata, not a change to the v4 template.

Usage: python3 tools/courier/swarm/make_prompts.py [--fields prompts/current_fields.json] [--out prompts/]
Re-running with an edited fields file rewrites the .md and .fields.json for every branch listed.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
import os
PLAN = Path(os.environ.get('MAKE_PROMPTS_PLAN', str(REPO / 'research_notes/PARENTING_BATTLE_PLAN_v4_2026-09-15.md')))

DEFAULT_FIELDS = {
    'F1': {
        'GAME': 'route worlds (READ/ROUTE over a 61-world graph)',
        'STYLE': 'training-wheels, supportive',
        'NUDGING': 'You do not suggest routes, methods or hypotheses.',
        'FOCUS': 'Watch whether it reads its records before it routes; ask what it noticed there, never what to do',
        'REFLECTION': {'mode': 'short', 'max_new_tokens': 1024},
    },
    'F2': {
        'GAME': 'math word problems with an exact checker',
        'STYLE': 'creative, supportive',
        'NUDGING': "You may say 'try a different route', 'think through several different solutions', 'run a different chain of thought' — never the answer itself.",
        'FOCUS': 'Watch whether its checks change anything; ask what it expected before it computed',
        'REFLECTION': {'mode': 'long', 'max_new_tokens': 3072},
    },
    'F3': {
        'GAME': 'small coding tasks with unit tests',
        'STYLE': 'harsh-critical of the reasoning, never personal',
        'NUDGING': 'You do not suggest methods, tests or hypotheses.',
        'FOCUS': 'Watch whether it runs a test or only reasons about one; ask what it can and cannot tell without running it',
        'REFLECTION': {'mode': 'long', 'max_new_tokens': 3072},
    },
    'F4': {
        'GAME': 'a grid hill-climbing puzzle',
        'STYLE': 'training-wheels, harsh',
        'NUDGING': 'You do not suggest moves, methods or hypotheses.',
        'FOCUS': 'Watch whether it re-plans after a bad move or repeats it; ask what surprised it',
        'REFLECTION': {'mode': 'short', 'max_new_tokens': 1024},
    },
}


def fixed_parent_template(plan_path=PLAN):
    text = plan_path.read_text()
    start = text.index('> You are the parent of a young model.')
    lines = []
    for line in text[start:].splitlines():
        if not line.startswith('> '):
            break
        lines.append(line[2:])
    return '\n'.join(lines)


def render(fields, template):
    required = {'GAME', 'STYLE', 'NUDGING', 'FOCUS', 'REFLECTION'}
    assert required <= set(fields) <= required | {'NEXT_GUIDANCE'}, 'field keys'
    guidance = fields.get('NEXT_GUIDANCE', '')
    assert isinstance(guidance, str) and len(guidance.encode()) <= 1024, 'next guidance bounds'
    for key in ('GAME', 'STYLE', 'NUDGING', 'FOCUS'):
        assert isinstance(fields[key], str) and '[' not in fields[key], key
    r = fields['REFLECTION']
    assert r['mode'] in ('short', 'long') and 1 <= int(r['max_new_tokens']) <= 8192, 'reflection bounds'
    return re.sub(r'\[(GAME|STYLE|NUDGING|FOCUS)\]', lambda m: fields[m.group(1)], template)


LANE_CAP_NOTE = {
    90: ("Lane contract: the broker discards unread any reply whose guidance exceeds ninety words, so keep each "
         "turn to one intervention of at most sixty words; tag must be ADD, STOP or SHIFT; intervention_class may "
         "contain only letters, digits, spaces, hyphens and underscores."),
    200: ("Lane contract: the broker discards unread any reply whose guidance exceeds two hundred words, so keep "
          "each turn well under that; tag must be ADD, STOP or SHIFT; intervention_class may contain only letters, "
          "digits, spaces, hyphens and underscores; no code, backticks or function definitions in guidance."),
}


def lane_word_cap(game):
    """The broker (gpu/orch_r110_claude_broker.py adapt_plan) caps route/grid guidance at 90 words, others at 200."""
    return 90 if re.search(r'route|grid', game, re.I) else 200


def with_lane_caps(guidance, game):
    """Append the lane's cap note to NEXT_GUIDANCE (once), trimming the head's text so the total stays <= 1024 bytes.
    Added 2026-09-15 18:50Z after 11 of 17 F3 sub-parent replies in 15 minutes were discarded for length."""
    note = LANE_CAP_NOTE[lane_word_cap(game)]
    guidance = guidance or ''
    if note in guidance:
        return guidance
    guidance = guidance.split('Lane contract:')[0].rstrip()  # replace any earlier wording of the note
    room = 1024 - len(note.encode()) - 2
    head = guidance.encode()[:max(room, 0)].decode('utf-8', 'ignore').rstrip()
    return (head + '\n\n' if head else '') + note


def apply_head_update(current, update, template):
    allowed = {'STYLE', 'FOCUS', 'REFLECTION', 'NEXT_GUIDANCE'}
    assert set(update) <= allowed, 'head may not change fixed fields'
    result = dict(current)
    result.update(update)
    reflection = result['REFLECTION']
    assert set(reflection) == {'mode', 'max_new_tokens'}, 'reflection fields'
    assert type(reflection['max_new_tokens']) is int, 'integer reflection budget'
    render(result, template)
    assert all(result[key] == current[key] for key in ('GAME', 'NUDGING')), 'fixed life fields'
    return result


def verify_binding(prompt_text, template):
    pattern = re.escape(template)
    for name in ('GAME', 'STYLE', 'NUDGING', 'FOCUS'):
        pattern = pattern.replace(re.escape('[' + name + ']'), '(?P<' + name + '>.*?)')
    return re.fullmatch(pattern, prompt_text.rstrip('\n'), flags=re.DOTALL) is not None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fields', type=Path, default=HERE / 'prompts/current_fields.json')
    ap.add_argument('--out', type=Path, default=HERE / 'prompts')
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    fields_all = json.loads(args.fields.read_text()) if args.fields.exists() else DEFAULT_FIELDS
    template = fixed_parent_template()
    for branch, fields in fields_all.items():
        prompt = render(fields, template)
        assert verify_binding(prompt, template), branch + ' binding'
        md = args.out / (branch + '.md')
        md.write_bytes(prompt.encode())  # no trailing newline: rendered == prompt.rstrip('\n')
        settings = {'schema': 'ORCH_R114_HEAD_FIELDS_V1',
                    'prompt_sha256': hashlib.sha256(prompt.encode()).hexdigest(),
                    'fields': fields}
        (args.out / (branch + '.fields.json')).write_text(json.dumps(settings, indent=1, sort_keys=True) + '\n')
        print(branch, len(prompt.encode()), 'bytes', settings['prompt_sha256'][:12])
    if not args.fields.exists():
        args.fields.write_text(json.dumps(fields_all, indent=1, sort_keys=True) + '\n')
    print('template sha256', hashlib.sha256(template.encode()).hexdigest()[:16])


if __name__ == '__main__':
    main()
