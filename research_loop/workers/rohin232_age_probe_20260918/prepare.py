"""Stage an explicit inference source closure and selected development assets."""

import io
import json
from pathlib import Path
import subprocess
import tarfile
import hashlib

from research_loop.workers.rohin232_age_probe_20260918.contract import select_fresh


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
REMOTE = '/localhome/local-rohing/orch_r232_age_probe_20260918'
DATA = REPO/'research_loop/workers/r177_caption_game_stage1_20260917/data_judge'


def send(alias, command, raw=None, timeout=120):
    return subprocess.run(['bash', 'gpu/'+alias+'_ssh.sh', command], input=raw,
        capture_output=True, check=True, timeout=timeout).stdout


def main():
    packet = json.loads((DATA/'IMAGE_TASKS_agent_development.private.json').read_bytes())
    manifest_path = DATA/'private/preparation3/DATA_MANIFEST.private.json'
    manifest = json.loads(manifest_path.read_bytes())
    capture_raw = send('ovx3', 'cat '+REMOTE+'/capture1/CAPTURE.json')
    capture = json.loads(capture_raw)
    evidence = dict(capture['exposure'])
    excluded = set(evidence['excluded_contest_ids']) | {str(row['contest_id']) for row in packet['tasks'][:3]}
    for group in manifest['scene_groups']:
        if set(group) & excluded:
            excluded.update(group)
    evidence['excluded_contest_ids'] = sorted(excluded)
    selected = select_fresh(packet, evidence)
    identifiers = {str(row['contest_id']) for row in selected}
    assert identifiers <= set(manifest['pools']['agent_development'])
    assert not any(set(group) & identifiers and set(group) & excluded for group in manifest['scene_groups'])
    payload = {}
    images, mapping = [], []
    for row in selected:
        identifier = str(row['contest_id'])
        image = row['image']
        image_path = Path(image['path'])
        raw = image_path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == image['sha256'] and len(raw) == image['bytes']
        handle = 'agentdev_' + hashlib.sha256(identifier.encode()).hexdigest()[:20]
        relative = 'images/' + handle + image_path.suffix
        payload[relative] = raw
        images.append(dict(handle=handle, path=REMOTE+'/'+relative, sha256=image['sha256'], bytes=len(raw)))
        mapping.append(dict(contest_id=identifier, image=handle, split='agent_development'))
        reference = manifest['contests'][identifier]['rows']
        rows_raw = Path(reference['path']).read_bytes()
        assert hashlib.sha256(rows_raw).hexdigest() == reference['sha256']
        row_name = 'private/rows/'+identifier+'.jsonl'
        payload[row_name] = rows_raw
        reference['path'] = REMOTE+'/'+row_name
    payload['images/IMAGE_PACKET.json'] = json.dumps(dict(schema='R177_VISION_IMAGES_V1', mode='DEVELOPMENT', images=images)).encode()
    payload['images/GAME_IMAGE_MAP.json'] = json.dumps(dict(schema='R177_GAME_IMAGE_RELEASE_MAP_V1', mode='DEVELOPMENT', contests=mapping)).encode()
    payload['private/DATA_MANIFEST.private.json'] = json.dumps(manifest).encode()
    payload['SELECTION.json'] = json.dumps(dict(selected=sorted(identifiers), excluded=sorted(excluded),
        source_manifest_sha256=hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        both_source_exposure=capture['exposure'], selection='packet_order_after_lifetime_exposure_and_existing_game_exclusions',
        scene_groups_disjoint=True, private_reference_rows_only_selected_development=True)).encode()
    sources = [ROOT/name for name in ['contract.py', 'runtime.py', 'exposure.py', 'test_contract.py']]
    sources.extend(REPO/name for name in ['gpu/ny_caption_vision.py',
        'research_loop/workers/rohin209_first_game_20260918/generate_c2.py',
        'research_loop/workers/rohin221_continuous_caption_20260918/freeform.py'])
    for path in sources:
        payload['source/'+str(path.relative_to(REPO))] = path.read_bytes()
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w:gz') as archive:
        for name, raw in payload.items():
            member = tarfile.TarInfo(name)
            member.size, member.mode = len(raw), 0o600
            archive.addfile(member, io.BytesIO(raw))
    raw = buffer.getvalue()
    send('ovx4', 'umask 077; cat > '+REMOTE+'/stage.tar.gz', raw)
    code = '''import hashlib,json,pathlib,shutil,tarfile
root=pathlib.Path(ROOT)
assert hashlib.sha256((root/'stage.tar.gz').read_bytes()).hexdigest()==SHA
old=pathlib.Path('/localhome/local-rohing/orch_r226_shared_caption_20260918/attempt2')
shutil.copytree(old/'source',root/'source')
(root/'assets').mkdir(mode=0o700)
for name in ['adapter','embedding','base_manifest.json','RULE.json','embedding_snapshot.json','pixel_config.json','relevance.json']:
 source=old/'assets'/name
 if source.is_dir(): shutil.copytree(source,root/'assets'/name)
 else: shutil.copyfile(source,root/'assets'/name)
with tarfile.open(root/'stage.tar.gz') as archive:
 assert all(member.isfile() and not member.name.startswith('/') and '..' not in pathlib.Path(member.name).parts for member in archive.getmembers())
 archive.extractall(root,filter='data')
(root/'queue').mkdir(mode=0o700)
files={str(path.relative_to(root/'source')):hashlib.sha256(path.read_bytes()).hexdigest() for path in (root/'source').rglob('*.py')}
(root/'SOURCE_MANIFEST.json').write_text(json.dumps(files,sort_keys=True))
print(json.dumps(dict(received=True,source_files=len(files),private_rows=3,source_manifest_sha256=hashlib.sha256((root/'SOURCE_MANIFEST.json').read_bytes()).hexdigest())))
'''.replace('ROOT', repr(REMOTE)).replace('SHA', repr(hashlib.sha256(raw).hexdigest()))
    result = send('ovx4', 'python3 -B -', code.encode())
    print(result.decode().strip())
    print(json.dumps(dict(selected=sorted(identifiers), ages=[item['absolute_sleep'] for item in capture['sources']],
        stage_archive_sha256=hashlib.sha256(raw).hexdigest())))


if __name__ == '__main__':
    main()
