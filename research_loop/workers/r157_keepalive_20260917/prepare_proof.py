"""Bind completed CPU tests and explicit runtime authority to the staged operator."""

import hashlib
import json
from pathlib import Path
import time


directory = Path(__file__).resolve().parent
repository = directory.parents[2]
log = directory / 'CPU_TESTS.log'
assert '123 passed, 197 subtests passed' in log.read_text()
operator = repository / 'gpu/orch_r157_node5_keepalive.py'
proof = dict(schema='R157_PROTECTED_KEEPALIVE_CPU_V1', passed=True, tests=123, subtests=197,
    operator_sha256=hashlib.sha256(operator.read_bytes()).hexdigest(),
    tests_sha256=hashlib.sha256(log.read_bytes()).hexdigest(),
    authority_sha256=hashlib.sha256((directory / 'AUTHORIZATION.json').read_bytes()).hexdigest(),
    recorded_unix=time.time(), boundary_wait_until_unix=1789616100.0,
    source_and_training_changes=False, purchases=False)
with (directory / 'CPU_PROVENANCE.json').open('x') as output:
    json.dump(proof, output, sort_keys=True, indent=2)
    output.write('\n')
