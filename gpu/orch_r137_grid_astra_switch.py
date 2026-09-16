"""Read-only F4 prospective Astra preflight; never dispatch or alter a child."""

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import time


ROOT = Path('/localhome/local-rohing/orch_r115_grid_pair_20260915/F4')
ASTRA = 'openai/openai/gpt-6-astra'
CLAUDE = 'claude-fable-5-1'
POLICY_SHA = '2f2bf57a62dc0658db1e4437ecd25eed60d2b2aa47c5ca61208f4d464a40a7b1'
SOURCE_PINS = {
    'gpu/orch_r119_grid_independent.py': 'a4129eca891e0cd9dc2f49f607e5d53d292c662b56a501d4a1611779feb8be7c',
    'gpu/orch_r119_grid_async_parent.py': '7b7be388e9c2d932ec24b699b0cf58e78c628514e7820b95f1af7c2d8681a520',
}
HARD_END = 1789596240.0
TRAIN_END = 1789596120.0


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())


def load(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, 'duplicate_JSON_key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=unique)


def number(name):
    match = re.fullmatch(r'P([0-9]{4,})(?:\.request\.json|\.response\.json|\.json|\.claim)', name)
    require(match is not None, 'parent_filename')
    return int(match.group(1))


def allocation(budget, high_water, historical_claims):
    require(budget['historical_caps']['PARENT'] == historical_claims == 298,
            'preserve_exhausted_Claude_cap298')
    require(budget['counter_reset'] is False and budget['optimizer_reset'] is False,
            'no_reset')
    require(budget['hard_end_unix'] == HARD_END
            and HARD_END <= budget['lease_end_unix'] - 21600, 'unchanged_wall')
    ceiling = budget['prospective_caps']['PARENT']
    require(type(ceiling) is int and type(high_water) is int
            and historical_claims <= high_water <= ceiling, 'cumulative_cap')
    return dict(segment='R137_F4_ASTRA_PROSPECTIVE_ONLY', requested_model=ASTRA,
                old_Claude_cap=298, old_Claude_claims=historical_claims,
                cumulative_parent_ceiling=ceiling, after_parent=high_water,
                proposed_segment_cap=ceiling - high_water,
                reserved_or_skipped_historical_slots=high_water,
                authorized_segment_cap=0, cap_extension=False,
                train_end_unix=TRAIN_END, hard_end_unix=HARD_END)


def eligibility(request, reservation, boundary, *, now, claimed=False,
                received=False, response_exists=False):
    if boundary.get('publication_unix') is None:
        return 'NOT_PUBLISHED'
    if request is None or reservation is None:
        return 'MISSING_NO_REDISPATCH'
    identifier = request.get('id', '')
    if not re.fullmatch(r'P[0-9]{4,}', identifier):
        return 'INVALID_ID'
    position = int(identifier[1:])
    if position <= boundary['after_parent']:
        return 'HISTORICAL_NO_REDISPATCH'
    if claimed or received or response_exists:
        return 'DISPOSED_NO_REDISPATCH'
    if (reservation.get('kind') != 'PARENT' or reservation.get('number') != position
            or reservation.get('reserved_unix', 0) <= boundary['publication_unix']):
        return 'NOT_NEW_RESERVATION'
    payload = request.get('payload', {})
    if (payload.get('life_id') != 'F4_FABLE' or payload.get('game') != 'grid'
            or payload.get('task_provenance', {}).get('split') != 'TRAIN'):
        return 'VISIBILITY_OR_LIFE_MISMATCH'
    if payload.get('cycle', -1) <= boundary['after_cycle']:
        return 'HISTORICAL_CYCLE'
    if payload.get('phase') != 'experience':
        return 'A4_NON_EPISODE_CADENCE_SKIP'
    deadline = request.get('lane_deadline_unix')
    if (type(deadline) not in (int, float) or not now < deadline - 30
            or not now < boundary['train_end_unix']):
        return 'EXPIRED_NO_REDISPATCH'
    if position > boundary['cumulative_parent_ceiling']:
        return 'CUMULATIVE_CAP_EXHAUSTED'
    return 'METADATA_ELIGIBLE_NOT_AUTHORIZED'


def consumer_probe():
    from organism_v6 import orch_r111_grid as policy
    require(sha(Path(policy.__file__).read_bytes()) == POLICY_SHA, 'pinned_consumer_policy')
    request = dict(id='P9999', payload={}, payload_sha256=policy.digest({}), lane_deadline_unix=200)
    response = dict(status='COMPLETE', actual_model=ASTRA, finished_unix=101,
                    request_sha256=policy.digest(request), payload_sha256=request['payload_sha256'],
                    usage={'input_tokens': 1, 'output_tokens': 1},
                    plan=dict(speak=True, message='synthetic CPU-only fixture'))
    original = deepcopy((request, response))
    f4 = policy.parent_disposition(request, response, 102, CLAUDE)
    a4 = policy.parent_disposition(request, response, 102, ASTRA)
    require(original == (request, response), 'immutable_probe_inputs')
    require(f4.get('reason') == 'actual_parent_model_mismatch' and a4['status'] == 'COMPLETE',
            'known_consumer_seam_changed')
    return dict(policy_sha256=POLICY_SHA, F4_truthful_Astra_status=f4['status'],
                F4_reason=f4['reason'], A4_truthful_Astra_status=a4['status'],
                synthetic_only=True, model_identity_spoofed=False)


def verify_native_source(source):
    for relative, expected in SOURCE_PINS.items():
        path = Path(source) / relative
        require(path.resolve() == path and sha(path.read_bytes()) == expected,
                'pinned_running_child_source')
    return dict(SOURCE_PINS)


def inspect(root, *, clock=time.time):
    root = Path(root).resolve()
    started = clock()
    inputs = {}

    def read(relative, limit=16 * 1024 * 1024):
        path = root / relative
        require(path.resolve() == path and path.is_file(), 'regular_immutable_input')
        require(path.stat().st_size <= limit, 'bounded_input')
        raw = path.read_bytes()
        require(len(raw) <= limit, 'bounded_input')
        inputs[relative] = sha(raw)
        return raw

    config = load(read('CONFIG.json'))
    require(config['life_id'] == 'F4_FABLE' and config['parent_model'] == CLAUDE, 'original_F4_identity')
    old = load(read('parent_claude/CONFIG.json'))
    budget = load(read('independent_r119_v1/LEASE_BUDGET.json'))
    require(budget['root'] == old['remote_root'] == str(root)
            and budget['config_sha256'] == inputs['CONFIG.json'], 'bound_budget_identity')
    require(old['max_parent_calls'] == 298, 'original_broker_cap')
    ledger_raw = read('LEDGER.jsonl')
    rows = [load(line) for line in ledger_raw.splitlines() if line]
    parents = [row for row in rows if row['kind'] == 'PARENT']
    require([row['number'] for row in parents] == list(range(1, len(parents) + 1)),
            'contiguous_parent_charges')
    length = budget['ledger_prefix_bytes']
    require(sha(ledger_raw[:length]) == budget['ledger_prefix_sha256'], 'preserve_original_ledger_prefix')
    inventories = {}
    for directory in ('parent_queue', 'parent_received', 'parent_claude'):
        folder = root / directory
        require(folder.resolve() == folder, 'no_symlink_directory')
        paths = sorted(folder.glob('P*'))
        require(len(paths) <= 1000000 and all(not path.is_symlink() for path in paths), 'bounded_inventory')
        inventories[directory] = [path.name for path in paths]
    claims = [name for name in inventories['parent_claude'] if name.endswith('.claim')]
    require([number(name) for name in claims] == list(range(1, 299)), 'original_298_claims_retained')
    positions = [number(name) for names in inventories.values() for name in names]
    high_water = max([len(parents), *positions])
    require(high_water == len(parents), 'queue_ledger_join')
    boundary = dict(after_parent=high_water, first_possible_parent=high_water + 1,
                    after_cycle=max(row['cycle'] for row in rows),
                    publication_unix=None, refresh_at_Main_publication_required=True,
                    train_end_unix=TRAIN_END,
                    cumulative_parent_ceiling=budget['prospective_caps']['PARENT'])
    latest = None
    latest_path = f'parent_queue/P{high_water:04d}.request.json'
    if (root / latest_path).is_file():
        request = load(read(latest_path))
        latest = dict(id=request['id'], cycle=request['payload']['cycle'],
                      phase=request['payload']['phase'], lane_deadline_unix=request['lane_deadline_unix'],
                      skip='HISTORICAL_AT_SNAPSHOT_EVEN_IF_UNEXPIRED')
    for relative, expected in inputs.items():
        require(sha((root / relative).read_bytes()) == expected, 'snapshot_changed_repeat_read_only')
    for directory, names in inventories.items():
        require(sorted(path.name for path in (root / directory).glob('P*')) == names,
                'snapshot_changed_repeat_read_only')
    return dict(schema='R137_F4_ASTRA_PREFLIGHT_V1', status='BLOCKED_CONSUMER_MODEL_BINDING',
                observed_start_unix=started, observed_end_unix=clock(), root=str(root),
                boundary=boundary, latest_request=latest,
                allocation=allocation(budget, high_water, len(claims)),
                inventory_counts={key: len(value) for key, value in inventories.items()},
                inventory_sha256=digest(inventories), input_sha256=inputs,
                cumulative_counts=dict(Counter(row['kind'] for row in rows)),
                old_runner_lock_exists=(root / 'parent_claude/RUNNER.lock').exists(),
                consumer=consumer_probe(), provider_calls=0, child_restart=False,
                optimizer_change=False, LoRA_change=False, input_writes=0,
                authorized=False, raw_exported=False,
                blocked_reason='Running child retains Claude parent_model in memory; no live reload seam. '
                               'Truthful Astra responses are rejected; do not spoof canonicalModel or write parent_received.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--expected-self-sha256', required=True)
    parser.add_argument('--native-source', type=Path,
                        default=Path('/localhome/local-rohing/orch_r119_grid_independent_source_20260915_v1'))
    args = parser.parse_args()
    require(args.root == ROOT, 'only_F4')
    require(sha(Path(__file__).read_bytes()) == args.expected_self_sha256, 'immutable_preflight_command')
    source_pins = verify_native_source(args.native_source)
    report = inspect(args.root)
    report['native_source_sha256'] = source_pins
    print(json.dumps(report, sort_keys=True, indent=2))
    return 3


if __name__ == '__main__':
    raise SystemExit(main())
