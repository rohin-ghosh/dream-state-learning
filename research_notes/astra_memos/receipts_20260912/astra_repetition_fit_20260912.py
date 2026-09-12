from dataclasses import asdict
import datetime
import json
import math
import os
from pathlib import Path
import subprocess
import sys

from organism_v6 import fundamental_repetition_corpus as repetition
from organism_v6 import rulegame_parenting_diagnostic as base
from organism_v6 import train_adapter_v3 as trainer
from gpu.astra_mini_sudoku_diagnostic import check_free

ROOT = Path.home() / 'astra_diagnostics/astra_fundamental_repetition_20260912_attempt1'
CELLS = {'teach_short': '0', 'control_short': '1', 'teach_long': '2', 'control_long': '3'}

def commands(cell, model):
    view = cell.split('_')[1]
    recipe = repetition.RECIPES[view]
    return [sys.executable, '-B', '-m', 'organism_v6.train_adapter_v3',
        '--corpus', str(ROOT / (cell + '.json')), '--out', str(ROOT / 'cells' / cell / 'fit' / 'adapter'),
        '--model', model, '--rank', '8', '--alpha', '16', '--dropout', '0.05', '--lr', '0.0003',
        '--epochs', '4', '--seed', '0', '--batch-size', str(recipe['batch_size']),
        '--grad-accum', str(recipe['grad_accum']), '--no-pack', '--no-eos',
        '--max-len', '2048', '--overflow', 'truncate']

def verify():
    plan = base.read(ROOT / 'fit_plan.json')
    assert base.digest(ROOT / 'fit_plan.json') == base.read(ROOT / 'fit_plan.sha256.json')['sha256']
    assert plan['source'] == str(base.REPO) and plan['script_sha256'] == base.digest(__file__)
    manifest = base.read(ROOT / 'manifest.json')
    assert base.digest(ROOT / 'manifest.json') == plan['material_manifest_sha256']
    assert manifest['source_code_sha256'] == dict(exporter=base.digest(repetition.__file__), trainer=base.digest(trainer.__file__))
    assert base.model_hashes(plan['model']) == plan['model_files']
    for cell in CELLS:
        assert base.digest(ROOT / (cell + '.json')) == manifest['output_sha256'][cell + '.json']
        assert asdict(trainer.config_from_args(trainer.build_parser().parse_args(commands(cell, plan['model'])[4:]))) == plan['configs'][cell]
    return plan

def fit(cell):
    assert cell in CELLS
    plan = verify()
    device = CELLS[cell]
    target = ROOT / 'cells' / cell
    assert not (target / 'fit').exists()
    assert plan['lease_end'] - datetime.datetime.now(datetime.timezone.utc).timestamp() > 21600 + 1800
    gpu, xml = check_free(device)
    (target / 'fit').mkdir()
    with (target / 'fit' / 'gpu.xml').open('x') as output:
        output.write(xml)
    result = base.supervise(target, dict(plan, device=device), target / 'fit' / 'worker', commands(cell, plan['model']))
    adapter = target / 'fit' / 'adapter'
    manifest = base.read(adapter / 'train_manifest.json')
    view = cell.split('_')[1]
    assert (adapter / 'DONE').is_file() and not (adapter / 'EMPTY_CORPUS').exists()
    assert manifest['config'] == plan['configs'][cell] and manifest['steps'] == 80 and manifest['epochs_run'] == 4
    assert manifest['micro_batches'] == (1280 if view == 'short' else 320)
    assert manifest['nonfinite_batches'] == 0 and math.isfinite(manifest['final_loss'])
    assert manifest['corpus']['sha256'] == base.digest(ROOT / (cell + '.json'))
    assert manifest['corpus']['n_items'] == manifest['corpus']['n_encoded'] == (1280 if view == 'short' else 80)
    assert manifest['tokens']['total'] == 72272 and manifest['tokens']['target'] == 14592
    assert manifest['train_tokens_seen'] == 289088 and manifest['packing']['mode'] == 'one_item_per_sequence'
    assert all(manifest['truncation'][key] == 0 for key in ('items_truncated', 'context_tokens_dropped', 'target_tokens_dropped', 'items_split'))
    assert manifest['truncation']['max_segment_tokens'] == (61 if view == 'short' else 976)
    receipt = dict(status='FIT_COMPLETE_PENDING_READOUT', cell=cell, device=device, gpu=gpu,
        adapter=str(adapter), adapter_files=base.tree_hashes(adapter), manifest=manifest, supervised=result)
    base.write_json(target / 'fit' / 'result.json', receipt)
    print(json.dumps(dict(cell=cell, status=receipt['status'], supervised=result, final_loss=manifest['final_loss']), sort_keys=True), flush=True)

stage = sys.argv[1]
if stage == 'prepare':
    reference = base.read(ROOT / 'main_native_reference_check.json')
    original = base.read(Path.home() / 'astra_diagnostics/astra_fundamental_teaching_20260912_attempt1/plan.json')
    assert reference['exact_reference_counts'] and reference['source'] == str(base.REPO)
    assert reference['manifest_sha256'] == 'eba01c800d4bf6e9772cefec413be8c6f41b26f0d6e9ab0ced66862d7f348160'
    plan = dict(model=reference['model'], model_files=reference['model_files'], lease_end=original['lease_end'],
        source=str(base.REPO), script_sha256=base.digest(__file__), material_manifest_sha256=reference['manifest_sha256'],
        configs={cell: asdict(trainer.config_from_args(trainer.build_parser().parse_args(commands(cell, reference['model'])[4:]))) for cell in CELLS},
        seed=0, devices=CELLS, role='LEVEL0_AUTHORED_REPETITION_NOT_CHILD_SLEEP',
        expected_updates=80, expected_input_tokens_seen=289088, expected_target_tokens_seen=58368,
        comparison='continuous context versus resets at matched repeated exposures and optimizer group schedule')
    assert not (ROOT / 'fit_plan.json').exists() and not (ROOT / 'cells').exists()
    base.write_json(ROOT / 'fit_plan.json', plan)
    base.write_json(ROOT / 'fit_plan.sha256.json', dict(sha256=base.digest(ROOT / 'fit_plan.json')))
    (ROOT / 'cells').mkdir()
    for cell in CELLS:
        (ROOT / 'cells' / cell).mkdir()
    verify()
    print(json.dumps(dict(status='FOUR_REPETITION_FITS_PREPARED', plan_sha256=base.digest(ROOT / 'fit_plan.json')), sort_keys=True))
elif stage == 'launch':
    plan = verify()
    for cell, device in CELLS.items():
        target = ROOT / 'cells' / cell
        assert not (target / 'launch').exists() and not (target / 'fit').exists()
        logs = target / 'launch'
        logs.mkdir()
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'fit', cell]
        environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONPATH=str(base.REPO),
            PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', OMP_NUM_THREADS='1')
        with (logs / 'controller.log').open('xb') as output:
            process = subprocess.Popen(command, cwd=base.REPO, env=environment, stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        receipt = dict(status='CONTROLLER_LAUNCHED_GPU_REQUIRES_INNER_VACANCY_CHECK', node=3, cell=cell,
            device=device, pid=process.pid, started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            source=str(base.REPO), script_sha256=base.digest(__file__), command=command,
            fit_plan_sha256=base.digest(ROOT / 'fit_plan.json'), continuous_reservation=True)
        base.write_json(logs / 'launch.json', receipt)
        print(json.dumps(receipt, sort_keys=True), flush=True)
elif stage == 'fit':
    fit(sys.argv[2])
else:
    raise ValueError('unsupported stage')
