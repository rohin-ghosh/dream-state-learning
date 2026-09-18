"""Read-only R233 cycle metrics and convergence alerts; never training filters."""

import argparse
import fcntl
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from difflib import SequenceMatcher
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import time


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CORRECTION = REPO / 'research_loop/workers/rohin232_correction_audit_20260918'
INTENTION = REPO / 'research_loop/workers/rohin227_intention_audit_20260918'
WRAPPERS = {'a40r_ssh.sh', 'ovx_ssh.sh', 'ovx2_ssh.sh', 'ovx3_ssh.sh', 'ovx4_ssh.sh'}
READER_SOURCE = (CORRECTION / 'reader.py').read_text()
SOURCE_BINDINGS = {str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in (CORRECTION / 'reader.py', CORRECTION / 'audit.py', INTENTION / 'audit.py',
                               HERE / 'movement.py')}


def module(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(result)
    return result


correction = module('r233_correction_metrics', CORRECTION / 'audit.py')
intention = module('r233_intention_metrics', INTENTION / 'audit.py')


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_suffix('.next')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    os.replace(temporary, path)


def summarize(evidence, label):
    frames = correction.frames(evidence)
    inboxes = {row['event_id']: row for row in evidence['records'] if row['kind'] == 'INBOX'}
    seen_sources, new_guidance = set(), set()
    prior_text, prior_cycle, repeat_run, unguided_run = None, None, 0, 0
    acts = []
    for frame in frames:
        request, response = frame['request'], frame['response']
        for event in request['external']:
            identity = event['event_id'] + ':' + event['source_sha256']
            if identity not in seen_sources:
                inbox = inboxes.get(event['event_id'])
                if event['actor'] == 'parent' and inbox and inbox['index'] < request['index']:
                    new_guidance.add(identity)
                seen_sources.add(identity)
        if frame['stage'] != 'ACT':
            continue
        text = response['text']
        normalized = ' '.join(text.casefold().split())
        similarity = SequenceMatcher(None, prior_text, normalized, autojunk=False).ratio() if prior_text else None
        cycle = request['cycle']
        repeated = similarity is not None and similarity >= .92
        consecutive_cycle = prior_cycle is not None and cycle == prior_cycle + 1
        repeat_run = repeat_run + 1 if repeated and consecutive_cycle else 1
        unguided_run = unguided_run + 1 if repeated and consecutive_cycle and not new_guidance else 0
        classification = intention.intention_act_classification(text)
        glyphs = len(re.findall(r'[\u3400-\u9fff\uff01-\uff60]', text))
        loop = bool(re.search(r'\b(\w+)(?:\s+\1){4,}\b', text, re.I))
        acts.append(dict(cycle=cycle, response=correction.ref(response), request=correction.ref(request),
            response_time_unix=response['time_unix'], text_sha256=hashlib.sha256(text.encode()).hexdigest(),
            classification=classification, cjk_fullwidth_character_count=glyphs,
            language='SCRIPT_COUNT_NOT_LANGUAGE_OR_QUALITY_PROOF', consecutive_word_loop=loop,
            similarity_to_prior_act=similarity, repeat_run_cycles=repeat_run,
            new_guidance_sources=sorted(new_guidance), new_guidance_count=len(new_guidance),
            unguided_repeat_transitions=unguided_run,
            alert_three_cycles_unguided=repeat_run >= 3 and unguided_run >= 2,
            parent_adjustment_required=repeat_run >= 2 or loop or glyphs > 0
                or classification['classification'] == 'INTENTION_ONLY_HEURISTIC',
            correct_checked_results=None,
            correctness_status='REQUIRES_ACTUAL_TASK_GRADING_NOT_INFERRED_FROM_TEXT'))
        prior_text, prior_cycle = normalized, cycle
        new_guidance.clear()
    sleeps = [dict(cycle=row['cycle'], record=correction.ref(row), checkpoint_sha256=row['checkpoint_sha256'],
        optimizer_steps=row['optimizer_steps'], recall_score=None, recall_status='SOURCE_BOUND_PROBE_REVIEW_REQUIRED',
        correction_level=None, correction_status='SEMANTIC_TRACE_REVIEW_REQUIRED',
        age_probe_status='RECONCILE_WITH_AGE_PROBE_QUEUE_NOT_ASSUMED_EVALUATED')
        for row in evidence['records'] if row['kind'] == 'SLEEP_COMPLETE' and row['status'] == 'COMPLETE']
    return dict(label=label, observed_unix=evidence['observed_unix'], journal_id=evidence['journal_id'],
        coverage_start=evidence['coverage_start'], through=evidence['through'], caught_up=evidence['caught_up'],
        acts=acts, sleeps=sleeps, act_class_counts=dict(Counter(row['classification']['classification'] for row in acts)),
        latest_act=acts[-1] if acts else None,
        last_observed_alert=acts[-1]['parent_adjustment_required'] if acts else None,
        current_alert=acts[-1]['parent_adjustment_required'] if acts and evidence['caught_up'] else None,
        three_cycle_unguided_alert=acts[-1]['alert_three_cycles_unguided'] if acts and evidence['caught_up'] else None,
        learning_changes=[], parent_writes=0, learner_signals=0,
        interpretation='Heuristic movement surfaces, not correctness, retention, emotion or causal learning.')


def collect(target):
    if not target.get('root'):
        return dict(label=target['label'], status=target.get('status', 'NO_NATIVE_ROOT'), latest_act=None)
    if target['wrapper'] not in WRAPPERS:
        raise ValueError('existing_transport_only')
    private = HERE / 'private' / target['label']
    evidence_path = private / 'EVIDENCE.json'
    old = json.loads(evidence_path.read_text()) if evidence_path.exists() else None
    after = old['through']['index'] if old and old.get('through') else None
    expected = old['journal_id'] if old else target.get('journal_id')
    program = READER_SOURCE + f'\nprint(json.dumps(collect({target["root"]!r}, {expected!r}, maximum=600, after={after!r})))\n'
    result = subprocess.run(['bash', str(REPO / 'gpu' / target['wrapper']),
        'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -'],
        input=program, capture_output=True, text=True, timeout=120)
    if result.returncode:
        save(private / 'ERROR.json', dict(observed_unix=time.time(), stderr=result.stderr[-2000:]))
        return dict(label=target['label'], status='READ_ERROR_NOT_ZERO_ACTIVITY')
    batch = json.loads(result.stdout)
    if old:
        if batch['journal_id'] != old['journal_id']:
            raise ValueError('same_incarnation_required')
        if batch['continuity']:
            first = batch['continuity'][0]
            if first['index'] != old['through']['index'] + 1 or first['previous_sha256'] != old['through']['sha256']:
                raise ValueError('incremental_chain_gap')
            batch['records'] = old['records'] + batch['records']
            batch['continuity'] = old['continuity'] + batch['continuity']
        else:
            batch['records'], batch['continuity'], batch['through'] = old['records'], old['continuity'], old['through']
            batch['caught_up'] = batch['through'] == batch['head']
        batch['coverage_start'] = old['coverage_start']
    save(evidence_path, batch)
    return summarize(batch, target['label'])


def run_once():
    targets = json.loads((CORRECTION / 'private/TARGETS.json').read_text())
    def checked(target):
        try:
            return collect(target)
        except Exception as error:
            save(HERE / 'private' / target['label'] / 'ERROR.json', dict(error=str(error), observed_unix=time.time()))
            return dict(label=target['label'], status='READ_ERROR_NOT_ZERO_ACTIVITY')
    with ThreadPoolExecutor(max_workers=3) as executor:
        rows = list(executor.map(checked, targets))
    report = dict(schema='R233_MOVEMENT_AUDIT_V1', observed_utc=datetime.now(timezone.utc).isoformat(),
        rows=rows, source_bindings=SOURCE_BINDINGS,
        source_roster='R232 existing native targets; extra/unlisted arms remain explicit pending reconciliation',
        remote_writes=0, learner_signals=0, automatic_semantic_reviews=0, parent_writes=0,
        alerts_are_not_adjustment_receipts=True)
    save(HERE / 'public/MOVEMENT_LATEST.json', report)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    save(HERE / 'public/cuts' / (stamp + '.json'), report)
    lines = ['# R233 movement audit', '', report['observed_utc'], '',
        'Heuristics trigger parent review, never row exclusion. Missing adjudications remain unknown.', '',
        '| Life | Last observed ACT | Cycle | Caught up? | Observed surface | Repeating cycles | New guidance | Current heuristic alert |',
        '| --- | ---: | ---: | --- | --- | ---: | ---: | --- |']
    for row in rows:
        act = row.get('latest_act')
        if act:
            lines.append(f'| {row["label"]} | {act["response"]["index"]} | {act["cycle"]} | {row["caught_up"]} | '
                f'{act["classification"]["classification"]} | {act["repeat_run_cycles"]} | '
                f'{act["new_guidance_count"]} | {row["current_alert"]} |')
        else:
            lines.append(f'| {row["label"]} | — | — | unknown | {row.get("status", "NO_ACT_IN_WINDOW")} | — | — | unknown |')
    lines.extend(['', 'Correctness, recall and correction level require source-bound task/probe reviews; '
        'this collector does not synthesize successful results. Parent-free age-probe completion comes from its queue.',
        'No alert is itself evidence that a parent changed or that an intervention worked. '
        'No heuristic alert is not a good-performance judgment. Uncaught-up windows have no current verdict.'])
    (HERE / 'public/MOVEMENT_LATEST.md').write_text('\n'.join(lines) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--end-unix', type=float)
    options = parser.parse_args()
    os.umask(0o077)
    lock = (HERE / 'MOVEMENT.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    save(HERE / 'public/MOVEMENT_PROCESS.json', dict(pid=os.getpid(), started_unix=time.time(),
        end_unix=options.end_unix, source_bindings=SOURCE_BINDINGS, mode='READ_ONLY_NO_PARENT_OR_LEARNER_CONTROLS'))
    while True:
        report = run_once()
        print(json.dumps(dict(observed_utc=report['observed_utc'], rows=len(report['rows']))), flush=True)
        if not options.end_unix or time.time() + 60 >= options.end_unix:
            break
        time.sleep(60)


if __name__ == '__main__':
    main()
