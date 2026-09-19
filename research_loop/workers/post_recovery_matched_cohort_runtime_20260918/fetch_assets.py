"""Fetch only the original birth, initial checkpoint and guarded Python closure."""

import hashlib
import json
from pathlib import Path
import subprocess
import tarfile


OWN = Path(__file__).resolve().parent
REPOSITORY = OWN.parents[2]


def main():
    observed = OWN.parent / 'post_recovery_parent_retention_adoption_20260918/SOURCE_STRUCTURE_OBSERVATION.json'
    observation = json.loads(observed.read_bytes())
    content = 'EXPECTED = ' + repr(observation['targets']['learner']) + '\n'
    content += 'OBSERVATION_SHA256 = ' + repr(hashlib.sha256(observed.read_bytes()).hexdigest()) + '\n'
    content += (OWN / 'export_assets.py').read_text()
    archive = OWN / 'ASSETS.tar'
    with archive.open('xb') as output:
        subprocess.run(['bash', str(REPOSITORY / 'gpu/ovx4_ssh.sh'),
            "CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B -"],
            input=content.encode(), stdout=output, check=True, timeout=150)
    destination = OWN / 'receiving'
    destination.mkdir()
    with tarfile.open(archive) as bundle:
        names = set()
        for member in bundle:
            path = Path(member.name)
            if not member.isfile() or path.is_absolute() or '..' in path.parts or member.name in names:
                raise ValueError('unique_relative_regular_assets_only')
            names.add(member.name)
            target = destination / path
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as output:
                output.write(bundle.extractfile(member).read())
    manifest = json.loads((destination / 'ASSET_MANIFEST.json').read_bytes())
    for relative, binding in manifest['files'].items():
        if hashlib.sha256((destination / relative).read_bytes()).hexdigest() != binding['sha256']:
            raise ValueError('exact_received_asset:' + relative)
    print(json.dumps(dict(status='EXACT_INITIAL_ASSETS_COPIED_CPU_ONLY',
        files=len(manifest['files']), bytes=archive.stat().st_size,
        context_limit=manifest['original_context_limit'], optimizer_steps=manifest['initial_checkpoint']['optimizer_steps'])))


if __name__ == '__main__':
    main()
