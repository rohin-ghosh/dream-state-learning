"""Old CODE forks: reuse tested kernel exit and stable-executable admission proofs."""

import argparse
import ast
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import resource
from types import SimpleNamespace

from gpu import orch_r119_code_old_fork as fork
from gpu import orch_admission_transient_exit as transient
from gpu import orch_math_feedback_uptake_r118_argv_admission as argv_admission


def bind_proof():
    path = Path(__file__).with_name('orch_math_feedback_uptake_r118_preinfer.py')
    tree = ast.parse(path.read_text())
    definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'bind_scan']
    fork.require(len(definitions) == 1, 'exact_existing_math_kernel_proof')
    namespace = dict(os=os, resource=resource, transient=transient, require=fork.require,
        deepcopy=deepcopy, hashlib=hashlib, json=json)
    exec(compile(ast.Module(body=definitions, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace['bind_scan']


def scan(root):
    from gpu import orch_rich_hot_a100_minor_scan as scanner
    plan = fork.plan_for(root)
    fork.require(os.geteuid() == 0 and scanner.pinned.host_identity() == plan['host_sha256'],
        'privileged_hashed_destination')
    def allocation(index):
        fork.require(index == plan['physical'], 'exact_owned_physical')
        return plan['gpu_uuid']
    scanner.pinned.policy = SimpleNamespace(DEVICES={plan['physical']: plan['gpu_uuid']},
        HOST_SHA=plan['host_sha256'], allocation=allocation, require=fork.require)
    return bind_proof()(lambda: argv_admission.scan(plan['physical'], Path(root)/'SERVICE_IDENTITY.json'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=('guard', 'native', 'scan', 'service'))
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    fork.MODULE = 'gpu.orch_r119_code_old_admission'
    if args.phase == 'scan':
        print(json.dumps(scan(args.root)))
    elif args.phase == 'service':
        print(json.dumps(fork.bound_scan(args.root, service=True)))
    else:
        getattr(fork, args.phase)(args.root)
