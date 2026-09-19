"""Portable, one-shot C2 source/checkpoint/tail CPU checks; never activate a life."""

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def raw_sha(path):
    path = Path(path)
    require(path.resolve() == path.absolute() and path.is_file(), 'literal_regular_evidence_file')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def verify_source(source, manifest):
    from manifest_checks import verify
    return verify(source, manifest)


def read_checkpoint_pair(boundary, binding, complete_index, complete_sha256, max_after=64):
    require(type(complete_index) is int and complete_index >= 0 and 1 <= max_after <= 128,
        'explicit_bounded_COMPLETE_selection')
    root = Path(binding['journal_root']) / 'records'
    identity = boundary.journal_identity(binding)
    records, intents, paths = [], {}, {}
    for index in range(complete_index, complete_index + max_after + 1):
        record_path = root / f'{index:020d}.json'
        intent_path = root / f'{index:020d}.intent.json'
        record = boundary.read(record_path, durable=True)
        intent = boundary.read(intent_path, durable=True)
        require(record['index'] == intent['index'] == index, 'exact_record_filename_index')
        if index == complete_index:
            require(record['kind'] == 'SLEEP_COMPLETE' and record['sha256'] == complete_sha256,
                'exact_historically_selected_COMPLETE')
        else:
            require(record['kind'] in ('INBOX', 'R184_LEARN_COMPLETE'), 'no_intervening_work_before_LEARN')
        records.append(record)
        intents[index] = intent
        paths[str(record_path)] = raw_sha(record_path)
        paths[str(intent_path)] = raw_sha(intent_path)
        if record['kind'] == 'R184_LEARN_COMPLETE':
            break
    candidate = boundary.validate_records(records, binding, intents=intents)
    require(candidate is not None, 'matching_COMPLETE_LEARN_required')
    require(boundary.journal_identity(binding) == identity
        and all(raw_sha(path) == value for path, value in paths.items()), 'unchanged_selected_completed_evidence')
    candidate.update(journal_identity=identity, durable=True, mailbox={})
    return candidate, paths


def verify_guard_template(effective, template, source):
    require(effective['source_root'] == str(source), 'guard_matches_actual_receiving_source')
    normalized = deepcopy(effective)
    for key in ('complete_index', 'complete_sha256'):
        normalized['checkpoint_tail_recovery'][key] = template['checkpoint_tail_recovery'][key]
    require(normalized == template, 'guard_only_reanchors_COMPLETE_no_recipe_wall_or_bridge_change')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('source', 'checkpoint', 'tail', 'guard'))
    parser.add_argument('--bundle', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--source', type=Path)
    parser.add_argument('--complete-index', type=int)
    parser.add_argument('--complete-sha256')
    parser.add_argument('--guard', type=Path)
    args = parser.parse_args()
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_only_environment_required')
    bundle = args.bundle.resolve()
    manifest = json.loads((bundle / 'EPOCH4_SOURCE.json').read_bytes())
    for name, expected in manifest['helper_pins'].items():
        require(raw_sha(bundle / 'tools' / name) == expected, 'exact_standalone_CPU_helper:' + name)
    source = args.source.resolve() if args.source else bundle / 'source'
    started = time.monotonic()
    pins = verify_source(source, manifest)
    result = dict(schema='C2_EPOCH4_READONLY_CPU_V1', mode=args.mode, passed=True,
        source=str(source), source_pins=pins, manifest_sha256=raw_sha(bundle / 'EPOCH4_SOURCE.json'),
        actual_checkpoint_validated=False, actual_tail_validated=False, current_boundary_authorized=False,
        live_handoff_authorization=False, admission_granted=False, journal_writes=0,
        native_signals=[], dispatches=[], GPU_calls=0, hard_end_unix=1789927200)
    if args.mode != 'source':
        boundary = load('c2_cpu_boundary', bundle / 'tools' / 'boundary.py')
        probe = load('c2_cpu_probe', bundle / 'tools' / 'cpu_probe.py')
        binding = manifest['historical_life_binding']
        plan = json.loads((bundle / 'control' / 'PLAN.template.json').read_bytes())
        require(raw_sha(bundle / 'control' / 'PLAN.template.json') == manifest['plan_template_sha256'],
            'exact_candidate_unbound_plan_template')
        if args.mode == 'checkpoint':
            selected = plan['checkpoint_tail_recovery']
            require((args.complete_index is None) == (args.complete_sha256 is None), 'supply_index_and_hash_together')
            complete_index = selected['complete_index'] if args.complete_index is None else args.complete_index
            complete_sha = selected['complete_sha256'] if args.complete_sha256 is None else args.complete_sha256
            candidate, evidence = read_checkpoint_pair(boundary, binding, complete_index, complete_sha)
            checkpoint = candidate['checkpoint']
            directory = Path(checkpoint['adapter_path']).parent
            require(directory.resolve() == directory
                and directory.parent == Path(binding['journal_root']).parent / 'checkpoints'
                and Path(checkpoint['optimizer_rng_path']) == directory / 'optimizer_rng.pt'
                and boundary.read(directory / 'COMMIT.json') == checkpoint, 'original_exact_C2_checkpoint_paths')
            checkpoint_paths = [directory / 'COMMIT.json', Path(checkpoint['optimizer_rng_path']),
                *sorted(Path(checkpoint['adapter_path']).iterdir())]
            evidence.update({str(path): raw_sha(path) for path in checkpoint_paths})
            result['proof'] = probe.probe(str(source), candidate, plan, 'checkpoint')
            require(all(raw_sha(path) == value for path, value in evidence.items()), 'unchanged_CPU_checkpoint_bytes')
            result.update(actual_checkpoint_validated=True, checkpoint_optimizer_steps=checkpoint['optimizer_steps'],
                candidate_complete_index=candidate['complete_index'], candidate_complete_sha256=candidate['complete_sha256'],
                resume_state_sha256=candidate['resume_state']['sha256'], evidence_pins=evidence,
                selection_role='EXACT_HISTORICAL_SAVED_CHECKPOINT_NOT_CURRENT_HANDOFF_AUTHORITY')
        elif args.mode == 'tail':
            candidate = boundary.read_boundary(binding, max_records=128, durable=True)
            require(candidate is not None, 'no_current_COMPLETE_LEARN_boundary_no_retry_or_signal')
            selection = deepcopy(plan['checkpoint_tail_recovery'])
            selection.update(complete_index=candidate['complete_index'], complete_sha256=candidate['complete_sha256'])
            plan['checkpoint_tail_recovery'] = selection
            result['proof'] = probe.probe(str(source), candidate, plan, 'tail', selection)
            boundary.same_boundary(candidate, boundary.read_boundary(binding, max_records=128, durable=True))
            result.update(actual_tail_validated=True, candidate_complete_index=candidate['complete_index'],
                candidate_complete_sha256=candidate['complete_sha256'],
                resume_state_sha256=candidate['resume_state']['sha256'])
        else:
            require(args.guard is not None, 'explicit_Main_prepared_guard_required')
            guard = boundary.read(args.guard)
            effective = boundary.read(guard['plan_path'])
            verify_guard_template(effective, plan, source)
            result['proof'] = probe.probe(str(source), {}, effective, 'guard', dict(guard_path=str(args.guard)))
    verify_source(source, manifest)
    result['elapsed_seconds'] = time.monotonic() - started
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
