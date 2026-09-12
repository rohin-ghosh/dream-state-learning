import json
from pathlib import Path

from organism_v6 import rulegame_parenting_diagnostic as diagnostic

home = Path.home()
prior = diagnostic.read(home / 'astra_diagnostics/astra_citation_sleep_preparation_20260912_attempt1/config.json')
root = home / 'astra_diagnostics/astra_rulegame_interaction_v2_20260912_attempt1'
assert diagnostic.model_hashes(prior['model_path']) == prior['expected_files']
plan = diagnostic.prepare(root, prior['model_path'], '0', '2026-09-25T21:03:00+00:00', 'interaction_v2')
assert plan['model_files'] == prior['expected_files']
tokenizer = diagnostic.native_tokenizer(plan['model'])
fixture = ['Situation native-fixture.\nMy measured action record: ' + body for body in (
    ' {"try":[1,2,3],"observed":true,"predicted":false,"relation":"mismatched"}\n',
    '{"try":[3,2,1],"observed":false,"predicted":null,"relation":"unavailable"}')]
tokens = diagnostic.audit_tokens(tokenizer, fixture)
receipt = dict(status='NATIVE_RULEGAME_PREPARATION_PASS', root=str(root), protocol='interaction_v2',
               source=str(diagnostic.REPO), plan_sha256=diagnostic.digest(root / 'plan.json'),
               fixture_tokens=tokens, native_fixture_not_training_material=True,
               model_origin='UNRESOLVED_LOCAL_HASHES_ONLY', source_hashes=plan['source_hashes'],
               lease_finish_cutoff='2026-09-25T21:03:00+00:00',
               claim_boundary=diagnostic.CLAIM_BOUNDARY)
diagnostic.write_json(root / 'native_preparation.json', receipt)
print(json.dumps(receipt, sort_keys=True))
