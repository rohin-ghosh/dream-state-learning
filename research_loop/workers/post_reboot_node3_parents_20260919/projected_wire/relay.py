"""Bounded authenticated SSH collect/install, then one existing-scorer dispatch."""

import shlex
import subprocess
import tempfile

from .contract import MAX_TRANSFER_BYTES, bounded, canonical, decode, digest, require, validate_receipt
from .receiver import envelope


MODULE = 'research_loop.workers.post_reboot_node3_parents_20260919.projected_wire.cli'


def exchange(wrapper, source, operation, binding_path, binding_sha256, payload, *, store=None):
    require(wrapper in ('gpu/ovx2_ssh.sh', 'gpu/ovx4_ssh.sh'), 'original_operator_SSH_wrappers_only')
    command = ['env', 'PYTHONPATH=' + source, '/usr/bin/python3', '-B', '-m', MODULE, operation,
        '--binding', binding_path, '--binding-sha256', binding_sha256]
    if store is not None:
        command += ['--store', store]
    with tempfile.TemporaryFile() as captured:
        subprocess.run(['bash', wrapper, shlex.join(command)], input=bounded(payload),
            stdout=captured, stderr=subprocess.PIPE, timeout=30, check=True)
        captured.seek(0)
        return bounded(captured.read(MAX_TRANSFER_BYTES + 1))


def prepare(binding, request, node, scorer):
    receipt_raw = exchange('gpu/ovx2_ssh.sh', node['source'], 'collect', node['binding_path'],
        node['binding_sha256'], canonical(request))
    receipt = validate_receipt(decode(receipt_raw), binding)
    require(receipt['request'] == request, 'same_authenticated_SSH_response')
    installed = decode(exchange('gpu/ovx4_ssh.sh', scorer['source'], 'install', scorer['binding_path'],
        scorer['binding_sha256'], receipt_raw, store=scorer['store']))
    require(set(installed) == {'attestation_sha256', 'binding_sha256'} and installed['binding_sha256'] == digest(binding)
        and installed['attestation_sha256'] == digest(receipt), 'exact_operator_installed_receipt')
    return envelope(binding, request, installed['attestation_sha256'])
