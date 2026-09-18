"""One bounded transport-only call; never publish to a child."""

import json
from pathlib import Path
import time

from gpu.orch_route_parent_campaign_providers import strong


root = Path(__file__).resolve().parent/'TRANSPORT_ONCE'
root.mkdir(mode=0o700)
try:
    response, model, usage = strong(
        'Transport readiness only. Return speak=false, message="", rationale="transport check" as JSON.',
        root, time.time()+120, 'Return exactly one JSON object with speak, message, rationale. No tools.',
        reasoning_effort='low')
    receipt = dict(status='COMPLETE', actual_model=model, usage=usage, utc_unix=time.time(),
                   child_publication=False, no_training=True, retries=0)
except Exception as error:
    receipt = dict(status='FAILED', error_type=type(error).__name__, utc_unix=time.time(),
                   child_publication=False, no_training=True, retries=0)
with (root/'RECEIPT.json').open('x') as stream:
    json.dump(receipt, stream, indent=2)
print(json.dumps(receipt))
