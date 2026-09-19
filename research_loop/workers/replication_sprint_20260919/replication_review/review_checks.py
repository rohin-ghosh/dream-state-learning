"""Offline independent checks; all outputs stay in this review directory."""

import argparse
import ast
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import time
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
CANDIDATE_ROOT = HERE.parent / 'replication'
REPO = HERE.parents[3]
sys.path.insert(0, str(CANDIDATE_ROOT))
import construct_candidate
import dispatch_sampling
import execution
import prepare_executable
import report_sampling
import sealed_runner
import test_candidate
import test_custody_repair
import test_execution


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RECEIPT = read(CANDIDATE_ROOT / 'ORIGINALS_RECEIPT.json')
CANDIDATE = read(CANDIDATE_ROOT / 'C2_SAMPLING_CANDIDATE_V2.json')
REGISTRY = execution.registry(CANDIDATE, RECEIPT)
CONTRACT_PATH = REPO / 'research_loop/workers/rohin232_age_probe_20260918/contract.py'
RUNNER_PATH = REPO / 'research_loop/workers/post_recovery_age_queue_20260918/runner.py'
EPOCH_PATH = REPO / 'research_loop/workers/post_recovery_age_queue_20260918/epoch.py'
CONTRACT = load_module('review_original_contract', CONTRACT_PATH)
EPOCH = load_module('review_original_epoch', EPOCH_PATH)


class FakeBackend:
    def __init__(self, identity):
        self.identity = deepcopy(identity)
        self.seeds = []
        self.requests = []

    def seed(self, seed):
        self.seeds.append(seed)

    def verify(self):
        return {key: deepcopy(self.identity[key]) for key in (
            'base_sha256', 'adapter_state_sha256', 'all_parameters_frozen')}

    def generate(self, messages, max_new_tokens):
        self.requests.append(deepcopy(messages))
        return dict(messages=deepcopy(messages), raw='Synthetic reviewer caption.',
            token_ids=[17] * max_new_tokens, prompt_tokens=10,
            terminal=False, truncated=True)


def fake_original(root, row, seeds):
    module = ModuleType('review_original_runner')
    backend = FakeBackend(row['identity'])
    scenes = sorted({cell['contest_id'] for cell in row['cell_budgets']})
    store = {
        str(root / 'GAME_MANIFEST.json'): dict(contests=[dict(contest_id=scene,
            canonical_scene='Synthetic reviewer scene ' + str(scene)) for scene in scenes]),
        str(root / 'sources/CAPTURE.json'): dict(sources=[row['source_age']]),
    }

    def write(path, value):
        store[str(path)] = deepcopy(value)

    def wait(path, deadline):
        if Path(path).name == 'JUDGE_LOADED.json':
            return dict(judge_epoch_sha256=construct_candidate.ADOPTED_EPOCH,
                binding=dict(adapter_sha256=EPOCH.ADAPTER_SHA),
                diagnostic_epoch_sha256=CANDIDATE['sampling_epoch_sha256'])
        request = store[str(path).replace('.result.json', '.request.json')]
        return dict(request_sha256=CONTRACT.digest(request),
            judge_epoch_sha256=construct_candidate.ADOPTED_EPOCH,
            diagnostic_epoch_sha256=CANDIDATE['sampling_epoch_sha256'],
            feedback='Synthetic feedback, unchanged between runs.', results=[], new_pixels=0)

    def verify(config):
        return Path(config['root']), config['identity']

    epoch = SimpleNamespace(**{name: getattr(EPOCH, name) for name in dir(EPOCH)
        if not name.startswith('__')})
    epoch.SEEDS = tuple(seeds)
    module.__dict__.update(Path=Path, time=time, os=SimpleNamespace(
        getpid=lambda: 1, environ={'CUDA_VISIBLE_DEVICES': 'synthetic-fixture'}),
        hashlib=hashlib, data=SimpleNamespace(require=construct_candidate.require),
        contract=CONTRACT, epoch=epoch, runtime=SimpleNamespace(
            Backend=lambda source, path: backend, read=lambda path: deepcopy(store[str(path)]),
            write=write, wait=wait), verify=verify)
    tree = ast.parse(RUNNER_PATH.read_text())
    selected = ast.Module(body=[node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == 'player'], type_ignores=[])
    exec(compile(selected, str(RUNNER_PATH), 'exec'), module.__dict__)
    return module, backend, store


def completion_fixture():
    config = test_execution.config_fixture(REGISTRY, REGISTRY['jobs'][0])
    source = RECEIPT['rows']['base']
    scenes = sorted({cell['contest_id'] for cell in source['cell_budgets']})
    cells = [dict(contest_id=scene, seed=seed, generated_tokens=1024,
        status='COMPLETE_FIXED_ACTUAL_TOKEN_BUDGET')
        for scene in scenes for seed in execution.SEEDS]
    common = dict(diagnostic_epoch_sha256=config['diagnostic_epoch_sha256'],
        judge_epoch_sha256=construct_candidate.ADOPTED_EPOCH,
        source_age=None, parent_tokens=0)
    loaded = dict(common, identity=deepcopy(source['identity']), snapshot_context_used=False)
    complete = dict(common, actual_generated_tokens=6144, cells=cells, training_updates=0,
        unchanged_identity=deepcopy(source['unchanged_identity']))
    return config, complete, loaded


class IndependentTests(unittest.TestCase):
    def test_local_original_functions_match_receiving_source_pins(self):
        for path in (CONTRACT_PATH, RUNNER_PATH, EPOCH_PATH):
            relative = str(path.relative_to(REPO))
            self.assertEqual(sha(path), RECEIPT['rows']['base']['source_closure'][relative])

    def test_declared_budget_and_non_lineage_identity(self):
        self.assertEqual(CANDIDATE['sampling_epoch']['sampling_seeds'], [23301, 23302])
        self.assertEqual(CANDIDATE['runtime_estimate']['generated_tokens'], 18432)
        self.assertEqual(len(REGISTRY['jobs']), 3)
        self.assertFalse(REGISTRY['independent_training_lineages'])

    def test_preregistration_and_actual_scene_ids_are_bound(self):
        self.assertEqual(sha(REPO / execution.PREREGISTRATION['repo_relative']),
            execution.PREREGISTRATION['sha256'])
        for job in REGISTRY['jobs']:
            actual = sorted({cell['contest_id'] for cell in RECEIPT['rows'][job['arm']]['cell_budgets']})
            self.assertEqual(actual, list(execution.SCENE_IDS))

    def test_original_player_and_sealed_wrapper_match_model_facing_behavior(self):
        for job in REGISTRY['jobs']:
            row = RECEIPT['rows'][job['arm']]
            config = test_execution.config_fixture(REGISTRY, job)
            with tempfile.TemporaryDirectory(dir=HERE) as directory:
                root = Path(directory)
                config['root'] = str(root)
                config['deadline_unix'] = time.time() + 600
                baseline, baseline_backend, baseline_store = fake_original(root, row, execution.SEEDS)
                wrapped, wrapped_backend, wrapped_store = fake_original(root, row, EPOCH.SEEDS)
                baseline.player(config)
                function = sealed_runner.wrapped_role(wrapped, config, 'player')
                with patch.object(sealed_runner, 'verify_public'):
                    function(config)
                self.assertEqual(baseline_backend.requests, wrapped_backend.requests)
                self.assertEqual(baseline_backend.seeds, [23301, 23302] * 3)
                self.assertEqual(baseline_backend.seeds, wrapped_backend.seeds)
                output = root / 'players' / config['identity']['condition'] / 'COMPLETE.json'
                before, after = baseline_store[str(output)], wrapped_store[str(output)]
                for result in (before, after):
                    self.assertEqual(result['actual_generated_tokens'], 6144)
                    self.assertEqual(len(result['cells']), 6)
                    self.assertTrue(all(cell['generated_tokens'] == 1024 for cell in result['cells']))
                self.assertEqual(after['diagnostic_epoch_sha256'], CANDIDATE['sampling_epoch_sha256'])
                self.assertEqual(wrapped.epoch.SEEDS, EPOCH.SEEDS)

    def test_valid_completion_fixture_passes(self):
        dispatch_sampling.validate_completion(*completion_fixture())

    def test_original_judge_keeps_extraction_feedback_and_private_panel_scoring(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            root = Path(directory)
            for name in ('queue', 'epoch', 'players/REVIEW_FIXTURE'):
                (root / name).mkdir(parents=True)
            config = test_execution.config_fixture(REGISTRY, REGISTRY['jobs'][0])
            config.update(root=str(root), epoch_root=str(root / 'epoch'),
                deadline_unix=time.time() + 30)
            config['identity']['condition'] = 'REVIEW_FIXTURE'
            scene = SimpleNamespace(contest_id='review-scene', canonical_scene='Synthetic scene')
            manifest = SimpleNamespace(contests=[scene])
            panels = [dict(selected=[dict(scene=scene.canonical_scene,
                caption='Private synthetic reference ' + str(index)) for index in range(64)],
                scores=list(range(64)))]
            panel_path = root / 'epoch/PRIMARY_PANELS.private.json'
            panel_path.write_text(json.dumps(panels))
            binding = dict(primary_config_sha256=config['primary_config_sha256'],
                selected_strings_sha256=EPOCH.digest([row['selected'] for row in panels]),
                adapter_sha256=EPOCH.ADAPTER_SHA, primary_panels_sha256=sha(panel_path))
            store = {
                str(root / 'GAME_MANIFEST.json'): {},
                str(root / 'assets/RULE.json'): dict(relevance_threshold=0.5),
                str(root / 'assets/pixel_config.json'): {},
                str(root / 'judge/REFERENCE_PANELS.private.json'): panels,
                str(panel_path): panels,
                str(root / 'epoch/JUDGE_EPOCH.json'): binding,
            }
            (root / 'epoch/JUDGE_EPOCH.json').write_text(json.dumps(binding))
            (root / 'players/REVIEW_FIXTURE/COMPLETE.json').write_text('{}')
            requests = []
            for position, stage in enumerate(('THINK', 'ACT')):
                path = root / 'queue' / (str(position) + '.request.json')
                request = dict(identity=dict(condition='REVIEW_FIXTURE', seed=23301,
                    contest_id=scene.contest_id), raw='A synthetic caption.',
                    raw_sha256=hashlib.sha256(b'A synthetic caption.').hexdigest(),
                    origin=dict(stage=stage, text_sha256=hashlib.sha256(b'A synthetic caption.').hexdigest()),
                    diagnostic_epoch_sha256=CANDIDATE['sampling_epoch_sha256'])
                path.write_text(json.dumps(request))
                store[str(path)] = request
                requests.append(request)
            original = ModuleType('review_original_judge')
            calls = dict(extraction=[], builds=[], submits=[])

            def extract(raw, scenes, **options):
                calls['extraction'].append(dict(raw=raw, scenes=deepcopy(scenes), options=options))
                return [dict(captions=['A synthetic caption.'])], {'fixture': True}

            def submit(contest, caption):
                calls['submits'].append((contest, caption))
                return dict(rank=25, accepted=True, status='new_pixel', relevance_score=1.0, cached=False)

            def build(*arguments, **options):
                calls['builds'].append(options)
                return SimpleNamespace(submit_caption=submit)

            def write(path, value):
                store[str(path)] = deepcopy(value)

            original.__dict__.update(Path=Path, time=time, hashlib=hashlib,
                os=SimpleNamespace(getpid=lambda: 1), contract=CONTRACT, epoch=EPOCH,
                data=SimpleNamespace(require=construct_candidate.require, file_ref=lambda path: {}),
                probe=SimpleNamespace(panel_scores=lambda rows, game: {scene.canonical_scene: rows[0]['scores']}),
                runtime=SimpleNamespace(read=lambda path: deepcopy(store[str(path)]), write=write),
                extract_batches=extract, verify=lambda config: (root, config['identity']))
            tree = ast.parse(RUNNER_PATH.read_text())
            selected = ast.Module(body=[node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == 'judge'], type_ignores=[])
            exec(compile(selected, str(RUNNER_PATH), 'exec'), original.__dict__)
            imports = {
                'gpu.ny_caption_game': dict(DevelopmentManifest=SimpleNamespace(from_mapping=lambda value: manifest)),
                'gpu.ny_caption_pixels': dict(PixelConfig=lambda **values: values),
                'gpu.ny_caption_relative_game': dict(build_game=build),
                'gpu.ny_caption_scalar_judge': dict(ScalarJudge=lambda *args, **kwargs: SimpleNamespace(reference={})),
                'gpu.ny_caption_similarity': dict(FrozenCPUEncoder=lambda *args, **kwargs: object()),
            }
            modules = {}
            for name, attributes in imports.items():
                module = ModuleType(name)
                module.__dict__.update(attributes)
                modules[name] = module
            function = sealed_runner.wrapped_role(original, config, 'judge')
            with patch.object(sealed_runner, 'verify_public'), patch.dict(sys.modules, modules):
                function(config)
            self.assertEqual([row['options']['explicit_candidates_only']
                for row in calls['extraction']], [True, False])
            self.assertEqual(calls['builds'][0]['top_k'], 50)
            self.assertEqual(calls['builds'][0]['relevance_threshold'], 0.5)
            self.assertEqual(len(calls['builds']), 1)
            for position, request in enumerate(requests):
                result = store[str(root / 'queue' / (str(position) + '.result.json'))]
                self.assertEqual(result['request_sha256'], CONTRACT.digest(request))
                self.assertEqual(result['diagnostic_epoch_sha256'], CANDIDATE['sampling_epoch_sha256'])
                self.assertEqual(result['judge_epoch_sha256'], EPOCH.digest(binding))
                self.assertEqual(result['feedback'],
                    'Caption 1: rank 25 of 65; accepted True; novelty new_pixel; relevance 1.0; cached False.')
                self.assertNotIn('Private synthetic reference', json.dumps(result))

    def test_misbound_weights_are_rejected(self):
        config, complete, loaded = completion_fixture()
        loaded['identity']['base_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            dispatch_sampling.validate_completion(config, complete, loaded)

    def test_cpu_repreparation_rejects_all_attempt_markers(self):
        markers = ('PREPARED.json', 'BLOCK_LAUNCH.json', 'BLOCK_FAILED.json',
            'PROOFS_COMPLETE.json', 'GPU_REVIEW.json', 'BLOCK_COMPLETE.json',
            'jobs/fixture/DISPATCH_INTENT.json', 'jobs/fixture/COMPLETION_VERIFIED.json',
            'jobs/fixture/view/player_run_STARTED.json',
            'jobs/fixture/view/judge_proof_FAILED.json',
            'jobs/fixture/view/player_CUSTODY_PROOF.json',
            'jobs/fixture/player_run.log', 'jobs/fixture/view/queue/test.request.json',
            'jobs/fixture/view/queue/test.result.json')
        for marker in markers:
            with self.subTest(marker=marker), tempfile.TemporaryDirectory(dir=HERE) as directory:
                root = Path(directory)
                execution.write_once(root / 'SOURCE_FREEZE.json', {'fixture': True})
                execution.write_once(root / 'REGISTRY.json', REGISTRY)
                path = root / marker
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('{}')
                with self.assertRaises(ValueError):
                    prepare_executable.unlaunched_inventory(root)
                self.assertTrue(path.exists())

    def test_manifest_backbone_hash_drift_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            path = Path(directory) / 'base.json'
            path.write_text('{}')
            primary = dict(base_model=dict(path=str(path), sha256='0' * 64))
            with self.assertRaisesRegex(ValueError, 'bound_file'):
                prepare_executable.backbone_directory(primary)

    def test_readable_empty_private_placeholder_is_not_a_denial(self):
        with tempfile.TemporaryDirectory(dir=HERE) as directory:
            path = Path(directory) / 'SYNTHETIC_PRIVATE_PLACEHOLDER.json'
            path.write_bytes(b'')
            path.chmod(0o644)
            self.assertFalse(sealed_runner.denial(path))
            path.write_bytes(b'Synthetic reviewer data, not a private panel.')
            self.assertFalse(sealed_runner.denial(path))
            self.assertTrue(sealed_runner.denial(Path(directory) / 'missing'))

    def test_partial_result_retains_denominators_without_full_budget_score(self):
        observation = partial_reporting_observation()
        self.assertTrue(observation['public_table_available'])
        self.assertEqual(observation['rows'], 6)
        first = observation['first_seed']
        self.assertEqual(first['status'], 'INCOMPLETE')
        self.assertIsNone(first['actual_generated_tokens'])
        self.assertEqual(first['incomplete_present_cells'], 1)
        self.assertEqual(first['missing_cells'], 2)
        self.assertEqual(first['complete_cells_only']['generated_tokens'], 0)
        self.assertIsNone(first['complete_cells_only']['accept_rate'])
        partial = next(cell for cell in first['cells']
            if cell['status'] == 'INCOMPLETE_ZERO_TOKEN_GENERATION')
        self.assertEqual(partial['observed_generated_tokens'], 128)
        self.assertEqual(partial['metrics']['generated_tokens'], 128)
        self.assertEqual(partial['sha256'], 'synthetic')


def mutation_observations():
    outcomes = []
    for field in ('tokenizer_backend_sha256', 'chat_template_sha256', 'decoder', 'library_versions'):
        config, complete, loaded = completion_fixture()
        loaded['identity'][field] = {'changed': True} if isinstance(loaded['identity'][field], dict) else '0' * 64
        try:
            dispatch_sampling.validate_completion(config, complete, loaded)
        except (ValueError, KeyError) as error:
            outcomes.append(dict(mutation=field, rejected=True, error=str(error)))
        else:
            outcomes.append(dict(mutation=field, rejected=False,
                concern='Protocol-drift mutation accepted by completion validator'))
    config, complete, loaded = completion_fixture()
    for cell in complete['cells']:
        cell['contest_id'] = 'unbound-scene-' + str(cell['contest_id'])
    try:
        dispatch_sampling.validate_completion(config, complete, loaded)
    except (ValueError, KeyError) as error:
        outcomes.append(dict(mutation='unbound_scene_ids', rejected=True, error=str(error)))
    else:
        outcomes.append(dict(mutation='unbound_scene_ids', rejected=False,
            concern='Any three scene IDs accepted instead of pinned scene set'))
    return outcomes


def partial_reporting_observation():
    root = Path(REGISTRY['root'])
    prepared = dict(registry_sha256='synthetic', jobs=[dict(job_id=job['job_id'],
        config_sha256='synthetic') for job in REGISTRY['jobs']])
    files = {root / 'REGISTRY.json': REGISTRY, root / 'PREPARED.json': prepared}
    for job in REGISTRY['jobs']:
        config = test_execution.config_fixture(REGISTRY, job)
        config['condition'] = config['identity']['condition']
        files[Path(job['root']) / 'CONFIG.json'] = config
    first = files[Path(REGISTRY['jobs'][0]['root']) / 'CONFIG.json']
    partial_path = Path(first['root']) / 'players' / first['condition'] / (
        execution.SCENE_IDS[0] + '_23301/RESULT.json')
    files[partial_path] = dict(diagnostic_epoch_sha256=REGISTRY['diagnostic_epoch_sha256'],
        contest_id=execution.SCENE_IDS[0], seed=23301,
        status='INCOMPLETE_ZERO_TOKEN_GENERATION', generated_tokens=128, budget=1024,
        events=[dict(origin={'stage': 'THINK'}, score={'results': []})])
    try:
        with patch.object(execution, 'read', side_effect=lambda path: deepcopy(files[path])), \
                patch.object(execution, 'regular'), patch.object(execution, 'sha', return_value='synthetic'), \
                patch.object(Path, 'exists', autospec=True, side_effect=lambda path: path == partial_path):
            result = report_sampling.report(root)
    except Exception as error:
        return dict(fixture='authentic_contract_partial_status_128_of_1024_tokens',
            public_table_available=False, error_type=type(error).__name__, error=str(error),
            concern='A present partial cell prevents reporting all six source/seed denominators')
    return dict(fixture='authentic_contract_partial_status_128_of_1024_tokens',
        public_table_available=True, rows=len(result['rows']),
        first_seed_status=result['rows'][0]['status'], first_seed=result['rows'][0])


def pins(seal_path):
    paths = list(CANDIDATE_ROOT.glob('*.py')) + [
        CANDIDATE_ROOT / 'C2_SAMPLING_CANDIDATE_V2.json',
        CANDIDATE_ROOT / 'ORIGINALS_RECEIPT.json', CONTRACT_PATH, RUNNER_PATH, EPOCH_PATH,
        REPO / execution.PREREGISTRATION['repo_relative'],
        REPO / 'research_loop/workers/rohin232_age_probe_20260918/runtime.py',
        REPO / 'research_loop/workers/post_reboot_probe_queue_20260919/version_v4_rebind/SOURCE_FREEZE_V4_REBIND.json']
    for name in ('EXECUTABLE_SOURCE_FREEZE.json', 'EXECUTION_REGISTRY.json'):
        path = CANDIDATE_ROOT / name
        if path.exists():
            paths.append(path)
    if seal_path.exists() and seal_path not in paths:
        paths.append(seal_path)
    for name in ('CPU_CUSTODY_REPAIR_V2.json', 'CPU_CUSTODY_REGISTRY_V2.json'):
        path = CANDIDATE_ROOT / name
        if path.exists():
            paths.append(path)
    return {str(path.relative_to(REPO)): sha(path) for path in sorted(paths)}


def seal_observation(path):
    if not path.exists():
        return dict(present=False)
    seal = read(path)
    mismatches = []
    for group in ('files', 'inputs', 'cpu_test_evidence'):
        for name, expected in seal[group].items():
            source = CANDIDATE_ROOT / name
            actual = sha(source) if source.exists() else None
            if actual != expected:
                mismatches.append(dict(group=group, path=name, declared=expected, actual=actual))
    return dict(present=True, path=str(path.relative_to(REPO)), sha256=sha(path), mismatches=mismatches,
        exact_runtime_file_set=set(seal['files']) == set(execution.RUNTIME_NAMES),
        current_source_and_tests_match=not mismatches,
        preregistration_matches=seal['preregistration'] == execution.PREREGISTRATION,
        diagnostic_epoch_matches=seal['diagnostic_epoch_sha256'] == CANDIDATE['sampling_epoch_sha256'],
        actual_receiving_proof=seal['actual_receiving_proof'], dispatch_performed=seal['dispatch_performed'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-freeze', default='EXECUTABLE_SOURCE_FREEZE.json')
    args = parser.parse_args()
    seal_path = CANDIDATE_ROOT / args.source_freeze
    if seal_path.parent != CANDIDATE_ROOT:
        raise ValueError('review_only_a_named_candidate_source_freeze')
    before = pins(seal_path)
    test_execution.HERE = HERE
    test_custody_repair.HERE = HERE
    suite = unittest.TestSuite()
    for module in (test_candidate, test_execution, test_custody_repair, sys.modules[__name__]):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    mutations = mutation_observations()
    partial_reporting = partial_reporting_observation()
    after = pins(seal_path)
    report = dict(observed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        scope='CPU_ONLY_NO_MODELS_NO_DISPATCH_NO_SHARED_WRITES',
        tests_run=result.testsRun, test_failures=len(result.failures), test_errors=len(result.errors),
        tests_passed=result.wasSuccessful(), candidate_stable_during_checks=before == after,
        mutation_observations=mutations, partial_reporting_observation=partial_reporting,
        executable_seal=seal_observation(seal_path),
        pins_before=before, pins_after=after,
        temporary_directory_redirect='test_execution.HERE and test_custody_repair.HERE -> replication_review only')
    suffix = time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
    for path, content in ((HERE / 'CPU_REVIEW_TESTS.log', stream.getvalue()),
            (HERE / 'CPU_REVIEW_RECEIPT.json', json.dumps(report, indent=2, sort_keys=True) + '\n')):
        if path.exists():
            archive = path.with_name(path.stem + '_BEFORE_' + suffix + path.suffix)
            with archive.open('x') as archive_stream:
                archive_stream.write(path.read_text())
        path.write_text(content)
    print(stream.getvalue())
    print(json.dumps({key: value for key, value in report.items() if not key.startswith('pins_')}, indent=2))
    return 0 if result.wasSuccessful() and before == after else 1


if __name__ == '__main__':
    raise SystemExit(main())
