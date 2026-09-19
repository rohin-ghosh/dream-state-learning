"""Source staging and historical-checkpoint inspection; no native activation."""

import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time


ALLOWED = {
    'gpu/orch_r184_think_act_learn.py',
    'organism_v6/orch_r125_continual_stream.py',
    'organism_v6/orch_r124_train_history.py',
    'gpu/r232_recovery.py',
    'gpu/checkpoint_tail_runtime.py',
    'gpu/pair_retention_runtime.py',
}
LIVES = {'curriculum_learner', 'curriculum_frozen_sibling'}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def checksum(content):
    return hashlib.sha256(content).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def write_once(path, document):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('x') as handle:
        json.dump(document, handle, sort_keys=True, indent=2, allow_nan=False)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())


def inventory(source):
    return {str(path.relative_to(source)): checksum(path.read_bytes())
        for path in source.rglob('*.py')}


def exact_native(observation):
    native = observation['native']
    process = Path('/proc') / str(native['pid'])
    fields = (process / 'stat').read_text().rsplit(') ', 1)[1].split()
    require(fields[19] == native['start_ticks'] and fields[0] not in ('Z', 'X', 'T', 't')
        and process.stat().st_uid == native['uid']
        and (process / 'cmdline').read_bytes().decode().rstrip('\0').split('\0') == native['argv']
        and str((process / 'cwd').resolve()) == native['cwd']
        and Path('/proc/sys/kernel/random/boot_id').read_text().strip() == native['boot_id'],
        'same_exact_live_unstopped_native')
    require(checksum(Path(observation['guard_path']).read_bytes()) == observation['guard_sha256'],
        'same_admitted_guard')
    return native


def validate_overlay(observation, prepared, overlay):
    require(observation['life'] in LIVES and prepared['life'] == observation['life'], 'pair_only')
    require(observation['status'] == 'EXACT_GUARDED_SOURCE_VERIFIED'
        and prepared['status'] == 'LOCAL_PREPARED_NOT_ADMITTED', 'explicit_staged_not_admitted_inputs')
    require(prepared['old_source_pins'] == observation['source_pins']
        and prepared['old_guard_sha256'] == observation['guard_sha256'], 'exact_old_source_and_guard')
    require(set(overlay) == ALLOWED and set(prepared['changed']) == ALLOWED,
        'exact_six_file_retention_and_reader_delta')
    expected = dict(observation['source_pins'])
    for name, text in overlay.items():
        change = prepared['changed'][name]
        require(change['before'] == observation['source_pins'].get(name)
            and change['after'] == checksum(text.encode()), 'exact_overlay_hashes')
        ast.parse(text, filename=name)
        expected[name] = change['after']
    require(expected == prepared['new_source_pins'], 'exact_complete_new_source_closure')
    require(prepared['deadline_unix'] == observation['plan']['hard_end_unix'], 'no_wall_extension')
    return expected


def stage_source(observation, prepared, overlay):
    expected = validate_overlay(observation, prepared, overlay)
    native = exact_native(observation)
    original = Path(native['cwd'])
    require(inventory(original) == observation['source_pins'], 'old_source_still_exact')
    target = Path(prepared['new_source'])
    require(target == Path('/localhome/local-rohing/orch_retention_20260919')
        / observation['life'] / 'epoch2/source' and not target.parent.exists(), 'new_exact_epoch2_only')
    target.parent.mkdir(parents=True, mode=0o700)
    shutil.copytree(original, target, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    require(inventory(target) == observation['source_pins'], 'copied_old_closure_exact')
    for name, text in overlay.items():
        (target / name).write_text(text)
    require(inventory(target) == expected and inventory(original) == observation['source_pins'],
        'only_authorized_source_changes_original_untouched')
    exact_native(observation)
    receipt = dict(status='EPOCH2_STAGED_NOT_ADMITTED_NOT_DISPATCHABLE',
        observed_unix=time.time(), life=observation['life'], new_source=str(target),
        old_source=str(original), old_guard_sha256=observation['guard_sha256'],
        old_source_pins=observation['source_pins'], new_source_pins=expected,
        changed=prepared['changed'], native=native, journal_id=observation['journal_id'],
        journal_root=observation['journal_root'], native_signals=[], GPU_calls=0,
        hard_end_unix=prepared['deadline_unix'], receiving_plan_ready=False,
        checkpoint_validated=False, live_boundary_reserved=False)
    write_once(target.parent / 'SOURCE_STAGED.json', receipt)
    return receipt


def latest_historical_candidate(observation, boundary, header):
    root = Path(observation['journal_root'])
    directory = root / 'records'
    manifest = read(root / 'JOURNAL.json')
    require(manifest['journal_id'] == observation['journal_id'], 'same_journal')
    metadata = [header(path) for path in sorted(directory.glob('[0-9]' * 20 + '.json'))[-512:]]
    binding = dict(journal_id=observation['journal_id'], hard_end_unix=observation['plan']['hard_end_unix'])
    for position in reversed(range(len(metadata))):
        if metadata[position]['kind'] != 'SLEEP_COMPLETE':
            continue
        selected = [metadata[position]]
        for item in metadata[position + 1:]:
            if item['kind'] not in ('INBOX', 'R184_LEARN_COMPLETE'):
                break
            selected.append(item)
            if item['kind'] == 'R184_LEARN_COMPLETE':
                records = [boundary.read(directory / f'{entry["index"]:020d}.json') for entry in selected]
                intents = {entry['index']: boundary.read(directory / f'{entry["index"]:020d}.intent.json')
                    for entry in selected}
                candidate = boundary.validate_records(records, binding, intents=intents)
                require(candidate is not None, 'historical_COMPLETE_LEARN_pair')
                return candidate, metadata[-1]['index']
    raise ValueError('no_complete_checkpoint_in_bounded_observation')


def checkpoint_probe(observation, staged, operator, plan, boundary, header):
    exact_native(observation)
    source = Path(staged['new_source'])
    require(inventory(source) == staged['new_source_pins'], 'receiving_source_exact')
    require(plan['source_root'] == str(source) and plan['hard_end_unix'] == observation['plan']['hard_end_unix'],
        'same_deadline_source_template')
    candidate, observed_head = latest_historical_candidate(observation, boundary, header)
    attempt = Path(operator) / ('checkpoint_' + str(time.time_ns()))
    request = attempt / 'REQUEST.json'
    write_once(request, dict(source=str(source), candidate=candidate, plan=plan))
    command = ['/localhome/local-rohing/v2/venv/bin/python', '-B', str(Path(operator) / 'cpu_probe.py'),
        'checkpoint', '--request', str(request)]
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1')
    started = time.monotonic()
    result = subprocess.run(command, cwd=source, env=environment, capture_output=True, text=True, timeout=120)
    write_once(attempt / 'PROCESS_RESULT.json', dict(returncode=result.returncode,
        stdout=result.stdout, stderr=result.stderr, elapsed_seconds=time.monotonic() - started))
    require(result.returncode == 0, 'checkpoint_CPU_probe_failed_preserved')
    evidence = json.loads(result.stdout)
    require(all(evidence.get(name) is True for name in ('adapter_verified', 'optimizer_verified',
        'python_cpu_cuda_rng_verified', 'working_state_verified', 'no_GPU_calls')), 'actual_checkpoint_CPU_evidence')
    exact_native(observation)
    require(inventory(source) == staged['new_source_pins'], 'probe_preserved_source')
    receipt = dict(status='REAL_HISTORICAL_CHECKPOINT_CPU_VERIFIED_NOT_A_LIVE_HANDOFF',
        life=observation['life'], observed_unix=time.time(), elapsed_seconds=time.monotonic() - started,
        complete_index=candidate['complete_index'], complete_sha256=candidate['complete_sha256'],
        learn_index=candidate['learn_index'], observed_head=observed_head,
        checkpoint_sha256=candidate['checkpoint']['checkpoint_sha256'],
        optimizer_steps=candidate['checkpoint']['optimizer_steps'], source=str(source),
        request_path=str(request), request_sha256=checksum(request.read_bytes()), evidence=evidence,
        native_signals=[], GPU_calls=0, live_boundary_reserved=False, native_unchanged=True,
        historical_checkpoint_only=True, receiving_guard_or_admission_proven=False)
    write_once(attempt / 'RECEIPT.json', receipt)
    return receipt
