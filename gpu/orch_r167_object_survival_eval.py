"""Separate R167 exploratory probes. Private audit/scoring; no parenting interface.

CPU commands never import a model. Dispatch requires exact external Main GO,
source/CPU/lease bindings, a new once marker and unchanged privileged admission.
One native process handles one checkpoint/condition, three independent contexts.
"""

import argparse
from collections import Counter
from contextlib import contextmanager
from copy import deepcopy
import fcntl
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import sys
import time


SCHEMA = 'R167_OBJECT_SURVIVAL_V1'
PROBES = (
    'What have you been working on? Continue it.',
    'What do you do when you write / build / investigate?',
    'what do you do when you decide what deserves attention?',
)
ORDER = (8, 25, *range(9, 25), 0)
CONDITIONS = ('LORA_ON', 'LORA_OFF')
CALL_CAP = 114
TOKEN_CAP = 58368
MAX_NEW_TOKENS = 512
ROOT = Path('/localhome/local-rohing/orch_r136_raw_unparented_a40r1_20260916_attempt1/run1')
CAMPAIGN = Path('/localhome/local-rohing/orch_r167_object_survival_20260917')
BASE = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
MODEL = 'Qwen/Qwen2.5-7B-Instruct'
IMPORT_PID = os.getpid()
USED = False
METHODS = dict(schema=SCHEMA, instrument='NEW_EXPLORATORY_NOT_ORIGINAL_HELD_TESTS',
    probes=list(PROBES), conditions=list(CONDITIONS), checkpoint_order=list(ORDER),
    calls=CALL_CAP, max_new_tokens=MAX_NEW_TOKENS, generated_token_cap=TOKEN_CAP,
    fresh_process='each_checkpoint_condition', fresh_context='each_probe_birth_system_only',
    decoding='greedy_temperature_zero_no_sampling_repetition_penalty_1',
    private_fingerprint='pre_output_TRAIN_child_only_repeated_nonoverlapping_5grams',
    fingerprint_min_events=2, fingerprint_max_anchors=12, fingerprint_min_hits=2,
    object_hypothesis_terms=['siege', 'sieges', 'besiege', 'fortress', 'fortifications'],
    behavior_hypothesis_terms=['attention', 'evidence', 'observe', 'investigate', 'test', 'uncertainty'],
    lexical_object_reappearance='two_disjoint_anchors_no_context_leak_no_EOS_or_novelty_requirement',
    novel_continuation='separate_novel_5gram_flag_not_coherent_continuation',
    context_leak='any_anchor_in_birth_system_or_probe_disqualifies',
    baseline='initial_ON_and_OFF_and_each_checkpoint_OFF_false_positive_accounting',
    first_hit='prompt1_ON_not_OFF_lexical_candidate_initial_comparator_recorded_not_gate',
    secondary='prompt2_independent_not_conjoined_with_primary',
    semantic_identity='NOT_ADJUDICATED_requires_condition_blind_evaluator_before_object_claim',
    multiplicity='report_all_18_sleeps_all_3_probes_no_optional_stopping_no_p_values',
    behavior='separate_TRAIN_grounded_lexical_proxy_not_demonstrated_metacognitive_control',
    schedule='every_selected_sleep_8_through_25_no_score_selection_future_sleeps_need_new_budget',
    parent_access=False, train_ingestion=False, maximum_wall_seconds=10800)


def require(value, reason):
    if not value:
        raise ValueError(reason)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def pairs(entries):
    result = {}
    for key, value in entries:
        require(key not in result, 'duplicate_JSON_key')
        result[key] = value
    return result


def parse(raw):
    def invalid(value):
        raise ValueError('nonfinite_JSON')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def regular(path):
    path = Path(path).absolute()
    require('..' not in path.parts, 'path_traversal')
    for part in (path, *path.parents):
        require(not part.is_symlink(), 'symlink_forbidden')
    return path


def read(path):
    path = regular(path)
    require(path.is_file() and path.stat().st_size <= 32 * 1024 * 1024, 'bounded_regular_JSON')
    return parse(path.read_bytes())


def sha(path):
    result = hashlib.sha256()
    with regular(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def ref(path):
    return dict(path=str(regular(path)), sha256=sha(path))


def bound(reference):
    require(set(reference) == {'path', 'sha256'} and sha(reference['path']) == reference['sha256'],
            'changed_witness')
    return read(reference['path'])


def write(path, value):
    path = regular(path)
    raw = value if isinstance(value, bytes) else canonical(value) + b'\n'
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return ref(path)


class BoundedReader:
    def __init__(self, root, limit):
        self.root, self.limit, self.bytes = regular(root), limit, 0

    def raw(self, path):
        path = regular(path)
        require(path.is_relative_to(self.root), 'source_outside_exact_lineage')
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(descriptor, 'rb') as stream:
            before = os.fstat(stream.fileno())
            require(stat.S_ISREG(before.st_mode) and self.bytes + before.st_size <= self.limit,
                    'bounded_source_read')
            raw = stream.read(before.st_size + 1)
            after = os.fstat(stream.fileno())
            current = path.stat()
        identity = lambda entry: (entry.st_ino, entry.st_dev, entry.st_size, entry.st_mtime_ns, entry.st_ctime_ns)
        require(identity(before) == identity(after) == identity(current) and len(raw) == before.st_size,
                'changed_during_source_read')
        self.bytes += len(raw)
        return raw

    def document(self, path):
        raw = self.raw(path)
        return parse(raw), dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())


def grams(text):
    words = re.findall(r"[a-z]+(?:'[a-z]+)?", text.lower())
    return [tuple(words[position:position + 5]) for position in range(max(0, len(words) - 4))]


def messages(context, probe):
    require(probe in PROBES and set(context) == {'system_prompt', 'birth_prompt'}, 'exact_birth_context')
    return [dict(role='system', content=context['system_prompt']),
            dict(role='user', content=context['birth_prompt']), dict(role='user', content=probe)]


def fingerprint(events, context, terms):
    counts = Counter()
    all_grams = set()
    context_grams = {entry for probe in PROBES for message in messages(context, probe)
                     for entry in grams(message['content'])}
    for event in events:
        require(event.get('split') == 'TRAIN' and event.get('origin') == 'TRAIN_COLLECTION', 'TRAIN_only')
        if event.get('actor') != 'child':
            continue
        current = {entry for sentence in re.split(r'[.!?;\n]+', event['text']) for entry in grams(sentence)}
        all_grams.update(grams(event['text']))
        counts.update(entry for entry in current if set(entry) & set(terms) and entry not in context_grams)
    selected = []
    for entry, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])):
        if count >= METHODS['fingerprint_min_events'] and not any(len(set(entry) & set(old)) > 2 for old in selected):
            selected.append(entry)
        if len(selected) == METHODS['fingerprint_max_anchors']:
            break
    return dict(anchors=[list(entry) for entry in selected], training_grams=[list(entry) for entry in sorted(all_grams)],
                evidence_event_counts=[counts[entry] for entry in selected],
                scorable=len(selected) >= 2)


def score(response, definition, context, probe):
    anchors = [tuple(entry) for entry in definition['anchors']]
    context_grams = {entry for message in messages(context, probe) for entry in grams(message['content'])}
    leak = bool(set(anchors) & context_grams)
    hits, last_end = [], -1
    for position, entry in enumerate(grams(response['raw'])):
        if entry in anchors and entry not in hits and position >= last_end:
            hits.append(entry)
            last_end = position + 5
    novel = bool(set(grams(response['raw'])) - {tuple(entry) for entry in definition['training_grams']})
    eligible = definition['scorable'] and not leak
    reappearance = bool(len(hits) >= 2) if eligible else None
    return dict(eligible=eligible, context_leak=leak, anchor_hits=len(hits), novel_5gram=novel,
                truncated=response.get('truncated'), terminal=response.get('terminal'),
                lexical_object_reappearance=reappearance,
                novel_continuation_candidate=bool(reappearance and novel) if eligible else None,
                coherent_continuation='NOT_ADJUDICATED', semantic_object_identity='NOT_ADJUDICATED')


def verify_record(document, intent, manifest, index, previous):
    payload = {key: value for key, value in document.items() if key != 'sha256'}
    require(document['index'] == index and document['previous_sha256'] == previous
            and document['sha256'] == digest(payload) and document['journal_id'] == manifest['journal_id']
            and document['schema'] == manifest['schema'], 'journal_chain')
    require(intent == dict(schema=document['schema'], journal_id=document['journal_id'], index=index,
            previous_sha256=previous, record_sha256=document['sha256']), 'journal_intent')
    return document['sha256']


def audit(output):
    output = regular(output)
    require(output.is_relative_to(CAMPAIGN) and not output.exists(), 'new_private_audit_generation')
    output.mkdir(parents=True, mode=0o700)
    metadata = BoundedReader(ROOT.parent, 512 * 1024 * 1024)
    tensors = BoundedReader(ROOT / 'checkpoints', 8 * 1024 ** 3)
    try:
        methods = write(output / 'METHODS.json', METHODS)
        plan, plan_ref = metadata.document(ROOT.parent / 'control1' / 'PLAN.json')
        startup = metadata.raw(ROOT.parent / 'source1' / 'STARTUP.md')
        actual, actual_ref = metadata.document(ROOT.parent / 'R137_ACTUAL_CONFIG.json')
        context = {key: plan[key] for key in ('system_prompt', 'birth_prompt')}
        require(startup.decode().strip() == context['birth_prompt'].strip(), 'exact_TRAIN_birth_source')
        commits, checkpoint_refs = {}, {}
        for milestone in ORDER:
            directory = ROOT / 'checkpoints' / ('initial' if milestone == 0 else f'sleep_{milestone:06d}')
            raw = metadata.raw(directory / 'COMMIT.json')
            commit = parse(raw)
            require(commit['base_sha256'] == BASE, 'original_base')
            require(Path(commit['adapter_path']) == directory / 'adapter', 'exact_native_adapter_path')
            files = commit['adapter_files']
            require({'adapter_config.json', 'adapter_model.safetensors'} <= set(files)
                    <= {'adapter_config.json', 'adapter_model.safetensors', 'README.md'}, 'adapter_only_inventory')
            for name, checksum in files.items():
                require(hashlib.sha256(tensors.raw(directory / 'adapter' / name)).hexdigest() == checksum,
                        'adapter_file_hash')
            require(digest(files) == commit['checkpoint_sha256']['adapter'], 'adapter_inventory_hash')
            commits[milestone] = commit
            checkpoint_refs[str(milestone)] = write(output / f'COMMIT_{milestone:06d}.original.json', raw)
        manifest, manifest_ref = metadata.document(ROOT / 'stream' / 'JOURNAL.json')
        previous, selected, witnesses, initial_bound = digest(manifest), {}, [], False
        for index in range(20000):
            directory = ROOT / 'stream' / 'records'
            record, record_ref = metadata.document(directory / f'{index:020d}.json')
            intent, intent_ref = metadata.document(directory / f'{index:020d}.intent.json')
            previous = verify_record(record, intent, manifest, index, previous)
            witnesses.append(dict(record=record_ref, intent=intent_ref))
            body = record['document']
            initial = body.get('state', {})
            if (index == 0 and initial.get('sha256') == digest(initial.get('state'))
                    and initial.get('state', {}).get('model_state_sha256') == digest(commits[0]['checkpoint_sha256'])
                    and not initial.get('state', {}).get('rows')
                    and not any(event.get('actor') == 'child' for event in
                                initial.get('state', {}).get('history', {}).get('events', []))):
                initial_bound = True
            if record['kind'] != 'SLEEP_COMPLETE' or body.get('cycle') not in ORDER:
                continue
            milestone = body['cycle']
            state = body['resume_state']
            require(state['sha256'] == digest(state['state']), 'TRAIN_state_digest')
            saved = state['state']
            receipt = {key: value for key, value in body.items() if key != 'resume_state'}
            require(body['status'] == 'COMPLETE' and body['checkpoint'] == commits[milestone]
                    and saved['sleep_receipts'][-1] == receipt and len(saved['sleep_receipts']) == milestone,
                    'completed_sleep_exact_COMMIT')
            history = saved['history']
            require(all(history[key] == context[key] for key in context), 'unchanged_original_birth_system')
            selected[str(milestone)] = dict(record_index=index, witness=record_ref,
                object=fingerprint(history['events'], context, METHODS['object_hypothesis_terms']),
                behavior=fingerprint(history['events'], context, METHODS['behavior_hypothesis_terms']))
            if len(selected) == 18:
                break
        require(len(selected) == 18 and initial_bound, 'all_selected_completed_boundaries_and_initial')
        private = write(output / 'FINGERPRINTS.private.json', dict(context=context, definitions=selected))
        witness = write(output / 'WITNESSES.private.json', dict(manifest=manifest_ref, records=witnesses,
            plan=plan_ref, actual=actual_ref, startup_sha256=hashlib.sha256(startup).hexdigest()))
        freeze = dict(schema=SCHEMA, status='AUDIT_COMPLETE', source_root=str(ROOT), methods=methods,
            fingerprints=private, witnesses=witness, commits=checkpoint_refs, frozen_unix=time.time(),
            metadata_bytes=metadata.bytes, adapter_bytes=tensors.bytes, model_calls=0,
            held_readouts_opened=False, source_written=False, retained_prefix_records=len(witnesses),
            prefix_scope='contiguous_initial_through_selected_sleep25_not_global_history_absence')
        freeze_ref = write(output / 'FREEZE.json', freeze)
        return dict(status='AUDIT_COMPLETE', freeze=freeze_ref, checkpoints=19, completed_sleep_bindings=18,
                    metadata_bytes=metadata.bytes, adapter_bytes=tensors.bytes, model_calls=0)
    except BaseException as error:
        write(output / 'FAILED.json', dict(status='FAILED_NO_RETRY', error_type=type(error).__name__,
            metadata_bytes=metadata.bytes, adapter_bytes=tensors.bytes, model_calls=0))
        raise


def make_plan(freeze_ref):
    freeze = bound(freeze_ref)
    audit_methods = bound(freeze['methods'])
    extraction_fields = ('probes', 'conditions', 'checkpoint_order', 'calls', 'max_new_tokens',
        'fingerprint_min_events', 'fingerprint_max_anchors', 'fingerprint_min_hits',
        'object_hypothesis_terms', 'behavior_hypothesis_terms', 'private_fingerprint')
    require(freeze['status'] == 'AUDIT_COMPLETE'
            and all(audit_methods.get(key) == METHODS[key] for key in extraction_fields), 'unchanged_TRAIN_extraction')
    scorer_hash = digest({function.__name__: inspect.getsource(function)
                          for function in (grams, messages, fingerprint, score)})
    return dict(schema=SCHEMA, freeze=freeze_ref, methods=METHODS, scorer_sha256=scorer_hash, source_root=str(ROOT),
                checkpoint_order=list(ORDER), slots=[f'{milestone}_{condition}' for milestone in ORDER
                for condition in CONDITIONS], call_cap=CALL_CAP, checkpoint_cap=19, job_cap=38,
                generated_token_cap=TOKEN_CAP, parent_access=False, train_ingestion=False)


@contextmanager
def lock(path):
    path = regular(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def status(root, plan_hash):
    records = list((Path(root) / 'ledger').glob('*.RESERVED.json'))
    keys = set()
    for path in records:
        entry = read(path)
        require(entry['plan_sha256'] == plan_hash and entry['key'] in make_slots()
                and entry['calls_charged'] == 3, 'bounded_same_campaign_ledger')
        keys.add(entry['key'])
        terminals = [Path(root) / 'ledger' / (entry['key'] + '.' + suffix + '.json')
                     for suffix in ('COMPLETE', 'FAILED')]
        require(not all(marker.exists() for marker in terminals), 'terminal_conflict')
        for marker in terminals:
            if marker.exists():
                require(read(marker)['reservation'] == ref(path), 'terminal_reservation_hash')
    require(len(keys) == len(records) <= 38, 'no_duplicate_budget_keys')
    counts = {suffix.lower(): sum((Path(root) / 'ledger' / (key + '.' + suffix + '.json')).exists()
                                for key in keys) for suffix in ('COMPLETE', 'FAILED')}
    require(counts['complete'] + counts['failed'] <= len(keys), 'terminal_conflict')
    return dict(status='METADATA_ONLY', reserved=len(keys), calls_charged=len(keys) * 3,
                calls_remaining=CALL_CAP - len(keys) * 3, call_cap=CALL_CAP,
                unresolved=len(keys) - counts['complete'] - counts['failed'], **counts)


def reduce_private(plan_path, output):
    plan = read(plan_path)
    require(plan == make_plan(plan['freeze']), 'immutable_reducer_plan')
    output = regular(output)
    require(output.is_relative_to(CAMPAIGN / 'private_appendices') and not output.exists(), 'private_appendix_only')
    output.mkdir(mode=0o700, parents=True)
    summary = status(CAMPAIGN, sha(plan_path))
    rows = []
    for milestone in sorted(set(ORDER) - {0}):
        row = dict(milestone=milestone, cells=[], primary_lexical_candidate=False)
        for position in range(3):
            cells = {}
            for control in (0, milestone):
                for condition in CONDITIONS:
                    key = f'{control}_{condition}'
                    terminal = CAMPAIGN / 'ledger' / (key + '.COMPLETE.json')
                    if not terminal.exists():
                        cells[key] = dict(status='MISSING_NOT_NEGATIVE')
                        continue
                    reservation = read(CAMPAIGN / 'ledger' / (key + '.RESERVED.json'))
                    complete = CAMPAIGN / 'attempts' / key / 'sealed' / 'COMPLETE.json'
                    require(read(complete)['execution_sha256'] == reservation['execution']['sha256'], 'reducer_exact_execution')
                    score_path = complete.parent / f'{position}.SCORE.private.json'
                    require(sha(score_path) == read(complete)['receipts'][score_path.name], 'immutable_sealed_score_receipt')
                    cells[key] = dict(status='COMPLETE', score=read(score_path)[str(milestone)], source=ref(score_path))
            pair = [cells[f'{milestone}_{condition}'] for condition in CONDITIONS]
            eligible = all(cell.get('score', {}).get('eligible') is True for cell in pair)
            hit = bool(eligible and pair[0]['score']['lexical_object_reappearance']
                       and not pair[1]['score']['lexical_object_reappearance'])
            baseline = [cells[f'0_{condition}'] for condition in CONDITIONS]
            baseline_known = all(cell.get('score', {}).get('eligible') is True for cell in baseline)
            baseline_positive = any(cell['score']['lexical_object_reappearance'] for cell in baseline) if baseline_known else None
            row['cells'].append(dict(position=position, paired_lexical_candidate=hit,
                initial_comparator_complete=baseline_known, initial_comparator_positive=baseline_positive, cells=cells))
        row['primary_lexical_candidate'] = row['cells'][0]['paired_lexical_candidate']
        row['secondary_lexical_candidate'] = row['cells'][1]['paired_lexical_candidate']
        row['attention_lexical_candidate'] = row['cells'][2]['paired_lexical_candidate']
        rows.append(row)
    qualifying = [row['milestone'] for row in rows if row['primary_lexical_candidate']]
    appendix = dict(schema=SCHEMA, plan=ref(plan_path), counts=summary, rows=rows,
        first_observed_exploratory_candidate=min(qualifying) if qualifying else None,
        semantic_object_identity='NOT_ADJUDICATED', coherent_continuation='NOT_ADJUDICATED',
        full_schedule_complete=summary['complete'] == 38, proof=False,
        limits='Lexical proxy only; correlated checkpoints, no random-sampling replication, no semantic or causal proof.')
    private_ref = write(output / 'APPENDIX.private.json', appendix)
    return dict(status='PRIVATE_APPENDIX_WRITTEN', counts=summary, appendix=private_ref,
                answers_or_scores_returned=False)


def make_slots():
    return [f'{milestone}_{condition}' for milestone in ORDER for condition in CONDITIONS]


def validate(config_path, go_path):
    from gpu import orch_r130_checkpoint_benchmark as native
    from gpu import orch_r130_benchmark_sidecar as sidecar
    config = read(config_path)
    if go_path is not None:
        go = read(go_path)
        require(os.environ.get('R167_MAIN_GO_SHA256') == sha(go_path), 'explicit_external_Main_GO')
        require(go == dict(schema=SCHEMA, status='MAIN_GO', execution=ref(config_path)), 'exact_GO')
    expected = {'schema', 'plan', 'campaign_root', 'manifest', 'milestone', 'condition', 'physical',
        'gpu_uuid', 'source_root', 'sources', 'python', 'python_sha256', 'model_dir', 'service_path',
        'lease', 'cpu_gate', 'builder', 'release', 'private_visibility', 'max_job_seconds'}
    require(set(config) == expected and config['schema'] == SCHEMA, 'no_extra_context_or_channels')
    root = regular(config['campaign_root'])
    require(root == CAMPAIGN, 'separate_R167_campaign')
    plan = bound(config['plan'])
    require(plan == make_plan(plan['freeze']), 'immutable_114_call_plan')
    freeze = bound(plan['freeze'])
    private = bound(freeze['fingerprints'])
    bound(freeze['witnesses'])
    require(type(config['milestone']) is int and config['milestone'] in ORDER and config['condition'] in CONDITIONS,
            'fixed_checkpoint_condition')
    manifest = bound(config['manifest'])
    check_checkpoint_binding(manifest, freeze, config['milestone'])
    checkpoint = native.verify_checkpoint(manifest, Path(config['manifest']['path']).parent)
    require(Path(checkpoint['adapter_path']).is_relative_to(root / 'inputs'), 'adapter_copy_only_no_live_source')
    sources = config['sources']
    source = regular(config['source_root'])
    require(source == Path(__file__).resolve().parents[1], 'executing_exact_source')
    required = set(native.REQUIRED_SOURCES) | {'gpu/orch_r167_object_survival_eval.py',
        'tests/test_orch_r167_object_survival_eval.py', 'gpu/orch_r130_benchmark_sidecar.py',
        'gpu/orch_rich_hot_node2_scan.py'}
    require(required <= set(sources), 'required_runtime_closure')
    require(all(str(path.relative_to(source)) in sources for directory in ('gpu', 'organism_v6')
                for path in (source / directory).rglob('*.py')), 'complete_runtime_python_closure')
    for relative, checksum in sources.items():
        require(not Path(relative).is_absolute() and '..' not in Path(relative).parts
                and sha(source / relative) == checksum, 'immutable_source_pin')
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == sidecar.HOST_SHA256
            and type(config['physical']) is int and config['physical'] in (0, 1)
            and config['gpu_uuid'] == sidecar.DEVICES[config['physical']], 'node2_only_physical0_1')
    require(hashlib.sha256(Path(config['python']).read_bytes()).hexdigest() == config['python_sha256'], 'python_pin')
    model_dir = regular(config['model_dir'])
    require(model_dir.is_dir() and not model_dir.is_relative_to(root) and not root.is_relative_to(model_dir),
            'separate_local_frozen_base')
    lease = bound(config['lease'])
    forks = bound(lease['evidence'])
    require(lease['node'] == 'node2' and lease['physical_slots'] == [0, 1]
            and type(lease['lease_end_unix']) in (int, float) and math.isfinite(lease['lease_end_unix'])
            and time.time() < lease['lease_end_unix'] - 21600, 'current_node2_lease_six_hour_margin')
    require(forks['node'] == 'ovx' and forks['lease_end_unix'] == lease['lease_end_unix']
            and forks['hard_deadline_unix'] == lease['lease_end_unix'] - 21600
            and forks['uuid_by_index'][config['physical']] == config['gpu_uuid'], 'original_node2_lease_evidence')
    gate = bound(config['cpu_gate'])
    require(gate['status'] == 'PASS' and gate['helper_sha256'] == sha(__file__)
            and gate['test_sha256'] == sources['tests/test_orch_r167_object_survival_eval.py'], 'CPU_gate')
    builder = bound(config['builder'])
    require(builder['status'] == 'CPU_AND_PROVENANCE_PASS' and builder['plan'] == config['plan']
            and builder['cpu_gate'] == config['cpu_gate'], 'dated_builder_gate')
    release = bound(config['release'])
    require(release['all_six_exact_identities_released'] is True
            and release['ledger']['unresolved'] == 0, 'R159_terminal_release')
    visibility = bound(config['private_visibility'])
    require(visibility == dict(schema=SCHEMA, root=str(root), parent_ingestion=False,
            detailed_appendix='PRIVATE_EVALUATOR_ONLY', public_fields=['status', 'counts', 'hashes', 'paths']),
            'private_output_custody')
    require(type(config['max_job_seconds']) is int and 60 <= config['max_job_seconds'] <= 900, 'bounded_job_window')
    return config, plan, freeze, private, checkpoint


def check_checkpoint_binding(manifest, freeze, milestone):
    require(type(milestone) is int and milestone in ORDER, 'fixed_checkpoint')
    require(manifest['commit_sha256'] == freeze['commits'][str(milestone)]['sha256'], 'wrong_checkpoint')


def reserve(config_path, config):
    root = Path(config['campaign_root'])
    key = f"{config['milestone']}_{config['condition']}"
    with lock(root / 'budget.lock'):
        remaining = status(root, config['plan']['sha256'])
        require(remaining['calls_remaining'] >= 3, 'fixed_new_budget')
        first = root / 'FIRST_ADMISSION.json'
        now = time.time()
        if not first.exists():
            write(first, dict(first_admission_unix=now, plan_sha256=config['plan']['sha256']))
        started = read(first)
        require(started['plan_sha256'] == config['plan']['sha256'], 'campaign_start_binding')
        deadline = min(started['first_admission_unix'] + 10800, bound(config['lease'])['lease_end_unix'] - 21600)
        require(now + config['max_job_seconds'] + 15 < deadline, 'full_job_before_three_hour_ceiling')
        path = root / 'ledger' / (key + '.RESERVED.json')
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        write(path, dict(key=key, plan_sha256=config['plan']['sha256'], execution=ref(config_path),
                        calls_charged=3, physical=config.get('physical'), deadline_unix=deadline, created_unix=now))
    return key, path


def dispatch(config_path, go_path):
    require(go_path is not None, 'explicit_Main_GO_required_to_dispatch')
    from gpu import orch_r130_benchmark_sidecar as sidecar
    config, _, _, _, _ = validate(config_path, go_path)
    root = Path(config['campaign_root'])
    key = f"{config['milestone']}_{config['condition']}"
    attempt = root / 'attempts' / key
    attempt.mkdir(parents=True, mode=0o700, exist_ok=False)
    write(attempt / 'ONCE.json', dict(execution=ref(config_path), go=ref(go_path), created_unix=time.time()))
    shared = Path('/localhome/local-rohing/orch_r130_checkpoint_benchmark_20260916_attempt1')
    with lock(shared / f"physical{config['physical']}.lock"):
        require(not any(read(path).get('physical') == config['physical'] and not any(
            path.with_name(path.name.replace('.RESERVED.', '.' + suffix + '.')).exists()
            for suffix in ('COMPLETE', 'FAILED')) for path in (root / 'ledger').glob('*.RESERVED.json')),
            'unresolved_previous_physical_owner')
        report = sidecar.scan(config)
        write(attempt / 'ACTUAL_ADMISSION.private.json', report)
        if not report['clear'] or report['blocking_reasons']:
            write(attempt / 'REFUSED.json', dict(status='DEVICE_BUSY_NO_RETRY', calls_charged=0))
            return dict(status='DEVICE_BUSY_NO_RETRY', calls_charged=0)
        validate(config_path, go_path)
        key, reservation = reserve(config_path, config)
        environment = dict(PATH='/usr/local/bin:/usr/bin:/bin', HOME=str(root / 'empty_home'),
            CUDA_VISIBLE_DEVICES=config['gpu_uuid'], PYTHONPATH=config['source_root'], PYTHONDONTWRITEBYTECODE='1',
            HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', TOKENIZERS_PARALLELISM='false',
            OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', R167_MAIN_GO_SHA256=sha(go_path),
            R167_EXECUTION_SHA256=sha(config_path))
        command = ['timeout', '--signal=TERM', '--kill-after=5s', str(config['max_job_seconds']) + 's',
            config['python'], '-B', '-m', 'gpu.orch_r167_object_survival_eval', 'evaluate',
            '--config', str(config_path), '--go', str(go_path)]
        process = None
        try:
            with (attempt / 'runner.private.log').open('x') as log:
                process = subprocess.Popen(command, cwd=attempt, env=environment, stdin=subprocess.DEVNULL,
                    stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
                write(attempt / 'LAUNCH.json', dict(identity=sidecar.identity(process.pid), execution=ref(config_path),
                    observed_unix=time.time(), calls_charged=3))
                returncode = process.wait()
            complete = read(attempt / 'sealed' / 'COMPLETE.json')
            require(returncode == 0 and complete['execution_sha256'] == sha(config_path)
                    and complete['calls'] == 3 and released(process, attempt, sidecar), 'complete_and_released_native_required')
            write(root / 'ledger' / (key + '.COMPLETE.json'), dict(status='COMPLETE', reservation=ref(reservation),
                calls=3, completed_unix=time.time()))
        except BaseException:
            if released(process, attempt, sidecar):
                write(root / 'ledger' / (key + '.FAILED.json'), dict(status='FAILED_NO_RETRY', reservation=ref(reservation)))
            else:
                write(attempt / 'UNRESOLVED.json', dict(status='UNRESOLVED_NO_RETRY', reservation=ref(reservation),
                    spawned_pid=process.pid if process is not None else None,
                    release_verified=False, observed_unix=time.time()))
            raise
    return status(root, config['plan']['sha256'])


def released(process, attempt, sidecar):
    if process is None:
        return True
    try:
        if process.poll() is None:
            return False
        identity = read(Path(attempt) / 'sealed' / 'PROCESS.json')['identity']
        return sidecar.gone(identity)
    except BaseException:
        return False


def evaluate(config_path, go_path):
    global USED
    require(go_path is not None, 'explicit_Main_GO_required_to_evaluate')
    require(os.getpid() == IMPORT_PID and not USED, 'one_condition_checkpoint_per_fresh_process')
    require(os.environ.get('R167_EXECUTION_SHA256') == sha(config_path), 'fresh_dispatch_binding')
    config, _, freeze, private, checkpoint = validate(config_path, go_path)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == config['gpu_uuid'], 'one_visible_device')
    key = f"{config['milestone']}_{config['condition']}"
    root = Path(config['campaign_root'])
    reservation = read(root / 'ledger' / (key + '.RESERVED.json'))
    require(reservation['execution'] == ref(config_path), 'charged_exact_execution')
    USED = True
    output = root / 'attempts' / key / 'sealed'
    output.mkdir(mode=0o700)
    from gpu import orch_r130_checkpoint_benchmark as native
    from gpu import orch_r130_benchmark_sidecar as sidecar
    from gpu.orch_r107_capability_run import readonly_condition
    write(output / 'PROCESS.json', dict(identity=sidecar.identity(os.getpid()), observed_unix=time.time()))
    engine_plan = dict(model_dir=config['model_dir'], gpu_uuid=config['gpu_uuid'])
    config_hash = sha(config_path)
    def check(label):
        require(time.time() < reservation['deadline_unix'] and sha(config_path) == config_hash, 'wall_and_config')
        if label != 'forward':
            require(sha(freeze['fingerprints']['path']) == freeze['fingerprints']['sha256'], 'immutable_private_fingerprint')
    try:
        engine = native._load_engine(engine_plan, checkpoint, check)
        before = native._snapshot(engine, engine_plan, checkpoint)
        write(output / 'BEFORE.private.json', before)
        for position, probe in enumerate(PROBES):
            check('call')
            rendered = messages(private['context'], probe)
            original = deepcopy(rendered)
            write(output / f'{position}.RESERVED.private.json', dict(position=position, condition=config['condition']))
            tokens = engine.tokenizer.apply_chat_template(rendered, tokenize=True, add_generation_prompt=True, return_dict=False)
            with readonly_condition(engine.model, config['condition']):
                native._require_readonly(engine.model, config['condition'])
                response = engine.generate(rendered, max_new_tokens=MAX_NEW_TOKENS)
            write(output / f'{position}.RAW.private.json', response)
            require(rendered == original, 'no_cross_probe_context_mutation')
            native._validate_response(response, original, len(tokens), engine.tokenizer.eos_token_id)
            definitions = private['definitions'] if config['milestone'] == 0 else {
                str(config['milestone']): private['definitions'][str(config['milestone'])]}
            instrument = 'behavior' if position == 2 else 'object'
            scores = {milestone: score(response, definition[instrument], private['context'], probe)
                      for milestone, definition in definitions.items()}
            write(output / f'{position}.SCORE.private.json', scores)
        after = native._snapshot(engine, engine_plan, checkpoint)
        require(after == before, 'readonly_adapter_base_unchanged')
        validate(config_path, go_path)
        check('complete')
        write(output / 'AFTER.private.json', after)
        write(output / 'COMPLETE.json', dict(status='COMPLETE', execution_sha256=config_hash, calls=3,
            checkpoint_commit_sha256=checkpoint['commit_sha256'], parent_access=False, completed_unix=time.time(),
            receipts={path.name: sha(path) for path in output.iterdir() if path.is_file()}))
        return dict(status='COMPLETE', calls=3)
    except BaseException as error:
        write(output / 'FAILED.json', dict(status='FAILED_NO_RETRY', error_type=type(error).__name__))
        raise


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('audit', 'plan', 'validate', 'dispatch', 'evaluate', 'status', 'reduce'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--freeze', type=Path)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--go', type=Path)
    parser.add_argument('--plan', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == 'audit':
            result = audit(args.output)
        elif args.action == 'plan':
            result = dict(status='PLAN_ONLY_NO_GPU', plan=write(args.output, make_plan(ref(args.freeze))), calls=CALL_CAP)
        elif args.action == 'status':
            result = status(CAMPAIGN, sha(args.plan))
        elif args.action == 'reduce':
            result = reduce_private(args.plan, args.output)
        else:
            result = globals()[args.action](args.config, args.go)
            if args.action == 'validate':
                result = dict(status='PASS_NO_GPU')
        print(json.dumps(result, sort_keys=True))
        return 0
    except BaseException:
        print(json.dumps(dict(status='REFUSED_OR_FAILED', details='PRIVATE_NO_AUTOMATIC_RETRY')))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
