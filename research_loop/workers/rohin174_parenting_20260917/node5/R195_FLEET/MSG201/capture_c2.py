"""Copy a read-only, hash-bound C2 checkpoint and separate console snapshot."""

import datetime
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile
import time


LIFE = Path('/localhome/local-rohing/orch_r153_community_C2_20260916_attempt1/life')
PHASE = Path('/localhome/local-rohing/orch_r153_r194_C2_20260917_console1')
NATIVE = 3018395
START = '23105951'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                   allow_nan=False).encode()).hexdigest()


def sha(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def record(path):
    value = read(path)
    require(value['sha256'] == digest({key: item for key, item in value.items() if key != 'sha256'}),
            'journal_record_digest')
    return value


def meta(path):
    with path.open('rb') as handle:
        handle.seek(max(0, path.stat().st_size - 4096))
        ending = handle.read()
    return json.loads(b'{' + ending[ending.rfind(b',"index":') + 1:])


def identity(process_id):
    process = Path('/proc') / str(process_id)
    fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    require(fields[0] not in ('Z', 'X'), 'live_identity')
    return dict(pid=process_id, start_ticks=fields[19], parent=int(fields[1]),
                uid=process.stat().st_uid, cwd=os.readlink(process / 'cwd'),
                argv_sha256=sha(process / 'cmdline'))


def ownership():
    native = identity(NATIVE)
    require(native['start_ticks'] == START and native['uid'] == 2524, 'exact_original_C2_native')
    timer = identity(native['parent'])
    supervisor = identity(timer['parent'])
    require(supervisor['pid'] == 3018393 and supervisor['start_ticks'] == '23105934', 'original_inner_supervisor')
    outer = identity(3018332)
    require(outer['pid'] == 3018332 and outer['start_ticks'] == '23105789', 'original_outer_owner')
    bridge = identity(3018251)
    require(bridge['start_ticks'] == '23105688', 'original_bridge_owner')
    return dict(native=native, timer=timer, supervisor=supervisor, outer=outer, bridge=bridge)


def inspect():
    before = ownership()
    arguments = (Path('/proc') / str(NATIVE) / 'cmdline').read_bytes().rstrip(b'\0').decode().split('\0')
    guard_path = Path(arguments[arguments.index('--config') + 1])
    require(guard_path == PHASE / 'control/GUARD.json', 'original_console_guard')
    guard = read(guard_path)
    plan_path = Path(guard['plan_path'])
    plan = read(plan_path)
    require(plan['root'] == str(LIFE) and plan['physical'] == 1 and sha(plan_path) == guard['plan_sha256'],
            'same_root_slot_and_plan')
    paths = sorted((LIFE / 'stream/records').glob('[0-9]' * 20 + '.json'))
    catalog = [meta(path) for path in paths[-400:]]
    complete_meta = next(item for item in reversed(catalog) if item['kind'] == 'SLEEP_COMPLETE')
    context_meta = next(item for item in reversed(catalog) if item['kind'] == 'CONTEXT_COMMITTED')
    mode_meta = next(item for item in reversed(catalog) if item['kind'] == 'R194_MODE')

    def path_for(index):
        return LIFE / 'stream/records' / f'{index:020d}.json'

    complete = record(path_for(complete_meta['index']))['document']
    context = record(path_for(context_meta['index']))['document']
    mode = record(path_for(mode_meta['index']))['document']
    require(mode['mode'] == 'REFLECTION' and mode['act_held'] and mode['learn_held'], 'interactive_hold_intact')
    require(not any(item['kind'] in ('UPDATE', 'SLEEP_RECIPE', 'SLEEP_REQUEST', 'SLEEP_COMPLETE')
                    for item in catalog if item['index'] > mode_meta['index']), 'no_post_hold_learning')
    saved = complete['resume_state']
    committed = context['state']
    require(saved['sha256'] == digest(saved['state']) and committed['sha256'] == digest(committed['state']),
            'exact_saved_and_console_envelopes')
    require(complete['status'] == 'COMPLETE' and saved['state']['pending'] is None
            and committed['state']['pending'] is None, 'complete_committed_not_pending')
    require(context['training_eligible'] is False, 'context_only_commit')
    require(saved['state']['rows'] == committed['state']['rows'], 'no_console_training_rows')
    require(saved['state']['sleep_frontier'] == committed['state']['sleep_frontier'], 'unchanged_sleep_frontier')
    prior_events = saved['state']['history']['events']
    current_events = committed['state']['history']['events']
    require(current_events[:len(prior_events)] == prior_events, 'saved_history_exact_prefix')
    checkpoint = complete['checkpoint']
    require(digest(checkpoint['checkpoint_sha256']) == saved['state']['model_state_sha256']
            == committed['state']['model_state_sha256'], 'same_learned_weights_in_both_snapshots')
    checkpoint_root = LIFE / 'checkpoints' / f"sleep_{complete['cycle']:06d}"
    require(read(checkpoint_root / 'COMMIT.json') == checkpoint, 'original_checkpoint_receipt')
    files = []

    def add(path, relative, expected=None):
        path = Path(path)
        require(path.is_file() and not path.is_symlink(), 'regular_source_file')
        require(path.is_relative_to(LIFE) or path.is_relative_to(PHASE), 'scoped_source_file')
        actual = sha(path)
        require(expected is None or actual == expected, 'exact_source_file_hash')
        files.append(dict(source=str(path), relative=relative, sha256=actual,
                          size=path.stat().st_size, mtime_ns=path.stat().st_mtime_ns))

    add(checkpoint_root / 'COMMIT.json', 'complete/COMMIT.json')
    require(Path(checkpoint['adapter_path']) == checkpoint_root / 'adapter', 'exact_adapter_directory')
    for name, expected in checkpoint['adapter_files'].items():
        require(Path(name).name == name, 'adapter_member_basename')
        add(checkpoint_root / 'adapter' / name, 'complete/adapter/' + name, expected)
    require(digest(checkpoint['adapter_files']) == checkpoint['checkpoint_sha256']['adapter'], 'adapter_bundle')
    require(checkpoint['checkpoint_sha256']['optimizer'] == checkpoint['checkpoint_sha256']['rng'], 'optimizer_rng_binding')
    add(checkpoint['optimizer_rng_path'], 'complete/optimizer_rng.pt', checkpoint['checkpoint_sha256']['optimizer'])
    add(path_for(complete_meta['index']), 'complete/SLEEP_COMPLETE.json')
    add(path_for(context_meta['index']), 'console/CONTEXT_COMMITTED.json')
    add(guard_path, 'source_binding/GUARD.json')
    add(plan_path, 'source_binding/PLAN.json', guard['plan_sha256'])
    source = Path(plan['source_root'])
    require(source == PHASE / 'source', 'actual_loaded_source_root')
    for relative, expected in guard['source_pins'].items():
        require(relative.endswith('.py') and '..' not in Path(relative).parts and not Path(relative).is_absolute(),
                'pinned_code_only_no_credentials')
        add(source / relative, 'source/' + relative, expected)

    turns = []
    console_files = set()
    for item in catalog:
        if item['index'] < mode_meta['index'] - 1 or item['index'] > catalog[-1]['index']:
            continue
        path = path_for(item['index'])
        add(path, 'console/records/' + path.name)
        if item['kind'] != 'R194_TURN':
            continue
        turn = record(path)['document']
        require(turn['training_eligible'] is False and turn['act_held'] and turn['learn_held'], 'masked_console_turn')
        response_path = path_for(item['index'] - 2)
        request_path = path_for(item['index'] - 3)
        committed_path = path_for(item['index'] - 1)
        response = record(response_path)
        request = record(request_path)
        turn_context = record(committed_path)
        require((request['kind'], response['kind'], turn_context['kind']) ==
                ('REQUEST', 'RESPONSE', 'CONTEXT_COMMITTED'), 'exact_console_record_sequence')
        require(digest(response['document']) == turn['response_sha256']
                == turn_context['document']['source_sha256'], 'actual_response_turn_commit_binding')
        require(request['document']['training_eligible'] is False
                and request['document']['render_receipt']['all_history_tokens_masked'], 'actual_request_masking')
        question_id = turn['parent_event_id'].split(':inbox:', 1)[1]
        question_path = LIFE / 'stream/inbox' / (question_id + '.json')
        question = read(question_path)
        require(question['speaker'] == 'Rohin', 'actual_console_question_speaker')
        if question_id not in console_files:
            add(question_path, 'console/questions/' + question_path.name)
            console_files.add(question_id)
        inbox_matches = [candidate for candidate in catalog if candidate['kind'] == 'INBOX'
                         and record(path_for(candidate['index']))['document']['message']['id'] == question_id]
        require(len(inbox_matches) == 1, 'exact_question_inbox_registration')
        turns.append(dict(question_id=question_id, question_sha256=sha(question_path),
            question_file_mtime_unix=question_path.stat().st_mtime, inbox_index=inbox_matches[0]['index'],
            request_index=request['index'], request_started_unix=request['document']['started_unix'],
            response_index=response['index'], response_record_sha256=response['sha256'],
            response_finished_unix=response['document']['finished_unix'],
            response_text_sha256=hashlib.sha256(response['document']['response']['raw'].encode()).hexdigest(),
            commit_index=turn_context['index'], commit_record_sha256=turn_context['sha256'],
            commit_file_mtime_unix=committed_path.stat().st_mtime,
            receipt_index=item['index'], receipt_record_sha256=item['sha256'],
            receipt_file_mtime_unix=path.stat().st_mtime, training_eligible=False,
            all_history_tokens_masked=True))
    inbox = {path.name: sha(path) for path in sorted((LIFE / 'stream/inbox').glob('*.json'))}
    after = ownership()
    require(before == after, 'unchanged_native_timer_outer_bridge_ownership')
    return dict(schema='MSG201_READ_ONLY_C2_SNAPSHOT_V1', observed_unix=time.time(),
        ownership=before, head=catalog[-1], complete_record=complete_meta, console_record=context_meta,
        mode=mode, cycle=complete['cycle'], optimizer_steps=checkpoint['optimizer_steps'],
        checkpoint=checkpoint, saved_state_sha256=saved['sha256'], console_state_sha256=committed['sha256'],
        learned_rows=len(saved['state']['rows']), saved_history_events=len(prior_events),
        console_history_events=len(current_events), console_new_training_rows=0,
        saved_history_prefix_preserved=True, model_state_unchanged=True, turns=turns,
        inbox_hashes=inbox, files=files, total_copy_bytes=sum(item['size'] for item in files),
        signals=0, publications=0, remote_writes=0, hold_released=False, weights_learned_console=False)


def send_archive(manifest):
    require(ownership() == manifest['ownership'], 'same_ownership_before_copy')
    with tarfile.open(fileobj=sys.stdout.buffer, mode='w|') as archive:
        for item in manifest['files']:
            path = Path(item['source'])
            require(sha(path) == item['sha256'] and path.stat().st_size == item['size'], 'source_unchanged_before_copy')
            archive.add(path, arcname=item['relative'], recursive=False)
    require(ownership() == manifest['ownership'], 'same_ownership_after_copy')


def main():
    if '--inspect' in sys.argv:
        print(json.dumps(inspect()))
        return
    if '--archive' in sys.argv:
        send_archive(json.load(sys.stdin))
        return
    here = Path(__file__).resolve().parent
    repo = here.parents[5]
    remote = ['bash', str(repo / 'gpu/ovx3_ssh.sh')]
    script = Path(__file__).read_text()
    captured = subprocess.run(remote + ['python3 -B -c ' + shlex.quote(script) + ' --inspect'],
                              capture_output=True, text=True, timeout=120)
    require(captured.returncode == 0, 'read_only_snapshot_inspection_failed:' + captured.stderr[-250:])
    manifest = json.loads(captured.stdout)
    output = here / ('C2_SNAPSHOT_' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    output.mkdir()
    (output / 'MANIFEST.json').write_text(json.dumps(manifest, sort_keys=True, indent=2) + '\n')
    archive_path = output / 'SNAPSHOT.tar'
    with archive_path.open('xb') as handle:
        copied = subprocess.run(remote + ['python3 -B -c ' + shlex.quote(script) + ' --archive'],
                                input=json.dumps(manifest).encode(), stdout=handle,
                                stderr=subprocess.PIPE, timeout=240)
    require(copied.returncode == 0, 'read_only_snapshot_copy_failed')
    expected = {item['relative']: item for item in manifest['files']}
    seen = set()
    with tarfile.open(archive_path) as archive:
        for member in archive:
            require(member.isfile() and member.name in expected and member.name not in seen, 'exact_snapshot_archive_member')
            handle = archive.extractfile(member)
            require(hashlib.file_digest(handle, 'sha256').hexdigest() == expected[member.name]['sha256'], 'copied_bytes_exact')
            seen.add(member.name)
            destination = output / member.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(member) as source_handle, destination.open('xb') as target:
                for block in iter(lambda: source_handle.read(1024 * 1024), b''):
                    target.write(block)
            destination.chmod(0o444)
    require(seen == set(expected), 'all_snapshot_files_copied')
    verified = dict(status='COPIED_HASH_VERIFIED_NOT_A_CLONE_LAUNCH', verified_unix=time.time(),
        manifest_sha256=sha(output / 'MANIFEST.json'), archive_sha256=sha(archive_path),
        copied_files=len(seen), copied_bytes=manifest['total_copy_bytes'],
        cycle=manifest['cycle'], optimizer_steps=manifest['optimizer_steps'],
        complete_index=manifest['complete_record']['index'], console_index=manifest['console_record']['index'],
        console_new_training_rows=0, original_ownership_preserved=True, hold_released=False)
    (output / 'VERIFIED.json').write_text(json.dumps(verified, sort_keys=True, indent=2) + '\n')
    for path in (output / 'MANIFEST.json', archive_path, output / 'VERIFIED.json'):
        path.chmod(0o444)
    print(json.dumps(dict(snapshot=str(output), **verified)))


if __name__ == '__main__':
    main()
