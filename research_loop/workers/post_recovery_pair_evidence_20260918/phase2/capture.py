"""Read only the two pinned native source closures and bounded compaction records."""

import hashlib
import json
from pathlib import Path
import subprocess


OWN = Path(__file__).resolve().parent
REPOSITORY = OWN.parents[3]
FILES = (
    'gpu/orch_r184_think_act_learn.py',
    'organism_v6/orch_r125_continual_stream.py',
    'organism_v6/orch_r124_train_history.py',
    'organism_v6/orch_r125_plain_context.py',
)


def main():
    reader = (OWN.parent / 'reader.py').read_text().split("if __name__ == '__main__':")[0]
    source = reader + '\n' + '''
result = {}
for label, target in TARGETS.items():
    native = process(target)
    source = Path(native['cwd'])
    files = {}
    for relative in FILES:
        raw, unused = stable_read(source / relative)
        files[relative] = dict(sha256=hashlib.sha256(raw).hexdigest(), text=raw.decode())
    guard = json.loads(stable_read(Path(native['guard_path']))[0])
    records = []
    if label == 'frozen':
        for index in range(2746, 2767):
            record, unused, unused_time = verified(Path(target['root']) / 'stream/records' / f'{index:020d}.json', target['journal_id'])
            if record['kind'] not in ('REQUEST', 'RESPONSE', 'COMMITTED'):
                records.append(record)
    result[label] = dict(native=native, files=files, guard=guard, records=records)
print(json.dumps(result))
'''
    source = 'FILES = ' + repr(FILES) + '\n' + source
    command = ['bash', str(REPOSITORY / 'gpu/ovx4_ssh.sh'),
        "CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B -"]
    received = subprocess.run(command, input=source, text=True, capture_output=True, timeout=60, check=True)
    data = json.loads(received.stdout)
    destination = OWN / 'private'
    destination.mkdir(exist_ok=True)
    (destination / 'capture.json').write_text(json.dumps(data, indent=2))
    for label, capture in data.items():
        for relative, content in capture['files'].items():
            path = destination / label / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content['text'])
        print(label, json.dumps({key: value['sha256'] for key, value in capture['files'].items()}))


if __name__ == '__main__':
    main()
