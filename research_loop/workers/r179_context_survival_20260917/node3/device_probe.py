"""Open/close device-ACL proof only; never create a CUDA context or a model."""

import argparse
import json
import os
from pathlib import Path
import stat


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def probe(policy, gpu_uuid):
    require(set(policy) == {'uid', 'gid', 'minor', 'unit'}, 'exact_policy')
    require(os.getuid() == policy['uid'] > 0 and os.getgid() == policy['gid'] > 0, 'same_nonroot_user')
    require(Path('/proc/self/cgroup').read_text().strip() == '0::/system.slice/' + policy['unit'] + '.service',
            'strict_service_cgroup')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == gpu_uuid, 'exact_UUID_environment')
    matches = []
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        if fields.get('GPU UUID', '').strip() == gpu_uuid:
            matches.append(int(fields['Device Minor'].strip()))
    require(matches == [policy['minor']], 'actual_uuid_minor')
    for path in Path('/proc/self/fd').iterdir():
        try:
            require(not os.readlink(path).startswith('/dev/nvidia'), 'no_inherited_GPU_descriptors')
        except FileNotFoundError:
            pass
    denied = []
    for minor in range(8):
        path = Path('/dev/nvidia' + str(minor))
        metadata = path.lstat()
        require(stat.S_ISCHR(metadata.st_mode) and os.major(metadata.st_rdev) == 195
                and os.minor(metadata.st_rdev) == minor, 'actual_character_device')
        try:
            descriptor = os.open(path, os.O_RDWR | os.O_CLOEXEC)
        except PermissionError:
            require(minor != policy['minor'], 'target_device_access_required')
            denied.append(minor)
        else:
            os.close(descriptor)
            require(minor == policy['minor'], 'foreign_device_access_forbidden')
    require(denied == [minor for minor in range(8) if minor != policy['minor']], 'all_seven_denied')
    return dict(status='PASS', policy=policy, gpu_uuid=gpu_uuid, denied_foreign_minors=denied,
        target_open_close=True, CUDA_context_created=False, model_calls=0, learner_signals=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--policy', required=True)
    parser.add_argument('--uuid', required=True)
    args = parser.parse_args()
    print(json.dumps(probe(json.loads(args.policy), args.uuid), sort_keys=True))
