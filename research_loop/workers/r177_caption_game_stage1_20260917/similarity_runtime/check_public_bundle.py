"""Verify the public integration export and emit safe pins without provider calls."""

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))
from gpu import ny_caption_similarity as runtime
from gpu.ny_caption_pixels import PixelConfig


BUNDLE_SHA = '3e850106b2e7742a3557bf1a291883756bac57754d0feb4849f52feef40adde4'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    arguments = parser.parse_args()
    root = HERE / 'public_bundle1'
    manifest_ref = dict(path=str(root / 'BUNDLE_MANIFEST.json'), sha256=BUNDLE_SHA)
    manifest = runtime.bound(manifest_ref)
    actual = {str(path.relative_to(root)) for path in root.rglob('*') if path.is_file()}
    runtime.require(actual == {*manifest['files'], 'BUNDLE_MANIFEST.json'}, 'exact_public_bundle_inventory')
    for name, expected in manifest['files'].items():
        path = root / name
        runtime.require(not path.is_symlink(), 'no_mutable_external_bundle_symlinks')
        reference = runtime.file_pin(path)
        runtime.require(all(reference[key] == value for key, value in expected.items()), 'frozen_export_file_pin')
    for name in ('source_code', 'source_tests'):
        reference = manifest[name]
        runtime.require(runtime.file_pin(reference['path']) == reference, 'exact_tested_source_snapshot')
    config_ref = runtime.file_pin(root / 'similarity_runtime.json')
    config = runtime.bound(config_ref)
    pixel_ref = runtime.file_pin(root / 'pixel_config.json')
    pixels = PixelConfig(**runtime.bound(pixel_ref))
    runtime.require(asdict(pixels) == config['pixel_config'], 'plain_and_full_config_agree')
    runtime.require(config['schema'] == 'NY_FROZEN_SIMILARITY_RUNTIME_V1' and config['verifier_required'] is True
        and config['provisional_model_annotations'] is True
        and config['label_prompt_sha256'] == runtime.sha(runtime.LABEL_SYSTEM.encode()), 'Main_CLI_compatible_instrument')
    snapshot = runtime.bound(config['encoder_manifest'])
    runtime.require(snapshot['model_id'] == pixels.embedding_model_id == runtime.MODEL_ID
        and snapshot['revision'] == pixels.embedding_revision == runtime.MODEL_REVISION,
        'frozen_calibration_and_encoder_identity')
    for name in ('similarity_runtime.json', 'pixel_config.json', 'embedding_snapshot.json', 'PUBLIC_CALIBRATION.json',
        'CPU_PORTABILITY_PROOF.json', 'BUNDLE_MANIFEST.json'):
        raw = (root / name).read_bytes()
        runtime.require(all(marker not in raw for marker in (
            b'"calibrated_pairs"', b'"pair_id"', b'"caption_a"', b'"caption_b"', b'.private.json')),
            'no_private_pair_references_or_contents_in_public_metadata')
    gate = runtime.bound(runtime.file_pin(HERE / 'campaign1/CPU_GATE.json'))
    runtime.bound(gate['scope'])
    proof_ref = runtime.file_pin(root / 'CPU_PORTABILITY_PROOF.json')
    proof = runtime.bound(proof_ref)
    runtime.require(proof['exact_vector_equality'] and proof['repeat_determinism']
        and proof['actual_pretrained_execution'] and proof['new_provider_calls'] == 0, 'bound_actual_portability_proof')
    tests_ref = runtime.file_pin(HERE / 'PUBLIC_BUNDLE_CPU_TESTS1.txt')
    runtime.require('175 passed' in Path(tests_ref['path']).read_text(), 'actual_current_CPU_regression_receipt')
    report = dict(schema='R177_PUBLIC_INTEGRATION_HANDOFF_V1', observed_utc=datetime.now(timezone.utc).isoformat(),
        status='READY_REAL_CPU_ENCODER_AND_SEPARATE_DEVELOPMENT_VERIFIER_SCOPE', bundle_manifest=manifest_ref,
        pixel_config=pixel_ref, embedding_snapshot=config['encoder_manifest'], Main_CLI_similarity_runtime=config_ref,
        source=manifest['source_code'], tests=manifest['source_tests'], actual_CPU_tests=dict(passed=175, receipt=tests_ref),
        CPU_portability_proof=proof_ref, API=runtime.file_pin(root / 'INTEGRATION_API.md'),
        unchanged_train_scope=gate['scope'], encoder_revision=runtime.MODEL_REVISION,
        factory_signature="make_same_joke_verifier(*, lane_id, budget_root, scope_ref, resolution='primary', api_key=None)",
        development_scope=dict(schema='NY_SIMILARITY_DEVELOPMENT_VERIFIER_SCOPE_V1', allowed_pool='agent_development',
            label_call_cap=0, pair_label_cap=0, maximum_verification_cap=32, no_budget_reset=True,
            one_pair_per_verifier_call=True, issuer='Main/Astra', maximum_active_seconds=3600,
            fixed_admitted_wall_required=True, lane_local_budget_root_required=True),
        new_provider_calls=0, new_GPU_calls=0, new_label_contents_read=0, granted_development_calls=0,
        prior_verification_smokes_remaining=0, private_contents_included=False,
        remaining_integration_action='Main binds its separately allocated agent_development scope and private lane budget root; no TRAIN relabeling.',
        limitation='Provisional model annotations, not human truth; primary heldout retrieval false split 8/30 cannot be repaired by above-rho-only verification.')
    if arguments.output:
        output = arguments.output.resolve()
        runtime.require(output.is_relative_to(HERE), 'owned_runtime_receipt_only')
        runtime.private_write(output, report)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
