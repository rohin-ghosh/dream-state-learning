"""One staggerable canonical baseline using existing route stages and guardians."""

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import subprocess
import sys
import time
from types import SimpleNamespace

from gpu import orch_guided_native as native
from gpu import orch_route_parent_campaign_run as run
from organism_v6 import orch_guided_bridge as bridge
from organism_v6 import orch_route_parent_campaign_canonical as policy


require = policy.require
_ADAPTER_IDENTITY_FOR = run.identity_for


@dataclass(frozen=True)
class BaseIdentity:
    base_sha256: str

    @property
    def state_sha256(self):
        return self.base_sha256

    def verify(self):
        require(bridge.valid_hash(self.base_sha256), 'verified_base_hash_required')
        return self

    def document(self):
        return dict(kind='FROZEN_QWEN_BASE_NO_ADAPTER', path=None, files=[],
                    state_sha256=self.base_sha256, base_sha256=self.base_sha256)

    @classmethod
    def from_document(cls, document):
        identity = cls(document['base_sha256']).verify()
        require(document == identity.document(), 'exact_no_adapter_identity_required')
        return identity


def observe_base(engine, expected):
    expected.verify()
    parameters = dict(engine.model.named_parameters())
    require(bool(parameters) and not any(native.is_lora(name) for name in parameters), 'no_lora_parameters_permitted')
    require(not getattr(engine.model, 'peft_config', None), 'no_peft_mount_permitted')
    require(not any(parameter.requires_grad for parameter in parameters.values()), 'base_only_must_be_frozen')
    engine.verify_base()
    require(native.state_hash(engine.model.state_dict(keep_vars=True)) == expected.base_sha256,
            'mounted_base_only_hash_drift')
    return expected


@dataclass
class LoadedBase:
    engine: object
    binding: object
    context: object
    process: tuple
    observed: BaseIdentity

    def verify_unchanged(self):
        require(native.process_identity() == self.process, 'base_stage_process_changed')
        self.context.validate(self.binding)
        return observe_base(self.engine, self.observed)


def load_stage(binding, *, model_dir, device, gpu_uuid, context, check,
               predecessor_processes=(), engine_factory=None, tokenizer_loader=None):
    if binding.arm != 'NO_LORA':
        return native.load_stage(binding, model_dir=model_dir, device=device, gpu_uuid=gpu_uuid,
            context=context, check=check, predecessor_processes=predecessor_processes,
            engine_factory=engine_factory, tokenizer_loader=tokenizer_loader)
    require(binding.phase in ('collection', 'sealed_readout'), 'no_lora_training_forbidden')
    require(os.getpid() == native._IMPORT_PID, 'native_stage_requires_exec_not_fork')
    require(Path(model_dir).is_absolute() and Path(model_dir).is_dir(), 'explicit_local_model_required')
    require(device == 'cuda:0' and os.environ.get('CUDA_VISIBLE_DEVICES') == gpu_uuid,
            'exact_no_lora_gpu_uuid_required')
    context.validate(binding)
    require(isinstance(binding.adapter, BaseIdentity), 'base_identity_not_adapter_required')
    binding.adapter.verify()
    for reference in binding.receipt_refs:
        reference.read()
    require(type(predecessor_processes) is tuple and all(type(item) is tuple and len(item) == 3
            for item in predecessor_processes), 'explicit_predecessor_processes_required')
    process = native.process_identity()
    fresh = process not in native._USED_PROCESSES and process not in predecessor_processes
    require(fresh, 'fresh_base_only_process_required')
    if binding.fresh_process:
        require(binding.cycle == 0 or bool(predecessor_processes), 'fresh_readout_predecessor_required')
    native._USED_PROCESSES.add(process)
    options = SimpleNamespace(model_dir=str(model_dir), device=device, gpu_uuid=gpu_uuid,
        phase='readout', adapter_dir=None, expected_base_sha256=binding.adapter.base_sha256)
    tokenizer = (tokenizer_loader or native.source.native.load_local_tokenizer)(str(model_dir))
    engine = (engine_factory or run.Engine)(options, tokenizer, check=check)
    observed = observe_base(engine, binding.adapter)
    binding.verify_loaded(adapter=observed, base_sha256=observed.base_sha256,
        parent_present=bool(context.private_guidance), fresh_process=fresh,
        transient_context=context.transient_context, sleep_prompt=context.sleep_prompt)
    return LoadedBase(engine, binding, context, process, observed)


def identity_for(root, arm, cycle, phase, initial):
    if arm != 'NO_LORA':
        return _ADAPTER_IDENTITY_FOR(root, arm, cycle, phase, initial)
    require(phase != 'source', 'no_lora_is_not_source_generator')
    base = BaseIdentity(initial['base_sha256']).verify()
    if cycle == 0:
        return base, ()
    if phase == 'readout':
        prior = run.read(root / arm / f'cycle{cycle}/sleep/COMPLETE.json')
        require(prior['arm'] == arm and prior['cycle'] == cycle and prior['status'] == 'COMPLETE'
                and prior['updates'] == 0 and prior['fits'] == 0, 'no_lora_own_noop_sleep_required')
        child = BaseIdentity.from_document(prior['output_adapter'])
        require(child == base, 'base_identity_changed')
        return child, (tuple(prior['process']),)
    prior = run.read(root / arm / f'cycle{cycle - 1}/sleep/COMPLETE.json') if cycle > 1 else None
    child = BaseIdentity.from_document(policy.next_identity(base.document(), arm, cycle, prior))
    return child, (tuple(prior['process']),) if prior else ()


def configure():
    require(not os.environ.get('ROUTE_PARENT_WIRE_RESUME') and not os.environ.get('ROUTE_PARENT_CONFIG'),
            'canonical_not_legacy_repair_or_config')
    run.policy = policy
    run.ROOT = Path(policy.ROOT)
    run.RUN_MODULE = 'gpu.orch_route_parent_campaign_canonical'
    run.DEVICES = {arm: (index, run.guardian.DEVICES[index]) for index, arm in enumerate(policy.ARMS)}
    run.native = SimpleNamespace(**{name: getattr(native, name) for name in dir(native) if not name.startswith('__')})
    run.native.load_stage = load_stage
    run.identity_for = identity_for


def dispatch(root, arm):
    run.verify(root)
    publication = run.read(root / 'PUBLICATION.json')
    require(publication['own_cpu_tests_passed'] and publication['dated_builder_receipt']
            and publication['prepare_sha256'] == run.sha(root / 'PREPARE.json'), 'canonical_pre_gpu_gate')
    release = run.read(root / f'LANE_RELEASE_{arm}.json')
    index, uuid = run.DEVICES[arm]
    require(release['released'] is True and release['physical_index'] == index
            and release['uuid'] == uuid and release['owner'] in ('ROUTE_PARENT_CAMPAIGN', 'Poincare', 'Main'),
            'explicit_per_lane_owner_release_required')
    if arm == 'GUIDED':
        prior = run.read(Path('/tmp/orch_route_parent_campaign_20260915_segment2/GUIDED_GUARD/COMPLETE.json'))
        require(prior['status'] == 'COMPLETE', 'preserve_active_previous_guided_life')
    require((root / 'START.json').exists(), 'prospective_common_clock_required')
    deadline = run.read(root / 'START.json')['hard_deadline_unix']
    require(time.time() < deadline - 360 and deadline <= policy.CAMPAIGN_DEADLINE
            and deadline < run.guardian.LEASE_CUTOFF - 6 * 3600, 'unchanged_campaign_and_lease_margins')
    marker = root / f'DISPATCH_{arm}.json'
    with marker.open('x') as stream:
        stream.write('{}\n')
    run.admit(root, index, root / f'LAUNCH_ADMISSION_{arm}.json', deadline)
    command = [run.guardian.PYTHON, '-B', '-m', run.RUN_MODULE, '--phase', 'lane', '--arm', arm]
    with (root / f'LANE_{arm}.log').open('x') as log:
        child = subprocess.Popen(command, cwd=run.TREE, env=dict(os.environ, PYTHONPATH=str(run.TREE)),
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    run.write(marker, dict(pid=child.pid, arm=arm, physical_index=index, uuid=uuid,
        launched_unix=time.time(), deadline_unix=deadline, command=command,
        start_time_offset_seconds=time.time() - run.read(root / 'START.json')['started_unix']))


def main():
    configure()
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=('prepare', 'launch', 'lane', 'source', 'experience', 'sleep', 'readout'), required=True)
    parser.add_argument('--arm', choices=policy.ARMS, default='GUIDED')
    parser.add_argument('--cycle', type=int, default=0)
    args = parser.parse_args()
    if args.phase == 'prepare':
        run.prepare(run.ROOT)
    elif args.phase == 'launch':
        dispatch(run.ROOT, args.arm)
    elif args.phase == 'lane':
        run.lane(run.ROOT, args.arm)
    else:
        run.stage(run.ROOT, args.arm, args.cycle, args.phase)


if __name__ == '__main__':
    main()
