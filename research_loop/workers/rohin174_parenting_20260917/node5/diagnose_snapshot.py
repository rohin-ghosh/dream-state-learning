"""Read-only exact-source TRAIN snapshot failure diagnosis; no controller retry."""

import json
from pathlib import Path
import shlex
import subprocess
import time

from activate_parent import read, reference, require, write


HERE = Path(__file__).resolve().parent
CASES = (('ACTIVATION_A_1789678829928180897', 'C3'),
         ('ACTIVATION_B_1789678847374158305', 'C1'),
         ('ACTIVATION_C_1789678852147451612', 'C4'),
         ('ACTIVATION_C_1789678852147451612', 'repo_reader'),
         ('ACTIVATION_D_1789678856612153632', 'C5'))
SCRIPT = '''import json,traceback
from gpu.orch_r166_parent_snapshot import poll
cursor=None; cursor_hash=None
try:
 for iteration in range(256):
  observed=poll(ROOT,cursor,cursor_sha256=cursor_hash)
  cursor=observed['cursor']; cursor_hash=observed['cursor_sha256']
  if observed['snapshot']['caught_up']: break
 print(json.dumps(dict(status='PASS' if observed['snapshot']['caught_up'] else 'INCOMPLETE', index=cursor['next_index'])))
except Exception as error:
 print(json.dumps(dict(status='FAIL', error_type=type(error).__name__, error=str(error), prior_index=cursor['next_index'] if cursor else 0, trace=traceback.format_exc())))
'''


def main():
    rows = []
    for name, label in CASES:
        manifest = read(HERE / name / (label + '_MANIFEST.json'))
        config = read(manifest['predecessor']['config']['path'])
        script = SCRIPT.replace('ROOT', repr(config['root']))
        command = 'PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=' + shlex.quote(manifest['remote_source'])
        command += ' python3 -B -c ' + shlex.quote(script)
        result = subprocess.run(['bash', str(Path(manifest['source']) / 'gpu/ovx3_ssh.sh'), command],
                                capture_output=True, text=True, timeout=45)
        require(result.returncode == 0, 'diagnostic_transport_failed')
        rows.append(dict(label=label, result=json.loads(result.stdout), root=config['root'],
                         source_sha256=manifest['source_pins']['gpu/orch_r166_parent_snapshot.py']))
    receipt = HERE / ('SNAPSHOT_DIAGNOSIS_' + str(time.time_ns()) + '.json')
    write(receipt, dict(observed_unix=time.time(), rows=rows, no_signals=True,
        no_journal_writes=True, no_cursor_writes=True, no_provider_calls=True, C2_read=False))
    print(json.dumps(dict(receipt=reference(receipt), rows=[dict(label=row['label'],
                     result=row['result']['status'], error=row['result'].get('error')) for row in rows])))


if __name__ == '__main__':
    main()
