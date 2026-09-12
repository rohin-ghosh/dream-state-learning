import datetime
import json
from pathlib import Path
import sys

from organism_v6 import rulegame_parenting_diagnostic as diagnostic
from gpu.astra_mini_sudoku_diagnostic import check_free

phase = sys.argv[1]
assert phase in ('formation', 'terminal')
root = Path.home() / 'astra_diagnostics/astra_rulegame_interaction_v2_20260912_attempt1'
plan = diagnostic.verify_plan(root)
assert plan['protocol'] == 'interaction_v2'
replay = diagnostic.replay(root)
assert replay['ok'], replay['failures']
tokenizer = diagnostic.native_tokenizer(plan['model'])
captures = {'formation': root / 'formation/data'}
if phase == 'terminal':
    for cell in diagnostic.CELLS:
        captures[cell] = root / 'evaluation' / cell / 'data'
    diagnostic.verify_material(root, plan)
    fits = diagnostic.verify_fits(root, plan)
else:
    fits = {}
for path in captures.values():
    diagnostic.audit_native_calls(tokenizer, path)
    assert diagnostic.read(path / 'backend.cleanup.json')['closed'] is True
supervision = {str(path.relative_to(root)): diagnostic.read(path)
               for path in root.glob('**/supervision.json')}
assert all(row['ok'] and row['reservation_release_verified'] for row in supervision.values())
gpu, xml = check_free(plan['device'])
receipt = dict(status='NATIVE_RULEGAME_' + phase.upper() + '_CAPTURE_PASS',
               observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
               source=str(diagnostic.REPO), plan_sha256=diagnostic.digest(root / 'plan.json'),
               root=str(root), model_origin='UNRESOLVED_LOCAL_HASHES_ONLY',
               native_token_text_audit=True, replay_ok=True, gpu_release=gpu,
               supervision=supervision, fits=fits,
               captures={name: {'manifest_sha256': diagnostic.digest(path / 'manifest.json'),
                                'result': diagnostic.read(path / 'result.json'),
                                'usage': diagnostic.read(path / 'usage.json')}
                         for name, path in captures.items()},
               formation_selection=diagnostic.select_records(replay['captures']['formation']),
               claim_boundary=diagnostic.CLAIM_BOUNDARY)
out = Path('/tmp/astra_rulegame_v2_' + phase + '_capture_20260912.json')
diagnostic.write_json(out, receipt)
print(json.dumps(receipt, sort_keys=True))
