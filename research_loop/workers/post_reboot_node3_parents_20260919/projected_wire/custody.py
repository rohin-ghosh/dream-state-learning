"""Private owner-file custody, installed only through the operator SSH channel."""

import os
from pathlib import Path
import stat
import uuid

from .contract import MAX_TRANSFER_BYTES, bounded, byte_digest, canonical, decode, is_sha, open_directory, read_at, require


class OwnerStore:
    def __init__(self, root, owner_uid):
        self.root = Path(root)
        self.owner_uid = owner_uid
        self.directory = open_directory(self.root)
        metadata = os.fstat(self.directory)
        if metadata.st_uid != owner_uid or stat.S_IMODE(metadata.st_mode) != 0o700:
            os.close(self.directory)
            raise ValueError('strict_owner_directory_0700')

    def close(self):
        os.close(self.directory)

    def check(self):
        metadata = os.fstat(self.directory)
        require(metadata.st_uid == self.owner_uid and stat.S_IMODE(metadata.st_mode) == 0o700,
            'strict_owner_directory_0700')

    def read(self, name):
        self.check()
        return read_at(self.directory, name, MAX_TRANSFER_BYTES, owner_uid=self.owner_uid, private=True)

    def put(self, name, raw, *, reuse=False):
        self.check()
        bounded(raw)
        require(Path(name).name == name and name not in ('.', '..'), 'single_owner_file_component')
        temporary = '.pending-' + uuid.uuid4().hex
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=self.directory)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, name, src_dir_fd=self.directory, dst_dir_fd=self.directory, follow_symlinks=False)
            except FileExistsError:
                require(reuse and self.read(name) == raw, 'existing_custody_or_dispatch_no_automatic_replay')
        finally:
            os.unlink(temporary, dir_fd=self.directory)
            os.fsync(self.directory)

    def install(self, receipt):
        raw = bounded(canonical(receipt))
        token = byte_digest(raw)
        self.put('receipt-' + token + '.json', raw, reuse=True)
        return token

    def receipt(self, token):
        require(is_sha(token), 'opaque_owner_receipt_digest_only')
        raw = self.read('receipt-' + token + '.json')
        require(byte_digest(raw) == token, 'owner_receipt_bytes_unchanged')
        return decode(raw)


def load_binding(path, owner_uid, expected_sha256):
    require(is_sha(expected_sha256), 'externally_pinned_binding_digest')
    path = Path(path)
    store = OwnerStore(path.parent, owner_uid)
    try:
        raw = store.read(path.name)
        require(byte_digest(raw) == expected_sha256, 'pinned_owner_binding_bytes')
        return decode(raw)
    finally:
        store.close()
