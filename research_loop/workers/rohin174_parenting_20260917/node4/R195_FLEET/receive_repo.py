"""Bind the existing safe repository tools to the exact new node4 slot5 life."""

import json
from pathlib import Path
import shutil
import sys
import time

from math_c import HOME, WALL, read, require, sha, write


ENVIRONMENT = (
    'This is a byte-pinned read-only repository snapshot and a private immutable proposal workspace. '
    'During ACT, use one literal line: repo_list . or repo_read relative/path.py 0 or repo_action followed by '
    'JSON with action note/propose/workspace_read, path, and content for writes. One action per response. '
    'There is no child code/test execution, shell, network, GPU, credentials, merge, or live repository modification. '
    'A proposal is not an applied patch or a passing test. Only actual tool receipts establish operations. '
)
SNAPSHOT_SHA = '9dbbaccfbe8597bd092fca66f9f027c89351825ec7825dbb552e91cb3f9b9a59'


def bind_transport(root, source, trial):
    require(root.name == 'SCALE_physical5' and trial == 'R203_NODE4_5_REPO_TRACE_B', 'exact_REPO_TRACE_B')
    snapshot = root / 'repository_snapshot'
    manifest_path = snapshot / 'MANIFEST.json'
    require(sha(manifest_path) == SNAPSHOT_SHA, 'exact_existing_safe_snapshot')
    tools_path = source / 'research_loop/workers/rohin183_repo_learning_20260917'
    tools_path.mkdir(parents=True, exist_ok=True)
    for name in ('tools.py', 'safe_snapshot.py'):
        shutil.copyfile(HOME / 'repo_dependencies' / name, tools_path / name)
    sys.path.insert(0, str(source))
    from research_loop.workers.rohin183_repo_learning_20260917 import tools
    settings = dict(schema='R183_REPO_TOOLS_V1', root=str(root / 'life'), snapshot=str(snapshot),
        snapshot_manifest=dict(path=str(manifest_path), sha256=SNAPSHOT_SHA),
        workspace=str(root / 'workspace'), receipts=str(root / 'tool_receipts'), hard_end_unix=WALL)
    inventory = tools.manifest(settings)
    for name in ('workspace', 'tool_receipts'):
        (root / name).mkdir(mode=0o700, exist_ok=True)
    write(root / 'TOOLS.json', settings)
    text = (HOME / 'repo_dependencies/repo_c_bridge.py').read_text()
    require(text.count("'R202_REPO_C_node2_clone1'") == 1 and "origin['record_index'] > 5846" in text,
        'existing_bridge_exact_binding_sites')
    text = text.replace("'R202_REPO_C_node2_clone1'", repr(trial))
    text = text.replace("origin['record_index'] > 5846", "type(origin['record_index']) is int and origin['record_index'] >= config['first_new_record']")
    text = text.replace('    sequence = 0\n',
        "    sequence = max((int(item.stem.split('_')[1]) for item in Path(settings['receipts']).glob('ACTION_*.json')), default=-1) + 1\n")
    compile(text, str(root / 'math_c_bridge.py'), 'exec')
    (root / 'math_c_bridge.py').write_text(text)
    (source / 'gpu/r184_cpu_bridge.py').write_text(text)
    smoke = root / 'repository_smoke_builder_only'
    for name in ('life/stream/inbox', 'workspace', 'receipts'):
        (smoke / name).mkdir(parents=True, mode=0o700)
    synthetic = dict(settings, root=str(smoke / 'life'), workspace=str(smoke / 'workspace'), receipts=str(smoke / 'receipts'))
    origin = dict(actor='child', split='TRAIN', record_index=0, record_sha256='0' * 64, synthetic_builder_test=True)
    target = 'gpu/orch_r125_continual_native.py'
    require(target in inventory['files'], 'real_manifest_approved_source_file')
    references = [tools.execute(synthetic, action, origin, sequence) for sequence, action in enumerate((
        dict(action='list', path='gpu'), dict(action='read', path=target, offset=0),
        dict(action='propose', path='synthetic_probe.md', content='Builder receiving probe, not applied and not child-authored.')))]
    receipt = read(smoke / 'receipts/ACTION_000001.json')
    require(receipt['source_sha256'] == inventory['files'][target]['sha256'] and receipt['returned_bytes'] > 0, 'real_read_bytes_match_manifest')
    try:
        tools.execute(synthetic, dict(action='read', path='../outside'), origin, 3)
    except ValueError:
        denied = True
    else:
        denied = False
    require(denied, 'repository_path_escape_denied')
    from organism_v6.orch_r125_plain_context import event_message
    from organism_v6.orch_r124_train_history import TrainEvent
    message = next(read(path) for path in (smoke / 'life/stream/inbox').glob('*.json')
        if '"action":"read"' in read(path)['text'])
    text = 'Tool: ' + message['text']
    event = TrainEvent(event_id='builder:receiving', episode_id='builder', source_id='builder:tool',
        source_sha256=sha(smoke / 'receipts/ACTION_000001.json'), actor='environment', phase='feedback',
        text=text, split='TRAIN', origin='TRAIN_COLLECTION')
    require(event_message(event) == dict(role='user', content=text), 'real_repository_feedback_visible_masked_user_context')
    write(root / 'REPOSITORY_RECEIVING.json', dict(status='PASS', observed_unix=time.time(),
        actual_list_read_private_proposal=True, escape_denied=True, code_execution=False, child_success_claim=False,
        snapshot_manifest_sha256=SNAPSHOT_SHA, snapshot_files=len(inventory['files']), references=references,
        environment_confound='Local existing safe snapshot differs from node2 REPO-C manifest; fixed C2 source is unchanged'))


if __name__ == '__main__':
    import r203_receive
    r203_receive.prepare(5)
