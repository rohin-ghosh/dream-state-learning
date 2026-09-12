import json
from pathlib import Path

from organism_v6 import rulegame_parenting_diagnostic as diagnostic
from organism_v6 import rulegame_record_material as material


home = Path.home()
source = home / 'astra_sources/610c6edd05ce9c85720ee6e992889badecc2c158'
assert diagnostic.REPO == source
assert diagnostic.digest(diagnostic.__file__) == 'e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526'
assert diagnostic.digest(material.__file__) == '7eb7bbd04068a34be4932f11a0eab0109ddabcceb03210a07b657d57a0c621c1'
prior = diagnostic.read(home / 'astra_diagnostics/astra_citation_sleep_preparation_20260912_attempt1/config.json')
root = home / 'astra_diagnostics/astra_rulegame_interaction_v3_20260912_attempt1'
assert diagnostic.model_hashes(prior['model_path']) == prior['expected_files']
plan = diagnostic.prepare(root, prior['model_path'], '2', '2026-09-25T21:03:00+00:00', 'interaction_v3')
assert plan['model_files'] == prior['expected_files']
tokenizer = diagnostic.native_tokenizer(plan['model'])
fixtures = []
for ordinal, predicted in enumerate((False, None)):
    execution = dict(eid='native-fixture-not-experience', tick=ordinal, values=[1, 2, 3],
                     observed=True, predicted=predicted, outcome='the box says: True for (1,2,3)')
    output = ('PREDICT: F\n' if predicted is False else '') + 'ACT: TRY 1,2,3'
    prompt = diagnostic.record_prompt(execution, output, 'interaction_v3')
    raw = json.dumps({'try': [1, 2, 3], 'observed': True, 'predicted': predicted,
                      'relation': 'mismatched' if predicted is False else 'unavailable'})
    rendered = tokenizer.apply_chat_template([dict(role='user', content=prompt)],
                                              tokenize=False, add_generation_prompt=True)
    response = dict(text=raw, rendered_prompt=rendered,
                    prompt_token_ids=tokenizer.encode(rendered, add_special_tokens=False))
    row = dict(arm='P' if ordinal == 0 else 'A', eid=execution['eid'],
               execution_id=f'fixture:{ordinal}', source_call_id='0000', call_id='0001')
    item, encoding = material._encode(prompt, response, row, tokenizer, 4096, set(), ordinal)
    assert item['spans'][1][0] == raw
    fixtures.append(encoding)
diagnostic.verify_plan(root)
receipt = dict(status='NATIVE_RULEGAME_V3_FORMATION_PREPARATION_PASS', root=str(root),
               protocol='interaction_v3', source=str(source), plan_sha256=diagnostic.digest(root / 'plan.json'),
               fixture_encoding=fixtures, native_fixture_not_training_material=True,
               no_model_forward_or_fit=True, actual_record_bridge_executed=False,
               model_origin='UNRESOLVED_LOCAL_HASHES_ONLY', source_hashes=plan['source_hashes'],
               material_source_sha256=diagnostic.digest(material.__file__),
               lease_finish_cutoff='2026-09-25T21:03:00+00:00',
               main_audit_contract=diagnostic.main_audit_contract('interaction_v3'),
               claim_boundary=diagnostic.CLAIM_BOUNDARY)
diagnostic.write_json(root / 'native_preparation.json', receipt)
print(json.dumps(receipt, sort_keys=True), flush=True)
