import hashlib
import json
from pathlib import Path
import statistics

root = Path('/tmp/astra_objective_terminal_20260912/astra_semantic_objective_20260912_attempt1')
original = Path('/tmp/astra_semantic_writer_terminal_20260912/astra_semantic_writer_Q0_20260912_attempt1')
read = lambda path: json.loads(path.read_text())
report = read(root / 'report.json')
old = read(original / 'stages/fit_r1_plus/DONE.json')['result']
fits = {}
for arm in ('full_response', 'first_choice'):
    steps = [json.loads(line) for line in (root / 'stages' / ('fit_' + arm) / 'steps.jsonl').read_text().splitlines()]
    assert len(steps) == 256
    fits[arm] = dict(epoch_common_metrics=[dict(epoch=epoch,
        **{field: statistics.mean(step[field] for step in steps if step['epoch'] == epoch)
           for field in ('decision_ce','full_response_ce','nondecision_nll','gold_vs_other_margin')})
        for epoch in (0,1)], final_lora_sha256=report['fits'][arm]['final_lora_sha256'])
control_equal = report['fits']['full_response']['final_lora_sha256'] == old['final_lora_sha256']
assert control_equal
result = dict(status='ORIGINAL_CONTROL_TENSOR_HASH_REPRODUCED', control_final_tensor_equal=control_equal,
    original_control_final_lora_sha256=old['final_lora_sha256'], fits=fits,
    states={state: dict(correct=value['correct'],n=value['n'],valid=value['valid'],actions=value['action_counts'])
            for state,value in report['states'].items()}, actual_cost=report['actual_cost'],
    report_sha256=hashlib.sha256((root / 'report.json').read_bytes()).hexdigest(),
    limitations='Training metrics are online pre-update/dropout-active, not final checkpoint losses. One seed/map; no held or retention test. Native tree/reload verification is separately recorded; weights omitted from local capsule.')
with Path('/tmp/astra_objective_analysis_20260912.json').open('x') as stream:
    json.dump(result,stream,indent=2,sort_keys=True)
print(json.dumps(result,sort_keys=True))
