"""Bounded node-to-node file frames; never an archive or a local raw forest."""

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys


def read_exact(stream, count):
    result = bytearray()
    while len(result) < count:
        part = stream.read(count-len(result))
        if not part:
            raise ValueError('incomplete_frame')
        result.extend(part)
    return bytes(result)


def transfer(mode, root):
    root = Path(root)
    if mode == 'send':
        stream = sys.stdout.buffer
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.is_symlink() or '__pycache__' in path.parts or path.name == 'hosts.env':
                continue
            size = path.stat().st_size
            if size > 16*1024*1024:
                raise ValueError('bounded_file_size')
            raw = path.read_bytes()
            metadata = json.dumps(dict(name=str(path.relative_to(root)), size=len(raw), sha256=hashlib.sha256(raw).hexdigest())).encode()
            stream.write(struct.pack('!I', len(metadata))+metadata+raw)
        stream.write(struct.pack('!I', 0))
        stream.flush()
    else:
        root.mkdir(parents=True, exist_ok=False)
        stream, files = sys.stdin.buffer, {}
        while True:
            length = struct.unpack('!I', read_exact(stream, 4))[0]
            if length == 0:
                break
            if length > 16384:
                raise ValueError('bounded_header')
            item = json.loads(read_exact(stream, length))
            relative = Path(item['name'])
            if relative.is_absolute() or '..' in relative.parts or not 0 <= item['size'] <= 16*1024*1024:
                raise ValueError('safe_relative_frame')
            raw = read_exact(stream, item['size'])
            if hashlib.sha256(raw).hexdigest() != item['sha256']:
                raise ValueError('frame_hash')
            destination = root/relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('xb') as output:
                output.write(raw)
            files[str(relative)] = item['sha256']
        print(json.dumps(dict(files=len(files), manifest_sha256=hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(), raw_local_files=0)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('send', 'receive'))
    parser.add_argument('root', type=Path)
    args = parser.parse_args()
    transfer(args.mode, args.root)
