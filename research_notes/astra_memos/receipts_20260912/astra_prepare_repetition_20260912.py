import json
from pathlib import Path

from organism_v6 import fundamental_repetition_corpus as repetition
from organism_v6 import rulegame_parenting_diagnostic as base

source = Path.home() / 'astra_diagnostics/astra_fundamental_teaching_20260912_attempt1'
out = Path.home() / 'astra_diagnostics/astra_fundamental_repetition_20260912_attempt1'
plan = base.read(source / 'plan.json')
assert base.digest(source / 'plan.json') == 'd5a3d0297290184061b5cfcc3bf7fa5ba36a5995fbaedb021df464be7879ec5e'
assert base.model_hashes(plan['model']) == plan['model_files']
repetition.export_material(source / 'teach.json', source / 'control.json', out,
    base.native_tokenizer(plan['model']), seeds=(0, 1, 2, 17))
manifest = base.read(out / 'manifest.json')
assert manifest['status'] == 'TOKENIZER_AND_V3_ORDER_VALIDATED_NO_FIT'
for arm in ('teach', 'control'):
    budgets = manifest['audit']['arms'][arm]
    assert budgets['original'] == dict(rows=80, input_tokens=4517, target_tokens=912, max_sequence_tokens=61)
    assert budgets['short'] == dict(rows=1280, input_tokens=72272, target_tokens=14592, max_sequence_tokens=61)
    assert budgets['long'] == dict(rows=80, input_tokens=72272, target_tokens=14592, max_sequence_tokens=976)
base.write_json(out / 'main_native_reference_check.json', dict(source=str(base.REPO),
    model=plan['model'], model_files=plan['model_files'], original_plan_sha256=base.digest(source / 'plan.json'),
    manifest_sha256=base.digest(out / 'manifest.json'), exact_reference_counts=True, gpu_calls=0, fits=0))
print(json.dumps(dict(status=manifest['status'], budgets=manifest['audit']['arms'],
    manifest_sha256=base.digest(out / 'manifest.json')), sort_keys=True))
