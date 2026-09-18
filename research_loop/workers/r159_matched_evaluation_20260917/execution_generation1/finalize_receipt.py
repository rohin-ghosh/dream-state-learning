import hashlib
import json
from pathlib import Path
import time


directory = Path(__file__).resolve().parent
worker = directory.parent
observation = json.loads((directory / 'OBSERVATION_07.json').read_bytes())
proposal = json.loads((worker / 'frozen_readmission_proposal1/PROPOSAL.json').read_bytes())
learning = observation['arms']['parented_learning']
assert learning['completed'] and not learning['failed']
assert observation['ledger']['reserved'] == observation['ledger']['completed'] == 1
assert observation['ledger']['calls_charged'] == 56 and observation['ledger']['unresolved'] == 0
dispositions = {}
for arm, filename in (('parented_frozen', 'FROZEN_DISPATCH_DISPOSITION.json'),
                      ('unparented_learning', 'THIRD_DISPATCH_DISPOSITION.json')):
    status = json.loads((directory / filename).read_bytes())
    assert status['sanitized_statuses'] == ['DEVICE_BUSY_NO_SIGNALS_NO_RESERVATION']
    assert not observation['arms'][arm]['reserved'] and not observation['arms'][arm]['processes']
    dispositions[arm] = dict(status='DEVICE_BUSY_NO_SIGNALS_NO_RESERVATION',
        charged_calls=0, retry_attempted=False, operator_once_retained=True,
        disposition_path=str(directory / filename),
        disposition_sha256=hashlib.sha256((directory / filename).read_bytes()).hexdigest())
result = dict(schema='R159_INITIAL3_EXECUTION_OUTCOME_V1', status='ONE_COMPLETE_TWO_PRE_RESERVATION_BLOCKED',
    observed_unix=observation['observed_unix'], created_unix=time.time(), ledger=observation['ledger'],
    learning_complete=learning['completed_receipt'], learning_completed_unix=learning['completed_observed_unix'],
    sealed_learning_completion=learning['sealed_completion_reference'],
    completed_call_count=56, admission_blocked=dispositions, active_evaluator_processes=0,
    initial3_control_complete=False, new_frozen_readmission=proposal['proposed_execution'],
    new_frozen_readmission_requires_new_Main_GO=True, new_frozen_readmission_launched=False,
    new_physical1_observation=proposal['full_scan'], historical_blocking_reason_recovered=False,
    hard_end_unix=1789632000, latest_dispatch_strictly_before_unix=1789628385,
    source_changed=False, existing_evaluator_interrupted=False, held_contents_returned=False,
    scores_returned=False, old_campaign_caps_unchanged=True)
with (directory / 'FINAL_RECEIPT.json').open('x') as stream:
    json.dump(result, stream, sort_keys=True, indent=2)
    stream.write('\n')
print(json.dumps(result, sort_keys=True))
