"""Bind the actual frozen runtime without a provider call or archive submission."""

import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
from gpu import ny_caption_similarity as runtime


def main():
    root = HERE / 'campaign1'
    config_ref = runtime.file_pin(root / 'calibration1/FROZEN_RUNTIME_CONFIG.json')
    config = runtime.bound(config_ref)
    encoder = runtime.FrozenCPUEncoder(config['encoder_manifest'])
    scope_ref = runtime.file_pin(root / 'SCOPE.json')
    budget = runtime.CallBudget(root / 'calls', scope_ref)
    before = budget.summary()
    verifier = runtime.SameJokeVerifier(runtime.AstraAnnotator(budget, key=''), lane_id='similarity_calibration')
    archive = runtime.archive_from_config(config_ref, encoder, verifier, agent_id='similarity_calibration',
        contest_id='CPU_binding_check', scene='Synthetic CPU-only scene; no caption is submitted.')
    runtime.require(archive.pixel_count == 0 and before == budget.summary(), 'binding_check_never_dispatches')
    print(json.dumps(dict(status='ACTUAL_FROZEN_RUNTIME_BOUND_NO_DISPATCH', config=config_ref,
        model_id=encoder.model_id, revision=encoder.revision, provider_calls=0, archive_submissions=0,
        verification_smoke_allowance_remaining=budget.scope['verification_call_cap'] - before['verification_calls_charged'],
        previous_actual_provider_integration_evidence=str(root / 'VERIFIER_SMOKES_PUBLIC.json')), sort_keys=True))


if __name__ == '__main__':
    main()
