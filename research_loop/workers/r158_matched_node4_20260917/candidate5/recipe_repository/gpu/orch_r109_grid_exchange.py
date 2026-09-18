"""Bounded TRAIN-only evidence reporter, separate from immutable grid residents."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time


BASE_SHA = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
PRINCIPLES_SHA = 'b7f4d6baef8158b41533d15acf0f7c924b4bc1e875a30d6ca31f874b5e1c589d'
STRONG = 'openai/openai/gpt-6-astra'
CADENCES = ('segment', 'hundred_segments', 'episode')
END = datetime(2026, 9, 15, 17, 7, tzinfo=timezone.utc).timestamp()
LANES = {
    'node2_7': dict(wrapper='ovx', root='/localhome/local-rohing/orch_r109_grid_20260915_attempt1',
        ready='20e88eff72cb6e84f1709f0781c51996a20cb09bfbd30b3b2767fc527b7f588d',
        source='40f0ff7884492041df7a953045dc1f1fccf09220188de90acbe207b6de41fe56'),
    'node3_5': dict(wrapper='ovx2', root='/localhome/local-rohing/orch_r109_grid_20260915_attempt1',
        ready='1041b72f2c7c6067c8908aaf63a14b679a95c58d2595ce6a5db3b5ec4e33ffc9',
        source='40f0ff7884492041df7a953045dc1f1fccf09220188de90acbe207b6de41fe56'),
    'node5_6': dict(wrapper='ovx3', root='/localhome/local-rohing/orch_r109_grid_node5_6_20260915_attempt1',
        ready='cf5191a5657018b8379c6444ca3fcf7fa4fa92fe8f5e605d5e99ed7fb83a1c97',
        source='2918e0decb28030ccc7cd84f02d3f577824c33cbb55bbebcf216b4d90a6088da'),
    'node5_7': dict(wrapper='ovx3', root='/localhome/local-rohing/orch_r109_grid_node5_7_20260915_attempt1',
        ready='e8727bccf6f101b848ca39ec51d1f60b1e29addd53c6e46ebde8ffb170401bcb',
        source='280da6ebf320b4598676b90eb5442f553aff6777702abc3786b2f93f051880fe'),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def reference(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def read(path):
    return json.loads(path.read_text())


def bound_read(root, evidence, folder, pattern):
    path = Path(evidence['path'])
    require(path.parent == root/folder and re.fullmatch(pattern, path.name)
        and path.resolve() == path, 'scoped_regular_evidence')
    require(reference(path)['sha256'] == evidence['sha256'], 'evidence_hash_drift')
    return read(path)


def action(raw):
    matches = re.findall(r'^ACTION:\s*(UP|DOWN|LEFT|RIGHT|WAIT)\s*$', raw, re.MULTILINE)
    return matches[0] if len(matches) == 1 and raw.strip().endswith('ACTION: '+matches[0]) else 'INVALID'


def joined(root, triple, proposal, task_id, before_purpose, after_purpose):
    before = bound_read(root, proposal, 'calls', r'N\d{5}\.json')
    after = bound_read(root, triple['continuation'], 'calls', r'N\d{5}\.json')
    for call in (before, after):
        require(call['status'] == 'COMPLETE' and call['split'] == 'TRAIN'
            and call['task_id'] == task_id and call['base_sha256'] == BASE_SHA
            and call['adapter'] is None, 'complete_TRAIN_base_call')
    require(before['purpose'] == before_purpose and after['purpose'] == after_purpose,
        'native_call_purpose')
    response = bound_read(root, triple['intervention']['response_ref'], 'parent_queue',
        r'P\d{4}\.response\.json')
    require(response['status'] == 'COMPLETE' and response['actual_model'] == STRONG
        and response['plan'] == triple['intervention']['plan'], 'actual_parent_join')
    identifier = response['id']
    require(re.fullmatch(r'P\d{4}', identifier), 'parent_id')
    request_path = root/'parent_queue'/f'{identifier}.request.json'
    require(request_path.resolve() == request_path, 'regular_parent_request')
    request = read(request_path)
    require(response['request_sha256'] == digest(request)
        and request['source_proposal'] == proposal
        and request['ready_sha256'] == reference(root/'READY.json')['sha256']
        and request['payload']['task_id'] == task_id
        and request['payload']['child_proposal'] == before['response']['raw'], 'parent_request_binding')
    require(type(response['plan']['speak']) is bool, 'parent_speak_boolean')
    return before, after, response


def cycle_receipt(root, lane, cadence, cycle):
    directory = root/cadence/f'cycle{cycle:02d}'/'train'
    complete_path = directory/'COMPLETE.json'
    if not complete_path.exists():
        return None
    complete = read(complete_path)
    require(complete['status'] == 'COMPLETE' and complete['no_adapter'] is True
        and complete['base_sha256'] == BASE_SHA and complete['optimizer_updates'] == 0
        and complete['held_parent_free'] is False and len(complete['results']) == 2,
        'completed_two_episode_TRAIN_cycle')
    evidence = [reference(complete_path)]
    counts = Counter()
    transitions = Counter()
    parents_seen = set()
    for position, summary in enumerate(complete['results'], 1):
        path = directory/f'episode{position}'/'EPISODE.json'
        episode = read(path)
        require(episode['split'] == 'TRAIN' and episode['task_id'] == summary['task_id']
            and 0 <= len(episode['triples']) <= 16, 'TRAIN_episode_binding')
        evidence.append(reference(path))
        for triple in episode['triples']:
            no_continuation = triple['no_continuation']
            before, after, response = joined(root, triple, triple['proposal'], episode['task_id'],
                'proposal', 'proposal' if no_continuation else 'continuation')
            require(no_continuation == (not response['plan']['speak']), 'silence_continuation_binding')
            require(not no_continuation or triple['proposal'] == triple['continuation'], 'silent_same_call')
            require(response['id'] not in parents_seen, 'unique_parent_per_cycle')
            parents_seen.add(response['id'])
            before_action, after_action = action(before['response']['raw']), action(after['response']['raw'])
            require(after_action == triple['actual_transition']['action'], 'executed_action_join')
            counts['spoken' if response['plan']['speak'] else 'silent'] += 1
            counts['changed_action' if before_action != after_action else 'unchanged_action'] += 1
            counts['invalid_before'] += before_action == 'INVALID'
            counts['invalid_after'] += after_action == 'INVALID'
            transitions[f'{before_action}->{after_action}'] += 1
    metacognitive_path = directory/'METACOGNITIVE_TRIPLE.json'
    triple = read(metacognitive_path)
    require(triple['weight_updates'] == 0 and triple['semantic_compiler'] is False
        and triple['reflection_is_context_only'] is True, 'context_only_metacognition')
    before, after, response = joined(root, triple, triple['before'], complete['results'][-1]['task_id'],
        'metacognitive_reflection', 'context_distillation')
    require(response['id'] not in parents_seen, 'unique_metacognitive_parent')
    counts['metacognitive_spoken' if response['plan']['speak'] else 'metacognitive_silent'] += 1
    evidence.append(reference(metacognitive_path))
    return dict(schema='R111_GRID_TRAIN_CYCLE_EXCHANGE_V1', half='Main', lane=lane, cadence=cadence,
        cycle=cycle, entry_id=f'MAIN_GRID/{lane}/{cadence}/C{cycle:02d}',
        finished_utc=datetime.fromtimestamp(complete['finished_unix'], timezone.utc).isoformat(),
        parent_model=STRONG, counts=dict(counts), action_transitions=dict(transitions),
        metacognitive_continuation_completed=True, semantic_parent_intent='UNASSESSED',
        semantic_child_change='UNASSESSED', causal_helpfulness='UNASSESSED', weight_updates=0,
        source_evidence=evidence, ready=reference(root/'READY.json'), source=reference(root/'SOURCE_SHA256.json'),
        note='Proposal versus executed action is observed, not a semantic or causal inference; '
            'held outputs and prior outcome scores never read; no live prompt/learning feedback')


def collect(lane):
    spec = LANES[lane]
    root = Path(spec['root'])
    require(reference(root/'READY.json')['sha256'] == spec['ready']
        and reference(root/'SOURCE_SHA256.json')['sha256'] == spec['source'], 'pinned_live_root')
    ready = read(root/'READY.json')
    require(ready['no_adapter'] is True and ready['principles_sha256'] == PRINCIPLES_SHA,
        'frozen_BASE_principles')
    result = []
    for cadence in CADENCES:
        for cycle in range(1, 9):
            receipt = cycle_receipt(root, lane, cadence, cycle)
            if receipt is not None:
                result.append(receipt)
    return result


def entry(receipt, compact):
    counts = receipt['counts']
    get = lambda name: counts.get(name, 0)
    return (
        f"\n\n<!-- {receipt['entry_id']} -->\n"
        f"## [Main / Laplace] {receipt['finished_utc']} — {receipt['lane']} "
        f"{receipt['cadence']} cycle {receipt['cycle']}\n"
        f"- Parent did (verified delivery, not intent): {get('spoken')} spoken / {get('silent')} silent "
        f"action interventions; metacognitive reply spoken={get('metacognitive_spoken')}, "
        f"silent={get('metacognitive_silent')}; actual Astra. Semantic intent UNASSESSED.\n"
        f"- Child changed (observed only): executed ACTION differs from pre-intervention proposal "
        f"{get('changed_action')} times; unchanged {get('unchanged_action')}; invalid ACTION "
        f"before/after={get('invalid_before')}/{get('invalid_after')}. Metacognitive continuation "
        "completed; semantic revision/helpfulness UNASSESSED, no causal or weight-learning claim.\n"
        "- Other-half pointer: Fable node5 physical0–3, this shared exchange; "
        "no matched grid-cycle counterpart bound.\n"
        "- Request/disagreement: please review source-linked parent/child turns for functional "
        "effort allocation, persistence and control. Action changes alone do not establish learning; "
        "no substantive agreement/disagreement inferred.\n"
        f"- Compact: `{compact['path']}` SHA256 `{compact['sha256']}`. "
        "Raw on owning node only; TRAIN-only telemetry, never live prompt feedback.\n")


def append_once(path, receipt, compact):
    marker = f"<!-- {receipt['entry_id']} -->"
    payload = entry(receipt, compact).encode()
    require(len(payload) <= 4096 and re.fullmatch(r'MAIN_GRID/[a-z0-9_]+/(segment|hundred_segments|episode)/C\d{2}',
        receipt['entry_id']), 'bounded_entry')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        stream.seek(0)
        existing = stream.read()
        if marker.encode() in existing:
            require(payload in existing, 'incomplete_or_changed_prior_entry')
            return False
        require(os.write(stream.fileno(), payload) == len(payload), 'complete_atomic_append')
        os.fsync(stream.fileno())
    return True


def publish(repo, receipts):
    output = repo/'research_notes/analysis/orch_r109_grid_20260915_attempt1/EXCHANGE'
    output.mkdir(parents=True, exist_ok=True)
    added = 0
    for receipt in receipts:
        require(receipt['lane'] in LANES and receipt['cadence'] in CADENCES
            and type(receipt['cycle']) is int and 1 <= receipt['cycle'] <= 8
            and receipt['entry_id'] == f"MAIN_GRID/{receipt['lane']}/{receipt['cadence']}/C{receipt['cycle']:02d}",
            'bounded_known_cycle')
        path = output/f"{receipt['lane']}_{receipt['cadence']}_{receipt['cycle']:02d}.json"
        if path.exists():
            require(read(path) == receipt, 'immutable_cycle_receipt_drift')
        else:
            with path.open('x') as stream:
                json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
                stream.write('\n')
        added += append_once(repo/'research_loop/PARENTING_EXCHANGE.md', receipt, reference(path))
    return added


def watch(repo, once=False):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_reporter')
    while time.time() <= END:
        summary = dict(observed_utc=datetime.now(timezone.utc).isoformat(), new_entries=0, lanes={},
            no_native_or_provider_calls=True, no_live_source_mutation=True, end_unix=END)
        for lane, spec in LANES.items():
            script = spec['root']+'/exchange_v1/orch_r109_grid_exchange.py'
            source_sha = reference(Path(__file__))['sha256']
            command = 'test "$(sha256sum '+shlex.quote(script)+" | cut -d ' ' -f 1)\" = "+source_sha+(
                ' && CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B '+shlex.quote(script)+
                ' --collect '+lane)
            try:
                result = subprocess.run(['bash', str(repo/'gpu'/f"{spec['wrapper']}_ssh.sh"), command],
                    capture_output=True, text=True, timeout=60, check=True)
                receipts = json.loads(result.stdout)
                require(len(receipts) <= 24 and all(value['lane'] == lane for value in receipts), 'bounded_lane_response')
                summary['new_entries'] += publish(repo, receipts)
                summary['lanes'][lane] = dict(completed_train_cycles=len(receipts), status='OK')
            except (OSError, subprocess.SubprocessError, ValueError, KeyError) as error:
                summary['lanes'][lane] = dict(status='REPORT_FAILED_NO_LIVE_EFFECT', error_type=type(error).__name__)
        print(json.dumps(summary, sort_keys=True), flush=True)
        if once:
            return summary
        remaining = END-time.time()
        if remaining <= 0:
            return summary
        time.sleep(min(120, remaining))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--collect', choices=LANES)
    parser.add_argument('--repo', type=Path)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    if args.collect:
        print(json.dumps(collect(args.collect), sort_keys=True))
    else:
        require(args.repo is not None, 'repository_required')
        watch(args.repo, once=args.once)
