"""Fetch each bounded cut through the existing approved transport, CPU only."""

from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


OWN = Path(__file__).resolve().parent
REPOSITORY = OWN.parents[2]


def capture(label, reproduce=False):
    command = "CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B - " + label
    destination = OWN / 'private'
    if reproduce:
        original = json.loads((destination / (label + '.json')).read_bytes())
        command += ' --cut-index ' + str(original['initial_head']['index']) + ' --cut-sha256 ' + original['initial_head']['sha256']
        destination = destination / 'reproduced'
        destination.mkdir(exist_ok=True)
    source = (OWN / 'reader.py').read_text()
    result = subprocess.run(['bash', str(REPOSITORY / 'gpu/ovx4_ssh.sh'), command],
        input=source, text=True, capture_output=True, timeout=180)
    if result.returncode:
        raise RuntimeError(result.stderr[-1500:])
    cut = json.loads(result.stdout)
    cut['reader_source_sha256'] = hashlib.sha256(source.encode()).hexdigest()
    if reproduce:
        if cut['records'] != original['records']:
            raise ValueError('reproduced_immutable_window_changed')
        cut['original_cut_file_sha256'] = hashlib.sha256((OWN / 'private' / (label + '.json')).read_bytes()).hexdigest()
        cut['exact_window_reproduced'] = True
    path = destination / (label + '.json')
    with path.open('x') as stream:
        json.dump(cut, stream, sort_keys=True, ensure_ascii=False)
    return dict(label=label, observed_utc=cut['observed_utc'], head=cut['initial_head'],
        complete_indices=cut['complete_indices'], records=len(cut['records']), bytes_read=cut['bytes_read'])


if __name__ == '__main__':
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', choices=('learner', 'frozen'), action='append')
    parser.add_argument('--reproduce', action='store_true')
    options = parser.parse_args()
    with ThreadPoolExecutor(max_workers=2) as executor:
        print(json.dumps(list(executor.map(lambda label: capture(label, options.reproduce), options.label or ('learner', 'frozen'))), indent=2))
