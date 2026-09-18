"""Source-bound decision observations; no decisions, filters or controls applied."""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re

from source_adapter import OWN, from_observer, load_prior_audit, prior_watcher_receipt, sha


DECISIONS = ('CONTINUE', 'BRANCH', 'STOP', 'AMBIGUOUS', 'UNKNOWN')
ACTION_PATTERNS = {
    'CONTINUE': re.compile(r'\b(?:I|we)\s+(?:(?:will|shall)\s+|(?:have\s+)?decided\s+to\s+|choose\s+to\s+|plan\s+to\s+)(?:now\s+)?(?:continue\b|keep\s+(?:working|exploring|trying|searching|testing)\b)', re.I),
    'BRANCH': re.compile(r'\b(?:I|we)\s+(?:(?:will|shall)\s+|(?:have\s+)?decided\s+to\s+|choose\s+to\s+|plan\s+to\s+)(?:now\s+)?(?:branch\b|(?:switch|move(?:\s+on)?|change)\s+to\s+(?:(?:a|the)\s+)?(?:new\s+|another\s+|different\s+)?(?:scene|direction|object|problem|approach|method)\b|try\s+(?:a\s+)?(?:new|different)\s+(?:scene|direction|approach|method)\b)', re.I),
    'STOP': re.compile(r'\b(?:(?:I|we)\s+(?:(?:will|shall)\s+|(?:have\s+)?decided\s+to\s+|choose\s+to\s+|plan\s+to\s+)(?:now\s+)?stop\b|I\s+am\s+done\b|we\s+are\s+done\b)', re.I),
}
EXHAUSTION = re.compile(r'\b(?:(?:I|we)\s+have\s+(?:exhausted\s+(?:this|the|all|my|our)\s+(?:scene|direction|options|ideas|approaches)|no\s+more\s+(?:ideas|options|approaches))|there\s+is\s+nothing\s+(?:new|else)\s+to\s+try|(?:this|the)\s+(?:scene|direction)\s+is\s+exhausted)\b', re.I)
DISCOVERY = re.compile(r'\b(?:I|we)\s+(?:have\s+)?(?:found|discovered)\s+(?:a\s+|another\s+|some\s+)?new\s+(?:idea|approach|result|direction|solution)\b', re.I)
OBJECT_LINE = re.compile(r'^\s*(Scene|Object|Direction|Task|Contest(?:_id)?)\s*(?::|=)\s*([^\r\n]{1,160})\s*$', re.I | re.M)
NUMERIC_SCENE = re.compile(r'^\s*Scene\s+(\d{1,6})\s*:?[ \t]*$', re.I | re.M)


def digest_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def mask_scaffolding(text):
    masked = list(text)
    fence = None
    offset = 0
    for line in text.splitlines(keepends=True):
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        inside = fence is not None
        if marker:
            if fence is None:
                fence = marker.group(1)[0]
            elif marker.group(1)[0] == fence:
                fence = None
        if inside or marker or re.match(r'^\s*>', line):
            for position in range(offset, offset + len(line)):
                if masked[position] not in '\r\n':
                    masked[position] = ' '
        offset += len(line)
    view = ''.join(masked)
    for match in re.finditer(r'"[^"\n]*"|“[^”\n]*”|(?<!\w)\x27[^\x27\n]*\x27(?!\w)|‘[^’\n]*’', view):
        masked[match.start():match.end()] = ' ' * (match.end() - match.start())
    return ''.join(masked), fence is not None


def declarations(text):
    if len(text) > 65536:
        return dict(decision='UNKNOWN', action_candidates=[], claims=[], reason='scan_bound_exceeded',
                    question_units=0, unterminated_fence=False)
    view, unfinished = mask_scaffolding(text)
    claims = []
    questions = 0
    for unit in re.finditer(r'[^\n.!?？]+[.!?？]?', view):
        content = unit.group()
        if content.rstrip().endswith(('?', '？')):
            questions += 1
            continue
        if re.match(r'^\s*Continue thinking\s*:', content, re.I):
            continue
        if re.match(r'^\s*(?:If|Suppose|Imagine|Perhaps|Maybe)\b', content, re.I):
            continue
        if re.search(r'\b(?:if|unless)\b', content, re.I):
            continue
        for kind, pattern in {**ACTION_PATTERNS, 'EXHAUSTION': EXHAUSTION, 'DISCOVERY': DISCOVERY}.items():
            direct = re.sub(r'^\s*(?:(?:Intentions?|Plan|Ready to act)\s*:\s*|(?:Now|Therefore),?\s*)', '', content, flags=re.I)
            if kind != 'EXHAUSTION' and not re.match(r'^\s*(?:I|we)\b', direct, re.I):
                continue
            for match in pattern.finditer(content):
                if kind == 'STOP' and re.match(r'\s+(?:saying|claiming|assuming|worrying|describing|using)\b', content[match.end():], re.I):
                    continue
                start, end = unit.start() + match.start(), unit.start() + match.end()
                claims.append(dict(kind=kind, start=start, end=end, span_sha256=digest_text(text[start:end]),
                                   basis='SELF_DECLARED_NOT_VERIFIED'))
        explicit = re.match(r'^\s*Decision\s*:\s*(continue|branch|stop)\s*[.!]?\s*$', content, re.I)
        if explicit:
            start, end = unit.start() + explicit.start(1), unit.start() + explicit.end(1)
            claims.append(dict(kind=explicit.group(1).upper(), start=start, end=end,
                               span_sha256=digest_text(text[start:end]), basis='SELF_DECLARED_NOT_VERIFIED'))
    actions = sorted({claim['kind'] for claim in claims if claim['kind'] in ACTION_PATTERNS})
    decision = actions[0] if len(actions) == 1 else 'AMBIGUOUS' if actions else 'UNKNOWN'
    return dict(decision=decision, action_candidates=actions, claims=claims,
                reason='explicit_source_claims_only' if actions else 'no_unambiguous_declaration',
                question_units=questions, unterminated_fence=unfinished)


def object_metadata(text):
    view, unused = mask_scaffolding(text)
    markers = []
    def add(kind, value, start, end, basis):
        kind = {'task': 'object', 'contest': 'scene', 'contest_id': 'scene'}.get(kind.lower(), kind.lower())
        normalized = ' '.join(value.strip().casefold().split())
        if not normalized:
            return
        markers.append(dict(kind=kind, identifier_sha256=digest_text(kind + '\0' + normalized),
                            span_sha256=digest_text(text[start:end]), start=start, end=end, basis=basis))
    for match in OBJECT_LINE.finditer(view):
        add(match.group(1), match.group(2), match.start(), match.end(), 'CHILD_AUTHORED_LABEL')
    for match in NUMERIC_SCENE.finditer(view):
        add('scene', match.group(1), match.start(), match.end(), 'CHILD_AUTHORED_LABEL')
    stripped = text.strip()
    fenced = re.fullmatch(r'```(?:json)?\s*\n([\s\S]*?)\n```', stripped, re.I)
    candidate = fenced.group(1) if fenced else stripped
    try:
        payload = json.loads(candidate)
    except (ValueError, RecursionError):
        payload = None
    objects = payload if isinstance(payload, list) else payload.get('actions', [payload]) if isinstance(payload, dict) else []
    if isinstance(objects, list):
        for item in objects[:100]:
            if not isinstance(item, dict):
                continue
            for key, kind in (('scene_id', 'scene'), ('contest_id', 'scene'), ('object_id', 'object'), ('direction_id', 'direction')):
                value = item.get(key)
                if isinstance(value, (str, int)) and len(str(value)) <= 160:
                    add(kind, str(value), 0, len(text), 'CHILD_AUTHORED_STRUCTURED_SELECTION')
    return markers


def compare_objects(previous, current):
    comparisons = {}
    for kind in ('scene', 'object', 'direction'):
        before = sorted({item['identifier_sha256'] for item in previous if item['kind'] == kind})
        after = sorted({item['identifier_sha256'] for item in current if item['kind'] == kind})
        relation = ('AMBIGUOUS' if len(before) > 1 or len(after) > 1 else
                    'UNKNOWN' if not before or not after else 'SAME_LABEL' if before == after else 'CHANGED_LABEL')
        comparisons[kind] = dict(previous_identifier_sha256=before, current_identifier_sha256=after, relation=relation)
    relations = {entry['relation'] for entry in comparisons.values()}
    inferred = ('AMBIGUOUS' if 'AMBIGUOUS' in relations else 'BRANCH' if 'CHANGED_LABEL' in relations else
                'CONTINUE' if 'SAME_LABEL' in relations else 'UNKNOWN')
    return dict(dimensions=comparisons, inferred_decision=inferred,
                basis='OBSERVED_CHILD_LABELS_NOT_ENVIRONMENT_CONFIRMATION')


def analyze(evidence, label):
    prior, dependency_sha = load_prior_audit()
    bound = prior.analyze(evidence, label)
    responses = {event['source_sha256']: event for event in evidence['events'] if event['kind'] == 'RESPONSE'}
    rows = []
    for row in bound['rows']:
        if row['stage'] not in ('THINK', 'ACT'):
            continue
        text = responses[row['source_sha256']]['document']['response']['raw']
        rows.append(dict(cycle=row['cycle'], stage=row['stage'], segment=row['segment'],
                         source_sha256=row['source_sha256'], target_sha256=row['target_sha256'],
                         request=row['request'], response=row['response'], commit=row['commit'],
                         stage_record=row['stage_record'], console_reply=row['console_reply'],
                         declaration=declarations(text), objects=object_metadata(text)))
    cycles = []
    previous_act = None
    previous_cycle_rows = []
    for cycle in bound['cycles']:
        selected = sorted([row for row in rows if row['cycle'] == cycle['cycle'] and not row['console_reply']],
                          key=lambda row: row['response']['index'])
        acts = [row for row in selected if row['stage'] == 'ACT']
        declared = [row for row in selected if row['declaration']['action_candidates']]
        final_declared = declared[-1]['declaration']['decision'] if declared else 'UNKNOWN'
        exhausted = [row for row in selected if any(claim['kind'] == 'EXHAUSTION' for claim in row['declaration']['claims'])]
        discoveries = [row for row in selected if any(claim['kind'] == 'DISCOVERY' for claim in row['declaration']['claims'])]
        transition = compare_objects([], [])
        relation = 'UNKNOWN'
        behavior = []
        if exhausted:
            behavior.append(dict(label='DECLARES_EXHAUSTION', basis='SELF_DECLARED_ONLY',
                                 response_indices=[row['response']['index'] for row in exhausted]))
        if final_declared == 'CONTINUE' and discoveries:
            behavior.append(dict(label='KEEPS_DISCOVERING', basis='SELF_DECLARED_CONTINUING_AND_DISCOVERY_NOT_VERIFIED',
                                 response_indices=[row['response']['index'] for row in discoveries]))
        if len(acts) == 1 and previous_act is not None:
            action = acts[0]
            transition = compare_objects(previous_act['objects'], action['objects'])
            transition['previous_response'] = previous_act['response']
            transition['current_response'] = action['response']
            relation = 'EXACT_REPEAT' if action['target_sha256'] == previous_act['target_sha256'] else 'DIFFERENT_BYTES_NOT_NOVELTY'
            stop_context = [row for row in previous_cycle_rows + selected
                            if row['response']['index'] < action['response']['index']
                            and any(claim['kind'] in ('STOP', 'EXHAUSTION') for claim in row['declaration']['claims'])]
            if stop_context and transition['inferred_decision'] == 'BRANCH':
                behavior.append(dict(label='STOPS_CHANGES', basis='DECLARED_STOP_OR_EXHAUSTION_THEN_OBSERVED_LABEL_CHANGE',
                                     response_indices=[row['response']['index'] for row in stop_context] + [action['response']['index']]))
            elif stop_context and relation == 'EXACT_REPEAT' and transition['inferred_decision'] != 'AMBIGUOUS':
                behavior.append(dict(label='STOPS_REPEATS', basis='DECLARED_STOP_OR_EXHAUSTION_THEN_EXACT_ACT_BYTES_REPEAT',
                                     response_indices=[row['response']['index'] for row in stop_context] + [action['response']['index']]))
        elif len(acts) > 1:
            transition['inferred_decision'] = 'AMBIGUOUS'
        if not behavior:
            behavior.append(dict(label='UNKNOWN', basis='INSUFFICIENT_EVIDENCE_NOT_FORCED_CHOICE', response_indices=[]))
        cycles.append(dict(cycle=cycle['cycle'], status=cycle['status'], complete=cycle['complete'],
                           think_responses=cycle['think_responses'], act_responses=len(acts),
                           self_declared_decision=final_declared,
                           declaration_source=declared[-1]['response'] if declared else None,
                           declaration_history=[dict(response=row['response'], stage=row['stage'], decision=row['declaration']['decision']) for row in declared],
                           declared_exhaustion=bool(exhausted), discovery_claim_present=bool(discoveries),
                           inferred_transition=transition, act_byte_relation=relation,
                           behavior_observations=behavior, verified_discovery='UNKNOWN_NO_ENVIRONMENT_NOVELTY_PROOF',
                           act_response_indices=[row['response']['index'] for row in acts],
                           normal_think_act_pairs=[pair for pair in bound['pairs'] if pair['cycle'] == cycle['cycle']]))
        previous_act = acts[0] if len(acts) == 1 else None
        previous_cycle_rows = selected
    return dict(schema='R228_DECISION_OBSERVATION_V1', label=label,
                metric_kind='CONSERVATIVE_OBSERVATION_HEURISTIC_NOT_A_POLICY',
                observed_utc=bound['observed_utc'], head=bound['head'], input_sha256=prior.digest(evidence),
                r227_binding_module_sha256=dependency_sha, rows=rows, cycles=cycles,
                counts={name: sum(cycle['self_declared_decision'] == name for cycle in cycles) for name in DECISIONS},
                counts_by_status={status: {name: sum(cycle['status'] == status and cycle['self_declared_decision'] == name for cycle in cycles)
                                           for name in DECISIONS} for status in ('COMPLETE', 'SLEEP_PENDING', 'OPEN')},
                uncertainties=bound['uncertainties'], raw_unknowns_preserved_privately=True,
                private_transcripts_included=False, semantic_exclusions=False, questions_are_failures=False,
                absence_of_act_means_stop=False, correctness_or_causality_claimed=False,
                learner_or_parent_changes=False, remote_calls=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', choices=('C2', 'P7'), required=True)
    arguments = parser.parse_args()
    os.umask(0o077)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    evidence, provenance = from_observer(arguments.label)
    report = analyze(evidence, arguments.label)
    report['source_observer'] = provenance
    report['decision_module_sha256'] = sha(Path(__file__).read_bytes())
    private = OWN / 'private'
    private.mkdir(mode=0o700, exist_ok=True)
    with (private / f'{arguments.label}_SOURCE_{stamp}.json').open('x') as output:
        json.dump(evidence, output, ensure_ascii=False)
    path = OWN / f'{arguments.label}_DECISIONS_{stamp}.json'
    with path.open('x') as output:
        json.dump(report, output, sort_keys=True, indent=2)
        output.write('\n')
    watcher = prior_watcher_receipt()
    with (OWN / f'R227_WATCHER_{stamp}.json').open('x') as output:
        json.dump(watcher, output, sort_keys=True, indent=2)
        output.write('\n')
    print(json.dumps(dict(report=path.name, sha256=sha(path.read_bytes()), observed_utc=report['observed_utc'],
                          counts=report['counts'], prior_watcher=watcher), indent=2))


if __name__ == '__main__':
    main()
