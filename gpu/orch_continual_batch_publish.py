"""Finite live-source batching and two-at-a-time sampled author review."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tarfile
import time

from organism_v6 import orch_continual_batch as policy
from research_loop.agents import run_agent, build_prompt


REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / 'research_notes/analysis/orch_continual_batch_20260915_attempt1'
REMOTE = '/localhome/local-rohing/orch_continual_batch_20260915_sidecar'
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
SOURCE = '/localhome/local-rohing/orch_rich_hot_a100_20260915_attempt1'
LINE_REVIEWS = False
REVIEW_PARALLEL = 2
SSH_SCRIPT = 'gpu/a100_ssh.sh'
SCP_SCRIPT = 'gpu/a100_scp.sh'
SNAPSHOT_MODULE = 'gpu.orch_continual_batch_snapshot'
RUNTIME_ROOT = None
RUNTIME_SOURCE = None
BRANCH_V3 = False


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.partial')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')
    temporary.replace(path)


def command(arguments):
    return subprocess.run(arguments, cwd=REPO, check=True, text=True, capture_output=True, timeout=240)


def remote(command_text):
    if RUNTIME_ROOT is not None:
        return command(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
                        os.environ['ORCH_CONTINUAL_BATCH_SSH_TARGET'], command_text])
    return command(['bash', SSH_SCRIPT, command_text])


def upload(paths, destination):
    if RUNTIME_ROOT is not None:
        return command(['scp', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', *map(str, paths),
                        os.environ['ORCH_CONTINUAL_BATCH_SSH_TARGET'] + ':' + destination])
    return command(['bash', SCP_SCRIPT, *map(str, paths), 'NODE:' + destination])


def download(source, destination):
    if RUNTIME_ROOT is not None:
        return command(['scp', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
                        os.environ['ORCH_CONTINUAL_BATCH_SSH_TARGET'] + ':' + source, str(destination)])
    return command(['bash', SCP_SCRIPT, 'NODE:' + source, str(destination)])


def extract_snapshot_once(archive_path, destination):
    destination = Path(destination).resolve()
    with tarfile.open(archive_path) as archive:
        members, targets = [], set()
        for member in archive.getmembers():
            relative = Path(member.name)
            policy.require(not relative.is_absolute() and '..' not in relative.parts and member.isfile(),
                           'unsafe_snapshot_archive')
            target = destination / relative
            resolved = target.resolve()
            policy.require(destination in resolved.parents, 'snapshot_path_escape')
            policy.require(resolved not in targets, 'duplicate_snapshot_member')
            policy.require(not target.exists() and not target.is_symlink(), 'snapshot_member_already_exists')
            targets.add(resolved)
            members.append((member, target))
        for member, target in members:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream, archive.extractfile(member) as source:
                shutil.copyfileobj(source, stream)


def schema():
    string = dict(type='string')
    axes = {axis: dict(type=['boolean', 'null']) for axis in policy.AXES}
    properties = dict(target_sha256=string, raw_call_sha256=string, student_prefix_sha256=string,
        status=dict(type='string', enum=['PASS', 'FAIL', 'UNRESOLVED']), reason=string, prefix_reason=string,
        full_text_read=dict(type='boolean'), evidence_spans=dict(type='array', items=string),
        gold_status=dict(type='string', enum=['VALID', 'INVALID', 'AMBIGUOUS']),
        independent_answer=string, gold_reason=string, has_meaningful_branch=dict(type='boolean'),
        branching_alternative=string, branch_rejection_reason=string,
        semantic_novelty=dict(type='string', enum=['APPLIED_REASONING', 'RAW_RECAP', 'UNRESOLVED']), **axes)
    review = dict(type='object', properties=properties, required=list(properties), additionalProperties=False)
    if LINE_REVIEWS:
        del properties['evidence_spans']
        properties['evidence_line_ids'] = dict(type='array', items=dict(type='integer', minimum=1), minItems=1)
        properties['independent_answer'] = dict(type='string',
            pattern=r'^-?(?:0|[1-9]\d*)(?:\.\d+|/[1-9]\d*)?$',
            description='Exact numeric answer only: 5, -2, 0.25, or 1/3. No units, prose, commas, spaces, plus sign or exponent. Never change an answer to match gold.')
        review['required'] = list(properties)
    if BRANCH_V3:
        line_ids = dict(type='array', items=dict(type='integer', minimum=1))
        approach = dict(approach_id=string, description=string, considered_line_ids=line_ids,
            pursued_line_ids=line_ids, rejected=dict(type='boolean'), rejection_reason=string,
            rejection_line_ids=line_ids)
        branch = dict(measurement_status=dict(type='string', enum=['MEASURED', 'UNKNOWN']),
            semantic_distinct_approaches_considered=dict(type=['integer', 'null'], minimum=0),
            semantic_distinct_approaches_pursued=dict(type=['integer', 'null'], minimum=0),
            approaches=dict(type='array', items=dict(type='object', properties=approach,
                required=list(approach), additionalProperties=False)), repetition_failure=dict(type=['boolean', 'null']),
            repetition_reason=string, repetition_line_ids=line_ids)
        properties['branch_metrics'] = dict(type='object', properties=branch, required=list(branch), additionalProperties=False)
        review['required'] = list(properties)
    return dict(type='object', properties=dict(reviews=dict(type='array', items=review)),
                required=['reviews'], additionalProperties=False)


def prepare():
    policy.require(not (ROOT / 'PREPARED.json').exists(), 'prepare_once')
    combined = REPO / 'research_notes/analysis/orch_combined_l1_20260915_attempt1'
    held = read(combined / 'COHORT.json')['tasks']
    from gpu.astra_goal_quality_train import goal
    route_ids = set()
    for probe in read(combined / 'ROUTE_COHORT.json')['probes']:
        route_ids.update(goal.identifiers(probe['collection']['world']))
    exclusions = dict(math_ids=sorted(task['id'] for task in held),
        question_hashes=sorted(policy.math.digest(' '.join(task['question'].lower().split())) for task in held),
        route_ids=sorted(route_ids), source_files={str(combined / name): sha(combined / name)
        for name in ('COHORT.json', 'ROUTE_COHORT.json')}, no_held_results_read=True)
    write(ROOT / 'EXCLUSIONS.json', exclusions)
    baseline = [combined / 'PACKET/ADMITTED_ROWS.json',
        REPO / 'research_notes/analysis/orch_continual_ingest_20260915/batch_math_final_delta76/ROWS.json']
    seen = sorted({row['target_sha256'] for path in baseline for row in read(path)})
    write(ROOT / 'SEEN_INITIAL.json', seen)
    write(ROOT / 'SEEN.json', seen)
    registration = read(ROOT / 'REGISTRATION.json')
    registration['registration_utc'] = datetime.now(timezone.utc).isoformat()
    write(ROOT / 'REGISTRATION.json', registration)
    workspace = ROOT / 'review_workspace'
    workspace.mkdir()
    shutil.copyfile(ROOT / 'REVIEW_INSTRUCTIONS.md', workspace / 'REVIEW_INSTRUCTIONS.md')
    provider_bin = ROOT / 'provider_bin'
    provider_bin.mkdir()
    shutil.copyfile(REPO / 'gpu/orch_continual_batch_codex.sh', provider_bin / 'codex')
    (provider_bin / 'codex').chmod(0o700)
    owned = ['gpu/orch_continual_batch_snapshot.py', 'gpu/orch_continual_batch_publish.py',
        'gpu/orch_continual_batch_codex.sh', 'organism_v6/orch_continual_batch.py',
        'tests/test_orch_continual_batch.py', 'research_loop/agents.py', 'research_loop/io.py',
        'organism_v6/orch_math_rich.py']
    source_inventory = {name: sha(REPO / name) for name in owned}
    write(ROOT / 'SOURCE_INVENTORY.json', source_inventory)
    write(ROOT / 'PREPARED.json', dict(source_inventory=source_inventory,
        files={name: sha(ROOT / name) for name in ('REGISTRATION.json', 'SOURCE_REGISTRY.json',
            'EXCLUSIONS.json', 'SEEN_INITIAL.json', 'REVIEW_INSTRUCTIONS.md', 'SOURCE_INVENTORY.json')},
        baseline={str(path): sha(path) for path in baseline}, codex_real=shutil.which('codex'),
        prepared_utc=datetime.now(timezone.utc).isoformat(), source_purpose=policy.PURPOSE))
    remote(f'mkdir -p {REMOTE}/source; test -f {REMOTE}/source/gpu/orch_rich_hot_a100_run.py || tar -xf {SOURCE}/source.tar -C {REMOTE}/source')
    upload([REPO / 'gpu/orch_continual_batch_snapshot.py'], REMOTE + '/source/gpu/')
    upload([REPO / 'organism_v6/orch_continual_batch.py'], REMOTE + '/source/organism_v6/')
    upload([ROOT / 'EXCLUSIONS.json', ROOT / 'SOURCE_REGISTRY.json'], REMOTE + '/')


def collect(number):
    batch = ROOT / f'batch_{number:03d}'
    batch.mkdir()
    upload([ROOT / 'SEEN.json'], REMOTE + '/')
    location = f'{REMOTE}/orch_continual_batch_snapshot_{number:03d}'
    result = remote(f'env CUDA_VISIBLE_DEVICES= HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 '
        f'PYTHONPATH={REMOTE}/source {PYTHON} -B -m {SNAPSHOT_MODULE} '
        f'--output {location} --exclusions {REMOTE}/EXCLUSIONS.json --seen {REMOTE}/SEEN.json --registry {REMOTE}/SOURCE_REGISTRY.json')
    (batch / 'SNAPSHOT_LOG.txt').write_text(result.stdout + result.stderr)
    download(location + '.tar.gz', batch / 'SOURCE_SNAPSHOT.tar.gz')
    extract_snapshot_once(batch / 'SOURCE_SNAPSHOT.tar.gz', batch)
    with (batch / 'ARCHIVE_BINDING.json').open('x') as stream:
        json.dump(dict(archive_path=str(batch / 'SOURCE_SNAPSHOT.tar.gz'),
            archive_sha256=sha(batch / 'SOURCE_SNAPSHOT.tar.gz'), unique_batch_directory=str(batch),
            extraction_mode='EXCLUSIVE_CREATE_NO_REFRESH_OR_OVERWRITE'), stream, indent=2)
    for name in ('EXCLUSIONS.json', 'REGISTRATION.json', 'SOURCE_REGISTRY.json'):
        shutil.copyfile(ROOT / name, batch / name)
    checks = read(batch / 'SOURCE_CHECKS.json')
    policy.require(checks['candidates_sha256'] == sha(batch / 'CANDIDATES.json') and
                   checks['exclusions_sha256'] == sha(ROOT / 'EXCLUSIONS.json') and
                   checks['source_registry_sha256'] == sha(ROOT / 'SOURCE_REGISTRY.json'), 'snapshot_binding_mismatch')
    for relative, digest in read(batch / 'RAW_INVENTORY.json').items():
        policy.require(sha(batch / 'raw' / relative) == digest, 'raw_source_corruption')
    rows = read(batch / 'CANDIDATES.json')
    if len(rows) != policy.BATCH_SIZE:
        write(batch / 'INSUFFICIENT.json', dict(selected=len(rows), required=policy.BATCH_SIZE))
        return batch, None
    selected = policy.sample(rows)
    write(batch / 'SAMPLE_REGISTRATION.json', dict(registration_sha256=sha(ROOT / 'REGISTRATION.json'),
        candidates_sha256=sha(batch / 'CANDIDATES.json'), sample_target_sha256s=[row['target_sha256'] for row in selected],
        registered_utc=datetime.now(timezone.utc).isoformat(), semantic_results_seen=False))
    for group in range(2):
        directory = ROOT / 'review_workspace' / f'batch_{number:03d}_{group}'
        directory.mkdir()
        subset = selected[group * 6:(group + 1) * 6]
        packet = [dict(target=row['target'], student_prefix=row['student_prefix'], question=row['question'],
            gold=row['gold'], target_sha256=row['target_sha256'], raw_call_sha256=row['provenance']['raw_call_sha256'],
            student_prefix_sha256=row['student_prefix_sha256']) for row in subset]
        if LINE_REVIEWS:
            for item in packet:
                item['target_source_lines'] = policy.source_lines(item.pop('target'))
        write(directory / 'PACKET.json', packet)
        write(directory / 'SCHEMA.json', schema())
    return batch, selected


def usage(directory):
    events, totals, tools = [], {}, []
    for line in (directory / 'reader/stdout.log').read_text().splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value.get('usage'), dict):
            events.append(value['usage'])
            for key, count in value['usage'].items():
                if isinstance(count, int):
                    totals[key] = totals.get(key, 0) + count
        item = value.get('item', {})
        if item.get('type') in ('command_execution', 'mcp_tool_call', 'web_search', 'file_change'):
            tools.append(item)
    return dict(reported_components=totals, usage_events=events, usage_reported=bool(events), tool_events=tools,
                cached_input_is_component_not_added_twice=True)


def review_group(number, group, rows):
    policy.require(RUNTIME_ROOT is not None and ROOT.resolve().is_relative_to(Path(RUNTIME_ROOT).resolve()),
                   'future_reviews_require_external_runtime')
    workspace = ROOT / 'review_workspace'
    directory = workspace / f'batch_{number:03d}_{group}'
    node = dict(provider='codex', allow_write=False, provider_attempts=1, provider_attempt_timeout_sec=300,
        prompt_file='REVIEW_INSTRUCTIONS.md', schema_file=str((directory / 'SCHEMA.json').relative_to(workspace)),
        context_files=[str((directory / 'PACKET.json').relative_to(workspace))],
        max_context_chars_per_file=64000, reasoning_effort='low')
    prompt = build_prompt(node, workspace)
    policy.require(len(prompt) <= 64000 and '[truncated to final' not in prompt, 'fulltext_prompt_budget_no_truncation')
    write(directory / 'INTENT.json', dict(started_unix=time.time(), prompt_sha256=policy.text_sha(prompt),
        prompt_characters=len(prompt), packet_sha256=sha(directory / 'PACKET.json'), attempts=1, timeout_seconds=300))
    status, result = run_agent(node, workspace, directory / 'reader', timeout_sec=300)
    measured = usage(directory)
    write(directory / 'USAGE.json', measured)
    policy.require(status == 0 and result is not None and not measured['tool_events'], 'review_failed_or_used_tools')
    if LINE_REVIEWS:
        result = policy.resolve_line_reviews(rows, result)
    reviews = policy.validate_review(rows, result)
    write(directory / 'ACCEPTED_REVIEW.json', reviews)
    return reviews, measured


def publish(number, batch, selected):
    with ThreadPoolExecutor(max_workers=REVIEW_PARALLEL) as pool:
        futures = [pool.submit(review_group, number, group, selected[group * 6:(group + 1) * 6]) for group in range(2)]
        results = [future.result() for future in futures]
    reviews = [review for result, measured in results for review in result]
    write(batch / 'SAMPLED_REVIEWS.json', reviews)
    write(batch / 'PROVIDER_USAGE.json', [measured for result, measured in results])
    rows = read(batch / 'CANDIDATES.json')
    decision, exported = policy.adjudicate(rows, reviews)
    write(batch / 'BATCH_DECISION.json', decision)
    checks = read(batch / 'SOURCE_CHECKS.json')
    hours = max((checks['snapshot_unix'] - checks['source_started_unix']) / 3600, 1e-9)
    normalized = [re.sub(r'\d+(?:\.\d+)?', '<N>', ' '.join(row['target'].lower().split())) for row in rows]
    metrics = dict(mechanically_valid_distinct_targets=len(rows), sampled_individually_passed=decision['sample_pass'],
        batch_admitted_rows=len(exported) if decision['accepted'] else 0, unsampled_individually_unreviewed=52,
        first_person_count=sum(review['first_person'] is True for review in reviews),
        meaningful_branch_count=sum(review['has_meaningful_branch'] for review in reviews),
        branching_alternatives=[review['branching_alternative'] for review in reviews],
        rejection_reasons=[review['branch_rejection_reason'] for review in reviews],
        semantic_novelty=[review['semantic_novelty'] for review in reviews],
        normalized_template_duplicate_rate=1 - len(set(normalized)) / len(normalized),
        raw_duplicate_skips=sum(row['reason'] == 'duplicate_target' for row in read(batch / 'SKIPPED.json')),
        captured_generation_tokens_per_hour=checks['captured_generated_tokens'] / hours,
        sampled_distinct_qualified_per_source_hour=decision['sample_pass'] / hours,
        batch_admitted_per_source_hour=(len(exported) if decision['accepted'] else 0) / hours,
        rates_are_snapshot_not_independent_effects=True)
    if LINE_REVIEWS:
        for key in ('captured_generation_tokens_per_hour', 'sampled_distinct_qualified_per_source_hour',
                    'batch_admitted_per_source_hour'):
            metrics.pop(key)
        metrics.update(first_native_capture_unix=checks['first_native_capture_unix'],
            last_native_capture_unix=checks['last_native_capture_unix'],
            selected_first_native_capture_unix=checks['selected_first_native_capture_unix'],
            selected_last_native_capture_unix=checks['selected_last_native_capture_unix'],
            captured_unique_targets=checks['captured_unique_targets'], captured_calls=checks['captured_calls'],
            captured_generated_tokens=checks['captured_generated_tokens'],
            source_snapshot_unix=checks['snapshot_unix'], source_started_unix=checks['source_started_unix'],
            no_rate_without_explicit_walltime=True)
    write(batch / 'METRICS.json', metrics)
    if not decision['accepted']:
        return None
    write(batch / 'ROWS.json', exported)
    manifest = dict(schema=policy.SCHEMA, batch_id=f'{ROOT.name}_math_sampled_{number:03d}',
        created_at_utc=datetime.now(timezone.utc).isoformat(), encoding='math', admission_mode=policy.MODE,
        eligibility_version='ROHIN98_SOURCE_BACKED_V2', batch_author_accepted=True,
        individual_semantic_status='SAMPLED_PASS_UNSAMPLED_UNREVIEWED', row_count=len(exported),
        rows_path='ROWS.json', rows_sha256=sha(batch / 'ROWS.json'),
        target_sha256s=[row['target_sha256'] for row in exported],
        source_native_archive_path='SOURCE_SNAPSHOT.tar.gz', source_native_archive_sha256=sha(batch / 'SOURCE_SNAPSHOT.tar.gz'),
        source_registry_path='SOURCE_REGISTRY.json', source_registry_sha256=sha(batch / 'SOURCE_REGISTRY.json'),
        registered_source_purpose=policy.PURPOSE, sampled_review_path='SAMPLED_REVIEWS.json',
        sampled_review_sha256=sha(batch / 'SAMPLED_REVIEWS.json'), sample_registration_path='SAMPLE_REGISTRATION.json',
        sample_registration_sha256=sha(batch / 'SAMPLE_REGISTRATION.json'),
        exclusions_path='EXCLUSIONS.json', exclusions_sha256=sha(batch / 'EXCLUSIONS.json'),
        exact_training_encoding_in_rows=True, train_context_limit=2048, no_silent_crop=True,
        new_gpu_calls=0, new_provider_calls=2, training_launched_by_this_manifest=False,
        requirements=['exclude frozen held IDs and hashes', 'append once by batch ID and rows hash',
            'preserve adapter optimizer RNG corpus cursor; rehearse old rows and matched masked control',
            'unsampled rows are not individually semantic PASS', 'parenting/L2 roots forbidden for ongoing L1'],
        metrics_path='METRICS.json', provider_usage_path='PROVIDER_USAGE.json')
    write(batch / 'MANIFEST.json', manifest)
    return str(batch / 'MANIFEST.json')


def watch():
    policy.require(RUNTIME_ROOT is not None, 'future_watch_requires_external_runtime')
    prepared = read(ROOT / 'PREPARED.json')
    policy.require(all(sha(REPO / path) == digest for path, digest in prepared['source_inventory'].items()), 'publisher_source_drift')
    policy.require(all(sha(ROOT / path) == digest for path, digest in prepared['files'].items()), 'frozen_registration_drift')
    ready = read(ROOT / 'READY.json')
    policy.require(ready['cpu_tests_passed'] and ready['prepare_sha256'] == sha(ROOT / 'PREPARED.json') and
                   ready['builder_receipt_sha256'] == sha(ROOT / 'BUILDER_RECEIPT.md'), 'builder_readiness_required')
    os.environ['ORCH_CONTINUAL_BATCH_CODEX_REAL'] = prepared['codex_real']
    os.environ['PATH'] = str(ROOT / 'provider_bin') + os.pathsep + os.environ['PATH']
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    start = time.time()
    with (ROOT / 'WATCH_LIFETIME.json').open('x') as stream:
        json.dump(dict(started_unix=start, deadline_unix=start + 1800, max_batches=4, max_provider_calls=8, pid=os.getpid()), stream)
    published = []
    for number in range(4):
        if time.time() + 360 >= start + 1800:
            break
        try:
            if number == 0:
                batch = ROOT / 'batch_000'
                selected = policy.sample(read(batch / 'CANDIDATES.json'))
            else:
                batch, selected = collect(number)
            if selected is None:
                time.sleep(30)
                continue
            seen = set(read(ROOT / 'SEEN.json')) | {row['target_sha256'] for row in read(batch / 'CANDIDATES.json')}
            write(ROOT / 'SEEN.json', sorted(seen))
            manifest = publish(number, batch, selected)
            if manifest:
                published.append(dict(path=manifest, sha256=sha(manifest)))
                write(ROOT / 'PUBLISHED.json', dict(manifests=published, trainer_ingestion_not_asserted=True))
        except Exception as error:
            write(ROOT / f'BATCH_{number:03d}_FAILED.json', dict(type=type(error).__name__, message=str(error)))
        time.sleep(10)
    write(ROOT / 'WATCH_TERMINAL.json', dict(manifests=published, finished_unix=time.time()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('prepare', 'collect', 'watch'))
    parser.add_argument('--number', type=int, default=0)
    options = parser.parse_args()
    if options.phase == 'collect':
        print(collect(options.number)[0])
    else:
        globals()[options.phase]()
