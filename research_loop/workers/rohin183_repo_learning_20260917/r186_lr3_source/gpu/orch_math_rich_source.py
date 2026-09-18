"""Check published source bytes without comparing cross-host ownership metadata."""

import hashlib
from pathlib import Path
import sys
import tarfile


def verify_archive(archive, directory):
    directory = Path(directory).resolve()
    verified = 0
    with tarfile.open(archive, 'r:') as stream:
        for member in stream:
            relative = Path(member.name)
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('unsafe_source_member')
            target = directory / relative
            if target.is_symlink():
                raise ValueError('source_symlink_forbidden')
            if member.isdir():
                if not target.is_dir():
                    raise ValueError('missing_source_directory')
                continue
            if not member.isfile():
                raise ValueError('unsupported_source_member')
            expected = hashlib.sha256(stream.extractfile(member).read()).digest()
            if not target.is_file() or hashlib.sha256(target.read_bytes()).digest() != expected:
                raise ValueError('source_bytes_changed:' + member.name)
            verified += 1
    if not verified:
        raise ValueError('empty_source_archive')
    return verified


if __name__ == '__main__':
    print('verified_source_files=' + str(verify_archive(sys.argv[1], sys.argv[2])))
