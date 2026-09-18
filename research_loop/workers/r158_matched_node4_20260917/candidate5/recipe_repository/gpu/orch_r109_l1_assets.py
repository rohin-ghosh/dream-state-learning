"""Hash-bound native asset packaging; stdout contains manifests, never payloads."""

import argparse
import hashlib
import json
from pathlib import Path
import tarfile


CHILD = '121655d491bc55ba6bbd8eb732bc4f7a65215a07d3b6b2492f4fa623026f80f1'
BASE = 'a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992'
ROOT = Path('/localhome/local-rohing/orch_r109_l1_20260915')


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def package():
    original=Path('/localhome/local-rohing/orch_combined_l1_continual_20260915_attempt1')
    checkpoint=original/'FULL/checkpoints/000008932'
    commit=json.loads((checkpoint/'COMMIT.json').read_text())
    assert commit['metadata']['update']==8932
    assert commit['metadata']['adapter']['state_sha256']==CHILD
    assert commit['metadata']['adapter']['base_sha256']==BASE
    assert all(sha(checkpoint/name)==digest for name,digest in commit['files'].items())
    assert sha(original/'CORPORA/000013.json')==commit['metadata']['corpus_sha256']
    candidates=[path for path in original.glob('*.tar') if sha(path)==commit['metadata']['source_sha256']]
    assert len(candidates)>=1,'exact_checkpoint_source_archive_required'
    anchors=Path('/localhome/local-rohing/orch_r107_base_anchors_20260915_attempt1')
    manifest=json.loads((anchors/'ANCHOR_MANIFEST.json').read_text())
    assert manifest['verified_anchors']==42 and manifest['before_after_verified'] is True
    assert sha(anchors/'ANCHOR_ROWS.json')==manifest['anchors_sha256']
    files={f'checkpoint/{name}':checkpoint/name for name in ['COMMIT.json',*commit['files']]}
    files.update({f'prior/{name}':original/name for name in ['CORPORA/000013.json','LEGACY_MATERIAL.json','OLD_MASKS.json','LEGACY_READOUT.json','TERMINAL.json']})
    files['prior/source.tar']=candidates[0]
    for path in anchors.rglob('*'):
        relative=path.relative_to(anchors)
        if path.is_file() and ('source' in relative.parts or relative.parts[0]=='readout' or len(relative.parts)==1):
            if path.suffix in ('.json','.py'):
                files['anchors/'+str(relative)]=path
    document=dict(schema='R109_NATIVE_ASSETS_V1',child_state_sha256=CHILD,base_sha256=BASE,
        original_checkpoint=str(checkpoint),original_commit_sha256=sha(checkpoint/'COMMIT.json'),
        exact_source_archive_sha256=sha(candidates[0]),files={name:sha(path) for name,path in files.items()})
    ROOT.mkdir(exist_ok=True)
    with tarfile.open(ROOT/'assets.tar','x') as archive:
        for name,path in sorted(files.items()):
            archive.add(path,arcname=name,recursive=False)
    document['archive_sha256']=sha(ROOT/'assets.tar')
    (ROOT/'ASSETS_MANIFEST.json').write_text(json.dumps(document,indent=2))
    print(json.dumps(document))


def receive():
    manifest=json.loads((ROOT/'ASSETS_MANIFEST.json').read_text())
    assert sha(ROOT/'assets.tar')==manifest['archive_sha256']
    destination=ROOT/'input'
    destination.mkdir(exist_ok=False)
    with tarfile.open(ROOT/'assets.tar') as archive:
        members=archive.getmembers()
        assert {member.name for member in members}==set(manifest['files'])
        assert all(member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts for member in members)
        archive.extractall(destination,filter='data')
    assert all(sha(destination/name)==digest for name,digest in manifest['files'].items())
    print(json.dumps(dict(status='VERIFIED',archive_sha256=manifest['archive_sha256'],
                         files=len(manifest['files']),child_state_sha256=manifest['child_state_sha256'])))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['package','receive'])
    options=parser.parse_args()
    package() if options.action=='package' else receive()
