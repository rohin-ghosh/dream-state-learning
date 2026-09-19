"""Validated native engine/confinement with diagnostic TRAIN hooks; no alternate trainer."""

from copy import deepcopy
import importlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

from gpu import orch_r125_continual_native as native
from gpu import orch_r125_stream_journal as journal_module
from gpu import orch_r184_think_act_learn as driver_module
from gpu import r205_runtime as confinement
from gpu import r232_runtime as frozen
from gpu.cohort_contract import ARMS, bound_events, digest, require, sha, validate_main, validate_treatment


def capture_adapter(plan, checkpoint, cycle):
    require(type(cycle) is int and 0 <= cycle <= plan['max_sleeps'], 'bounded_capture_cycle')
    expected = Path(plan['root']) / 'checkpoints' / ('initial' if cycle == 0 else f'sleep_{cycle:06d}')
    require(Path(checkpoint['adapter_path']) == expected / 'adapter', 'same_arm_completed_checkpoint')
    require(native.read(expected / 'COMMIT.json') == checkpoint, 'committed_checkpoint_exact')
    native.NativeChild.verify_checkpoint(checkpoint)
    allowed = {'adapter_config.json', 'adapter_model.safetensors', 'README.md'}
    require(set(checkpoint['adapter_files']) <= allowed
        and {'adapter_config.json', 'adapter_model.safetensors'} <= set(checkpoint['adapter_files']),
        'adapter_only_export_no_optimizer_or_history')
    destination = Path(plan['root']).parent / 'eval_exports' / f'sleep_{cycle:06d}'
    destination.parent.mkdir(exist_ok=True)
    require(not destination.exists(), 'capture_no_implicit_overwrite')
    with tempfile.TemporaryDirectory(prefix='.capture-', dir=destination.parent) as temporary:
        prepared = Path(temporary) / 'complete'
        prepared.mkdir()
        adapter = prepared / 'adapter'
        adapter.mkdir()
        for name in sorted(checkpoint['adapter_files']):
            original = expected / 'adapter' / name
            require(not original.is_symlink() and sha(original) == checkpoint['adapter_files'][name], 'immutable_adapter_asset')
            shutil.copyfile(original, adapter / name)
            require(sha(adapter / name) == checkpoint['adapter_files'][name], 'copied_adapter_hash')
        metadata = dict(schema='MATCHED_COHORT_ADAPTER_ONLY_V1', arm=plan['cohort']['arm'], cycle=cycle,
            base_sha256=checkpoint['base_sha256'], adapter_files=checkpoint['adapter_files'],
            adapter_state_sha256=checkpoint['adapter_state_sha256'], checkpoint_commit_sha256=sha(expected / 'COMMIT.json'),
            plan_sha256=digest(plan), evaluation_performed=False,
            excludes=['optimizer', 'RNG', 'history', 'working_state', 'journal', 'parent', 'scores'])
        native.write_once(prepared / 'CAPTURE.json', metadata)
        os.rename(prepared, destination)
    return destination


def hook_context(driver):
    return dict(schema='MATCHED_COHORT_TRAIN_CONTEXT_V1',
        cycle=len(driver.stream.sleep_receipts) + 1, segment=len(driver.stream.rows),
        source_root=driver.child.plan['source_root'])


def diagnostic_driver(base, main, guided):
    class DiagnosticDriver(base):
        def drain_console(self, stage):
            require(not self.journal.read_inbox(), 'diagnostic_inputs_only_through_bound_MAIN_interface')
            return []

        def _generate_stage(self, stage, *, incoming, **options):
            require(not incoming, 'no_undeclared_inbox_inputs')
            if stage == 'THINK':
                context = hook_context(self)
                supplied = main.before_think(deepcopy(context))
                require(type(supplied) is dict and set(supplied) == {'environment', 'parent'}, 'explicit_THINK_inputs')
                require(supplied['environment'], 'environment_before_every_THINK')
                require(guided or not supplied['parent'], 'unparented_condition_rejects_parent_advice')
                incoming = bound_events(supplied['environment'], actor='environment',
                    cycle=context['cycle'], segment=context['segment'])
                if guided:
                    incoming += bound_events(supplied['parent'], actor='parent',
                        cycle=context['cycle'], segment=context['segment'])
                self.journal.record('COHORT_TRAIN_INPUT', dict(cycle=context['cycle'], segment=context['segment'],
                    inputs=deepcopy(supplied), all_external_tokens_masked=True, training_eligible=False))
            return super()._generate_stage(stage, incoming=incoming, **options)

        def _cpu(self, origin):
            raise ValueError('MAIN_CPU_executor_not_enrolled_use_recorded_TRAIN_feedback_hook')

        def act(self):
            outcome = super().act()
            context = hook_context(self)
            context.update(act_text=self.stream.rows[-1]['target'],
                act_source_sha256=self.stream.rows[-1]['source_sha256'], native_outcome=deepcopy(outcome))
            supplied = main.after_act(deepcopy(context))
            events = bound_events(supplied, actor='environment', cycle=context['cycle'], segment=context['segment'])
            for event in events:
                self.stream.history.append(event)
            self.journal.record('COHORT_TRAIN_FEEDBACK', dict(cycle=context['cycle'],
                act_source_sha256=context['act_source_sha256'], sources=deepcopy(supplied),
                training_eligible=False, heldout_evaluation=False))
            return outcome

    return DiagnosticDriver


def install(plan):
    validate_treatment(plan)
    require(plan['cohort']['main_configured'], 'MAIN_TRAIN_configuration_required_before_model_load')
    validate_main(plan['cohort']['main'], plan['source_root'])
    main = importlib.import_module('gpu.cohort_train_interface')
    require(callable(main.before_think) and callable(main.after_act), 'MAIN_TRAIN_hooks_required')
    driver_module.ThinkActLearn = diagnostic_driver(driver_module.ThinkActLearn, main, plan['cohort']['guided'])
    original_loop = driver_module.run_loop

    def finite_loop(child, stream, journal, anchors, current_plan, root, plan_path, completed_sleeps):
        require(completed_sleeps == 0 and not stream.rows, 'fresh_initial_diagnostic_only_no_resume_of_completed_campaign')
        capture_adapter(current_plan, native.read(root / 'checkpoints/initial/COMMIT.json'), 0)
        return original_loop(child, stream, journal, anchors, current_plan, root, plan_path, completed_sleeps)

    driver_module.run_loop = finite_loop
    native.fresh_readout = lambda child, plan_path, checkpoint, cycle: capture_adapter(child.plan, checkpoint, cycle)
    if not plan['cohort']['weight_updates']:
        frozen.INITIAL = native.read(Path(plan['root']) / 'checkpoints/initial/COMMIT.json')
        native.NativeChild = frozen.FrozenChild
        native.ContinualStream = frozen.FrozenStream
        journal_module.StreamJournal = frozen.FrozenJournal


def main():
    require('--config' in sys.argv, 'guard_config_required')
    config_path = Path(sys.argv[sys.argv.index('--config') + 1])
    config = native.read(config_path)
    plan = native.read(config['plan_path'])
    validate_treatment(plan)
    require(plan['cohort']['main_configured'], 'MAIN_TRAIN_configuration_required_no_dispatch')
    validate_main(plan['cohort']['main'], plan['source_root'])
    confinement.DEVICES = {treatment['physical']: (treatment['gpu_uuid'], treatment['pci']) for treatment in ARMS.values()}
    confinement.MODULE = 'gpu.cohort_runtime'
    confinement.install_runtime = install
    confinement.main()


if __name__ == '__main__':
    main()
