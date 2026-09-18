"""Prospectively bounded continuation; old pilot artifacts are read-only."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import time

from gpu import orch_continual_batch_publish as publisher
from gpu import orch_continual_batch_handoff as handoff
from organism_v6 import orch_continual_batch as policy


WORKSPACE = Path('/data/home/rohing/dream-state-orch')
PILOT = WORKSPACE / 'research_notes/analysis/orch_continual_batch_20260915_attempt1'
ROOT = WORKSPACE / 'research_notes/analysis/orch_continual_batch_20260915_segment2'
REMOTE = '/localhome/local-rohing/orch_continual_batch_20260915_segment2'
JOURNAL = WORKSPACE / 'research_loop/workers/CONTINUAL_BATCH.md'
read, write, sha = publisher.read, publisher.write, publisher.sha


def configure():
    publisher.REPO = WORKSPACE
    publisher.ROOT = ROOT
    publisher.REMOTE = REMOTE
    publisher.LINE_REVIEWS = True


def journal(text):
    with JOURNAL.open('a') as stream:
        stream.write('\n\n## ' + datetime.now(timezone.utc).isoformat() + ' — CONTINUAL SEGMENT2\n\n' + text + '\n')


def select_node2():
    publisher.SSH_SCRIPT = 'gpu/ovx_ssh.sh'
    publisher.SCP_SCRIPT = 'gpu/ovx_scp.sh'
    publisher.SNAPSHOT_MODULE = 'gpu.orch_continual_batch_snapshot_node2'


def add_node2():
    policy.require(not (ROOT / 'WATCH_LIFETIME.json').exists(), 'prospective_source_addition_only')
    select_node2()
    source = '/localhome/local-rohing/orch_rich_hot_node2_20260915_attempt1'
    original = read(WORKSPACE / 'research_notes/analysis/orch_rich_hot_node2_20260915_attempt1/PREPARE.json')
    registry = read(ROOT / 'SOURCE_REGISTRY.json')
    registry['sources'][source] = dict(purpose=policy.PURPOSE, family='math',
        source_purpose='L1_EXTERNAL_GENERATION', parenting_experience=False,
        source_archive_sha256=original['source_sha256'], protocol_sha256=original['files']['PROTOCOL.md'],
        authority='Rohin continuous LIVE math/code/route generation; node2 original L1 richness only, never L2 sibling roots')
    write(ROOT / 'SOURCE_REGISTRY.json', registry)
    publisher.remote(f'mkdir -p {REMOTE}/source; tar -xf {source}/source.tar -C {REMOTE}/source')
    publisher.upload([WORKSPACE / 'gpu/orch_continual_batch_snapshot_node2.py',
                      WORKSPACE / 'gpu/orch_continual_batch_snapshot.py'], REMOTE + '/source/gpu/')
    publisher.upload([WORKSPACE / 'organism_v6/orch_continual_batch.py'], REMOTE + '/source/organism_v6/')
    publisher.upload([ROOT / 'EXCLUSIONS.json', ROOT / 'SOURCE_REGISTRY.json'], REMOTE + '/')
    frozen = read(ROOT / 'PREPARED.json')
    names = set(frozen['source_inventory']) | {'gpu/orch_continual_batch_snapshot_node2.py'}
    for name in sorted(names):
        shutil.copyfile(WORKSPACE / name, ROOT / 'pinned_source' / name)
    inventory = {name: sha(ROOT / 'pinned_source' / name) for name in sorted(names)}
    write(ROOT / 'SOURCE_INVENTORY.json', inventory)
    frozen.update(source_inventory=inventory)
    frozen['files'] = {name: sha(ROOT / name) for name in frozen['files']}
    write(ROOT / 'PREPARED.json', frozen)
    batch, selected = publisher.collect(1)
    write(ROOT / 'NODE2_FIRST_CAPTURE.json', dict(batch=str(batch), complete_sample=selected is not None,
        checks_sha256=sha(batch / 'SOURCE_CHECKS.json')))


def prepare():
    policy.require((PILOT / 'WATCH_TERMINAL.json').exists(), 'pilot_must_be_terminal')
    ROOT.mkdir()
    registration = dict(read(PILOT / 'REGISTRATION.json'), max_batches=64, max_provider_calls=128,
        watcher_seconds=7200, serialization='IMMUTABLE_TARGET_LINE_IDS_V2',
        source_purpose='L1_EXTERNAL_GENERATION', parenting_experience=False,
        future_only_no_pilot_relabel_or_review=True, pilot_root=str(PILOT),
        source_priority=['new_route', 'new_code', 'V2_prompt_math', 'registered_existing_live_math'],
        unavailable_sources='observe producer journals; require separately bound mechanical adapter before intake',
        minimum_available_memory_bytes=800 * 1024**2, two_parallel_memory_bytes=2400 * 1024**2,
        registration_utc=datetime.now(timezone.utc).isoformat())
    write(ROOT / 'REGISTRATION.json', registration)
    registry = read(PILOT / 'SOURCE_REGISTRY.json')
    registry['external_generation_required'] = True
    for source in registry['sources'].values():
        source.update(source_purpose='L1_EXTERNAL_GENERATION', parenting_experience=False)
    write(ROOT / 'SOURCE_REGISTRY.json', registry)
    instructions = (PILOT / 'REVIEW_INSTRUCTIONS.md').read_text()
    instructions = instructions.replace('Cite short exact literal target spans for actual operations,\nown account, checks or the identified defect.',
        'Select evidence_line_ids from target_source_lines for actual operations,\nown account, checks or the identified defect. Read ALL numbered lines.\n'
        'Do not retype evidence_spans: the publisher copies the exact immutable selected lines.\n'
        'independent_answer MUST be a numeric STRING: 5, -2, 0.25, or 1/3.\n'
        'No units, FINAL prefix, prose, commas, leading/trailing spaces, plus sign, or exponent.\n'
        'Use an exact fraction rather than rounding. Never change a wrong answer to match gold.')
    policy.require('Select evidence_line_ids' in instructions, 'future_prompt_replacement_required')
    (ROOT / 'REVIEW_INSTRUCTIONS.md').write_text(instructions)
    publisher.prepare()
    frozen = read(ROOT / 'PREPARED.json')
    prior_files = sorted(path for path in PILOT.rglob('*') if path.is_file())
    write(ROOT / 'PILOT_INVENTORY.json', {str(path.relative_to(PILOT)): sha(path) for path in prior_files})
    seen = set(read(PILOT / 'SEEN.json')) | set(read(ROOT / 'SEEN_INITIAL.json'))
    for path in PILOT.glob('batch_*/CANDIDATES.json'):
        seen.update(row['target_sha256'] for row in read(path))
    old = WORKSPACE / 'research_notes/analysis/orch_continual_ingest_20260915/batch_math_content_readmission473'
    manifest = read(old / 'MANIFEST.json')
    policy.require(sha(old / manifest['rows_path']) == manifest['rows_sha256'], 'old473_binding')
    seen.update(row['eligibility']['target_sha256'] for row in read(old / manifest['rows_path']))
    write(ROOT / 'SEEN_INITIAL.json', sorted(seen))
    write(ROOT / 'SEEN.json', sorted(seen))
    names = set(frozen['source_inventory']) | {
        'gpu/orch_continual_batch_segment.py', 'gpu/orch_continual_batch_handoff.py',
        'tests/test_orch_continual_batch_serialization.py', 'tests/test_orch_continual_batch_handoff.py',
        'tests/test_orch_continual_batch_immutable.py',
        'gpu/orch_continual_batch_runtime.py', 'tests/test_orch_continual_batch_runtime.py',
        'gpu/__init__.py', 'organism_v6/__init__.py', 'research_loop/__init__.py'}
    pinned = ROOT / 'pinned_source'
    for name in sorted(names):
        destination = pinned / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(WORKSPACE / name, destination)
    inventory = {name: sha(pinned / name) for name in sorted(names)}
    write(ROOT / 'SOURCE_INVENTORY.json', inventory)
    registration = read(ROOT / 'REGISTRATION.json')
    lifetime = json.loads(publisher.remote(f'cat {publisher.SOURCE}/LIFETIME.json').stdout)
    registration['source_lease_deadline_unix'] = lifetime['hard_deadline_unix']
    registration['segment_deadline_unix'] = min(time.time() + 7200, lifetime['hard_deadline_unix'])
    write(ROOT / 'REGISTRATION.json', registration)
    frozen.update(source_inventory=inventory, pinned_source=str(pinned))
    frozen['files'] = {name: sha(ROOT / name) for name in (*frozen['files'], 'PILOT_INVENTORY.json')}
    write(ROOT / 'PREPARED.json', frozen)
    batch, selected = publisher.collect(0)
    write(ROOT / 'FIRST_CAPTURE.json', dict(batch=str(batch), complete_sample=selected is not None,
        checks_sha256=sha(batch / 'SOURCE_CHECKS.json')))


def memory_available():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1]) * 1024
    return 0


def source_notices():
    observations = {}
    for name in ('RICH_HOT_NODE2.md', 'RICH_HOT_NODE3.md', 'RICH_HOT_NODE1.md'):
        path = WORKSPACE / 'research_loop/workers' / name
        if path.exists():
            observations[name] = dict(sha256=sha(path), modified_unix=path.stat().st_mtime)
    for name in ('orch_rich_hot_node3_20260915_route_v2/PUBLICATION.json',
                 'orch_rich_hot_node2_floor98_20260915_attempt1/PUBLICATION.json'):
        path = WORKSPACE / 'research_notes/analysis' / name
        if path.exists():
            observations[name] = dict(sha256=sha(path), modified_unix=path.stat().st_mtime,
                pending='new route/code source publication detected; requires bound domain encoder/consumer adapter, not automatic admission')
    previous = read(ROOT / 'SOURCE_NOTICES.json') if (ROOT / 'SOURCE_NOTICES.json').exists() else {}
    write(ROOT / 'SOURCE_NOTICES.json', dict(observed_unix=time.time(), producers=observations,
        changed=[name for name, value in observations.items() if previous.get('producers', {}).get(name) != value],
        admission='metadata_only_no_unregistered_or_parenting_intake', priorities=['new_route', 'new_code', 'V2_math']))


def watch():
    policy.require(publisher.RUNTIME_ROOT is not None, 'use_external_hash_bound_runtime_launcher')
    select_node2()
    prepared = read(ROOT / 'PREPARED.json')
    policy.require(all(sha(Path(publisher.RUNTIME_SOURCE or prepared['pinned_source']) / path) == digest
                       for path, digest in prepared['source_inventory'].items()), 'pinned_source_drift')
    policy.require(all(sha(ROOT / path) == digest for path, digest in prepared['files'].items()), 'registration_drift')
    ready = read(ROOT / 'READY.json')
    policy.require(ready['cpu_tests_passed'] and ready['prepare_sha256'] == sha(ROOT / 'PREPARED.json') and
                   ready['builder_receipt_sha256'] == sha(ROOT / 'BUILDER_RECEIPT.md'), 'dated_builder_receipt_required')
    registration = read(ROOT / 'REGISTRATION.json')
    start = time.time()
    deadline = registration['segment_deadline_unix']
    policy.require(start < deadline, 'segment_expired_no_reset')
    with (ROOT / 'WATCH_LIFETIME.json').open('x') as stream:
        json.dump(dict(started_unix=start, deadline_unix=deadline, max_batches=64, max_provider_calls=128,
            inherited_lease_deadline_unix=registration['source_lease_deadline_unix'], pid=os.getpid()), stream)
    os.environ['ORCH_CONTINUAL_BATCH_CODEX_REAL'] = prepared['codex_real']
    os.environ['PATH'] = str(ROOT / 'provider_bin') + os.pathsep + os.environ['PATH']
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    published, totals, targets, qualified, admitted = [], {}, set(), set(), set()
    first_native, last_native, number, reserved = None, None, 0, 0
    while time.time() + 660 < deadline and reserved < 128:
        if shutil.disk_usage(ROOT).free < 512 * 1024**2:
            write(ROOT / 'DISK_WAIT.json', dict(observed_unix=time.time(), free_bytes=shutil.disk_usage(ROOT).free))
            time.sleep(30)
            continue
        source_notices()
        available = memory_available()
        if available < registration['minimum_available_memory_bytes']:
            write(ROOT / 'MEMORY_WAIT.json', dict(observed_unix=time.time(), available_bytes=available))
            time.sleep(30)
            continue
        publisher.REVIEW_PARALLEL = 2 if available >= registration['two_parallel_memory_bytes'] else 1
        capture_start = time.time()
        batch = ROOT / f'batch_{number:03d}'
        outcome = 'NO_FULL_BATCH'
        try:
            if (batch / 'SOURCE_CHECKS.json').exists():
                rows = read(batch / 'CANDIDATES.json')
                selected = policy.sample(rows) if len(rows) == 64 else None
            else:
                batch, selected = publisher.collect(number)
            if selected is not None and time.time() + 660 < deadline:
                rows = read(batch / 'CANDIDATES.json')
                targets.update(row['target_sha256'] for row in rows)
                stamps = [row['provenance']['native_finished_unix'] for row in rows]
                first_native = min(stamps + ([first_native] if first_native is not None else []))
                last_native = max(stamps + ([last_native] if last_native is not None else []))
                write(ROOT / 'SEEN.json', sorted(set(read(ROOT / 'SEEN.json')) | targets))
                with (batch / 'REVIEW_RESERVATION.json').open('x') as stream:
                    json.dump(dict(calls=[reserved + 1, reserved + 2], reserved_unix=time.time(),
                        deadline_unix=deadline, parallelism=publisher.REVIEW_PARALLEL, memory_available_bytes=available), stream)
                reserved += 2
                write(ROOT / 'REVIEW_BUDGET.json', dict(reserved=reserved, limit=128, no_retry=True))
                manifest_path = publisher.publish(number, batch, selected)
                outcome = 'ACCEPTED' if manifest_path else 'REJECTED'
                reviews = read(batch / 'SAMPLED_REVIEWS.json')
                qualified.update(review['target_sha256'] for review in reviews if review['status'] == 'PASS')
                if manifest_path:
                    wrapper = handoff.emit(batch)
                    wrapped = read(wrapper)
                    admitted.update(wrapped['target_sha256s'])
                    published.append(dict(path=str(wrapper), sha256=sha(wrapper), row_count=wrapped['row_count']))
                    write(ROOT / 'INGEST_HANDOFFS.json', dict(manifests=published, training_ingestion_not_asserted=True))
                    journal(f'Laplace/Main: NEW sampled-wrapper available `{wrapper}` SHA256 `{sha(wrapper)}`; '
                        f'{wrapped["row_count"]} batch-eligible rows; sampled PASS / unsampled individually UNREVIEWED preserved. '
                        'No trainer consumption claimed; append once without reset. Segment continues within its original bound.')
        except Exception as error:
            outcome = 'FAILED_PRESERVED_NO_RETRY'
            write(ROOT / f'BATCH_{number:03d}_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        for group in range(2):
            usage_path = ROOT / 'review_workspace' / f'batch_{number:03d}_{group}' / 'USAGE.json'
            if usage_path.exists():
                for key, value in read(usage_path)['reported_components'].items():
                    totals[key] = totals.get(key, 0) + value
        elapsed = time.time() - start
        write(ROOT / 'LIVE_STATUS.json', dict(observed_unix=time.time(), publisher_started_unix=start,
            actual_publisher_wall_seconds=elapsed, deadline_unix=deadline, snapshot_number=number,
            last_batch_outcome=outcome, last_batch_wall_seconds=time.time() - capture_start,
            first_selected_native_capture_unix=first_native, last_selected_native_capture_unix=last_native,
            distinct_mechanically_valid_targets=len(targets), distinct_sampled_individually_qualified=len(qualified),
            distinct_batch_admitted_targets=len(admitted), published_batches=len(published), reserved_review_calls=reserved,
            reported_provider_components=totals, components_not_assumed_disjoint=True,
            sampled_qualified_per_publisher_hour=len(qualified) * 3600 / max(elapsed, 1),
            batch_admitted_per_publisher_hour=len(admitted) * 3600 / max(elapsed, 1), trainer_ingestion_not_asserted=True))
        number += 1
        time.sleep(30 if outcome == 'NO_FULL_BATCH' else 2)
    unchanged = all((PILOT / path).exists() and sha(PILOT / path) == digest
                    for path, digest in read(ROOT / 'PILOT_INVENTORY.json').items())
    write(ROOT / 'WATCH_TERMINAL.json', dict(finished_unix=time.time(), deadline_unix=deadline,
        manifests=published, reserved_review_calls=reserved, pilot_inventory_unchanged=unchanged,
        reason='REGISTERED_CAP_OR_DEADLINE_MARGIN', actual_publisher_wall_seconds=time.time() - start))
    journal(f'Segment2 terminal at registered cap/deadline margin; {reserved}/128 reserved calls, '
        f'{len(published)} published batches; pilot unchanged={unchanged}. No automatic budget reset.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'watch'))
    options = parser.parse_args()
    configure()
    globals()[options.phase]()
