"""Exact original-node read-only RPC and nonce-bound CPU owner-fence transport."""

import base64
import hashlib
import json
from pathlib import Path
import secrets
import shlex
import subprocess
import time

import common as core
from common import digest, encoded, pinned, pins_match, require


class Remote:
    def __call__(self, action, plan, value):
        require(action in ('drain', 'loaded'), 'remote_readonly_actions_only')
        wrapper = core.REPO / 'gpu/ovx3_ssh.sh'
        require(str(wrapper) in plan['source_pins'], 'original_C2_transport_source_pin')
        pins_match({str(wrapper): plan['source_pins'][str(wrapper)]})
        remote = plan['remote_files']
        directory = plan['remote_adapter_directory']
        require(set(remote) == {str(Path(directory) / name) for name in ('common.py', 'c2_owner_binding.py')},
            'exact_remote_readonly_adapter_closure')
        script = ('import hashlib,json,sys\nfrom pathlib import Path\n'
            'pins=' + repr(remote) + '\n'
            'if not all(hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected for path,expected in pins.items()): '
            'raise ValueError("exact_remote_helper_source")\n'
            'sys.path.insert(0,' + repr(directory) + ');import c2_owner_binding as adapter;'
            'envelope=json.loads(sys.stdin.read());'
            'result=adapter.drain(envelope["plan"],envelope["value"]) if envelope["action"]=="drain" '
            'else adapter.verify(envelope["value"]["path"],envelope["value"]["sha256"]);'
            'print(json.dumps(dict(nonce=envelope["nonce"],result=result)))')
        envelope = dict(action=action, plan=plan, value=value, nonce=secrets.token_hex(24))
        command = 'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 python3 -B -c ' + shlex.quote(script)
        result = subprocess.run(['bash', str(wrapper), command], input=encoded(envelope), capture_output=True,
            check=True, timeout=90, close_fds=True)
        require(len(result.stdout) <= 4 * 1024**2, 'bounded_remote_response')
        reply = json.loads(result.stdout)
        require(reply['nonce'] == envelope['nonce'] and reply['result']['native_signals'] == 0
            and reply['result']['journal_writes'] == 0, 'bound_readonly_remote_response')
        proof = reply['result']
        if action == 'drain':
            require(proof['schema'] == 'C2_DRAIN_REMOTE_VERIFIED_V1'
                and proof['life_binding_sha256'] == digest(plan['old_life'])
                and proof['inventory_sha256'] == digest(value), 'same_C2_drained_inventory')
        else:
            require(proof['schema'] == 'C2_ACTUAL_POST_LOADED_REBIND_VERIFIED_V1'
                and proof['binding_sha256'] == value['sha256']
                and proof['life_binding_sha256'] == digest(plan['old_life'])
                and proof['source_epoch'] == plan['source_epoch'], 'same_actual_C2_successor')
        return proof


def owner_exchange(request, dependency, cpu):
    from owner import verify_fence
    require(request['schema'] == 'C2_OWNER_CHECK_REQUEST_V1' and request['dependency'] == dependency,
        'exact_original_owner_request')
    receipt = pinned(dependency)
    plan = core.read(receipt['plan_path'])
    require(request['life_binding_sha256'] == receipt['life_binding_sha256']
        and request['source_epoch'] == receipt['source_epoch'] and request['source_pins'] == plan['source_pins'],
        'same_source_epoch_owner_request')
    checked = verify_fence(dependency, cpu)
    raw = core.file_bytes(dependency['path'])
    require(hashlib.sha256(raw).hexdigest() == dependency['sha256'], 'dependency_unchanged')
    return dict(schema='C2_OWNER_CHECK_RESPONSE_V1', nonce=request['nonce'], dependency=dependency,
        dependency_base64=base64.b64encode(raw).decode(), recheck=checked,
        source_pins=plan['source_pins'], verification_location='ORIGINAL_C2_OWNER_PROC_AND_FILESYSTEM')


class OwnerBridge:
    def __init__(self, command, dependency, source_pins):
        require(command and all(type(item) is str and item for item in command), 'explicit_Main_owner_command')
        self.command, self.dependency, self.source_pins = list(command), dependency, source_pins
        self.budget = None

    def check(self, binding, epoch):
        started = time.time()
        request = dict(schema='C2_OWNER_CHECK_REQUEST_V1', nonce=secrets.token_hex(24), dependency=self.dependency,
            life_binding_sha256=digest(binding), source_epoch=epoch, source_pins=self.source_pins)
        timeout = 2 if self.budget is None else self.budget.timeout(2)
        result = subprocess.run(self.command, input=encoded(request), capture_output=True, check=True,
            timeout=timeout, close_fds=True)
        if self.budget is not None:
            self.budget.check()
        require(len(result.stdout) <= 32 * 1024**2, 'bounded_owner_response')
        response = json.loads(result.stdout)
        require(response['schema'] == 'C2_OWNER_CHECK_RESPONSE_V1' and response['nonce'] == request['nonce']
            and response['dependency'] == self.dependency and response['source_pins'] == self.source_pins
            and response['verification_location'] == 'ORIGINAL_C2_OWNER_PROC_AND_FILESYSTEM', 'original_owner_bound_nonce')
        raw = base64.b64decode(response['dependency_base64'], validate=True)
        require(hashlib.sha256(raw).hexdigest() == self.dependency['sha256'], 'original_dependency_not_mirror')
        checked = response['recheck']
        require(checked['schema'] == 'C2_OWNER_FENCE_RECHECK_V1' and checked['dependency'] == self.dependency
            and checked['life_binding_sha256'] == digest(binding) and checked['source_epoch'] == epoch
            and checked['delivery_fenced'] is True and type(checked['inflight_deliveries']) is int
            and checked['inflight_deliveries'] == 0
            and checked['ledger_pins_verified'] is True and checked['native_signals'] == 0
            and started - 2 <= checked['observed_unix'] <= time.time() + 2, 'fresh_actual_C2_fence')
        return checked
