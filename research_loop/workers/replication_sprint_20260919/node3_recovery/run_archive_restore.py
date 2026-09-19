"""Run only the approved destination-side restore check through its original route."""

import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def main():
    source = (HERE / 'archive_restore.py').read_bytes()
    copy_receipt = json.loads((HERE / 'ARCHIVE_COPY_VERIFIED.json').read_bytes())
    if copy_receipt['status'] != 'ALL_ARCHIVE_MEMBERS_STREAM_RESTORED_AND_VERIFIED':
        raise ValueError('require_verified_complete_copy')
    program = base64.b64encode(source).decode()
    expression = "import base64;exec(compile(base64.b64decode('" + program + "'),'archive_restore.py','exec'))"
    with (HERE / 'ARCHIVE_FULL_RESTORE_STARTED.json').open('x') as record:
        json.dump(dict(utc=datetime.now(timezone.utc).isoformat(),
            destination_root=copy_receipt['destination_root'], code_sha256=hashlib.sha256(source).hexdigest(),
            archive_sha256=copy_receipt['archive_sha256'], source_mutations=False), record, indent=2)
    with (HERE / 'ARCHIVE_FULL_RESTORE_VERIFIED.json').open('x') as output, \
            (HERE / 'ARCHIVE_FULL_RESTORE.stderr').open('x') as errors:
        result = subprocess.run(['bash', str(REPO / 'gpu/ovx4_ssh.sh'),
            'python3 -B -c ' + shlex.quote(expression)], stdout=output, stderr=errors)
    if result.returncode:
        with (HERE / 'ARCHIVE_FULL_RESTORE_FAILED.json').open('x') as record:
            json.dump(dict(status=result.returncode, no_automatic_retry=True,
                partial_destination_preserved=True, source_mutations=False), record)
        raise RuntimeError('destination restore verification failed; inspect preserved stderr')


if __name__ == '__main__':
    main()
