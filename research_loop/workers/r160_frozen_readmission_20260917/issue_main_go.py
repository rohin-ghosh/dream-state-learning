import hashlib
import json
from pathlib import Path
import time


def checksum(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


base = Path(__file__).resolve().parent
prepared_path = base / 'PREPARED_READMISSION.json'
assert checksum(prepared_path) == '4a916df78c8a4dd09749b6746fd73f0b5b3887111eaaef8832f117a577d897b8'
prepared = json.loads(prepared_path.read_bytes())
binding = prepared['required_GO_binding']
assert prepared['status'] == 'CPU_PREPARED_NO_GO_NO_GPU'
assert checksum(base / 'GUARD.json') == binding['config_sha256']
assert checksum(base / 'PROVENANCE.json') == prepared['provenance']['sha256']
assert checksum(base / 'ALLOCATION.json') == binding['allocation_sha256']
assert binding['phase'] == 'run' and binding['physical'] == 6
assert binding['matched_arm'] == 'parented_frozen' and binding['resume'] is False
assert binding['matched_cohort_sha256'] == 'da04b4cd814f6f695ca49a1ace66f9378039f6166d04e26bbd27ed7692ad0b4b'
assert binding['hard_end_unix'] == 1789646400
current = time.time()
assert current + 1800 < binding['hard_end_unix']
document = dict(schema='R158_MAIN_GO_V1', decision='GO', issuer='Main', binding=binding,
    initialization=prepared['initialization'],
    readmission=dict(path=prepared['required_GO_readmission_path'], sha256=checksum(prepared_path)),
    not_before_unix=current - 1, expires_unix=current + 1800)
path = base / 'MAIN_GO.json'
with path.open('x') as stream:
    json.dump(document, stream, indent=2, sort_keys=True)
    stream.write('\n')
print(json.dumps(dict(path=str(path), sha256=checksum(path), issued_unix=current)))
