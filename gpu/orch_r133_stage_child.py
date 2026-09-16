"""Create a new, immutable continual-child plan; admission/launch remain separate."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import socket
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def stage(template_path, source, control, root, startup_path, lease_path,
          physical, gpu_uuid, builder_commit, cpu_receipt_path):
    template_path, source, control, root, startup_path, lease_path, cpu_receipt_path = map(Path,
        (template_path, source, control, root, startup_path, lease_path, cpu_receipt_path))
    for path in (source, control, root, startup_path, lease_path, cpu_receipt_path):
        require(path.is_absolute() and '..' not in path.parts, 'absolute_operator_paths')
    require(not root.exists(), 'new_life_only_no_reset')
    require(startup_path.resolve().is_relative_to(source.resolve()), 'startup_in_source')
    require(re.fullmatch(r'[0-9a-f]{40}', builder_commit), 'pushed_commit_required')
    cpu = json.loads(cpu_receipt_path.read_text())
    require(cpu.get('passed') is True and cpu.get('tests', 0) > 0, 'CPU_receipt_required')
    lease = json.loads(lease_path.read_text())
    require(time.time() < lease['hard_end_unix'] <= lease['lease_end_unix']-120, 'lease_margin')
    template = json.loads(template_path.read_text())
    require('authorized_wall_extension' not in template and 'preupdate_recovery' not in template,
            'fresh_template_without_resume_authority')
    plan = dict(template, source_root=str(source), root=str(root), physical=physical,
                gpu_uuid=gpu_uuid, birth_prompt=startup_path.read_text(),
                hard_end_unix=lease['hard_end_unix'], lease_end_unix=lease['lease_end_unix'])
    plan['startup_context'] = dict(version='R127_STARTUP_V1', path=str(startup_path), sha256=sha(startup_path))
    control.mkdir(parents=True, exist_ok=False)

    def write(name, value):
        with (control/name).open('x') as output:
            json.dump(value, output, sort_keys=True, indent=2, allow_nan=False)

    write('PLAN.json', plan)
    write('ALLOCATION.json', dict(schema='R125_NATIVE_ALLOCATION_V1',
        builder_entry='R133/R134 new-life CPU and provenance gate', builder_entry_pushed=True,
        builder_commit=builder_commit, cpu_tests_passed=True, cpu_receipt_path=str(cpu_receipt_path),
        cpu_receipt_sha256=sha(cpu_receipt_path), declared_unix=time.time(), gpu_uuid=gpu_uuid,
        physical=physical, plan_sha256=sha(control/'PLAN.json')))
    config = dict(schema='R125_CONTINUAL_GUARD_V1', allocation_path=str(control/'ALLOCATION.json'),
        allocation_sha256=sha(control/'ALLOCATION.json'), attempt_dir=str(control),
        hard_end_unix=plan['hard_end_unix'], host_sha256=hashlib.sha256(socket.gethostname().encode()).hexdigest(),
        lease_path=str(lease_path), lease_sha256=sha(lease_path), next_reserved_unix=lease['lease_end_unix'],
        plan_path=str(control/'PLAN.json'), plan_sha256=sha(control/'PLAN.json'), resume=False,
        source_pins={str(path.relative_to(source)): sha(path) for path in source.rglob('*.py')})
    write('GUARD.json', config)
    return dict(config_path=str(control/'GUARD.json'), plan_sha256=config['plan_sha256'],
                startup_sha256=sha(startup_path), gpu_uuid=gpu_uuid, physical=physical,
                launch_attempted=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('template-path', 'source', 'control', 'root', 'startup-path', 'lease-path', 'cpu-receipt-path'):
        parser.add_argument('--' + name, required=True, type=Path)
    parser.add_argument('--physical', required=True, type=int)
    parser.add_argument('--gpu-uuid', required=True)
    parser.add_argument('--builder-commit', required=True)
    print(json.dumps(stage(**vars(parser.parse_args())), sort_keys=True))
