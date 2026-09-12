from collections import Counter
import datetime
import hashlib
import json
from pathlib import Path
import tarfile

home = Path.home()
run = home / 'astra_diagnostics/astra_coached_note_replay_20260912_attempt1'
logs = home / 'astra_diagnostics/astra_coached_note_replay_20260912_attempt1_logs'
prep = home / 'astra_diagnostics/astra_coached_note_write_20260912_attempt1'
capsule = Path('/tmp/astra_coached_note_terminal_20260912')
capsule.mkdir()
roots = [run, logs, prep, home / 'astra_sources/f00164c0dbfe81401230f47dc1bf11650a22632a', home / 'astra_sources/e711e849731c288e8a09c60540819e259297c560']
cleanup = json.loads((logs / 'worker.cleanup.json').read_text())
assert cleanup['reservation_release_verified'] is True
records = [json.loads(line) for line in (run / 'records.jsonl').read_text().splitlines()]
events = [json.loads(line) for line in (run / 'generations.jsonl').read_text().splitlines()]
summary = dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), records=len(records), arms={}, cleanup=cleanup, preparation=json.loads((prep / 'preparation/write_prep.json').read_text()), generation_batch_seconds=sum(event['elapsed_seconds'] for event in events if event['kind'] == 'batch_return'), elapsed_cost_scope='Batch generation only; not full GPU reservation or cold load', original_P0_capsule_sha256='13ca1bcefa98d2c4336197f46093abe807f141b937aa5d3d78876ac58122c208')
for arm in ('lesson', 'sham'):
    rows = [row for row in records if row['arm'] == arm]
    summary['arms'][arm] = dict(count=len(rows), faithful=sum(row['judgment']['faithful'] for row in rows), rejections=dict(Counter(row['judgment']['judge_record'].get('reason', 'eligible') for row in rows)), delivered_text_echo=sum(row['judgment']['delivered_text_echo'] for row in rows), prompt_tokens=sum(row['tokens']['prompt_tokens'] for row in rows), output_retokenized_tokens=sum(row['output_retokenized_tokens'] for row in rows), coach_standalone_tokens=sum(row['tokens']['coach_standalone_tokens'] for row in rows))
files = [path for root in roots for path in sorted(root.rglob('*')) if path.is_file()]
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
manifest = {path.relative_to(home).as_posix(): digest(path) for path in files}
(capsule / 'summary.json').write_text(json.dumps(summary, sort_keys=True, indent=2))
(capsule / 'manifest.json').write_text(json.dumps(manifest, sort_keys=True, indent=2))
archive = Path('/tmp/astra_coached_note_terminal_20260912.tgz')
with tarfile.open(archive, 'x:gz') as output:
    for path in files:
        output.add(path, arcname='node3/' + path.relative_to(home).as_posix(), recursive=False)
    output.add(capsule, arcname='audit')
assert manifest == {path.relative_to(home).as_posix(): digest(path) for path in files}
with tarfile.open(archive, 'r:gz') as source:
    for name, expected in manifest.items():
        assert hashlib.sha256(source.extractfile('node3/' + name).read()).hexdigest() == expected
print(json.dumps(dict(archive=str(archive), sha256=digest(archive), content_files_verified=len(manifest), summary=summary), sort_keys=True))
