"""Dedicated readout entry inside the unchanged node2 strict device service."""

import argparse
import os
from pathlib import Path
import time

from gpu import orch_r125_continual_guard as guard
from gpu import orch_r125_continual_native as native
from gpu import orch_r186_behavior_readout as readout
from gpu import r184_node2_confinement as containment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--guard', type=Path, required=True)
    parser.add_argument('--unit', required=True)
    parser.add_argument('--device-only', action='store_true')
    args = parser.parse_args()
    config, plan = guard.validate(args.guard)
    attempt = Path(config['attempt_dir'])
    proof = containment.verify(args.unit)
    readout._write_once(attempt / ('DEVICE_PROOF.json' if args.device_only else 'READOUT_DEVICE_PROOF.json'), proof)
    if args.device_only:
        return
    admission = native.read(attempt / 'ADMISSION.json')
    report = admission['report']
    native.require(report['scanner_euid'] == 0 and report['clear'] and not report['blocking_reasons']
        and report['gpu']['uuid'] == plan['gpu_uuid']
        and admission['guard_sha256'] == native.sha(args.guard)
        and 0 <= time.time() - admission['verified_unix'] <= 120, 'fresh_exact_readout_admission')
    os.environ['R125_ADMISSION_PLAN_SHA256'] = config['plan_sha256']
    os.environ[readout.CONFIG_BINDING] = config['behavior_config_sha256']
    readout._write_once(attempt / 'READOUT_DISPATCHED.json', dict(
        schema='R186_ACTUAL_BEHAVIOR_DISPATCH_V1', pid=os.getpid(),
        startticks=Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19],
        started_unix=time.time(), gpu_uuid=plan['gpu_uuid'], physical=plan['physical'],
        checkpoint_path=config['checkpoint_path'], plan_sha256=config['plan_sha256'],
        config_sha256=config['behavior_config_sha256'], guard_sha256=native.sha(args.guard),
        admission_sha256=native.sha(attempt / 'ADMISSION.json'), device_proof=proof,
        output_path=config['behavior_output'], model_loaded=False, raw_outputs_released=False))
    complete = readout.run(config['plan_path'], config['checkpoint_path'],
        config['behavior_config_path'], config['behavior_output'])
    readout._write_once(attempt / 'READOUT_COMPLETE_METADATA.json', dict(
        schema='R186_BEHAVIOR_OPERATIONAL_COMPLETION_V1', status=complete['status'],
        finished_unix=complete['finished_unix'], calls=complete['calls'],
        checkpoint_commit_sha256=complete['checkpoint_commit_sha256'],
        adapter_state_sha256=complete['adapter_state_sha256'],
        config_sha256=complete['config_sha256'], plan_sha256=complete['plan_sha256'],
        complete_receipt_sha256=native.sha(Path(config['behavior_output']) / 'COMPLETE.json'),
        before_after_verified=complete['before_after_verified'], rng=complete['rng'],
        output_path=config['behavior_output'], raw_outputs_released=False,
        semantic_results_read=False, learning_claim=False))


if __name__ == '__main__':
    main()
