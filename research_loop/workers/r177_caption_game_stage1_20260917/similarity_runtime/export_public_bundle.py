"""Once-only clean export and actual CPU relocation proof; never dispatches a provider."""

from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))
from gpu import ny_caption_similarity as runtime
from gpu.ny_caption_pixels import PixelConfig, embedding_text


CONFIG_SHA = 'e2619a1ca22b7d934f317b05ba0dc2ae6708b42562edb66c03ae7920dfa5f27b'
ENCODER_SHA = '110116b20f71ecbd1149332d0fabbeb1bf15a48d51ff8bc0f80b52eee1f1e2a6'
READINESS_SHA = 'd4b27b71083128976817f9d29ff34aac7d0ad265364421891615c7cf42b87cdf'


def write_once(path, value):
    raw = json.dumps(value, indent=2, sort_keys=True, allow_nan=False).encode() + b'\n'
    reference = runtime.private_write(path, raw)
    Path(path).chmod(0o444)
    return reference


def main():
    source_config = runtime.bound(dict(path=str(HERE / 'campaign1/calibration1/FROZEN_RUNTIME_CONFIG.json'),
        sha256=CONFIG_SHA))
    source_manifest_ref = dict(path=str(HERE / 'encoder_acquisition1/ENCODER_MANIFEST.json'), sha256=ENCODER_SHA)
    source_manifest = runtime.bound(source_manifest_ref)
    readiness = runtime.bound(dict(path=str(HERE / 'PUBLIC_READINESS_20260917.json'), sha256=READINESS_SHA))
    pixel_config = PixelConfig(**source_config['pixel_config'])
    runtime.require(asdict(pixel_config) == source_config['pixel_config'], 'exact_preexisting_frozen_thresholds')
    runtime.require(source_config['label_prompt_sha256'] == runtime.sha(runtime.LABEL_SYSTEM.encode()),
        'unchanged_verifier_instrument')
    original = runtime.FrozenCPUEncoder(source_manifest_ref, threads=2)
    output = HERE / 'public_bundle1'
    output.mkdir(mode=0o755, exist_ok=False)
    for name, checksum in sorted(source_manifest['files'].items()):
        source = Path(source_manifest['root']) / name
        target = output / 'embedding' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o444)
        runtime.require(runtime.file_pin(target)['sha256'] == checksum, 'exact_copy_of_frozen_encoder')
    snapshot = dict(schema='NY_SENTENCE_ENCODER_SNAPSHOT_V1', directory='embedding',
        model_id=source_manifest['model_id'], revision=source_manifest['revision'], files=source_manifest['files'])
    snapshot_ref = write_once(output / 'embedding_snapshot.json', snapshot)
    write_once(output / 'pixel_config.json', source_config['pixel_config'])
    runtime_config = {key: source_config[key] for key in (
        'schema', 'pixel_config', 'label_model', 'label_prompt_sha256', 'no_cross_arm_state',
        'verifier_budget_not_increased', 'verifier_required', 'provisional_model_annotations')}
    runtime_config.update(encoder_manifest=snapshot_ref, source_calibration_config_sha256=CONFIG_SHA)
    write_once(output / 'similarity_runtime.json', runtime_config)
    for name in ('RUNTIME_DEPENDENCIES.txt', 'INTEGRATION_API.md'):
        shutil.copyfile(HERE / name, output / name)
        (output / name).chmod(0o444)
    portable = runtime.FrozenCPUEncoder(snapshot_ref, threads=2)
    texts = [embedding_text('Synthetic CPU-only scene.', caption) for caption in (
        'A synthetic relocation check.', 'A separate synthetic CPU check.')]
    original_vectors = original.encode_many(texts)
    portable_vectors = portable.encode_many(texts)
    runtime.require(original_vectors == portable_vectors, 'portable_vectors_exactly_match_original')
    runtime.require(portable_vectors == portable.encode_many(texts), 'portable_CPU_determinism')
    runtime.require(all(len(vector) == 384 for vector in portable_vectors), 'actual_384_dimensions')
    proof = dict(schema='NY_PORTABLE_ENCODER_CPU_PROOF_V1', observed_utc=datetime.now(timezone.utc).isoformat(),
        actual_pretrained_execution=True, source_manifest_sha256=ENCODER_SHA, snapshot_sha256=snapshot_ref['sha256'],
        exact_vector_equality=True, repeat_determinism=True, dimensions=384, device='cpu',
        model_id=portable.model_id, revision=portable.revision, parameters_frozen=True,
        synthetic_CPU_identity_checks=2, new_provider_calls=0, new_scientific_annotations=0,
        captions_or_labels_read=0, thresholds_recalibrated=False)
    write_once(output / 'CPU_PORTABILITY_PROOF.json', proof)
    public = {key: readiness[key] for key in ('annotations_obtained', 'fitting_contests', 'holdout_contests',
        'fitting_pair_slots', 'holdout_pair_slots', 'unresolved_fitting_pairs_by_resolution', 'limitations',
        'provider_reported_token_usage', 'verification_smoke_calls_remaining') if key in readiness}
    public.update(schema='NY_PORTABLE_SIMILARITY_PUBLIC_CALIBRATION_V1', provisional_model_annotations=True,
        validated_human_truth=False, selected_contests=30, pair_count=300, label_related_calls=45,
        verification_smoke_calls=32, failed_calls=0, retries=0, primary_holdout_false_merge=dict(count=0, total=30),
        primary_holdout_false_split=dict(count=8, total=30), development_allowance_granted=0,
        source_calibration_config_sha256=CONFIG_SHA)
    write_once(output / 'PUBLIC_CALIBRATION.json', public)
    inventory = {}
    for path in sorted(output.rglob('*')):
        if path.is_file():
            reference = runtime.file_pin(path)
            inventory[str(path.relative_to(output))] = dict(sha256=reference['sha256'], bytes=reference['bytes'])
    manifest = dict(schema='NY_PUBLIC_SIMILARITY_BUNDLE_V1', files=inventory,
        source_code=runtime.file_pin(REPO / 'gpu/ny_caption_similarity.py'),
        source_tests=runtime.file_pin(REPO / 'tests/test_ny_caption_similarity.py'),
        model_revision=runtime.MODEL_REVISION, private_content_included=False, provider_calls_during_export=0,
        development_scope_schema='NY_SIMILARITY_DEVELOPMENT_VERIFIER_SCOPE_V1',
        development_allowance_granted=0, prior_training_scope_unchanged=True,
        prior_frozen_config_unchanged=runtime.file_pin(HERE / 'campaign1/calibration1/FROZEN_RUNTIME_CONFIG.json')['sha256'] == CONFIG_SHA)
    manifest_ref = write_once(output / 'BUNDLE_MANIFEST.json', manifest)
    print(json.dumps(dict(status='PUBLIC_BUNDLE_EXPORTED_ACTUAL_CPU_PROOF_PASS', bundle=manifest_ref,
        provider_calls=0, files=len(inventory), model_revision=runtime.MODEL_REVISION), sort_keys=True))


if __name__ == '__main__':
    main()
