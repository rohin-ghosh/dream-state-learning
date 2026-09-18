"""Read-only native progress capture and explicitly non-promotional handoffs."""

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time


REMOTE = '/localhome/local-rohing/orch_combined_l1_continual_20260915_attempt1'


def capture(root):
    documents = {}
    paths = ['INGEST_RECEIPTS/000000128.json', 'WINDOWS/000000128.json',
             'FULL_CHILD_HANDOFF.json', 'PREPARE.json', 'SOURCE_TRANSITION.json']
    paths += [f'{arm}/checkpoints/000000128/COMMIT.json' for arm in ('FULL', 'OFF')]
    handoff = json.loads((root / 'FULL_CHILD_HANDOFF.json').read_text())
    paths += [f'FULL/checkpoints/{handoff["updates"]:09d}/COMMIT.json']
    for name in dict.fromkeys(paths):
        data = (root / name).read_bytes()
        documents[name] = dict(sha256=hashlib.sha256(data).hexdigest(),
                               base64=base64.b64encode(data).decode())
    logs = {}
    for path in sorted(root.glob('*/RANK*_LOSSES_*.jsonl')):
        lines = path.read_text().splitlines()
        records = []
        for line in lines:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                break
        if not records:
            continue
        recent = records[-128:]
        elapsed = recent[-1]['finished_unix'] - recent[0]['finished_unix']
        updates = recent[-1]['update'] - recent[0]['update']
        logs[str(path)] = dict(rows=len(records), first=records[0], last=records[-1],
            recent_seconds_per_update=elapsed / updates if updates else None,
            timing_includes_any_boundary_waits=True)
    processes = []
    for folder in Path('/proc').glob('[0-9]*'):
        try:
            arguments = (folder / 'cmdline').read_bytes().replace(b'\0', b' ').decode()
            if '--root ' + str(root) in arguments and 'orch_combined_l1_continual_' in arguments:
                processes.append(dict(pid=int(folder.name), cmdline=arguments,
                    start_ticks=int((folder / 'stat').read_text().rsplit(')', 1)[1].split()[19])))
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    return dict(schema='COMBINED_CONTINUAL_NATIVE_RECEIPT_V1', captured_unix=time.time(),
        root=str(root), logs=logs, processes=processes, documents=documents,
        held_outputs_accessed=False, native_calls=0)


def publish(repository, output):
    command = ('/localhome/local-rohing/v2/venv/bin/python -B -c ' +
               shlex.quote(Path(__file__).read_text()) + ' --remote-root ' + shlex.quote(REMOTE))
    result = subprocess.run(['bash', str(repository / 'gpu/a100_ssh.sh'), command],
                            check=True, capture_output=True, text=True, timeout=60)
    receipt = json.loads(result.stdout)
    stamp = datetime.fromtimestamp(receipt['captured_unix'], timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destination = output / ('RECEIPT_' + stamp)
    destination.mkdir(exist_ok=False)
    for name, document in receipt['documents'].items():
        data = base64.b64decode(document.pop('base64'))
        assert hashlib.sha256(data).hexdigest() == document['sha256']
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
    handoff = json.loads((destination / 'FULL_CHILD_HANDOFF.json').read_text())
    handoff.update(recipient='Cicero', use='CHECKPOINT_DERIVED_L1_EXTERNAL_GENERATION',
        teacher_source_allowed=False, parenting_experience_allowed=False,
        sealed_outputs_included=False, promotion_claim=False,
        provenance_handoff_sha256=receipt['documents']['FULL_CHILD_HANDOFF.json']['sha256'])
    with (destination / 'CICERO_CHECKPOINT_AVAILABLE.json').open('x') as stream:
        json.dump(handoff, stream, indent=2, sort_keys=True)
    with (destination / 'NATIVE_STATUS.json').open('x') as stream:
        json.dump(receipt, stream, indent=2, sort_keys=True)
    print(json.dumps(dict(receipt=str(destination), logs=receipt['logs'],
                         cicero_child=handoff['child_path']), indent=2))


def staging(repository, output):
    sources = set()
    for directory in ('gpu', 'organism_v6', 'tests'):
        for prefix in ('orch_combined_l1', 'orch_rich_breadth_bootstrap', 'test_orch_combined_l1'):
            sources.update(path for path in (repository / directory).glob(prefix + '*.py'))
    sources.add(repository / 'research_loop/workers/COMBINED_L1_CONTINUAL.md')
    manifest = json.loads((output / 'CORPUS_MANIFEST.json').read_text())
    data = {output / name for name in manifest['files']}
    data.update(output.glob('*.json'))
    data.update(output.glob('*.md'))
    data.add(output / 'source_content_v2.tar')
    for folder in ('INBOX', 'CONTENT_QUEUE', 'HANDOFFS'):
        data.update((output / folder).rglob('*.json'))
        data.update((output / folder).rglob('PINNED_POLICY.py'))
    for folder in output.glob('RECEIPT_*'):
        data.update(folder.rglob('*.json'))
    inventory = {}
    for category, paths in (('owned_source_tests', sources), ('frozen_data_and_receipts', data)):
        inventory[category] = {str(path.relative_to(repository)): hashlib.sha256(path.read_bytes()).hexdigest()
                               for path in sorted(paths) if path.is_file()}
    inventory.update(no_git_mutation=True, sealed_outputs_excluded=True,
        deployed_source='source_content_v2.tar',
        warning='Current source edits are not automatically deployed. The immutable archive and versioned PREPARE bind the live job.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destination = output / ('STAGE_' + stamp)
    with destination.with_suffix('.json').open('x') as stream:
        json.dump(inventory, stream, indent=2, sort_keys=True)
    with destination.with_suffix('.txt').open('x') as stream:
        stream.write('\n'.join(sorted(set(inventory['owned_source_tests']) |
                                      set(inventory['frozen_data_and_receipts']))) + '\n')
    print(str(destination.with_suffix('.txt')))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--remote-root', type=Path)
    parser.add_argument('--repository', type=Path, default=Path.cwd())
    parser.add_argument('--output', type=Path)
    parser.add_argument('--staging-only', action='store_true')
    options = parser.parse_args()
    if options.remote_root:
        json.dump(capture(options.remote_root), sys.stdout)
    else:
        assert options.output is not None
        if options.staging_only:
            staging(options.repository.resolve(), options.output.resolve())
        else:
            publish(options.repository.resolve(), options.output.resolve())
