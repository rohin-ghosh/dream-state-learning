"""Download only the approved public pinned Qwen files, with no model import."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import time
from urllib.request import urlopen


MODEL_ID = 'Qwen/Qwen2.5-VL-7B-Instruct'
REVISION = 'cc594898137f460bfe9f0759e9844b3ce807cfb5'
LIMIT = 20 * 1024 ** 3
FILES = {'chat_template.json', 'config.json', 'generation_config.json', 'merges.txt',
         'model.safetensors.index.json', 'preprocessor_config.json', 'tokenizer.json',
         'tokenizer_config.json', 'vocab.json'} | {
             'model-' + str(index).zfill(5) + '-of-00005.safetensors' for index in range(1, 6)}


def require(condition, code):
    if not condition:
        raise ValueError(code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--metadata-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    raw = arguments.metadata.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == arguments.metadata_sha256, 'exact_official_metadata_pin')
    metadata = json.loads(raw)
    require(metadata['id'] == MODEL_ID and metadata['sha'] == REVISION, 'exact_public_model_revision')
    files = {row['rfilename']: row for row in metadata['siblings'] if row['rfilename'] in FILES}
    require(set(files) == FILES, 'complete_pinned_file_listing')
    total = sum(row['size'] for row in files.values())
    require(0 < total <= LIMIT, 'approved_20_GiB_download_ceiling')
    require(shutil.disk_usage(arguments.output.parent).free >= total + 2 * 1024 ** 3, 'disk_check_before_download')
    arguments.output.mkdir(mode=0o700)
    manifest = dict(model_id=MODEL_ID, revision=REVISION, total_bytes=total, files={},
                    official_metadata_sha256=arguments.metadata_sha256, gpu_model_loaded=False)
    for name in sorted(files, key=lambda item: (item.endswith('.safetensors'), item)):
        entry = files[name]
        checksum = hashlib.sha256()
        blob = hashlib.sha1(('blob ' + str(entry['size']) + '\0').encode())
        partial = arguments.output / (name + '.part')
        size = 0
        url = 'https://[REDACTED_HOST]/' + MODEL_ID + '/resolve/' + REVISION + '/' + name
        with urlopen(url, timeout=90) as response, partial.open('xb') as handle:
            while chunk := response.read(4 * 1024 * 1024):
                size += len(chunk)
                require(size <= entry['size'], 'remote_file_exceeds_pinned_size')
                checksum.update(chunk)
                blob.update(chunk)
                handle.write(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        require(size == entry['size'], 'incomplete_download_no_model_load')
        require(checksum.hexdigest() == entry['lfs']['sha256'] if 'lfs' in entry else
                blob.hexdigest() == entry['blobId'], 'official_LFS_or_git_blob_hash_mismatch')
        partial.chmod(0o444)
        partial.rename(arguments.output / name)
        manifest['files'][name] = dict(sha256=checksum.hexdigest(), bytes=size)
        print(json.dumps(dict(status='PUBLIC_FILE_VERIFIED', name=name, bytes=size,
                              sha256=checksum.hexdigest(), observed_unix=time.time())), flush=True)
    manifest['completed_unix'] = time.time()
    with (arguments.output / 'SNAPSHOT_MANIFEST.json').open('x') as handle:
        json.dump(manifest, handle, sort_keys=True, indent=2)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
        os.fchmod(handle.fileno(), 0o444)
    print(json.dumps(dict(status='PINNED_PUBLIC_SNAPSHOT_COMPLETE', bytes=total,
                          gpu_model_loaded=False, path=str(arguments.output))), flush=True)


if __name__ == '__main__':
    main()
