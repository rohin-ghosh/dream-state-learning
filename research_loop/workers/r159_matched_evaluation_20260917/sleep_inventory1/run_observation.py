import json
from pathlib import Path
import subprocess


directory = Path(__file__).resolve().parent
worker = directory.parent
repository = worker.parents[2]
base = (worker/'observation_20260917_generation2/observe.py').read_text()
inventory = (directory/'inventory.py').read_text()
program = "base={'__name__':'metadata_reader'}\nexec(" + repr(base) + ",base)\n" + inventory
program += '\nprint(json.dumps(observe(base),sort_keys=True))\n'
with (directory/'TRANSPORT.stderr').open('xb') as errors:
    result = subprocess.run(['bash',str(repository/'gpu/a40r_ssh.sh'), 'python3 -B -'],
        input=program.encode(), stdout=subprocess.PIPE, stderr=errors, timeout=240, check=True)
if len(result.stdout) > 16*1024*1024:
    raise ValueError('return_limit')
metadata = json.loads(result.stdout)
with (directory/'OBSERVATION.json').open('xb') as stream:
    stream.write(result.stdout)
print(json.dumps(dict(observed_unix=metadata['observed_unix'], scanned_bytes=metadata['scanned_bytes'],
    returned_bytes=len(result.stdout), arms={arm:dict(coverage=report['coverage'],
    records=report.get('verified_record_count'), sleeps=len(report['sleep_complete_records']),
    checkpoints={key:entry['disposition'] for key,entry in report['intended'].items()})
    for arm,report in metadata['arms'].items()}),sort_keys=True))
