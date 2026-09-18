import argparse
import hashlib
import json
from pathlib import Path
import time


def checksum(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument('--prepared-sha256', required=True)
arguments = parser.parse_args()
base = Path(__file__).resolve().parent
inputs = base / 'candidate5_inputs'
prepared_path = inputs / 'PREPARED_EXECUTION.json'
assert checksum(prepared_path) == arguments.prepared_sha256
prepared = json.loads(prepared_path.read_bytes())
assert prepared['status'] == 'PREPARED_FROZEN_NO_GPU_NO_MAIN_GO'
configuration = prepared['configurations'][0]
assert configuration['phase'] == 'initialize' and configuration['physical'] == 5
assert configuration['arm'] == 'parented_learning'
assert configuration['receipt_dir'] == '/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5/attempts/initialize-parented_learning-attempt1'
binding = configuration['required_GO_binding']
for filename, field in [('COHORT.json', 'matched_cohort_sha256'),
                        ('LEASE_BUDGET.json', 'lease_sha256'),
                        ('parented_learning.PLAN.json', 'plan_sha256'),
                        ('control/initialize-parented_learning/GUARD.json', 'config_sha256'),
                        ('control/CPU_GATE.json', 'cpu_gate_sha256')]:
    assert checksum(inputs / filename) == binding[field]
assert binding['source_manifest_sha256'] == prepared['source_manifest']['sha256']
assert binding['allowed_physical'] == [5, 6, 7] and binding['resume'] is False
assert binding['requested_scope'] == 'R158_NODE4_MATCHED_INITIALIZE_RUN_5_6_7'
assert binding['hard_end_unix'] == 1789646400
current = time.time()
assert current + 1800 < binding['hard_end_unix']
document = dict(schema='R158_MAIN_GO_V1', decision='GO', issuer='Main', binding=binding,
    not_before_unix=current - 1, expires_unix=current + 1800, initialization=None)
path = base / 'candidate5_main_release/INITIALIZER_MAIN_GO.json'
with path.open('x') as stream:
    json.dump(document, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps(dict(path=str(path), sha256=checksum(path), issued_unix=current,
    config=configuration['config'], receipt_dir=configuration['receipt_dir']), sort_keys=True))
