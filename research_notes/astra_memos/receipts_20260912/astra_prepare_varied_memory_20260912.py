from datetime import datetime, timezone
import json
from pathlib import Path
import sys


source = Path.home() / 'astra_sources/dc2e9a3c11ccd9a3f10ea28513723bbfb8420247'
sys.path.insert(0, str(source))
from organism_v6 import varied_memory_replay_corpus as varied
from organism_v6 import rulegame_parenting_diagnostic as base

assert Path(varied.__file__).resolve().parent.parent == source
assert base.digest(varied.__file__) == 'fbdcb87ec2d2475b1b988e7b19ee53cb8318f0bafe2e805807871059d2cbfaa2'
original = Path.home() / 'astra_diagnostics/astra_fundamental_teaching_20260912_attempt1'
assert base.digest(original / 'plan.json') == 'd5a3d0297290184061b5cfcc3bf7fa5ba36a5995fbaedb021df464be7879ec5e'
plan = base.read(original / 'plan.json')
model = Path(plan['model'])
assert base.model_hashes(model) == plan['model_files']
tokenizer = base.native_tokenizer(model)
root = Path.home() / 'astra_diagnostics/astra_varied_memory_replay_20260912_attempt1'
root.mkdir()
result = varied.prepare(root / 'material', original / 'teach.json', tokenizer, seeds=(0, 1, 2))
varied.verify(root / 'material')
assert base.model_hashes(model) == plan['model_files']
receipt = dict(status='ACTUAL_NATIVE_TOKENIZER_AUDIT_PASS_NO_FIT', prepared_utc=datetime.now(timezone.utc).isoformat(),
               source_root=str(source), source_commit='dc2e9a3c11ccd9a3f10ea28513723bbfb8420247',
               material=str(root / 'material'), material_manifest_sha256=base.digest(root / 'material/manifest.json'),
               model=str(model), model_files=plan['model_files'], original_plan_sha256=base.digest(original / 'plan.json'),
               original_teach_sha256=base.digest(original / 'teach.json'), source_hashes=varied.source_hashes(),
               native_tokenizer_class=type(tokenizer).__module__ + '.' + type(tokenizer).__name__,
               tokenizer_matches_original_model_files=True, origin_authenticated=False,
               origin='UNRESOLVED_LOCAL_HASHES_ONLY', no_model_forward_or_training=True,
               token_totals=result['token_totals'], preparation_script_sha256=base.digest(__file__))
base.write_json(root / 'native_prepare.json', receipt)
print(json.dumps(dict(status=receipt['status'], root=str(root), manifest_sha256=receipt['material_manifest_sha256'],
                      token_totals=receipt['token_totals']), indent=2), flush=True)
