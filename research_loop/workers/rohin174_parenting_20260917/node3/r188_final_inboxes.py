"""Freeze old publication directories and preserve their final inbox bytes."""

import json
import os
from pathlib import Path
import socket
import subprocess
import time

import r181_boundary as base


def main():
    base.require(socket.gethostname() == '[REDACTED_HOST]', 'node3_only')
    output = base.HERE / 'r188/final_inboxes_20260917t2350z'
    output.mkdir(exist_ok=False)
    for physical in (0, 1, 2, 3, 4, 7):
        control = base.HERE / ('r188' if physical in (1, 2) else 'r181') / ('physical' + str(physical))
        spec = base.read(control / 'LIVE_HANDOFF.json')
        inbox = Path(spec['backing_root']) / 'stream/inbox'
        previous = inbox.stat().st_mode & 0o777
        inbox.chmod(previous & ~0o222)
        folder = output / ('physical' + str(physical))
        folder.mkdir()
        subprocess.run(['cp', '-a', '--reflink=auto', str(inbox), str(folder / 'inbox')], check=True)
        files = {path.name: base.sha(path) for path in inbox.iterdir() if path.is_file()}
        copied = {path.name: base.sha(path) for path in (folder / 'inbox').iterdir() if path.is_file()}
        base.require(files == copied, 'actual_final_inbox_copy_exact')
        base.write(folder / 'FROZEN.json', dict(physical=physical, observed_unix=time.time(),
            original_inbox=str(inbox), old_mode=previous, frozen_mode=inbox.stat().st_mode & 0o777,
            ordinary_publication_write_bits_removed=True, inbox_files=files,
            apply_after_final_state_packet=True, receiving_inbox_mode=previous,
            no_new_baseline_or_publication=True))
    print(json.dumps(dict(status='ALL_SIX_SOURCE_INBOXES_FROZEN_AND_CAPTURED', output=str(output))), flush=True)


if __name__ == '__main__':
    main()
