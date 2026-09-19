"""Prepare prospective R130 enrollment; no process, READY or GPU actions."""

from copy import deepcopy
import math
from pathlib import Path
import re

from gpu import orch_r130_checkpoint_scheduler as scheduler
from gpu.orch_r146_checkpoint_scheduler import dispatch_window


SCHEMA = 'R146_CHECKPOINT_ENROLLMENT_PROPOSAL_V1'
REFERENCE_FIELDS = {'manifest_path', 'manifest_sha256', 'commit_sha256'}
ROLES = {'initial', 'firstsleep', 'latest'}
require = scheduler.require
sha = scheduler.sha
read = scheduler.read


def bound_file(path, checksum, roots):
    require(scheduler.sidecar.runner._hash(checksum), 'explicit_file_hash')
    path = scheduler.regular_path(path, roots)
    require(path.is_file() and sha(path) == checksum, 'exact_bound_regular_file')
    return path


def copied_checkpoint(reference, roots):
    require(isinstance(reference, dict) and set(reference) == REFERENCE_FIELDS,
            'exact_checkpoint_reference_fields')
    path = bound_file(reference['manifest_path'], reference['manifest_sha256'], roots)
    manifest = scheduler.sidecar.runner.parse_json(path.read_bytes())
    require(set(manifest) == {'schema', 'adapter_path', 'commit_path', 'commit_sha256'},
            'unchanged_runner_manifest_fields')
    for key in ('adapter_path', 'commit_path'):
        candidate = Path(manifest[key])
        if not candidate.is_absolute():
            candidate = path.parent / candidate
        scheduler.regular_path(str(candidate), roots)
    verified = scheduler.sidecar.runner.verify_checkpoint(manifest, path.parent)
    require(verified['commit_sha256'] == reference['commit_sha256'], 'same_original_commit')
    commit = scheduler.sidecar.runner.parse_json(Path(verified['commit_path']).read_bytes())
    require(type(commit['optimizer_steps']) is int and commit['optimizer_steps'] >= 0,
            'native_nonnegative_steps')
    require(scheduler.finite_number(commit['created_unix']) and commit['created_unix'] > 0,
            'native_creation_time')
    return dict(reference, optimizer_steps=commit['optimizer_steps'],
                created_unix=commit['created_unix'], adapter_state_sha256=verified['adapter_state_sha256'])


def proposal(document, previous_registry, copy_roots, custody_roots, now):
    require(isinstance(document, dict) and set(document) == {'schema', 'entry', 'checkpoints', 'custody'}
            and document['schema'] == SCHEMA, 'exact_enrollment_proposal_schema')
    previous = scheduler.enrolled_lineages(previous_registry)
    entry = document['entry']
    require(isinstance(entry, dict) and entry.get('cohort') == 'R137'
            and entry.get('lineage_id') not in previous, 'new_programme_lineage_only')
    combined = dict(schema=scheduler.LINEAGES_SCHEMA,
                    lineages=[*deepcopy(previous_registry['lineages']), deepcopy(entry)])
    scheduler.enrolled_lineages(combined)
    require(scheduler.finite_number(now) and entry['programme_start_unix'] <= now,
            'programme_start_not_future')
    references = document['checkpoints']
    require(isinstance(references, dict) and set(references) == ROLES, 'three_real_checkpoint_roles')
    checkpoints = {role: copied_checkpoint(reference, copy_roots)
                   for role, reference in references.items()}
    initial, first, latest = (checkpoints[role] for role in ('initial', 'firstsleep', 'latest'))
    require(initial['commit_sha256'] == entry['initial_commit_sha256']
            and initial['optimizer_steps'] == 0, 'actual_native_initial_step_zero')
    require(first['commit_sha256'] == entry['first_sleep_commit_sha256']
            and first['optimizer_steps'] > 0, 'actual_native_first_sleep')
    require(initial['created_unix'] <= first['created_unix'] <= latest['created_unix'] <= now
            and entry['programme_start_unix'] <= first['created_unix']
            and first['optimizer_steps'] <= latest['optimizer_steps'], 'chronological_checkpoint_roles')
    custody = document['custody']
    require(isinstance(custody, dict) and set(custody) == {'receipt_path', 'receipt_sha256'},
            'explicit_source_custody_binding')
    bound_file(custody['receipt_path'], custody['receipt_sha256'], custody_roots)
    return dict(entry=deepcopy(entry), checkpoints=checkpoints, custody=deepcopy(custody),
                source_custody_content_independently_reviewed=False)


def extend_registry(previous, verified):
    scheduler.enrolled_lineages(previous)
    require(isinstance(verified, list) and 1 <= len(verified) <= 8, 'bounded_prospective_enrollment')
    registry = dict(schema=scheduler.LINEAGES_SCHEMA,
                    lineages=[*deepcopy(previous['lineages']),
                              *(deepcopy(item['entry']) for item in verified)])
    scheduler.enrolled_lineages(registry)
    return registry


def registry_delta(previous, proposed):
    old = scheduler.enrolled_lineages(previous)
    new = scheduler.enrolled_lineages(proposed)
    require(all(name in new and new[name] == entry for name, entry in old.items()),
            'every_prior_lineage_binding_preserved')
    require(1 <= len(new) - len(old) <= 8, 'bounded_new_lineages_only')


def prospective_config(previous, registry_path, registry_sha256, builder_path, builder_sha256,
                       output_root, now, wall, remaining_jobs):
    require(previous['physical_devices'] == [0, 1], 'only_reserved_benchmark_devices')
    require(scheduler.finite_number(now) and scheduler.finite_number(wall)
            and now < wall <= previous['lease_end_unix'] - 21600, 'unchanged_lease_margin')
    require(type(remaining_jobs) is int and 1 <= remaining_jobs <= 8, 'bounded_segment_jobs')
    root = Path(previous['operator_root'])
    destination = Path(output_root)
    require(destination.parent == root and re.fullmatch('scheduler_run_r146_[a-z0-9_]+', destination.name)
            and not destination.exists() and not destination.is_symlink(), 'new_segment_output')
    registry = bound_file(registry_path, registry_sha256, [str(root)])
    original_registry = bound_file(previous['lineages_path'], previous['lineages_sha256'], [str(root)])
    registry_delta(read(original_registry), read(registry))
    builder = bound_file(builder_path, builder_sha256, [str(root)])
    require(builder.read_text().startswith('## [Builder] 2026-09-16'), 'dated_builder_scope')
    first = (math.floor(now / 1800) + 1) * 1800
    end = min(wall, now + 7200)
    require(dispatch_window(dict(hard_end_unix=end, job_max_seconds=previous['job_max_seconds']),
                            first)['status'] == 'FULL_JOB_WINDOW_AVAILABLE',
            'enough_time_for_fixed_dispatch')
    return dict(deepcopy(previous), lineages_path=str(registry), lineages_sha256=registry_sha256,
                builder_entry_path=str(builder), builder_entry_sha256=builder_sha256,
                created_unix=now, hard_end_unix=end, first_dispatch_unix=first,
                output_root=str(destination), max_jobs=remaining_jobs)


def config_delta(previous, proposed):
    changed = {'lineages_path', 'lineages_sha256', 'builder_entry_path', 'builder_entry_sha256',
               'created_unix', 'hard_end_unix', 'first_dispatch_unix', 'output_root', 'max_jobs'}
    restored = deepcopy(proposed)
    for key in changed:
        restored[key] = previous[key]
    require(restored == previous, 'frozen_protocol_ledger_source_budget_fields_preserved')


def remaining_budget(total_call_cap, historical_taken, previous_phase_admitted, phase_job_cap):
    require(type(total_call_cap) is int and 360 <= total_call_cap <= 4800
            and total_call_cap % 60 == 0, 'original_total_call_cap')
    require(isinstance(historical_taken, set) and type(previous_phase_admitted) is int
            and previous_phase_admitted >= 0 and type(phase_job_cap) is int
            and 0 <= previous_phase_admitted <= phase_job_cap <= 58, 'bound_prior_phase_accounting')
    return max(0, min(8, total_call_cap // 60 - len(historical_taken),
                      phase_job_cap - previous_phase_admitted))


def ready_candidates(verified):
    pending = {}
    for item in verified:
        for checkpoint in item['checkpoints'].values():
            document = dict(schema=scheduler.READY_SCHEMA, lineage_id=item['entry']['lineage_id'],
                            **{key: checkpoint[key] for key in REFERENCE_FIELDS})
            key = scheduler.key_for(document['lineage_id'], document['commit_sha256'])
            if key in pending:
                require(pending[key] == document, 'one_manifest_per_lineage_checkpoint')
            pending[key] = document
    return list(pending.values())
