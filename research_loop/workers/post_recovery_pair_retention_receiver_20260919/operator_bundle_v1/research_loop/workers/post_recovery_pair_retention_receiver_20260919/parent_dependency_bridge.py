"""Bound read-only CPU-owner RPC; no fence, rebind, signal or activation command."""

import argparse
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import secrets
import subprocess
import sys
import time


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(content):
    return hashlib.sha256(content).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def owner_exchange(request, dependency_path, dependency_hash, owner):
    require(set(request) == {'schema', 'nonce', 'dependency_path', 'dependency_sha256',
        'life_binding_sha256', 'source_epoch', 'owner_source_pins'}, 'exact_owner_request_fields')
    require(request['schema'] == 'PAIR_PARENT_OWNER_CHECK_REQUEST_V1'
        and request['dependency_path'] == str(dependency_path)
        and request['dependency_sha256'] == dependency_hash, 'pinned_owner_dependency_request')
    raw = owner.file_bytes(dependency_path)
    require(sha(raw) == dependency_hash, 'original_dependency_file_bytes')
    dependency = json.loads(raw)
    require(dependency['life_binding_sha256'] == request['life_binding_sha256']
        and dependency['source_epoch'] == request['source_epoch'], 'same_owner_life_and_epoch')
    plan = owner.read(Path(dependency_path).parent / 'PLAN.json')
    require(plan['source_pins'] == request['owner_source_pins'], 'reviewed_exact_owner_source_closure')
    recheck = owner.verify_fence(dependency_path, dependency_hash, owner.LinuxCPU())
    require(owner.file_bytes(dependency_path) == raw, 'owner_dependency_did_not_change')
    return dict(schema='PAIR_PARENT_OWNER_CHECK_RESPONSE_V1', nonce=request['nonce'],
        dependency_path=str(dependency_path), dependency_sha256=dependency_hash,
        dependency_base64=base64.b64encode(raw).decode(), owner_source_pins=plan['source_pins'],
        original_ledger_pins=dependency['ledger_pins'], recheck=recheck,
        verification_location='ORIGINAL_CPU_OWNER_FILESYSTEM_AND_PROC', native_signals=0)


class ParentDependencyBridge:
    def __init__(self, command, *, dependency_path, dependency_sha256, owner_source_pins,
            timeout_seconds=2, max_clock_skew_seconds=5):
        require(command and all(isinstance(part, str) and part for part in command), 'reviewed_owner_command')
        require(Path(dependency_path).is_absolute() and '..' not in Path(dependency_path).parts,
            'absolute_original_owner_dependency_path')
        require(owner_source_pins and 0 < timeout_seconds <= 2 and 0 <= max_clock_skew_seconds <= 5,
            'bounded_fresh_owner_recheck')
        self.command = list(command)
        self.path, self.sha256 = str(dependency_path), dependency_sha256
        self.source_pins = dict(owner_source_pins)
        self.timeout = timeout_seconds
        self.skew = max_clock_skew_seconds
        self.last_evidence = None

    def check(self, binding, epoch_id):
        request = dict(schema='PAIR_PARENT_OWNER_CHECK_REQUEST_V1', nonce=secrets.token_hex(24),
            dependency_path=self.path, dependency_sha256=self.sha256,
            life_binding_sha256=sha(canonical(binding)), source_epoch=epoch_id,
            owner_source_pins=self.source_pins)
        started = time.monotonic()
        wall_started = time.time()
        try:
            result = subprocess.run(self.command, input=canonical(request), capture_output=True,
                timeout=self.timeout, check=True)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as error:
            raise ValueError('owner_fence_recheck_failed_no_native_action') from error
        require(time.monotonic() - started <= self.timeout and len(result.stdout) <= 16 * 1024**2,
            'bounded_owner_response')
        response = json.loads(result.stdout)
        require(response['schema'] == 'PAIR_PARENT_OWNER_CHECK_RESPONSE_V1'
            and response['nonce'] == request['nonce'] and response['dependency_path'] == self.path
            and response['dependency_sha256'] == self.sha256
            and response['owner_source_pins'] == self.source_pins
            and response['verification_location'] == 'ORIGINAL_CPU_OWNER_FILESYSTEM_AND_PROC'
            and response['native_signals'] == 0, 'fresh_bound_original_owner_response')
        raw = base64.b64decode(response['dependency_base64'], validate=True)
        require(sha(raw) == self.sha256, 'original_dependency_bytes_not_a_mirror')
        dependency = json.loads(raw)
        recheck = response['recheck']
        require(recheck['schema'] == 'PAIR_PARENT_FENCE_RECHECK_V1'
            and recheck['dependency_path'] == self.path and recheck['dependency_sha256'] == self.sha256
            and recheck['life_binding_sha256'] == dependency['life_binding_sha256'] == request['life_binding_sha256']
            and recheck['source_epoch'] == dependency['source_epoch'] == epoch_id
            and recheck['old_parent'] == dependency['old_parent']
            and recheck['delivery_fenced'] is True and type(recheck['inflight_deliveries']) is int
            and recheck['inflight_deliveries'] == 0 and recheck['ledger_pins_verified'] is True
            and recheck['native_signals'] == 0 and response['original_ledger_pins'] == dependency['ledger_pins']
            and wall_started - self.skew <= recheck['observed_unix'] <= time.time() + self.skew,
            'effective_exact_parent_fence_and_original_complete_ledger_inventory')
        self.last_evidence = response
        return dict(path=self.path, sha256=self.sha256, receipt=dependency)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['owner-check'])
    parser.add_argument('--sidecar', type=Path, required=True)
    parser.add_argument('--sidecar-sha256', required=True)
    parser.add_argument('--dependency', type=Path, required=True)
    parser.add_argument('--dependency-sha256', required=True)
    args = parser.parse_args()
    require(args.sidecar.is_absolute() and args.sidecar.resolve() == args.sidecar
        and sha(args.sidecar.read_bytes()) == args.sidecar_sha256, 'exact_Kuhn_sidecar_file')
    request_raw = sys.stdin.buffer.read(1024 * 1024 + 1)
    require(len(request_raw) <= 1024 * 1024, 'bounded_owner_request')
    request = json.loads(request_raw)
    require(request['owner_source_pins'].get(str(args.sidecar)) == args.sidecar_sha256,
        'owner_sidecar_is_in_reviewed_source_pins')
    for name, expected in request['owner_source_pins'].items():
        path = Path(name)
        require(path.is_absolute() and path.resolve() == path and sha(path.read_bytes()) == expected,
            'unchanged_owner_import_closure_before_import')
    sys.path.insert(0, str(args.sidecar.parent))
    spec = importlib.util.spec_from_file_location('verified_pair_parent_owner', args.sidecar)
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    response = owner_exchange(request, args.dependency, args.dependency_sha256, owner)
    print(json.dumps(response, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
