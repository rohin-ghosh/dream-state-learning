"""Release three already-selected development images without evaluator data."""

import argparse
import hashlib
import io
import json
from pathlib import Path
import shlex
import subprocess
import tarfile
import time

from gpu.ny_caption_development import require, save_once
from gpu.ny_caption_similarity import bound, canonical, file_pin


def project(document, remote_root):
    require(document['schema'] == 'NY_LOCAL_QWEN_IMAGE_TASKS_V1' and
            document['pool'] == 'agent_development' and document['local_Qwen_only'] is True and
            all(document[key] is False for key in ('FINAL_included', 'historical_captions_included', 'ratings_included')),
            'released_agent_development_images_only')
    require(type(document['tasks']) is list and len(document['tasks']) == 19, 'original_nineteen_image_release')
    remote_root = Path(remote_root)
    require(remote_root.is_absolute() and '..' not in remote_root.parts, 'absolute_receiving_image_root')
    selected = document['tasks'][:3]
    require(len({row['contest_id'] for row in selected}) == 3, 'three_distinct_contests')
    images, mappings, payload = [], [], {}
    for row in selected:
        require(set(row) == {'contest_id', 'image', 'policy'}, 'no_extra_task_content')
        image = row['image']
        require(set(image) == {'path', 'sha256', 'bytes', 'source_url'}, 'image_reference_only')
        source = Path(image['path'])
        require(source.is_absolute() and source.is_file() and not source.is_symlink() and
                0 < image['bytes'] <= 16 * 1024 * 1024 and source.stat().st_size == image['bytes'],
                'bounded_regular_source_image')
        raw = source.read_bytes()
        require(len(raw) == image['bytes'] and hashlib.sha256(raw).hexdigest() == image['sha256'],
                'exact_released_image_bytes')
        suffix = '.png' if raw.startswith(b'\x89PNG\r\n\x1a\n') else '.jpg' if raw.startswith(b'\xff\xd8\xff') else None
        require(suffix is not None, 'only_released_PNG_or_JPEG')
        handle = 'agentdev_' + hashlib.sha256(str(row['contest_id']).encode()).hexdigest()[:20]
        name = handle + suffix
        require(name not in payload, 'unique_image_handle')
        payload[name] = raw
        images.append(dict(handle=handle, path=str(remote_root/name), sha256=image['sha256'], bytes=len(raw)))
        mappings.append(dict(contest_id=str(row['contest_id']), image=handle, split='agent_development'))
    packet = dict(schema='R177_VISION_IMAGES_V1', mode='DEVELOPMENT', images=images)
    mapping = dict(schema='R177_GAME_IMAGE_RELEASE_MAP_V1', mode='DEVELOPMENT', contests=mappings,
        selection_rule='FIRST_THREE_IN_PREEXISTING_FROZEN_AGENT_DEVELOPMENT_PACKET_ORDER',
        source_manifest_sha256=document['source_manifest_sha256'], canonical_scenes_available=False,
        historical_captions_included=False, ratings_included=False, FINAL_included=False)
    payload['IMAGE_PACKET.json'] = canonical(packet)
    payload['GAME_IMAGE_MAP.json'] = canonical(mapping)
    return packet, mapping, payload


def release(reference, output, remote_root):
    output = Path(output).resolve()
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    packet, mapping, payload = project(bound(reference), remote_root)
    save_once(output/'IMAGE_PACKET.json', packet)
    save_once(output/'GAME_IMAGE_MAP.json', mapping)
    archive = output/'IMAGES.tar'
    with tarfile.open(archive, 'x') as stream:
        for name, raw in payload.items():
            info = tarfile.TarInfo(name)
            info.size, info.mode = len(raw), 0o600
            stream.addfile(info, io.BytesIO(raw))
    inventory = {name: dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)) for name, raw in payload.items()}
    save_once(output/'DISPATCH_STARTED.json', dict(source=reference, archive=file_pin(archive),
        remote_root=remote_root, expected_files=inventory, started_unix=time.time(), GPU_calls=0))
    remote = '''import hashlib,json,pathlib,sys,tarfile,time
root=pathlib.Path(ROOT)
inventory=INVENTORY
assert root.is_absolute() and root.resolve()==root
root.mkdir(mode=0o700,parents=True,exist_ok=False)
seen=set()
with tarfile.open(fileobj=sys.stdin.buffer,mode='r|') as archive:
 for entry in archive:
  assert entry.isfile() and entry.name in inventory and entry.name not in seen
  expected=inventory[entry.name]
  assert entry.size==expected['bytes'] and entry.size<=16*1024*1024
  raw=archive.extractfile(entry).read(entry.size+1)
  assert len(raw)==entry.size and hashlib.sha256(raw).hexdigest()==expected['sha256']
  with (root/entry.name).open('xb') as destination: destination.write(raw)
  (root/entry.name).chmod(0o600)
  seen.add(entry.name)
assert seen==set(inventory)
receipt=dict(status='THREE_DEVELOPMENT_IMAGES_RECEIVED_VERIFIED',received_unix=time.time(),files=inventory,GPU_calls=0)
with (root/'RECEIVED.json').open('x') as destination: json.dump(receipt,destination,sort_keys=True)
print(json.dumps(receipt,sort_keys=True))
'''.replace('ROOT', repr(remote_root), 1).replace('INVENTORY', repr(inventory), 1)
    result = subprocess.run(['bash', 'gpu/a40r_ssh.sh', 'python3 -B -c ' + shlex.quote(remote)],
        input=archive.read_bytes(), capture_output=True, timeout=120, check=False)
    require(result.returncode == 0 and len(result.stdout) <= 65536, 'image_receiving_failed_preserved_inspect_before_retry')
    received = json.loads(result.stdout)
    require(received['files'] == inventory, 'remote_verified_inventory_matches')
    receipt = dict(status='ACTUAL_IMAGE_ONLY_RELEASE_COMPLETE', source=reference,
        packet=dict(path=str(Path(remote_root)/'IMAGE_PACKET.json'), sha256=file_pin(output/'IMAGE_PACKET.json')['sha256']),
        mapping=file_pin(output/'GAME_IMAGE_MAP.json'), remote_received=received,
        GPU_calls=0, historical_captions_read=False, FINAL_read=False, source_selection_changed=False)
    save_once(output/'COMPLETED.json', receipt)
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--source-sha256', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--remote-root', required=True)
    arguments = parser.parse_args()
    result = release(dict(path=str(Path(arguments.source).resolve()), sha256=arguments.source_sha256),
                     arguments.output, arguments.remote_root)
    print(json.dumps(dict(status=result['status'], packet=result['packet'], GPU_calls=0), sort_keys=True))
