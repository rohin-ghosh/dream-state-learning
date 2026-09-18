import hashlib
import json
from pathlib import Path
import time


def checksum(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


base = Path(__file__).resolve().parent
inputs = base / 'candidate5_inputs'
evidence = base / 'candidate5_initializer_attempt1'
remote = Path('/localhome/local-rohing/orch_r158_matched_node4_20260917_attempt5')
pins = {
    'common_initial/INITIALIZED.json': 'dc3d091ab32aedb1c327f027db33b28f6959fa60a96964ffb0496084c5fc6071',
    'common_initial/COMMIT.json': '2bff223d4c2730c93976f9f99c7546705e661359dc21f31708bf4f86305ef978',
    'common_initial/capacity_validation/RESULT.json': '014e882ad551608b68603f0f03460ca899da2ea753cac77e2571c83fecbe4708',
    'attempts/initialize-parented_learning-attempt1/LIFECYCLE.json': 'b50b3ee539792d1924b862f1f906164f6106f05cc42b7d0c37789b7f38afbc4e',
}
for name, digest in pins.items():
    assert checksum(evidence / name) == digest
initialized = json.loads((evidence / 'common_initial/INITIALIZED.json').read_bytes())
capacity = json.loads((evidence / 'common_initial/capacity_validation/RESULT.json').read_bytes())
lifecycle = json.loads((evidence / 'attempts/initialize-parented_learning-attempt1/LIFECYCLE.json').read_bytes())
assert initialized['cohort_sha256'] == checksum(inputs / 'COHORT.json')
assert initialized['checkpoint_commit_sha256'] == pins['common_initial/COMMIT.json']
assert initialized['observed_initial_state'] == initialized['recovered_initial_state_before_validation']
assert initialized['observed_initial_state']['optimizer_steps'] == 0
assert capacity['status'] == 'PASS' and capacity['restoration_status'] == 'VERIFIED'
assert capacity['state_restored'] is True and capacity['generation_calls'] == capacity['optimizer_updates'] == 0
assert capacity['maximum_shape']['full_input_tokens'] == 16384
assert capacity['maximum_shape']['target_tokens'] == 512
assert capacity['maximum_shape']['free_after_bytes'] >= capacity['minimum_headroom_bytes']
assert lifecycle['status'] == 'SERVICE_EXIT_VERIFIED'
assert lifecycle['cgroup_empty_verified'] is True and lifecycle['service_returncode'] == 0
assert checksum(inputs / 'PREPARED_EXECUTION.json') == '7878fbd8510461cc00678a161b888071baea17835816c7b506557278c88d6f25'
prepared = json.loads((inputs / 'PREPARED_EXECUTION.json').read_bytes())
proof = {name: dict(path=str(remote / relative), sha256=pins[relative]) for name, relative in {
    'initialized': 'common_initial/INITIALIZED.json', 'commit': 'common_initial/COMMIT.json',
    'lifecycle': 'attempts/initialize-parented_learning-attempt1/LIFECYCLE.json'}.items()}
current = time.time()
assert current + 1800 < 1789646400
receipts = []
for configuration in prepared['configurations'][1:]:
    arm = configuration['arm']
    assert configuration['phase'] == 'run'
    binding = configuration['required_GO_binding']
    assert checksum(inputs / ('control/run-' + arm + '/GUARD.json')) == binding['config_sha256']
    assert checksum(inputs / (arm + '.PLAN.json')) == binding['plan_sha256']
    assert binding['matched_cohort_sha256'] == initialized['cohort_sha256']
    document = dict(schema='R158_MAIN_GO_V1', decision='GO', issuer='Main', binding=binding,
        not_before_unix=current - 1, expires_unix=current + 1800, initialization=proof)
    path = base / ('candidate5_main_release/RUN_' + arm + '_MAIN_GO.json')
    with path.open('x') as stream:
        json.dump(document, stream, indent=2, sort_keys=True)
        stream.write('\n')
    receipts.append(dict(arm=arm, path=str(path), sha256=checksum(path), configuration=configuration))
print(json.dumps(dict(issued_unix=current, run_gos=receipts), sort_keys=True))
