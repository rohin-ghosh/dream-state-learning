"""Exact-root retirement audit; public receipts never include commands or raw rows."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import subprocess


PROTECTED = {
    'r213_r226_caption_observation_fork': 0,
    'r213_math_a': 1,
    'r213_math_b_fork': 2,
    'r213_r226_caption_perspective_fork': 3,
    'r213_math_c': 4,
    'r213_r226_caption_revision_fork': 5,
    'r213_r226_caption_selfderive_fork': 6,
    'r213_r226_caption_unparented_fork': 7,
}
OBSOLETE = (
    'conversational', 'fresh_math', 'frozen_c2', 'lr03', 'lr3', 'p32', 'p4',
    'peer_math', 'peer_repo', 'r213_r224_challenger_audit_fork',
    'r213_siege_envoy_fork', 'r213_siege_scout_fork',
    'r213_siege_negotiator_fork', 'r213_siege_quartermaster_fork',
    'r213_siege_challenger_fork',
    'fresh_math_failed_command_defaults_0353', 'fresh_math_failed_no_pytest_0352',
    'frozen_c2_failed_command_defaults_0353',
)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as handle:
        json.dump(value, handle, sort_keys=True, indent=2)
        handle.write('\n')


def record(path):
    value = json.loads(path.read_bytes())
    payload = json.dumps({key: item for key, item in value.items() if key != 'sha256'},
        sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    if hashlib.sha256(payload).hexdigest() != value['sha256']:
        raise ValueError('journal digest mismatch')
    return value


def metadata(path):
    with path.open('rb') as handle:
        handle.seek(max(0, path.stat().st_size - 8192))
        found = re.findall(rb',"index":(\d+),"journal_id":"[^"]+","kind":"([^"]+)"', handle.read())
    if not found or int(found[-1][0]) != int(path.stem):
        raise ValueError('journal metadata mismatch')
    return found[-1][1].decode()


def identity(pid):
    process = Path('/proc', str(pid))
    fields = process.joinpath('stat').read_text().rsplit(')', 1)[1].split()
    command = process.joinpath('cmdline').read_bytes()
    try:
        cwd = os.readlink(process / 'cwd')
    except PermissionError:
        cwd = ''
    return dict(pid=pid, start_ticks=fields[19], state=fields[0], ppid=int(fields[1]),
        command_sha256=hashlib.sha256(command).hexdigest(),
        args=[part.decode(errors='replace') for part in command.split(b'\0') if part],
        cwd=cwd)


def exact_lives(root, process):
    selected = set()
    for argument in process['args'] + [process['cwd']]:
        value = argument.split('=', 1)[-1] if '=' in argument else argument
        try:
            relative = Path(value).relative_to(root)
        except ValueError:
            continue
        if relative.parts and relative.parts[0] in set(PROTECTED) | set(OBSOLETE):
            selected.add(relative.parts[0])
    return selected


def census(root):
    processes = []
    for entry in Path('/proc').iterdir():
        if entry.name.isdigit():
            try:
                item = identity(int(entry.name))
                if item['state'] not in ('Z', 'X'):
                    item['lives'] = sorted(exact_lives(root, item))
                    if item['lives']:
                        processes.append(item)
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                pass
    return processes


def public_identity(process):
    return {key: process[key] for key in ('pid', 'start_ticks', 'state', 'ppid', 'command_sha256')}


def is_native(process):
    arguments = process['args']
    if not arguments or not Path(arguments[0]).name.startswith('python') or '-m' not in arguments:
        return False
    position = arguments.index('-m')
    return (all(argument in ('-B', '-u', '-I', '-s') for argument in arguments[1:position])
        and len(arguments) > position + 2 and arguments[position + 2] == 'native')


def verified_checkpoint(arm):
    for commit in sorted((arm / 'raw/checkpoints').glob('*/COMMIT.json'), reverse=True):
        document = json.loads(commit.read_bytes())
        hashes = document.get('checkpoint_sha256', {})
        if set(hashes) != {'adapter', 'optimizer', 'rng'}:
            continue
        state_path = commit.parent / 'optimizer_rng.pt'
        if not state_path.exists() or sha(state_path) != hashes['optimizer'] or hashes['optimizer'] != hashes['rng']:
            continue
        adapter = document.get('adapter_files', {})
        if not adapter or any(not (commit.parent / 'adapter' / name).is_file()
            or sha(commit.parent / 'adapter' / name) != digest for name, digest in adapter.items()):
            continue
        return dict(relative=str(commit.relative_to(arm)), commit_sha256=sha(commit),
            checkpoint_sha256=hashes, adapter_files=adapter, all_file_hashes_verified=True,
            resident_partial_continuity_claimed=False)
    return None


def preserve(arm, destination):
    checkpoint = verified_checkpoint(arm)
    destination.mkdir(parents=True, exist_ok=False)
    selected = []
    if checkpoint:
        selected.append(Path(checkpoint['relative']).parent)
    if (arm / 'raw/stream').exists():
        selected.append(Path('raw/stream'))
    selected.extend(Path(path.name) for path in arm.iterdir()
        if path.name not in ('.nv', '.triton', '__pycache__', 'raw', 'logical'))
    for relative in selected:
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['cp', '-a', '--reflink=auto', str(arm / relative), str(target)], check=True)
    files, links = [], []
    for path in sorted(destination.rglob('*')):
        if path.is_symlink():
            links.append(dict(relative=str(path.relative_to(destination)),
                target_sha256=hashlib.sha256(os.readlink(path).encode()).hexdigest()))
        elif path.is_file():
            files.append(dict(relative=str(path.relative_to(destination)), bytes=path.stat().st_size, sha256=sha(path)))
    manifest = dict(life=arm.name, observed_utc=stamp(), files=files, links=links,
        checkpoint=checkpoint, original_entire_root_retained=True,
        older_checkpoints_and_readouts_retained_in_original=True,
        raw_stream_pending_rows_records_and_tail_copied=(destination / 'raw/stream').exists())
    save(destination / 'PRESERVATION_MANIFEST.json', manifest)
    return dict(manifest_sha256=sha(destination / 'PRESERVATION_MANIFEST.json'),
        manifest_relative=str(Path(arm.name) / 'PRESERVATION_MANIFEST.json'),
        files=len(files), bytes=sum(item['bytes'] for item in files), checkpoint=checkpoint,
        raw_stream_preserved=manifest['raw_stream_pending_rows_records_and_tail_copied'])


def terminate(root, expected, allowed_life):
    if allowed_life not in OBSOLETE or expected['lives'] != [allowed_life]:
        raise ValueError('only a single exact obsolete root is authorized')
    descriptor = os.pidfd_open(expected['pid'])
    try:
        current = identity(expected['pid'])
        if (current['start_ticks'], current['command_sha256'], exact_lives(root, current)) != (
            expected['start_ticks'], expected['command_sha256'], {allowed_life}):
            raise ValueError('process identity changed')
        signal.pidfd_send_signal(descriptor, signal.SIGTERM)
        poller = select.poll()
        poller.register(descriptor, select.POLLIN)
        return dict(**public_identity(current), signal='SIGTERM', exit_observed=bool(poller.poll(30000)))
    finally:
        os.close(descriptor)


def audit(root, output, retire=False):
    processes = census(root)
    protected = []
    for name, gpu in PROTECTED.items():
        natives = [item for item in processes if item['lives'] == [name] and is_native(item)]
        if len(natives) != 1:
            raise ValueError('protected native missing or ambiguous: ' + name)
        protected.append(dict(life=name, gpu=gpu, **public_identity(natives[0])))
    rows = []
    for name in OBSOLETE:
        arm = root / name
        owners = [item for item in processes if name in item['lives']]
        row = dict(life=name, processes=[public_identity(item) for item in owners], signals=[])
        if not arm.exists():
            row['status'] = 'ROOT_ABSENT_NOT_LAUNCHED_CLAIMED'
            rows.append(row)
            continue
        if owners and not retire:
            row['status'] = 'LIVE_OBSOLETE_REQUIRES_EXACT_RETIRE'
            rows.append(row)
            continue
        if owners:
            preserve(arm, output / 'pre_signal' / name)
            for owner in sorted(owners, key=lambda item: 'native' not in item['args']):
                try:
                    row['signals'].append(terminate(root, owner, name))
                except (ProcessLookupError, FileNotFoundError):
                    pass
            if any(name in item['lives'] for item in census(root)):
                raise ValueError('obsolete process remains; no completion claim')
        row['preservation'] = preserve(arm, output / 'preserved' / name)
        loaded = None
        records = sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))
        for path in reversed(records):
            if metadata(path) == 'LOADED':
                value = record(path)
                loaded = dict(index=value['index'], sha256=value['sha256'], pid=value['document'].get('pid'))
                break
        row.update(status='RETIRED_NOW' if owners else ('ALREADY_ENDED' if loaded else 'NO_LOADED_RECEIPT'),
            last_LOADED=loaded, old_start_ticks_not_inferred=True,
            tail_record=dict(index=int(records[-1].stem), sha256=record(records[-1])['sha256']) if records else None,
            exit_receipts=[dict(relative=str(path.relative_to(arm)), sha256=sha(path),
                exit_code=json.loads(path.read_bytes()).get('exit_code')) for path in sorted(arm.glob('control*/EXIT.json'))])
        rows.append(row)
        save(output / 'rows' / (name + '.json'), row)
    for item in protected:
        current = identity(item['pid'])
        if current['start_ticks'] != item['start_ticks'] or current['state'] in ('Z', 'X'):
            raise ValueError('protected process changed during audit')
    receipt = dict(observed_utc=stamp(), node='node3', protected=protected, obsolete=rows,
        pauses=0, refills=0, broad_signals=0, native_policy_changes=0,
        stopped_stale_services=sum(len(row['signals']) for row in rows),
        preservation_location='node3_private_operator_archive', code_sha256=sha(Path(__file__)))
    save(output / 'RETIREMENT.json', receipt)
    print(json.dumps(dict(observed_utc=receipt['observed_utc'], protected=len(protected),
        statuses={status: sum(row['status'] == status for row in rows) for status in sorted({row['status'] for row in rows})},
        signals=sum(len(row['signals']) for row in rows), receipt_sha256=sha(output / 'RETIREMENT.json'))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--retire', action='store_true')
    options = parser.parse_args()
    audit(options.root, options.output, options.retire)
