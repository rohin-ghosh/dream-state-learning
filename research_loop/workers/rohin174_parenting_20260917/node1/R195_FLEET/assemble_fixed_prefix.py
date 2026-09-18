"""Reuse the R201 retained-prefix assembly; create no messages or native jobs."""

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import time
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parent
REMOTE = Path('/localhome/local-rohing/rohin174_parenting_20260917/node1/R195_FLEET/creative_b1')
CAPTURE_SHA = '29ca04c2c51671c7df922a4b05448586e74eec35da45b03009877baccbccce84'
PREFIX_SHA = '3a3b0a2f1cdb9144b30a6c3fba82de246e3db27d164d45b2addff0bd3968d57f'
SUFFIX_SHA = '271a13510cb0d9b14d8696efac9eb19d6ac5e29ba549a6a4d368b3ac27307aa0'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def digest(document):
    return hashlib.sha256(json.dumps(document, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def extract(path, target, expected_sha, permitted):
    require(sha(path) == expected_sha, 'fixed_archive_bytes')
    with tarfile.open(path) as archive:
        for member in archive.getmembers():
            name = Path(member.name)
            require(member.isfile() and not name.is_absolute() and '..' not in name.parts
                    and permitted(name) and not (target / name).exists(), 'no_overwrite_regular_prefix_member')
        archive.extractall(target, filter='data')


def main():
    require(ROOT == REMOTE and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'own_node1_CPU_namespace')
    require(sha(ROOT / 'MANIFEST.json') == CAPTURE_SHA, 'same_source_manifest')
    source = ROOT / 'source'
    sys.path.insert(0, str(source))
    from gpu import orch_r125_stream_journal as journal
    from organism_v6.orch_r125_continual_stream import ContinualStream
    capture = read(ROOT / 'MANIFEST.json')
    raw = ROOT / 'life'
    raw.mkdir(mode=0o700)
    extract(ROOT / 'RETAINED_PREFIX_0_5128.tar.gz', raw, PREFIX_SHA,
            lambda name: str(name) == 'PRESERVATION_RECEIPT.json' or name.parts[0] == 'stream')
    require(sha(raw / 'PRESERVATION_RECEIPT.json') ==
            'cc7d7f07ed29c952d8f57f17f679f0fdd2084d85711a763ddebba1a2f518f91e', 'original_prefix_receipt')
    extract(ROOT / 'FIXED_PREFIX_SUFFIX.tar.gz', raw / 'stream', SUFFIX_SHA,
            lambda name: len(name.parts) == 2 and name.parts[0] in ('records', 'inbox'))
    require(len(list((raw / 'stream/records').iterdir())) == 2 * 5847, 'full_contiguous_record_and_intent_count')
    (raw / 'stream/WRITER.lock').touch(exist_ok=False)
    previous = digest(read(raw / 'stream/JOURNAL.json'))
    registrations = {}
    for index in range(5847):
        record = read(raw / 'stream/records' / f'{index:020d}.json')
        require(record['index'] == index and record['previous_sha256'] == previous
                and record['sha256'] == digest({key: value for key, value in record.items() if key != 'sha256'}),
                'exact_immutable_full_prefix_chain')
        previous = record['sha256']
        if record['kind'] == 'INBOX':
            entry = record['document']
            registrations[Path(entry['source_id']).name] = entry['source_sha256']
    require(previous == capture['console_record']['sha256'] and record['kind'] == 'CONTEXT_COMMITTED',
            'exact_shared_console_cut_5846')
    unused = ROOT / 'captured_unregistered_inbox_not_replayed'
    unused.mkdir(mode=0o700)
    for path in (raw / 'stream/inbox').iterdir():
        if path.name not in registrations:
            path.rename(unused / path.name)
    require({path.name: sha(path) for path in (raw / 'stream/inbox').iterdir()} == registrations,
            'registered_history_only_no_future_inbox')
    checkpoint = raw / 'checkpoints/sleep_000051'
    checkpoint.mkdir(parents=True)
    for name in ('COMMIT.json', 'optimizer_rng.pt'):
        shutil.copy2(ROOT / 'snapshot/complete' / name, checkpoint / name)
    shutil.copytree(ROOT / 'snapshot/complete/adapter', checkpoint / 'adapter')
    source_plan = read(ROOT / 'snapshot/source_binding/PLAN.json')
    base_path = Path('/localhome/local-rohing/orch_r181_node1_20260917/operator/r144_base.py')
    require(sha(base_path) == '6e4d91c9581d952924ae269d7f4831fc9840c741805ebcddf2f2c78e8d356270', 'existing_snapshot_verifier')
    spec = importlib.util.spec_from_file_location('existing_r144_snapshot', base_path)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    base.verify_snapshot(raw / 'stream', source_plan['root'], capture['console_state_sha256'],
                         SimpleNamespace(journal=journal))
    state = record['document']['state']
    restored = ContinualStream.restore(state, expected_sha256=capture['console_state_sha256'])
    require(restored.checkpoint() == state and restored.pending is None
            and restored.sleep_frontier == len(restored.rows), 'actual_receiving_roundtrip')
    require(sha(checkpoint / 'optimizer_rng.pt') == capture['checkpoint']['checkpoint_sha256']['optimizer'],
            'complete51_optimizer_not_historical41')
    report = dict(status='FIXED_PREFIX_ASSEMBLED_AND_VERIFIED_NOT_LAUNCHED', observed_unix=time.time(),
        physical_new_clone_root=str(raw), inherited_logical_root=source_plan['root'],
        full_journal_records=5847, prefix_terminal_sha256=previous,
        context_state_sha256=state['sha256'], complete_cycle=51, optimizer_steps=4908,
        registered_inbox=len(registrations), unregistered_not_replayed=len(list(unused.iterdir())),
        full_receiving_journal_and_intents_verified=True, source41_weights_used=False,
        new_console_inputs=0, parent_publications=0, native_jobs=0, signals=0,
        next_input_order=['Main exact Rohin202 PART ONE', 'new Parent-B environment opening'],
        think_arm='STRUCTURED_EXACT_MAIN_PROMPT_PENDING', parent_guided_cycles=3, parent_withdrawn_cycles=3,
        peer_treatment=False, original_C2_creative_test_input_copied=False)
    with (ROOT / 'FIXED_PREFIX_READY.json').open('x') as output:
        json.dump(report, output, sort_keys=True, indent=2)
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
