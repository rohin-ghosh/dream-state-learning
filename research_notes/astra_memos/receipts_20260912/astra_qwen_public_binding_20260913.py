"""Read-only comparison of cached files with official revision metadata."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import time

REPOSITORY = 'Qwen/Qwen2.5-7B-Instruct'
REVISION = 'a09a35458c702b33eeacc393d103063234e8bc28'
URL = 'https://huggingface.co/api/models/'+REPOSITORY+'/revision/'+REVISION+'?blobs=true'


def check_files(model, metadata):
    model = Path(model)
    if metadata['id'] != REPOSITORY or metadata['sha'] != REVISION:
        raise ValueError('public repository/revision mismatch')
    rows = {}
    for entry in metadata['siblings']:
        name = entry['rfilename']
        if Path(name).is_absolute() or '..' in Path(name).parts or name in rows:
            raise ValueError('unsafe or duplicate public filename')
        filename = model/name
        before = filename.stat()
        if before.st_size != entry['size']:
            raise ValueError('public size mismatch: '+name)
        sha256 = hashlib.sha256()
        blob = hashlib.sha1(('blob '+str(before.st_size)+'\0').encode())
        with filename.open('rb') as stream:
            while chunk := stream.read(1024*1024):
                sha256.update(chunk)
                if 'lfs' not in entry:
                    blob.update(chunk)
        after = filename.stat()
        if any(getattr(before,key) != getattr(after,key) for key in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')):
            raise ValueError('file changed during hash: '+name)
        if 'lfs' in entry:
            matched = sha256.hexdigest() == entry['lfs']['sha256'] and after.st_size == entry['lfs']['size']
            kind = 'LFS_SHA256'
        else:
            matched = blob.hexdigest() == entry['blobId']
            kind = 'GIT_BLOB_SHA1'
        if not matched:
            raise ValueError('public content hash mismatch: '+name)
        rows[name] = dict(sha256=sha256.hexdigest(), size=after.st_size, public_match=kind)
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True)
    parser.add_argument('--metadata', required=True)
    parser.add_argument('--metadata-sha256', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    data = Path(args.metadata).read_bytes()
    if hashlib.sha256(data).hexdigest() != args.metadata_sha256:
        raise ValueError('metadata receipt hash mismatch')
    header, body = data.decode().split('\n',1)
    if header != '===== '+URL:
        raise ValueError('expected official metadata URL header')
    started = time.time()
    files = check_files(args.model, json.loads(body))
    result = dict(status='PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING', repository=REPOSITORY,
        revision=REVISION, metadata_url=URL, metadata_sha256=args.metadata_sha256,
        model=str(Path(args.model).absolute()), files=files, file_count=len(files),
        checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), elapsed_seconds=time.time()-started,
        historical_receipts_changed=False, clean_lineage_certified=False,
        limitation='Official HTTPS metadata content comparison; historical plans and data contamination labels are unchanged.')
    with Path(args.out).open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status=result['status'], files=len(files), seconds=result['elapsed_seconds'], out=args.out)))


if __name__ == '__main__':
    main()
