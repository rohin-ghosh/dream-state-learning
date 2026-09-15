"""A2 scan sampling repair, retaining strict r110 three-observation checks."""

import argparse
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from gpu import orch_math_feedback_uptake_r124_readout as run
from gpu import orch_math_feedback_uptake_r118_argv_admission as argv


PRIOR = Path('/localhome/local-rohing/orch_math_feedback_uptake_r124_runtime_source_20260915_v2/gpu/orch_math_feedback_uptake_r124_runtime.py')
PRIOR_SHA = 'b27d8196b9a6f4edae3e239abbd699858426d8d2f056640bb3c72eba28c4a1b5'
SERVICE = run.ROOT/'A2/runtime_recovery5'


def extra_samples(directory, target, identity_reader):
    samples = []
    for position in range(2):
        sample = dict(visibility_complete=False)
        try:
            before = identity_reader(directory)
            sample.update(before)
            executable = (directory/'exe').stat()
            sample['executable_identity'] = [executable.st_dev, executable.st_ino]
            entries = (directory/'environ').read_bytes().split(b'\0')
            values = [entry.split(b'=',1)[1].decode() for entry in entries if entry.startswith(b'CUDA_VISIBLE_DEVICES=')]
            run.require(len(values) <= 1, 'unique_CVD')
            sample['cvd'] = values[0] if values else None
            opened = False
            for descriptor in (directory/'fd').iterdir():
                try:
                    opened |= os.readlink(descriptor) == target
                except FileNotFoundError:
                    continue
            after = identity_reader(directory)
            final_executable = (directory/'exe').stat()
            run.require(all(before[key] == after[key] for key in argv.original.KERNEL_KEYS), 'stable_kernel_identity')
            run.require((executable.st_dev,executable.st_ino) == (final_executable.st_dev,final_executable.st_ino), 'no_exec_transition')
            sample.update(target_open=opened,visibility_complete=True)
        except (OSError,UnicodeError,ValueError,KeyError):
            pass
        samples.append(sample)
    return samples


def enriched_scan(index, service):
    source = inspect.getsource(argv.original.scan)
    needle = "observations.setdefault(identity['pid'], []).append(sample)"
    run.require(source.count(needle) == 1, 'exact_original_sampling_seam')
    source = source.replace(needle,needle+"\n        observations[identity['pid']].extend(extra_samples(directory, target, original))")
    def reconciler(report, observations):
        result = argv.reconcile(report, observations)
        result['all_identity_observations'] = {str(pid):samples for pid,samples in observations.items()}
        return result
    namespace = dict(argv.original.scan.__globals__,reconcile=reconciler,extra_samples=extra_samples)
    exec(compile(source,__file__+':three_observation_sampling','exec'),namespace)
    return namespace['scan'](index,service)


def scan():
    run.configure()
    plan = run.validate(run.ROOT/'A2')
    run.old.admission.life.previous.math.bind()
    report = run.old.admission.bind_scan(lambda: enriched_scan(plan['index'],run.control.ORIGINAL/'SERVICE_IDENTITY.json'))
    report['sampling_repair'] = 'TWO_ADDITIONAL_REAL_KERNEL_EXE_CVD_FD_OBSERVATIONS_PER_SCANNER_IDENTITY'
    return report


def subprocess_api(scan_process):
    return SimpleNamespace(**dict(vars(subprocess), run=scan_process))


def runtime():
    run.require(run.sha(PRIOR) == PRIOR_SHA,'exact_frozen_runtime_dependency')
    spec=importlib.util.spec_from_file_location('math_runtime_v1',PRIOR)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SERVICE, module.__file__ = SERVICE, __file__
    original_run = subprocess.run
    def scan_process(command, **kwargs):
        expected=['sudo','-n','env','CUDA_VISIBLE_DEVICES=','PYTHONPATH='+str(run.SOURCE),
            module.PYTHON,'-B','-m',run.MODULE,'scan','--root',str(run.ROOT/'A2')]
        run.require(command == expected,'only_exact_scan_command_rebound')
        replacement=command[:7]+[str(Path(__file__).resolve()),'scan']
        return original_run(replacement,**kwargs)
    module.subprocess=subprocess_api(scan_process)
    return module


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('phase',choices=('guard','resident','scan'))
    phase=parser.parse_args().phase
    if phase == 'scan':
        print(json.dumps(scan()))
    else:
        module=runtime()
        if phase == 'guard':
            prior_service=run.ROOT/'A2/runtime_recovery4'
            module.require_absent(run.read(prior_service/'GUARD_STARTED.json')['identity'])
            run.require(not (prior_service/'LAUNCH.json').exists(),'no_model_dispatch_in_last_guard')
            report=run.read(prior_service/'ADMISSION.json')
            run.require(report['clear'] is False and report['blocking_reasons'] == ['process_identity_drift:4121286'], 'exact_last_failed_admission')
            module.require_absent({'pid':4121286})
        getattr(module,phase)()
