"""Separate bounded exhaustion publisher; old publisher state is read-only."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import tomllib
import urllib.request

from gpu import orch_continual_batch_publish as publisher
from gpu.orch_continual_batch_handoff import wrap_row
from organism_v6 import orch_continual_batch as policy


DEADLINE = 1789459200.0
MAX_OUTPUT = 8192
MODEL = 'openai/openai/gpt-6-astra'
METHOD_KINDS = ('SAME_PREMISE_METHOD', 'CANDIDATE_PATH', 'COUNTERFACTUAL',
                'INTERPRETATION_CHECK', 'CONTRADICTORY_PREMISE')
BASE_SCHEMA = publisher.schema
_CONTROLLER_LOCK = None


def guard_controller(config, runtime):
    global _CONTROLLER_LOCK
    policy.require(config['deadline_unix'] == DEADLINE and config['initial_reserved'] == 0,
                   'new_segment_exact_deadline_and_fresh_ledger')
    prior = read(config['old_terminal_path'])
    policy.require(sha(config['old_terminal_path']) == config['old_terminal_sha256']
                   and prior['reserved'] == 96 and prior['deadline_unix'] < DEADLINE,
                   'old_terminal_preserved')
    policy.require(not Path('/proc/3443504').exists(), 'old_publisher_must_be_terminal')
    _CONTROLLER_LOCK = (runtime / 'CONTROLLER.lock').open('a')
    fcntl.flock(_CONTROLLER_LOCK, fcntl.LOCK_EX | fcntl.LOCK_NB)


def review_schema():
    previous = publisher.LINE_REVIEWS, publisher.BRANCH_V3
    try:
        publisher.LINE_REVIEWS, publisher.BRANCH_V3 = True, True
        schema = BASE_SCHEMA()
    finally:
        publisher.LINE_REVIEWS, publisher.BRANCH_V3 = previous
    properties = schema['properties']['reviews']['items']['properties']
    approach = properties['branch_metrics']['properties']['approaches']['items']
    approach['properties'].update(method_kind=dict(type='string', enum=list(METHOD_KINDS)),
        distinctness_reason=dict(type='string'), worked_line_ids=dict(type='array',
            items=dict(type='integer', minimum=1)))
    approach['required'] = list(approach['properties'])
    return schema


def validate_reviews(rows, result):
    resolved = policy.resolve_line_reviews(rows, deepcopy(result))
    reviews = policy.validate_review(rows, resolved)
    targets = {row['target_sha256']: row['target'] for row in rows}
    for review in reviews:
        branch = review['branch_metrics']
        lines = {line['line_id']: line['text'] for line in policy.source_lines(targets[review['target_sha256']])}
        for approach in branch['approaches']:
            policy.require(approach['method_kind'] in METHOD_KINDS and approach['distinctness_reason'].strip(),
                           'explicit_semantic_method_classification')
            identifiers = approach['worked_line_ids']
            policy.require(isinstance(identifiers, list) and all(type(index) is int and index in lines for index in identifiers),
                           'worked_method_line_binding')
            policy.require(not identifiers or bool(approach['pursued_line_ids']), 'worked_method_was_pursued')
            approach['worked_evidence_spans'] = [lines[index] for index in identifiers]
    return reviews


def method_measurement(review):
    branch = review['branch_metrics']
    measured = branch['measurement_status'] == 'MEASURED'
    return dict(target_sha256=review['target_sha256'], measurement_status=branch['measurement_status'],
        same_premise_worked_methods=sum(approach['method_kind'] == 'SAME_PREMISE_METHOD'
            and bool(approach['worked_line_ids']) for approach in branch['approaches']) if measured else None,
        category_counts={kind: sum(approach['method_kind'] == kind for approach in branch['approaches'])
            for kind in METHOD_KINDS} if measured else None,
        repetition_failure=branch['repetition_failure'], source='AUTHOR_SEMANTIC_SAMPLE_NOT_HEADING_COUNTS')


def steering_counts(rows):
    counts = {}
    for row in rows:
        provenance = row['provenance']
        label = str(provenance['steering_degree']) + ':' + provenance['instruction_regime']
        counts[label] = counts.get(label, 0) + 1
    return counts


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('provider_redirect_forbidden')


def provider_payload(prompt, instructions):
    return dict(model=MODEL, instructions=instructions, input=prompt, max_output_tokens=MAX_OUTPUT,
        tools=[], tool_choice='none', store=False, reasoning=dict(effort='low'))


def parse_provider(envelope):
    policy.require(envelope.get('model') == MODEL and envelope.get('status') == 'completed'
                   and not envelope.get('error'), 'exact_completed_provider_identity')
    policy.require(all(item.get('type') in ('message', 'reasoning') for item in envelope.get('output', [])),
                   'provider_tool_calls_forbidden')
    usage = envelope.get('usage', {})
    policy.require(type(usage.get('output_tokens')) is int and 0 <= usage['output_tokens'] <= MAX_OUTPUT
                   and type(usage.get('input_tokens')) is int, 'actual_usage_and_output_cap_required')
    texts = [part['text'] for item in envelope['output'] if item.get('type') == 'message'
             for part in item.get('content', []) if part.get('type') == 'output_text']
    policy.require(len(texts) == 1, 'single_provider_response')
    text = texts[0]
    if text.startswith('```json\n') and text.endswith('\n```'):
        text = text[8:-4]
    components = {key: usage[key] for key in ('input_tokens', 'output_tokens')}
    for parent, child, label in (('input_tokens_details', 'cached_tokens', 'cached_input_tokens'),
                                  ('output_tokens_details', 'reasoning_tokens', 'reasoning_output_tokens')):
        if child in usage.get(parent, {}):
            components[label] = usage[parent][child]
    return json.loads(text), dict(reported_components=components, usage_events=[usage],
        usage_reported=True, tool_events=[], cached_input_is_component_not_added_twice=True)


def review_group_http(number, group, rows):
    directory = publisher.ROOT / 'review_workspace' / f'batch_{number:03d}_{group}'
    reader = directory / 'reader'
    reader.mkdir(exist_ok=False)
    config_path = Path.home() / '.codex/nvidia-astra.config.toml'
    config = tomllib.loads(config_path.read_text())
    provider = config['model_providers'][config['model_provider']]
    policy.require(config['model'] == MODEL and provider['wire_api'] == 'responses'
        and provider['base_url'] == 'https://inference-api.nvidia.com/v1'
        and provider['env_key'] == 'NVIDIA_API_KEY', 'existing_verified_provider_only')
    policy.require(time.time() + 300 < DEADLINE, 'no_late_provider_dispatch')
    packet = (directory / 'PACKET.json').read_text()
    schema = (directory / 'SCHEMA.json').read_text()
    prompt = 'Review these immutable numbered source lines. Return JSON matching this schema:\n' + schema + '\nPACKET:\n' + packet
    policy.require(len(packet) <= 58000 and len(prompt) <= 90000, 'bounded_complete_review_packet')
    payload = provider_payload(prompt, (publisher.ROOT / 'review_workspace/REVIEW_INSTRUCTIONS.md').read_text())
    write_once(reader / 'API_REQUEST.json', payload)
    write_once(reader / 'DISPATCH.json', dict(started_unix=time.time(), attempts=1, retries=0,
        maximum_output_tokens=MAX_OUTPUT, model=MODEL, request_sha256=sha(reader / 'API_REQUEST.json'),
        config_sha256=sha(config_path), timeout_seconds=300))
    request = urllib.request.Request(provider['base_url'] + '/responses', data=json.dumps(payload).encode(),
        headers={'Authorization': 'Bearer ' + os.environ['NVIDIA_API_KEY'], 'Content-Type': 'application/json'})
    opener = urllib.request.build_opener(NoRedirect, urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=300) as response:
            raw = response.read()
        with (reader / 'RAW_RESPONSE.json').open('xb') as stream:
            stream.write(raw)
        result, measured = parse_provider(json.loads(raw))
        write_once(reader / 'result.json', result)
        write_once(directory / 'USAGE.json', measured)
        reviews = validate_reviews(rows, result)
        write_once(directory / 'ACCEPTED_REVIEW.json', reviews)
        return reviews, measured
    except Exception as error:
        if isinstance(error, urllib.error.HTTPError):
            with (reader / 'HTTP_ERROR.txt').open('xb') as stream:
                stream.write(error.read())
        write_once(reader / 'FAILED.json', dict(type=type(error).__name__, finished_unix=time.time(), retries=0))
        raise


def review_group(number, group, rows):
    directory = publisher.ROOT / 'review_workspace' / f'batch_{number:03d}_{group}'
    try:
        subprocess.run([sys.executable, '-B', '-m', 'gpu.orch_continual_exhaustion_publish',
            'provider', '--directory', str(directory)], check=True, timeout=310,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.SubprocessError as error:
        write_once(directory / 'PROCESS_FAILED.json', failure_summary(error))
        raise
    return validate_reviews(rows, read(directory / 'reader/result.json')), read(directory / 'USAGE.json')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write_once(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)


def verify_native(root):
    frozen = read(root / 'NATIVE_READY.json')
    policy.require(all(sha(root / name) == digest for name, digest in frozen['files'].items()), 'native_runtime_drift')
    policy.require(time.time() < read(root / 'REGISTRATION.json')['segment_deadline_unix'], 'original_deadline_expired')
    registration = read(root / 'REGISTRATION.json')
    policy.require(registration['segment_deadline_unix'] == DEADLINE and
                   registration['review_call_limit'] == 128 and registration['aggregate_allocation_ceiling'] == 256,
                   'new_segment_fixed_bounds')
    registry = read(root / 'PUBLISHER_REGISTRY.json')
    policy.require(registry['batching_rule'] == 'MIXED_STEERING_SAME_37EC'
                   and registry['causal_prompt_comparison'] is False
                   and registry['source_registry_sha256'] == sha(root / 'SOURCE_REGISTRY.json'),
                   'prospective_mixed_steering_registry')


def native_prepare(root, number):
    from gpu.orch_continual_exhaustion_feed import snapshot
    verify_native(root)
    batch = root / f'orch_continual_exhaustion_feed_batch_{number:03d}'
    snapshot(batch, root / 'EXCLUSIONS.json', root / 'SEEN.json', root / 'SOURCE_REGISTRY.json')
    for name in ('REGISTRATION.json',):
        with (batch / name).open('xb') as stream:
            stream.write((root / name).read_bytes())
    rows, checks = read(batch / 'CANDIDATES.json'), read(batch / 'SOURCE_CHECKS.json')
    validate_candidates(rows, read(root / 'SOURCE_REGISTRY.json'))
    policy.require(all(sha(root / name) == sha(batch / name) for name in ('SOURCE_REGISTRY.json', 'EXCLUSIONS.json')),
                   'snapshot_inputs_exact')
    result = dict(number=number, native_batch_path=str(batch), native_archive_path=str(batch) + '.tar.gz',
        native_archive_sha256=sha(str(batch) + '.tar.gz'), source_checks_sha256=sha(batch / 'SOURCE_CHECKS.json'),
        candidates_sha256=sha(batch / 'CANDIDATES.json'), candidate_count=len(rows),
        source_checks=checks, native_raw_stays_native=True, steering_counts=steering_counts(rows),
        source_mix='MIXED_STEERING_SAME_37EC', causal_prompt_comparison=False)
    if len(rows) == 64:
        policy.require(not {row['target_sha256'] for row in rows}.intersection(read(root / 'SEEN.json')),
                       'all_prior_seen_excluded')
        selected = policy.sample(rows)
        sample = dict(sample_target_sha256s=[row['target_sha256'] for row in selected],
            candidates_sha256=result['candidates_sha256'], semantic_results_seen=False,
            registration_sha256=sha(root / 'REGISTRATION.json'), registered_unix=time.time())
        write_once(batch / 'SAMPLE_REGISTRATION.json', sample)
        packets = []
        for group in range(2):
            packet = [dict(target_source_lines=policy.source_lines(row['target']),
                student_prefix=row['student_prefix'], question=row['question'], gold=row['gold'],
                target_sha256=row['target_sha256'], raw_call_sha256=row['provenance']['raw_call_sha256'],
                student_prefix_sha256=row['student_prefix_sha256'],
                instruction_regime=row['provenance']['instruction_regime'],
                steering_degree=row['provenance']['steering_degree']) for row in selected[group * 6:(group + 1) * 6]]
            policy.require(len(json.dumps(packet)) <= 58000, 'bounded_fulltext_packet_only')
            write_once(batch / f'REVIEW_PACKET_{group}.json', packet)
            packets.append(packet)
        result.update(packets=packets, sample_registration_sha256=sha(batch / 'SAMPLE_REGISTRATION.json'))
    write_once(batch / 'CAPTURE_REFERENCE.json', {key: value for key, value in result.items() if key != 'packets'})
    return result


def reserve_budget(state, deadline, now):
    policy.require(deadline == DEADLINE and type(state['reserved']) is int and state['reserved'] >= 0
                   and state['reserved'] % 2 == 0 and state['old_reserved'] == 96,
                   'separate_new_segment_not_old_extension')
    policy.require(now + 660 < deadline, 'original_deadline_margin_no_reset')
    policy.require(state['reserved'] + 2 <= state['limit'] == 128, 'inherited_call_cap')
    policy.require(state['old_reserved'] + state['reserved'] + 2 <= 256, 'aggregate_ceiling')
    return dict(state, reserved=state['reserved'] + 2)


def validate_candidates(rows, registry):
    policy.require(len(rows) <= 64 and len({row['target_sha256'] for row in rows}) == len(rows),
                   'bounded_distinct_source_population')
    identities = set()
    for row in rows:
        provenance = row['provenance']
        source = Path(provenance['source_native_path'])
        matches = [entry for path, entry in registry['sources'].items() if source.is_relative_to(Path(path))]
        policy.require(len(matches) == 1 and matches[0]['source_purpose'] == 'L1_EXTERNAL_GENERATION'
            and matches[0]['parenting_experience'] is False and provenance['parenting_experience'] is False
            and provenance['source_purpose'] == 'L1_EXTERNAL_GENERATION'
            and provenance['generator_classification'] in ('ORIGINAL37EC_CONTROL', 'BASE_CONTROL'),
            'only_registered_external_baseline_sources')
        policy.require(row['mechanical_pass'] is True and row['outcome_pass'] is True
            and row['token_contract_pass'] is True and row['semantic_status'] == 'UNREVIEWED'
            and row['admitted'] is False and row['trainingAllowed'] is False,
            'all_rows_mechanical_only_before_review')
        policy.require(policy.text_sha(row['target']) == row['target_sha256']
            and row['training_encoding']['sequence_length'] <= 2048, 'exact_target_context_no_crop')
        policy.require(row['actor']['state_sha256'] == matches[0]['generator_state_sha256']
            and row['actor']['base_sha256'] == matches[0]['generator_base_sha256'], 'registered_actor_base')
        policy.require(provenance['instruction_regime'] in ('EXHAUSTION_ONLY', 'STEERED')
            and type(provenance['steering_degree']) is int and 0 <= provenance['steering_degree'] <= 3,
            'explicit_per_row_steering')
        identities.add((row['actor']['state_sha256'], row['actor']['base_sha256'], provenance['generator_classification']))
    policy.require(len(identities) <= 1, 'never_mix_BASE_and_37ec')


def failure_summary(error):
    if isinstance(error, subprocess.SubprocessError):
        return dict(type=type(error).__name__, returncode=getattr(error, 'returncode', None),
                    reason='transport_or_subprocess_failed_details_retained_in_process_not_hostname_logs')
    return dict(type=type(error).__name__, error=str(error))


def native_reserve(root, number):
    verify_native(root)
    batch = root / f'orch_continual_exhaustion_feed_batch_{number:03d}'
    with (root / 'BUDGET.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        policy.require(not (batch / 'REVIEW_RESERVATION.json').exists(), 'single_attempt_batch_reservation')
        rows = read(batch / 'CANDIDATES.json')
        policy.require(len(rows) == 64, 'full64_before_spending')
        sample = read(batch / 'SAMPLE_REGISTRATION.json')
        policy.require(sample['candidates_sha256'] == sha(batch / 'CANDIDATES.json') and
            sample['sample_target_sha256s'] == [row['target_sha256'] for row in policy.sample(rows)],
            'prospective_sample_bound')
        state = reserve_budget(read(root / 'BUDGET.json'), read(root / 'REGISTRATION.json')['segment_deadline_unix'], time.time())
        publisher.write(root / 'BUDGET.json', state)
        write_once(batch / 'REVIEW_RESERVATION.json', dict(calls=[state['reserved'] - 1, state['reserved']], reserved_unix=time.time()))
        seen = set(read(root / 'SEEN.json')) | {row['target_sha256'] for row in read(batch / 'CANDIDATES.json')}
        publisher.write(root / 'SEEN.json', sorted(seen))
    return state


def native_verify_upload(root, number):
    batch = root / f'orch_continual_exhaustion_feed_batch_{number:03d}'
    directory = batch / 'PROVIDER_UPLOAD'
    inventory = read(directory / 'UPLOAD_INVENTORY.json')
    policy.require(all(sha(directory / name) == digest for name, digest in inventory.items()), 'native_upload_hash_mismatch')
    receipt = dict(verified=True, inventory_sha256=sha(directory / 'UPLOAD_INVENTORY.json'), files=len(inventory), verified_unix=time.time())
    write_once(batch / 'PROVIDER_UPLOAD_VERIFIED.json', receipt)
    return receipt


def native_finalize(root, number):
    verify_native(root)
    batch = root / f'orch_continual_exhaustion_feed_batch_{number:03d}'
    policy.require(read(batch / 'PROVIDER_UPLOAD_VERIFIED.json')['verified'], 'verified_native_provider_bytes_required')
    rows = read(batch / 'CANDIDATES.json')
    validate_candidates(rows, read(batch / 'SOURCE_REGISTRY.json'))
    sample = read(batch / 'SAMPLE_REGISTRATION.json')
    policy.require(sample['candidates_sha256'] == sha(batch / 'CANDIDATES.json') and
        sample['registration_sha256'] == sha(root / 'REGISTRATION.json'), 'finalize_frozen_candidate_binding')
    selected = policy.sample(rows)
    policy.require(sample['sample_target_sha256s'] == [row['target_sha256'] for row in selected],
                   'same_prospectively_selected_sample')
    reviews, usage = [], []
    for group in range(2):
        directory = batch / 'PROVIDER_UPLOAD' / f'batch_{number:03d}_{group}'
        result, measured = read(directory / 'reader/result.json'), read(directory / 'USAGE.json')
        policy.require(not measured['tool_events'], 'provider_tools_forbidden')
        subset = selected[group * 6:(group + 1) * 6]
        reviews.extend(validate_reviews(subset, result))
        usage.append(measured)
    decision, exported = policy.adjudicate(rows, reviews)
    write_once(batch / 'SAMPLED_REVIEWS.json', reviews)
    write_once(batch / 'PROVIDER_USAGE.json', usage)
    write_once(batch / 'BATCH_DECISION.json', decision)
    result = dict(number=number, decision=decision, all_adjudicated_sample_pass_sha256s=
        [review['target_sha256'] for review in reviews if review['status'] == 'PASS'],
        legacy_meaningful_branch_label_count=sum(review['has_meaningful_branch'] for review in reviews),
        method_measurements=[method_measurement(review) for review in reviews],
        population_steering_counts=steering_counts(rows), sampled_steering_counts=steering_counts(selected),
        source_mix='MIXED_STEERING_SAME_37EC', causal_prompt_comparison=False,
        semantic_novelty_counts={label: sum(review['semantic_novelty'] == label for review in reviews)
                                for label in ('APPLIED_REASONING', 'RAW_RECAP', 'UNRESOLVED')},
        native_reviews_path=str(batch / 'SAMPLED_REVIEWS.json'), native_reviews_sha256=sha(batch / 'SAMPLED_REVIEWS.json'),
        reported_provider_components={key: sum(item['reported_components'].get(key, 0) for item in usage)
                                      for key in {key for item in usage for key in item['reported_components']}},
        accepted_sample_pass_sha256s=[], admitted_target_sha256s=[], unsampled_unreviewed=0)
    result['sampled_branch_measurements'] = [dict(target_sha256=review['target_sha256'],
        measurement_status=review.get('branch_metrics', {}).get('measurement_status', 'UNKNOWN'),
        semantic_distinct_approaches_considered=review.get('branch_metrics', {}).get('semantic_distinct_approaches_considered'),
        semantic_distinct_approaches_pursued=review.get('branch_metrics', {}).get('semantic_distinct_approaches_pursued'),
        repetition_failure=review.get('branch_metrics', {}).get('repetition_failure'),
        native_evidence_path=str(batch / 'SAMPLED_REVIEWS.json')) for review in reviews]
    if decision['accepted']:
        binding = dict(schema=policy.SCHEMA, admission_mode=policy.MODE, batch_author_accepted=True,
            source_checks_sha256=sha(batch / 'SOURCE_CHECKS.json'), reviews_sha256=sha(batch / 'SAMPLED_REVIEWS.json'),
            candidates_sha256=sha(batch / 'CANDIDATES.json'), sample_sha256=sha(batch / 'SAMPLE_REGISTRATION.json'))
        write_once(batch / 'BATCH_BINDING.json', binding)
        wrappers = [wrap_row(row, sha(batch / 'BATCH_BINDING.json')) for row in exported]
        write_once(batch / 'ROWS.json', wrappers)
        manifest = dict(schema=policy.SCHEMA, batch_id=f'orch_continual_exhaustion_segment1_{number:03d}',
            encoding='math_content_v2', admission_mode=policy.MODE, wrapper_policy='ROHIN98_BATCH_SAMPLED_AUTHOR_REVIEW_V2',
            source_purpose='L1_EXTERNAL_GENERATION', parenting_experience=False, row_count=len(wrappers),
            source_actor=rows[0]['actor'], source_classification=rows[0]['provenance']['generator_classification'],
            instruction_regimes=sorted({row['provenance']['instruction_regime'] for row in rows}),
            steering_counts=steering_counts(exported), source_mix='MIXED_STEERING_SAME_37EC',
            causal_prompt_comparison=False,
            method_measurement_schema='SAME_PREMISE_METHOD_VS_COUNTERFACTUAL_V1',
            batch_author_accepted=True, individual_semantic_status='SAMPLED_PASS_UNSAMPLED_UNREVIEWED',
            rows_path='ROWS.json', rows_sha256=sha(batch / 'ROWS.json'),
            target_sha256s=[row['target_sha256'] for row in exported],
            source_native_archive_path=str(batch) + '.tar.gz', source_native_archive_sha256=sha(str(batch) + '.tar.gz'),
            source_batch_manifest_path=str(batch / 'BATCH_BINDING.json'), source_batch_manifest_sha256=sha(batch / 'BATCH_BINDING.json'),
            sampled_review_path=str(batch / 'SAMPLED_REVIEWS.json'), sampled_review_sha256=sha(batch / 'SAMPLED_REVIEWS.json'),
            sample_registration_path=str(batch / 'SAMPLE_REGISTRATION.json'), sample_registration_sha256=sha(batch / 'SAMPLE_REGISTRATION.json'),
            exclusions_path=str(batch / 'EXCLUSIONS.json'), exclusions_sha256=sha(batch / 'EXCLUSIONS.json'),
            source_registry_path=str(batch / 'SOURCE_REGISTRY.json'), source_registry_sha256=sha(batch / 'SOURCE_REGISTRY.json'),
            created_at_utc=datetime.now(timezone.utc).isoformat(), trainer_ingested=False,
            raw_storage='NATIVE_ONLY_NO_VM_COPY', exact_training_encoding_in_rows=True, train_context_limit=2048)
        write_once(batch / 'MANIFEST.json', manifest)
        result.update(native_manifest_path=str(batch / 'MANIFEST.json'), native_manifest_sha256=sha(batch / 'MANIFEST.json'),
            native_rows_path=str(batch / 'ROWS.json'), native_rows_sha256=sha(batch / 'ROWS.json'),
            native_archive_path=str(batch) + '.tar.gz', native_archive_sha256=manifest['source_native_archive_sha256'],
            admitted_target_sha256s=manifest['target_sha256s'],
            accepted_sample_pass_sha256s=[row['target_sha256'] for row in exported if row['review'] is not None],
            unsampled_unreviewed=sum(row['review'] is None for row in exported))
    write_once(batch / 'RESULT_REDUCTION.json', result)
    return result


def cleanup_verified_packets(directory, receipt, expected_inventory):
    policy.require(receipt.get('verified') is True and receipt['inventory_sha256'] == expected_inventory,
                   'do_not_delete_before_native_hash_verification')
    policy.require(directory.name.startswith('review_batch_') and directory.is_relative_to(Path('/tmp')),
                   'only_owned_temporary_packets')
    shutil.rmtree(directory)


def vm_watch(config_path):
    config = read(config_path)
    runtime, reductions = Path(config['runtime']), Path(config['reductions'])
    policy.require(runtime.is_relative_to(Path('/tmp')) and Path(__file__).resolve().is_relative_to(runtime / 'source'), 'external_pinned_controller_only')
    policy.require(all(sha(runtime / name) == digest for name, digest in config['runtime_files'].items()), 'controller_source_drift')
    policy.require(time.time() < config['deadline_unix'], 'original_deadline_expired')
    guard_controller(config, runtime)
    write_once(runtime / 'WATCH_IDENTITY.json', dict(pid=os.getpid(), started_unix=time.time(), new_segment_reserved=config['initial_reserved']))
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    publisher.RUNTIME_ROOT, publisher.LINE_REVIEWS, publisher.BRANCH_V3 = runtime, True, True
    publisher.schema, publisher.review_group = review_schema, review_group
    target = os.environ['ORCH_CONTINUAL_BATCH_SSH_TARGET']
    native = config['native_root']

    def ssh(command):
        return subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', target, command],
            cwd=runtime, check=True, text=True, capture_output=True, timeout=min(240, max(1, config['deadline_unix'] - time.time())))

    def rpc(phase, number):
        response = ssh(f'env CUDA_VISIBLE_DEVICES= HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 '
            f'PYTHONPATH={native}/source {config["native_python"]} -B -m gpu.orch_continual_exhaustion_publish '
            f'{phase} --root {native} --number {number}')
        return json.loads(response.stdout)

    def upload(source, destination):
        subprocess.run(['scp', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', str(source), target + ':' + destination],
            cwd=runtime, check=True, text=True, capture_output=True, timeout=min(120, max(1, config['deadline_unix'] - time.time())))

    number, reserved = config['next_number'], config['initial_reserved']
    all_pass, accepted_pass, admitted = (set(config[name]) for name in ('all_sample_pass', 'accepted_sample_pass', 'admitted_targets'))
    while time.time() + 660 < config['deadline_unix'] and reserved < 128:
        available = int(next(line.split()[1] for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))) * 1024
        if available < 800 * 1024**2:
            time.sleep(30)
            continue
        receipt, local = None, runtime / f'review_batch_{number:03d}'
        try:
            first_packet = Path(config['first_packet_path']) if config.get('first_packet_path') else None
            capture = read(first_packet) if number == config['next_number'] and first_packet and first_packet.exists() else rpc('native_prepare', number)
            packets = capture.pop('packets', None)
            write_once(reductions / f'CAPTURE_{number:03d}.json', capture)
            if packets is None:
                number += 1
                time.sleep(30)
                continue
            budget = rpc('native_reserve', number)
            reserved = budget['reserved']
            write_once(reductions / f'RESERVATION_{number:03d}.json', budget)
            workspace = local / 'review_workspace'
            workspace.mkdir(parents=True)
            if number == config['next_number'] and first_packet and first_packet.exists():
                shutil.copyfile(first_packet, workspace / 'FIRST_NATIVE_PACKET.json')
            shutil.copyfile(runtime / 'REVIEW_INSTRUCTIONS.md', workspace / 'REVIEW_INSTRUCTIONS.md')
            publisher.ROOT = local
            sampled = []
            for group, packet in enumerate(packets):
                directory = workspace / f'batch_{number:03d}_{group}'
                directory.mkdir()
                write_once(directory / 'PACKET.json', packet)
                write_once(directory / 'SCHEMA.json', publisher.schema())
                sampled.append([dict(target=''.join(line['text'] for line in row['target_source_lines']),
                    target_sha256=row['target_sha256'], gold=row['gold'], student_prefix_sha256=row['student_prefix_sha256'],
                    provenance=dict(raw_call_sha256=row['raw_call_sha256'])) for row in packet])
            errors = []
            with ThreadPoolExecutor(max_workers=2 if available >= 2400 * 1024**2 else 1) as pool:
                futures = [pool.submit(publisher.review_group, number, group, sampled[group]) for group in range(2)]
                for future in futures:
                    try:
                        future.result()
                    except Exception as error:
                        errors.append(failure_summary(error))
            upload_root = capture['native_batch_path'] + '/PROVIDER_UPLOAD'
            files = {str(path.relative_to(workspace)): path for path in workspace.rglob('*') if path.is_file()}
            inventory = {name: sha(path) for name, path in files.items()}
            write_once(workspace / 'UPLOAD_INVENTORY.json', inventory)
            ssh('mkdir ' + upload_root)
            for name, path in files.items():
                parent = str(Path(upload_root) / Path(name).parent)
                ssh('mkdir -p ' + parent)
                upload(path, str(Path(upload_root) / name))
            upload(workspace / 'UPLOAD_INVENTORY.json', upload_root + '/UPLOAD_INVENTORY.json')
            receipt = rpc('native_verify_upload', number)
            policy.require(receipt['inventory_sha256'] == sha(workspace / 'UPLOAD_INVENTORY.json'), 'native_copy_receipt_binding')
            write_once(reductions / f'TRANSFER_VERIFIED_{number:03d}.json', receipt)
            if errors:
                write_once(reductions / f'FAILED_{number:03d}.json', dict(errors=errors, native_provider_bytes_preserved=True))
            else:
                result = rpc('native_finalize', number)
                write_once(reductions / f'RESULT_{number:03d}.json', result)
                all_pass.update(result['all_adjudicated_sample_pass_sha256s'])
                accepted_pass.update(result['accepted_sample_pass_sha256s'])
                admitted.update(result['admitted_target_sha256s'])
                if result['decision']['accepted']:
                    with Path(config['journal']).open('a') as stream:
                        stream.write(f'\n\n{datetime.now(timezone.utc).isoformat()} — Laplace/Main native-only accepted batch{number}: '
                            f'{result["decision"]["exported_rows"]}rows; {len(result["accepted_sample_pass_sha256s"])}samplePASS/'
                            f'{result["unsampled_unreviewed"]}UNREVIEWED. Node2 native manifest `{result["native_manifest_path"]}` '
                            f'SHA256 `{result["native_manifest_sha256"]}`. Raw/ROWS/archive remain native; VM reduction only. '
                            'No native trainer consumption claimed.\n')
            cleanup_verified_packets(local, receipt, sha(workspace / 'UPLOAD_INVENTORY.json'))
            if number == config['next_number'] and first_packet and first_packet.exists():
                first_packet.unlink()
        except Exception as error:
            path = reductions / f'PIPELINE_FAILED_{number:03d}.json'
            if not path.exists():
                write_once(path, dict(**failure_summary(error), temporary_packets_preserved=local.exists()))
            if local.exists() and receipt is None:
                write_once(reductions / 'BLOCKED_UNVERIFIED_TEMPORARY_TRANSFER.json', dict(number=number, reserved=reserved,
                    reason='stop rather than accumulate undeletable temporary raw packets; native transfer must be verified'))
                return
        elapsed = time.time() - config['publisher_started_unix']
        publisher.write(reductions / 'LIVE_STATUS.json', dict(observed_unix=time.time(), pid=os.getpid(), reserved_review_slots=reserved,
            deadline_unix=config['deadline_unix'], actual_publisher_wall_seconds=elapsed,
            sampled_pass_all_adjudicated_batches=len(all_pass), sampled_pass_in_accepted_batches=len(accepted_pass),
            sampled_pass_outside_accepted_batches=len(all_pass - accepted_pass), batch_admitted_distinct_targets=len(admitted),
            individually_unreviewed_in_accepted_batches=len(admitted - accepted_pass),
            all_sample_pass_per_publisher_hour=len(all_pass) * 3600 / elapsed,
            accepted_sample_pass_per_publisher_hour=len(accepted_pass) * 3600 / elapsed,
            batch_admitted_per_publisher_hour=len(admitted) * 3600 / elapsed,
            no_native_source_window_rate_inferred=True, raw_storage='NATIVE_ONLY', old_budget_reset=False, segment='EXHAUSTION_NEW128', old_reserved_preserved=96, aggregate_allocation_ceiling=256))
        number += 1
        time.sleep(2)
    write_once(reductions / 'WATCH_TERMINAL.json', dict(finished_unix=time.time(), reserved=reserved, deadline_unix=config['deadline_unix']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('native_prepare', 'native_reserve', 'native_verify_upload', 'native_finalize', 'vm_watch', 'provider'))
    parser.add_argument('--root', type=Path)
    parser.add_argument('--number', type=int)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--directory', type=Path)
    options = parser.parse_args()
    if options.phase == 'provider':
        directory = options.directory.resolve()
        policy.require(directory.is_relative_to(Path('/tmp')) and directory.parent.name == 'review_workspace',
                       'owned_temporary_provider_directory')
        publisher.ROOT = directory.parent.parent
        parts = directory.name.split('_')
        packet = read(directory / 'PACKET.json')
        rows = [dict(target=''.join(line['text'] for line in row['target_source_lines']),
            target_sha256=row['target_sha256'], gold=row['gold'], student_prefix_sha256=row['student_prefix_sha256'],
            provenance=dict(raw_call_sha256=row['raw_call_sha256'])) for row in packet]
        review_group_http(int(parts[1]), int(parts[2]), rows)
    elif options.phase == 'vm_watch':
        vm_watch(options.config)
    else:
        try:
            print(json.dumps(globals()[options.phase](options.root, options.number)))
        except Exception as error:
            print(json.dumps(dict(error_type=type(error).__name__, error=str(error))))
            raise
