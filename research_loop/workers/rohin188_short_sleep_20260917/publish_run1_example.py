import hashlib
import json
import os
from pathlib import Path
import sys
import time


source = Path('/localhome/local-rohing/orch_r179_context_C2_20260917_attempt4/source')
sys.path.insert(0, str(source))
from gpu.orch_r127_pilot_console import publish_parent


root = '/localhome/local-rohing/orch_r125_continual_20260916_attempt1/run1'
output = Path('/localhome/local-rohing/orch_r188_main_run1_example_20260917')
message = (
    'Rohin offers a useful demonstration: C2 chose a k=3 case that separated two formulas, '
    'checked it, revised its judgment, and carried the correction. Apply that method to '
    'your own current investigation, not C2\'s formulas. Name a case where your alternatives '
    'predict different results, run one check, and use the actual receipt to decide the '
    'next step. Should you keep thinking, or are you better off with new data? '
    'A completed process alone does not verify the answer.')
assert len(message.split()) <= 90
output.mkdir(exist_ok=True)
publication_path = output / 'PUBLICATION.json'
if publication_path.exists():
    print(publication_path.read_text())
else:
    intent = dict(authorization='Rohin188', root=root, speaker='Astra',
        author='Builder-authored demonstration; not a gateway model call',
        source='Rohin/Fable reported C2 example, not newly verified task output',
        message=message, message_sha256=hashlib.sha256(message.encode()).hexdigest(),
        started_unix=time.time(), original_arm_withdrawal_previously_completed=True,
        new_intervention='R188_REPORTED_WORKED_EXAMPLE_V1')
    with (output / 'INTENT.json').open('x') as target:
        json.dump(intent, target, sort_keys=True)
        target.flush()
        os.fsync(target.fileno())
    publication = publish_parent(root, 'Astra', message)
    receipt = dict(intent, publication=publication, published_unix=time.time(),
        rendered_verified=False, training_target=False)
    with publication_path.open('x') as target:
        json.dump(receipt, target, sort_keys=True)
        target.flush()
        os.fsync(target.fileno())
    print(json.dumps(receipt, sort_keys=True))
