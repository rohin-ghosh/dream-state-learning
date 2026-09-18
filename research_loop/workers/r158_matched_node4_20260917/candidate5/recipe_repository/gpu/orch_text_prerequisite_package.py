"""Snapshot read-only portable sources plus owned files on the data volume."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile


def main():
    root = Path(__file__).resolve().parents[1]
    output = Path('/data/home/rohing/dream-state-orch/gpu_artifacts_local/orch_text_prerequisite_20260914_attempt1')
    source = output / 'source'
    source.mkdir(exist_ok=False)
    paths = set(subprocess.check_output(['git', 'ls-files', 'gpu', 'organism_v6'], cwd=root, text=True).splitlines())
    paths.update(str(path.relative_to(root)) for directory, pattern in
        [('gpu', 'orch_text_prerequisite*'), ('organism_v6', 'orch_text_prerequisite*'),
         ('tests', 'test_orch_text_prerequisite*')]
        for path in (root / directory).glob(pattern) if path.is_file())
    manifest = {}
    for name in sorted(paths):
        path = root / name
        if path.is_symlink() or not path.is_file() or name.endswith('hosts.env'):
            raise ValueError('unsafe_source:' + name)
        destination = source / name
        destination.parent.mkdir(exist_ok=True, parents=True)
        shutil.copyfile(path, destination)
        manifest[name] = hashlib.sha256(destination.read_bytes()).hexdigest()
    (source / 'SOURCE_MANIFEST.json').write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n')
    archive = output / 'source.tar.gz'
    with tarfile.open(archive, 'w:gz') as packed:
        for path in sorted(source.rglob('*')):
            if path.is_file():
                packed.add(path, arcname=str(path.relative_to(source)))
    receipt = dict(source_files=len(manifest), source_archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        source_manifest_sha256=hashlib.sha256((source / 'SOURCE_MANIFEST.json').read_bytes()).hexdigest(),
        source_base_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip())
    target = root / 'research_notes/analysis/orch_text_prerequisite_20260914_attempt1/SOURCE_RECEIPT.json'
    target.write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
