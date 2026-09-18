"""Filter the preserved snapshot by the current metadata policy without recapture."""

from collections import Counter
import json
from pathlib import Path
import tarfile

from research_loop.workers.rohin183_repo_learning_20260917 import safe_snapshot as safe


def release(snapshot, output, archive):
    snapshot, output, archive = map(Path, (snapshot, output, archive))
    raw = (snapshot/'MANIFEST.json').read_bytes()
    original = json.loads(raw)
    files = {name: value for name,value in original['files'].items() if safe.permitted_path(name)}
    safe.require(files and not output.exists() and not archive.exists(), 'new_filtered_release_only')
    counts = Counter(name.split('/')[0] if '/' in name else 'root' for name in files)
    manifest = dict(original, files=files, coverage=dict(counts), snapshot_bytes=sum(item['bytes'] for item in files.values()),
        preserved_manifest=dict(path=str(snapshot/'MANIFEST.json'), sha256=safe.digest(raw)),
        metadata_refiltered_exclusions=len(original['files'])-len(files),
        metadata_excluded_contents_opened=False,
        content_pattern_exclusions=original['excluded_counts'].get('credential_pattern_no_disclosure',0),
        policy_source_sha256=safe.digest(Path(safe.__file__).read_bytes()))
    manifest.pop('excluded_contents_opened',None)
    reference = safe.write(output,manifest)
    with tarfile.open(archive, 'x:gz') as packed:
        for name, item in files.items():
            path = snapshot/name
            safe.require(not path.is_symlink() and path.stat().st_size == item['bytes'], 'preserved_snapshot_regular_size')
            safe.require(safe.digest(path.read_bytes()) == item['sha256'], 'preserved_snapshot_hash')
            packed.add(path,arcname='snapshot/'+name,recursive=False)
        packed.add(output,arcname='SNAPSHOT_MANIFEST.json',recursive=False)
    return dict(manifest=reference,archive=str(archive),files=len(files),coverage=dict(counts),snapshot_bytes=manifest['snapshot_bytes'])


if __name__ == '__main__':
    root=Path(__file__).resolve().parent
    print(json.dumps(release(root/'SNAPSHOT',root/'SNAPSHOT_MANIFEST.json',root/'SNAPSHOT_RELEASE.tar.gz'),sort_keys=True))
