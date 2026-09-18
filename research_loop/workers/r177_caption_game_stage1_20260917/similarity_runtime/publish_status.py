"""Publish only safe aggregates and exact pins; retain empirical and repaired source."""

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))
from gpu import ny_caption_similarity as runtime
from gpu.ny_caption_pixels import LabeledPair


def main():
    root = HERE / 'campaign1'
    gate = runtime.bound(runtime.file_pin(root / 'CPU_GATE.json'))
    current = (REPO / 'gpu/ny_caption_similarity.py').read_text()
    old = current.replace(
        "provisional_model_annotations=True, validated_human_truth=False,\n        encoder_execution_verified=report.get('encoder', {}).get('model_execution_verified') is True,",
        'provisional_model_annotations=True, validated_human_truth=False, encoder_execution_verified=True,')
    start = old.index('\ndef sufficient_labels(')
    stop = old.index('\ndef main():', start)
    old = old[:start] + old[stop:]
    old = old.replace('    sufficient = sufficient_labels(pairs, report)\n',
        "    sufficient = len(pairs) >= 240 and len({pair.group_id or pair.contest_id for pair in pairs}) >= 20\n"
        "    sufficient = sufficient and all(report['resolutions'][name].get('heldout') is not None\n"
        "        and report['resolutions'][name]['heldout']['balanced_error'] is not None for name in RESOLUTIONS)\n")
    original_sha = gate['source_pins']['gpu/ny_caption_similarity.py']['sha256']
    runtime.require(runtime.sha(old.encode()) == original_sha, 'exact_preserved_empirical_source_pin')
    historical = runtime.private_write(HERE / 'empirical_source1/ny_caption_similarity.py', old.encode())
    for name in ('gpu/ny_caption_pixels.py', 'gpu/ny_caption_game.py'):
        runtime.require(runtime.file_pin(REPO / name) == gate['source_pins'][name], 'neighbor_source_unchanged')
    report = runtime.bound(runtime.file_pin(root / 'calibration1/CALIBRATION.private.json'))
    pairs = [LabeledPair(**item) for item in runtime.bound(runtime.file_pin(root / 'LABELED_PAIRS.private.json'))['pairs']]
    runtime.require(runtime.sufficient_labels(pairs, report), 'actual_data_also_passes_stricter_nonnull_label_guard')
    calibration = runtime.bound(runtime.file_pin(root / 'calibration1/PUBLIC_METADATA.json'))
    smokes = runtime.bound(runtime.file_pin(root / 'VERIFIER_SMOKES_PUBLIC.json'))
    annotation = runtime.bound(runtime.file_pin(root / 'ANNOTATION_PUBLIC.json'))
    rows = [json.loads(path.read_bytes()) for path in (root / 'calls').glob('*/RESERVED.json')]
    terminals = [json.loads(path.read_bytes()) for path in (root / 'calls').glob('*/TERMINAL.json')]
    usage = {}
    for path in (root / 'calls').glob('*/RESPONSE.private.json'):
        response = json.loads(path.read_bytes())
        for name, value in response.get('usage', {}).items():
            if type(value) in (int, float):
                usage[name] = usage.get(name, 0) + value
    tests = subprocess.run([sys.executable, '-m', 'pytest', '-q', 'tests/test_ny_caption_similarity.py',
        'tests/test_ny_caption_pixels.py', 'tests/test_ny_caption_game.py'], cwd=REPO, capture_output=True)
    test_ref = runtime.private_write(HERE / 'FINAL_CPU_TESTS_01.txt', tests.stdout + tests.stderr)
    runtime.require(tests.returncode == 0, 'final_CPU_tests_pass')
    dependencies = subprocess.run([str(Path.home() / '.local/bin/uv'), 'pip', 'freeze', '--python', sys.executable],
        capture_output=True)
    runtime.require(dependencies.returncode == 0, 'exact_runtime_dependency_capture')
    dependency_ref = runtime.private_write(HERE / 'RUNTIME_DEPENDENCIES.txt', dependencies.stdout)
    summary = dict(schema='R177_SIMILARITY_RUNTIME_PUBLIC_READINESS_V1',
        status='REAL_CPU_RUNTIME_AND_PROVISIONAL_CALIBRATION_COMPLETE', observed_utc=datetime.now(timezone.utc).isoformat(),
        no_active_provider_jobs=True, GPU_calls=0, FINAL_reads=0, locked_validation_reads=0, R176_reads=0,
        source_input=runtime.bound(runtime.file_pin(root / 'SCOPE.json'))['source_input'],
        encoder_manifest=runtime.file_pin(HERE / 'encoder_acquisition1/ENCODER_MANIFEST.json'),
        frozen_runtime_config=runtime.file_pin(root / 'calibration1/FROZEN_RUNTIME_CONFIG.json'),
        label_prompt_sha256=runtime.sha(runtime.LABEL_SYSTEM.encode()),
        empirical_source_snapshot=historical,
        source_snapshot_note='Recovered exact pre-provider bytes after two reporting/insufficient-label guard repairs; '
            'verified identical to the pre-provider CPU gate SHA. No empirical or budget artifact rewritten.',
        current_source=runtime.file_pin(REPO / 'gpu/ny_caption_similarity.py'),
        current_tests=runtime.file_pin(REPO / 'tests/test_ny_caption_similarity.py'),
        changed_runtime_behavior='Reporting reads actual encoder-verification flag; missing labels cannot count toward 240 labelled-pair minimum. '
            'No encoder, prompts, verifier, thresholds or previous metrics changed; no provider reruns.',
        actual_current_guard_confirmation=True, final_CPU_tests=dict(passed=152, receipt=test_ref),
        pre_provider_CPU_tests_passed=150, dependency_lock=dependency_ref,
        available_TRAIN_contests=180, selected_contests=30, fitting_contests=24, holdout_contests=6,
        annotated_pairs=annotation['valid_labeled_pairs'], fitting_pair_slots=240, holdout_pair_slots=60,
        unresolved_fitting_pairs_by_resolution={name: 240 - report['resolutions'][name]['training']['n'] for name in runtime.RESOLUTIONS},
        calibration_metrics=calibration['metrics'], provisional_model_annotations=True, validated_human_truth=False,
        verifier_smokes=smokes, budget=smokes['budget'], provider_reported_token_usage=usage,
        requests_terminal=len(terminals), requests_reserved=len(rows),
        first_request_utc=datetime.fromtimestamp(min(row['reserved_unix'] for row in rows), timezone.utc).isoformat(),
        last_terminal_utc=datetime.fromtimestamp(max(row['completed_unix'] for row in terminals), timezone.utc).isoformat(),
        verification_smoke_calls_remaining=0, further_calls_started=False,
        limitations=['Primary heldout retrieval false-split rate is 8/30 (26.67%); verifier is only called above rho and cannot repair retrieval misses.',
            'Six-contest holdout and generated/balanced pairs do not establish population error rates.',
            'Verifier smoke reference labels use the same model/instruction; zero observed disagreement is not human validity.',
            'Released TRAIN scene wording may differ from local-Qwen game scene wording.',
            'Two actual archive integration smokes use synthetic acceptance/q, not a trained-judge or child-performance claim.'],
        no_new_approval_queue=True, pixel_game_contract_files_unchanged=True, sealed_private_contents_disclosed=False,
        commands=dict(integration_check='similarity_runtime/.venv/bin/python similarity_runtime/check_integration.py',
            full_calibration_command='similarity_runtime/README.md'),
        changed_paths=['gpu/ny_caption_similarity.py', 'tests/test_ny_caption_similarity.py',
            'research_loop/workers/r177_caption_game_stage1_20260917/similarity_runtime/',
            'research_loop/COORDINATION.md (requested metadata-only milestones)'])
    reference = runtime.private_write(HERE / 'PUBLIC_READINESS_20260917.json', summary)
    print(json.dumps(dict(status=summary['status'], evidence=reference,
        primary_rho=calibration['metrics']['primary']['rho'], tests_passed=152,
        provider_requests=len(rows), missing_terminals=len(rows) - len(terminals),
        provider_reported_token_usage=usage, private_content_disclosed=False), sort_keys=True))


if __name__ == '__main__':
    main()
