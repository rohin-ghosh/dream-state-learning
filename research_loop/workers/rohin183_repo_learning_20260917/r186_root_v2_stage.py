"""Stage declared root-repair payloads once, CPU only; never dispatch a GPU."""

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess

from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import write, digest, require


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
REMOTE = '/localhome/local-rohing/orch_r153_r186_c2_plasticity_20260917'


def stage(item):
    label, metadata = item
    payload = Path(metadata['archive']).read_bytes()
    require(digest(payload) == metadata['archive_sha256'], 'unchanged_declared_payload')
    remote = REMOTE + '/' + label + '2'
    command = 'set -eu; mkdir -p ' + REMOTE + '; mkdir ' + remote + '; cd ' + remote + '; ' + (
        'cat > PAYLOAD.tar.gz; printf "%s  PAYLOAD.tar.gz\\n" ' + metadata['archive_sha256'] +
        ' | sha256sum -c -; tar -xzf PAYLOAD.tar.gz; CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 ' +
        '/localhome/local-rohing/v2/venv/bin/python -B receive.py prepare ' + label)
    with (ROOT / ('R186_ROOT_V2_' + label.upper() + '_RECEIVING.log')).open('x') as output:
        result = subprocess.run(['bash', 'gpu/ovx_ssh.sh', command], cwd=REPO,
            input=payload, stdout=output, stderr=subprocess.STDOUT, timeout=120)
    return dict(label=label, returncode=result.returncode, GPU_dispatch=False)


if __name__ == '__main__':
    manifest = json.loads((ROOT / 'R186_ROOT_V2_BUILD.json').read_bytes())
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(stage, manifest.items()))
    print(json.dumps(write(ROOT / 'R186_ROOT_V2_STAGING.json', results), sort_keys=True))
