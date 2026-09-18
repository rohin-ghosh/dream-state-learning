"""Apply the pinned non-material rendering repair to an unlaunched clone."""

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from prepare_repo_c import ROOT, SOURCE, PYTHON, read, write, sha, require


def main():
    require(not (ROOT / 'STARTED.json').exists(), 'unlaunched_repo_source_only')
    repair = ROOT / 'tool_render_repair'
    manifest = read(repair / 'TOOL_FEEDBACK_REPAIR.json')
    require(manifest['schema'] == 'R202_TOOL_FEEDBACK_REPAIR_V1', 'specific_nonmaterial_repair')
    backup = repair / 'before'
    backup.mkdir()
    for entry in manifest['files']:
        name = entry['path']
        require(name in ('organism_v6/orch_r125_plain_context.py', 'tests/test_orch_r125_plain_context.py'), 'two_exact_repair_paths')
        require(sha(repair / name) == entry['after_sha256'], 'Jason_frozen_repair_bytes')
        target = SOURCE / name
        if target.exists():
            preserved = backup / name
            preserved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, preserved)
        shutil.copy2(repair / name, target)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
        PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', PYTHONPATH=os.pathsep.join((str(ROOT), str(SOURCE), str(SOURCE / 'tests'), str(ROOT / 'test_support'))))
    files = [str(SOURCE / name) for name in read(ROOT.parent / 'main_ready/READY.json')['files'] if name.startswith('tests/')]
    files.extend([str(SOURCE / 'tests/test_orch_r125_plain_context.py'),
        str(SOURCE / 'research_loop/workers/rohin183_repo_learning_20260917/test_tools.py'), str(ROOT / 'repo_receiving_checks.py')])
    with (repair / 'CPU.log').open('x') as output:
        result = subprocess.run([PYTHON, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', *files,
            '-k', 'not all_scaffolding_rows_skip_training_without_fabricating_progress'], cwd=SOURCE,
            env=environment, stdout=output, stderr=subprocess.STDOUT, timeout=180)
    require(result.returncode == 0, 'receiving_render_repair_regressions')
    finish()


def finish():
    require(not (ROOT / 'STARTED.json').exists(), 'unlaunched_repo_source_only')
    repair = ROOT / 'tool_render_repair'
    manifest = read(repair / 'TOOL_FEEDBACK_REPAIR.json')
    require(all(sha(SOURCE / entry['path']) == entry['after_sha256'] for entry in manifest['files']), 'tested_repair_still_pinned')
    require(' failed' not in (repair / 'CPU.log').read_text(), 'passing_preserved_test_log')
    sys.path.insert(0, str(SOURCE))
    from organism_v6.orch_r125_plain_context import event_message, replay_prefix
    from organism_v6.orch_r124_train_history import TrainEvent
    smoke = ROOT / 'repository_smoke_only_not_child'
    messages = [read(path) for path in (smoke / 'life/stream/inbox').glob('*.json')]
    actual = next(message for message in messages if '"action":"read"' in message['text'])
    text = 'Tool: ' + actual['text']
    event = TrainEvent(event_id='receiving:repo_read', episode_id='receiving', source_id='receiving:tool',
        source_sha256=sha(smoke / 'receipts/ACTION_000001.json'), actor='environment', phase='feedback',
        text=text, split='TRAIN', origin='TRAIN_COLLECTION')
    rendered = event_message(event)
    require(rendered == dict(role='user', content=text), 'actual_receiving_read_and_receipt_rendered')
    replay = replay_prefix([dict(role='system', content='synthetic'), dict(role='user', content='synthetic'), rendered],
        dict(system_prompt='synthetic', birth_prompt='synthetic'))
    require(replay[-1] == rendered, 'actual_receiving_read_and_receipt_replayed')
    count = int(re.search(r'(\d+) passed', (repair / 'CPU.log').read_text())[1])
    pins = {str(path.relative_to(SOURCE)): sha(path) for path in SOURCE.rglob('*.py')}
    proof = dict(status='PASS', observed_unix=time.time(), tests_run=count, synthetic_builder_test=True,
        real_pinned_repository_read=True, live_child_REQUEST_render_not_yet_claimed=True,
        actual_tool_text_sha256=__import__('hashlib').sha256(text.encode()).hexdigest(),
        actual_tool_content_and_receipt_visible=True, tool_role='user', target_creation=False,
        repair_manifest_sha256=sha(repair / 'TOOL_FEEDBACK_REPAIR.json'), log_sha256=sha(repair / 'CPU.log'),
        known_preexisting_test_deselected='test_all_scaffolding_rows_skip_training_without_fabricating_progress')
    write(ROOT / 'TOOL_RENDER_RECEIVING.json', proof)
    cpu = dict(passed=True, tests_run=count, source_pins=pins, log_sha256=sha(repair / 'CPU.log'),
        observed_unix=time.time(), tool_render_receiving_sha256=sha(ROOT / 'TOOL_RENDER_RECEIVING.json'))
    source = dict(read(ROOT / 'SOURCE.json'), source_pins=pins, tool_render_repair_sha256=proof['repair_manifest_sha256'])
    for target in (ROOT / 'CPU.json', ROOT / 'SOURCE.json', ROOT / 'control/RECEIVING_CPU.json'):
        target.rename(target.with_name('PRE_TOOL_RENDER_' + target.name))
    write(ROOT / 'CPU.json', cpu)
    write(ROOT / 'SOURCE.json', source)
    write(ROOT / 'control/RECEIVING_CPU.json', cpu)
    print(json.dumps(dict(proof, cpu_sha256=sha(ROOT / 'CPU.json'), source_sha256=sha(ROOT / 'SOURCE.json'))))


if __name__ == '__main__':
    main()
