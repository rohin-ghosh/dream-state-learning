import datetime
import json
from pathlib import Path
import subprocess

from organism_v6 import relation_surface_diagnostic as diagnostic
from gpu.astra_mini_sudoku_diagnostic import check_free

base = diagnostic.base
root = Path.home() / 'astra_diagnostics/astra_relation_surface_20260912_attempt1'
plan, cases = diagnostic.verify(root)
result = base.read(root / 'reduction.json')
assert len(result['rows']) == 9 and result['native_token_text_audit'] is True
assert base.read(root / 'run/worker/supervision.json')['ok'] is True
launch_root = root.parent / (root.name + '_launch')
launch = base.read(launch_root / 'launch.json')
assert not (Path('/proc') / str(launch['pid'])).exists()
gpu, xml = check_free('0')
with (root / 'main_release_gpu.xml').open('x') as output:
    output.write(xml)
release = dict(observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    status='TERMINAL_NATIVE_AUDIT_AND_FULL_RELEASE_VERIFIED', device='0', gpu=gpu,
    controller_pid=launch['pid'], controller_absent=True, full_device_process_queue_check=True,
    native_reduction_sha256=base.digest(root / 'reduction.json'), source=str(base.REPO),
    results={surface: sum(row['correct'] for row in result['rows'] if row['surface'] == surface)
             for surface in diagnostic.SURFACES}, denominator_per_surface=3,
    fits=0, parent_calls=0, world_actions=0, model_origin='UNRESOLVED_LOCAL_HASHES_ONLY')
base.write_json(root / 'main_release.json', release)
archive = Path('/tmp/astra_relation_surface_terminal_20260912.tgz')
assert not archive.exists()
subprocess.run(['tar', '-czf', str(archive), '-C', str(root.parent), root.name, launch_root.name], check=True)
print(json.dumps(dict(release=release, archive=str(archive), archive_sha256=base.digest(archive)), sort_keys=True))
