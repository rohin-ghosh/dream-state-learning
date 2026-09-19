"""Seal a local epoch3 from exact epoch2 plus the approved history byte overlay."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import types

from prepare_epoch2 import (HERE, LIVES, checksum, delta, document, plan_template,
    publish, read, require, run_checks, seal_source)


HISTORY = 'organism_v6/orch_r124_train_history.py'
EXPECTED_HISTORY = '8d44b45941228b229340a1546d3bf984965b0f9d2acfab12967c829d48f16315'
CHECKS = HERE.parent / 'post_recovery_pair_receiving_checks_20260919'
BENCHMARKS = dict(curriculum_learner='curriculum_learner_ACCELERATED_COST_1789782985.json',
    curriculum_frozen_sibling='curriculum_frozen_sibling_ACCELERATED_COST_1789782975.json')


def source_files(source):
    result = {}
    for path in sorted(source.rglob('*')):
        require(not path.is_symlink(), 'no_epoch_source_symlinks')
        if path.is_file():
            result[str(path.relative_to(source))] = path.read_bytes()
    return result


def history_parity(original, proposed):
    modules = []
    for name, content in (('_pair_epoch3_legacy_history', original), ('_pair_epoch3_history', proposed)):
        module = types.ModuleType(name)
        require(name not in sys.modules, 'isolated_history_module_name')
        sys.modules[name] = module
        modules.append(module)
        exec(compile(content, name, 'exec'), module.__dict__)
    try:
        histories = [module.TrainHistory(system_prompt='system 🧬', birth_prompt='birth ü') for module in modules]
        texts = ('', 'ordinary', 'λ漢字🧬', '\n\t"\\', '\ud800', 'parent kept')
        for index, text in enumerate(texts):
            for module, history in zip(modules, histories):
                event = module.TrainEvent(event_id=str(index), actor='parent' if index == 5 else 'child',
                    text=text, split='TRAIN', phase='experience', episode_id='one', source_id='retained',
                    source_sha256='a' * 64, origin='TRAIN_COLLECTION')
                require(history.append(event) and not history.append(event), 'append_and_duplicate_parity')
            for count in range(index + 2):
                require(modules[0].asdict(histories[0].frontier(count))
                    == modules[1].asdict(histories[1].frontier(count)), 'every_prefix_exact_canonical_hash')
            require(histories[0].to_json() == histories[1].to_json(), 'legacy_checkpoint_bytes_unchanged')
        for module, history in zip(modules, histories):
            history.pin_parent_event('5')
            summary = module.TrainEvent(event_id='summary', actor='child', text='kept summary', split='TRAIN',
                phase='compaction', episode_id='one', source_id='retained', source_sha256='a' * 64,
                origin='TRAIN_COLLECTION')
            history.compact(summary, through=history.frontier(3))
        require(histories[0].to_json() == histories[1].to_json(), 'retention_and_compaction_bytes_unchanged')
        document = histories[0].checkpoint()
        for module, history in zip(modules, histories):
            restored = module.TrainHistory.restore(document, expected_sha256=document['state_sha256'])
            require(restored.to_json() == history.to_json()
                == deepcopy(history).to_json(), 'restore_and_deepcopy_bytes_unchanged')
            corrupted = deepcopy(document)
            corrupted['events'][0]['text'] = 'tampered'
            try:
                module.TrainHistory.restore(corrupted)
            except ValueError:
                pass
            else:
                raise ValueError('tamper_must_refuse')
        return dict(passed=True, all_prefixes=True, Unicode=True, surrogate_escaping=True,
            retention_compaction=True, legacy_checkpoint_bytes=True, restore=True, deepcopy=True, tamper_rejected=True)
    finally:
        for module in modules:
            del sys.modules[module.__name__]


def prepare(output, *, epoch2=HERE / 'prepared_epoch2_v2', python=sys.executable):
    output, epoch2 = Path(output).absolute(), Path(epoch2).absolute()
    require(output.resolve() == output and output.is_relative_to(HERE) and not output.exists(),
        'new_local_worker_epoch3_output_only')
    require(epoch2.resolve() == epoch2 and epoch2.is_relative_to(HERE), 'local_preserved_epoch2_only')
    port_path = CHECKS / 'frontier_port.py'
    port_bytes = port_path.read_bytes()
    namespace = {'__name__': '_reviewed_pair_frontier_port'}
    exec(compile(port_bytes, str(port_path), 'exec'), namespace)
    main_receipt_path = CHECKS / 'TEST_RECEIPT_1789783461.json'
    main_receipt = read(main_receipt_path)
    prepared_inputs = {}
    for life in LIVES:
        previous = epoch2 / life / 'epoch2'
        receipt_path = previous / 'EPOCH2_SOURCE.json'
        receipt = read(receipt_path)
        files = source_files(previous / 'source')
        pins = {name: checksum(content) for name, content in files.items() if name.endswith('.py')}
        assets = {name: checksum(content) for name, content in files.items() if not name.endswith('.py')}
        require(pins == receipt['new_source_pins'] and assets == {name: entry['sha256']
            for name, entry in receipt['additional_assets'].items()}, 'complete_exact_epoch2_preimage')
        staged_path = CHECKS / (life + '_STAGED.json')
        staged = read(staged_path)
        require(staged['new_source_pins'] == pins and staged['new_source'] == receipt['new_source'],
            'epoch2_matches_actual_main_staged_closure')
        proposed = namespace['port'](files[HISTORY])
        require(checksum(proposed) == EXPECTED_HISTORY, 'exact_user_approved_history_overlay')
        benchmark_path = CHECKS / BENCHMARKS[life]
        benchmark = read(benchmark_path)
        require(benchmark['original_history_sha256'] == pins[HISTORY]
            and benchmark['overlay_sha256'] == EXPECTED_HISTORY
            and benchmark['result']['checkpoint_history_byte_equivalent'] is True
            and benchmark['result']['authorizes_native_handoff'] is False, 'actual_historical_byte_equivalence_only')
        prepared_inputs[life] = (previous, receipt, files, proposed, benchmark_path, staged_path, receipt_path)
    document(output / 'INPUTS.json', dict(observed_utc=datetime.now(timezone.utc).isoformat(),
        port_path=str(port_path), port_sha256=checksum(port_bytes), expected_history_sha256=EXPECTED_HISTORY,
        main_test_receipt_path=str(main_receipt_path), main_test_receipt_sha256=checksum(main_receipt_path.read_bytes()),
        main_receipt_port_pin_matches_current=main_receipt['source_pins'].get(
            str(port_path.relative_to(HERE.parents[2]))) == checksum(port_bytes),
        note='Earlier main test receipt is historical; current port/output are independently verified here.',
        preparer_sha256=checksum(Path(__file__).read_bytes()),
        source_checks_sha256=checksum((HERE / 'source_checks.py').read_bytes())))
    results = {}
    for life, (previous, old, files, proposed, benchmark_path, staged_path, receipt_path) in prepared_inputs.items():
        epoch = output / life / 'epoch3'
        source = epoch / 'source'
        revised = dict(files, **{HISTORY: proposed})
        for name, content in revised.items():
            publish(source / name, content)
        pins = {name: checksum(content) for name, content in revised.items() if name.endswith('.py')}
        changes = delta(old['new_source_pins'], pins)
        require(set(changes) == {HISTORY} and len(pins) == 209, 'one_existing_history_file_only_209_file_closure')
        remote = str(Path(old['new_source']).parent.parent / 'epoch3' / 'source')
        plan = plan_template(read(previous / 'control/PLAN.template.json'), remote)
        require(plan['hard_end_unix'] == old['deadline_unix'], 'no_wall_extension')
        document(epoch / 'control/PLAN.template.json', plan)
        document(epoch / 'control/PARENT_DEPENDENCY_PENDING.json', dict(status='PENDING_ACTUAL_KUHN_FENCE_AND_REBIND',
            parent_owner='Kuhn', previous_contract=read(previous / 'control/PARENT_DEPENDENCY_PENDING.json'),
            source_epoch_must_be_rebound=True, dependency_receipt=None, rebind_receipt=None))
        parity = history_parity(files[HISTORY], proposed)
        tests = run_checks(source, epoch / 'cpu', python)
        cpu = dict(schema='PAIR_EPOCH3_LOCAL_SOURCE_CPU_V1', passed=True, source_pins=pins,
            no_GPU_calls=True, checkpoint_tail_port_passed=True, pair_controls_passed=True,
            synthetic_only=True, actual_checkpoint_validated=False, admission_granted=False,
            live_handoff_authorization=False, history_parity=parity, tests=tests)
        document(epoch / 'cpu/LOCAL_SOURCE_CPU.json', cpu)
        require(source_files(previous / 'source') == files and source_files(source) == revised,
            'epoch2_preserved_and_epoch3_tested_bytes_unchanged')
        seal_source(source)
        receipt = dict(schema='PAIR_EPOCH3_LOCAL_PREPARATION_V1', status='LOCAL_PREPARED_NOT_ADMITTED',
            life=life, local_source=str(source), new_source=remote, new_source_pins=pins,
            old_source=old['old_source'], old_source_pins=old['old_source_pins'],
            old_guard_sha256=old['old_guard_sha256'], changed=delta(old['old_source_pins'], pins),
            epoch2_source=old['new_source'], epoch2_source_pins=old['new_source_pins'],
            epoch2_to_epoch3_delta=changes, epoch1_preserved=True, epoch2_preserved=True,
            source_immutability='EXACT_HASH_PINS_FILES_0444_DIRECTORIES_0555',
            additional_assets=old['additional_assets'], journal_root=old['journal_root'],
            journal_id=old['journal_id'], copy_raw=old['copy_raw'], deadline_unix=old['deadline_unix'],
            lease_end_unix=old['lease_end_unix'], plan_template_candidate_bound=False,
            plan_template_sha256=checksum((epoch / 'control/PLAN.template.json').read_bytes()),
            local_CPU_sha256=checksum((epoch / 'cpu/LOCAL_SOURCE_CPU.json').read_bytes()),
            historical_evidence_pins={str(path): checksum(path.read_bytes())
                for path in (benchmark_path, staged_path, receipt_path, main_receipt_path)},
            receiving_plan_ready=False, admission_granted=False, parent_dependency_status='PENDING',
            live_checkpoint_validated=False, live_binding_reverified=False, transport_performed=False,
            native_signals=[], reservations=[], dispatches=[], GPU_calls=0)
        document(epoch / 'EPOCH3_SOURCE.json', receipt)
        results[life] = dict(receipt=str(epoch / 'EPOCH3_SOURCE.json'), local_source=str(source),
            new_source=remote, python_files=len(pins), epoch2_to_epoch3_delta=changes,
            source_tests=tests['result'], parity=parity)
    summary = dict(schema='PAIR_EPOCH3_LOCAL_PREPARATION_SUMMARY_V1', observed_utc=datetime.now(timezone.utc).isoformat(),
        status='LOCAL_PREPARED_CPU_TESTED_NOT_ADMITTED', results=results, native_signals=[],
        reservations=[], dispatches=[], transport_performed=False, admission_granted=False)
    document(output / 'SUMMARY.json', summary)
    publish(output / 'BUILDER_PROVENANCE.md', ('[Builder] ' + summary['observed_utc'] +
        ' Non-material exact-source epoch3 local preparation only: one existing history-file performance overlay, '
        '209-file closures, 14 actual-source synthetic tests per arm plus old/new history byte/parity checks. '
        'Epoch2/epoch1 and original deadline preserved. No live signal, reservation, transport, GPU, '
        'dispatch, parent action, service management or admission. Historical evidence is not current-head proof.\n').encode())
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(prepare(arguments.output), sort_keys=True, indent=2))
