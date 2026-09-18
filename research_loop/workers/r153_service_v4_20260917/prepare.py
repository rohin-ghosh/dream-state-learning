"""Prepare an explicitly validated successor without modifying community state."""

import json
from pathlib import Path

from gpu.orch_r153_community_transport import source_pins
from gpu.orch_r153_service_handoff import validate_transition


directory = Path(__file__).resolve().parent
previous = json.loads((directory.parent / 'r153_service_v2_20260916/SERVICE_CONFIG_V2.json').read_text())
successor = json.loads(json.dumps(previous))
successor['hosts']['ovx3']['repository'] = '/localhome/local-rohing/orch_r153_service_source_v4_20260917'
successor['hosts']['ovx3']['source_sha256'] = source_pins(directory / 'source')
validate_transition(previous, successor)
with (directory / 'SERVICE_CONFIG_V4.json').open('x') as output:
    json.dump(successor, output, sort_keys=True, indent=2)
    output.write('\n')
