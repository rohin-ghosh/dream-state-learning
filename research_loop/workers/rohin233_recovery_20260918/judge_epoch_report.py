"""Read-only, text-free counting of adopted judge epochs and paired scores."""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        allow_nan=False).encode()).hexdigest()


def read(path):
    if path.is_symlink() or path.stat().st_size > 1024 * 1024:
        raise ValueError('bounded_regular_epoch_receipt_required')
    return json.loads(path.read_bytes())


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def hour(timestamp):
    return datetime.fromtimestamp(timestamp, timezone.utc).strftime('%Y-%m-%dT%H:00:00Z')


def counters():
    return dict(act_origins=0, scored_occurrences=0, accepted_occurrences=0,
        new_pixel_occurrences=0, inherited_cache_occurrences=0, distinct_scored=0,
        distinct_accepted=0, distinct_new_pixels=0, paired_comparisons=0,
        old_pass_new_pass=0, old_pass_new_fail=0, old_fail_new_pass=0,
        old_fail_new_fail=0, pending_admissions=0, pending_shadows=0)


def summarize(root, expected_epoch, cut):
    binding = read(root / 'BINDING.json')
    require(digest(binding) == expected_epoch, 'exact_player_epoch_binding')
    require(binding['primary_step'] == 15625 and binding['primary_rank'] == 8
        and binding['shadow_step'] == 6250 and binding['top_k'] == 50, 'adopted_judge_pair')
    totals, hours, receipts = counters(), {}, []

    def include(path, value):
        receipts.append(dict(name=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        bucket = hours.setdefault(hour(value), counters())
        return totals, bucket

    for path in sorted(root.glob('ACT_*.json')):
        event = read(path)
        require(event['epoch_sha256'] == expected_epoch and event['primary_step'] == 15625
            and event['primary_rank'] == 8, 'ACT_from_same_adopted_epoch')
        origin = event['origin'].get('record_sha256') or event['origin'].get('request_sha256')
        require(path.name == 'ACT_' + str(origin) + '.json', 'one_ACT_per_source_origin')
        if event['unix'] > cut:
            continue
        for bucket in include(path, event['unix']):
            bucket['act_origins'] += 1
            for source, destination in (('new_scored', 'scored_occurrences'),
                    ('raw_accepted', 'accepted_occurrences'), ('new_pixels', 'new_pixel_occurrences'),
                    ('inherited_cached', 'inherited_cache_occurrences')):
                require(type(event[source]) is int and event[source] >= 0, 'nonnegative_actual_count')
                bucket[destination] += event[source]

    for path in sorted(root.glob('*.json')):
        if len(path.stem) != 64 or any(character not in '0123456789abcdef' for character in path.stem):
            continue
        admitted = read(path)
        require(admitted['epoch_sha256'] == expected_epoch and admitted['player'] == binding['player'],
            'admitted_string_from_same_player_epoch')
        require(path.stem == digest(dict(epoch=expected_epoch, contest=admitted['contest_id'],
            caption_sha256=admitted['caption_sha256'])), 'dedup_key_is_scene_and_exact_string')
        if admitted['admitted_unix'] > cut:
            continue
        buckets = include(path, admitted['admitted_unix'])
        complete_path = path.with_name(path.stem + '.COMPLETE.json')
        if not complete_path.is_file():
            for bucket in buckets:
                bucket['pending_admissions'] += 1
            continue
        complete = read(complete_path)
        require(complete['admission_sha256'] == digest(admitted), 'completed_score_bound_to_admission')
        receipts.append(dict(name=complete_path.name,
            sha256=hashlib.sha256(complete_path.read_bytes()).hexdigest()))
        primary, shadow = complete['primary'], complete['shadow']
        require(type(primary.get('accepted')) is bool and type(primary.get('rank')) is int,
            'completed_score_has_explicit_outcome')
        require(not primary['accepted'] or primary['rank'] <= 50, 'accepted_rank_at_most_50')
        if shadow is not None:
            require(admitted['shadow_due'] and type(shadow.get('accepted')) is bool,
                'actual_same_string_shadow_outcome')
        for bucket in buckets:
            bucket['distinct_scored'] += 1
            bucket['distinct_accepted'] += primary['accepted']
            bucket['distinct_new_pixels'] += primary.get('status') == 'new_pixel'
            if shadow is None:
                bucket['pending_shadows'] += admitted['shadow_due']
            else:
                bucket['paired_comparisons'] += 1
                label = 'old_' + ('pass' if shadow['accepted'] else 'fail')
                label += '_new_' + ('pass' if primary['accepted'] else 'fail')
                bucket[label] += 1

    for bucket in [totals, *hours.values()]:
        bucket['distinct_accept_rate'] = (bucket['distinct_accepted'] / bucket['distinct_scored']
            if bucket['distinct_scored'] else None)
    active_path = root / 'ACTIVE.json'
    active = read(active_path) if active_path.is_file() else None
    require(active is None or active['epoch_sha256'] == expected_epoch, 'same_active_epoch')
    return dict(player=binding['player'], epoch_sha256=expected_epoch, totals=totals,
        hours=hours, active=active, receipt_count=len(receipts), receipts_sha256=digest(receipts),
        restored_seen_count=binding['previous_seen_count'], captions_parsed=None,
        format_faults=None, no_caption_acts=None, generated_tokens=None,
        missing_metrics_reason='Not present in the immutable epoch ledger; not inferred or zero-filled.',
        interpretation='Judge acceptance is not a manual humor judgment; occurrence counts are not distinct strings.',
        raw_text_exported=False)


def process(pid):
    root = Path('/proc') / str(pid)
    fields = root.joinpath('stat').read_text().rsplit(') ', 1)[1].split()
    command = root.joinpath('cmdline').read_bytes()
    return dict(pid=pid, start_ticks=fields[19], state=fields[0],
        command_sha256=hashlib.sha256(command).hexdigest()), command.split(b'\0')


def collect(specification):
    remaining = int(specification['cutoff_unix'] - time.time() - 5)
    require(remaining > 0, 'existing_source_lease_still_open')
    signal.alarm(min(30, remaining))
    before, command = process(specification['pid'])
    require(before['state'] not in ('Z', 'X') and before['start_ticks'] == str(specification['start_ticks'])
        and before['command_sha256'] == specification['command_sha256'], 'exact_live_scorer_incarnation')
    config_path = Path(os.fsdecode(command[command.index(b'--config') + 1]))
    config = read(config_path)
    root = Path(config['root'])
    require(config_path.parent == root and root.parent.name == 'orch_r233_judge15625_20260918',
        'existing_adopted_scorer_root')
    require(config['deadline_unix'] <= specification['cutoff_unix'], 'scorer_inside_existing_allocation')
    cut = time.time()
    results = []
    for entry in specification['players']:
        require(Path(entry['player']).name == entry['player'], 'single_player_directory')
        results.append(summarize(root / 'epochs' / entry['player'], entry['epoch_sha256'], cut))
    after, unused = process(specification['pid'])
    require(all(after[field] == before[field] for field in ('pid', 'start_ticks', 'command_sha256')),
        'scorer_identity_unchanged_during_read')
    return dict(role=specification['role'], observed_utc=datetime.fromtimestamp(cut, timezone.utc).isoformat(),
        completed_utc=datetime.now(timezone.utc).isoformat(), process=after, players=results,
        config_sha256=hashlib.sha256(config_path.read_bytes()).hexdigest(),
        remote_writes=0, native_signals=[], GPU_work=0,
        completion_race_note='Immutable admissions at cut; a concurrent completion may be observed during this bounded read.')


def collect_fleet():
    from concurrent.futures import ThreadPoolExecutor
    import shlex
    import subprocess

    here = Path(__file__).resolve().parent
    repository = here.parents[2]
    owner = here.parent / 'rohin233_ovx4_recovery_20260918'
    supports = read(owner / 'SUPPORT_COMPONENT_TABLE.json')
    source = Path(__file__).read_text()
    specifications = []
    for role, component, wrapper in (('SHARED2', 'shared_node3_scorer', 'ovx4'),
            ('SHARED3', 'shared_node2_scorer', 'ovx4'), ('BASE', 'base_scorer', 'ovx4'),
            ('P3', 'P3_scorer', 'a40r')):
        adopted = read(owner / ('JUDGE_' + role + '_ADOPTED.json'))['actual_loaded']
        identity = next(row for row in supports['rows'] if row['name'] == component)
        require(identity['pid'] == adopted['pid'], 'support_identity_matches_loaded_judge')
        specifications.append(dict(role=role, pid=adopted['pid'], start_ticks=identity['start_ticks'],
            command_sha256=identity['command_sha256'], cutoff_unix=adopted['deadline_unix'],
            players=[dict(player=row['player'], epoch_sha256=row['epoch_sha256'])
                for row in adopted['sessions']], wrapper=wrapper))

    def fetch(specification):
        response = subprocess.run(['bash', str(repository / ('gpu/' + specification['wrapper'] + '_ssh.sh')),
            'python3 -B -c ' + shlex.quote(source)], input=json.dumps(specification),
            capture_output=True, text=True, timeout=40)
        if response.returncode:
            return dict(role=specification['role'], status='READ_FAILED_NOT_ZERO_COUNTS',
                stderr_sha256=hashlib.sha256(response.stderr.encode()).hexdigest(),
                error_type=response.stderr.splitlines()[-1].split(':')[0] if response.stderr else None)
        return json.loads(response.stdout)

    with ThreadPoolExecutor(max_workers=4) as executor:
        roles = list(executor.map(fetch, specifications))
    stamp = datetime.now(timezone.utc).strftime('%H%M%S')
    result = dict(schema='R233_ADOPTED_JUDGE_EPOCH_AUDIT_V1', observed_utc=datetime.now(timezone.utc).isoformat(),
        reader_sha256=hashlib.sha256(source.encode()).hexdigest(), roles=roles,
        old_and_new_epochs_combined=False, raw_text_exported=False, native_signals=[], GPU_work=0)
    output = here / ('JUDGE_EPOCH_AUDIT_' + stamp + '.json')
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + '\n')
    lines = ['# Adopted judge epoch counts — ' + result['observed_utc'], '',
        'Distinctness is exact caption string within scene and player, not certified humor or semantic novelty.',
        'Old cached scores and retrospective rescoring do not count as new adopted-judge outcomes.', '',
        '| Player | ACT origins | Distinct scored | Distinct accepted | New pixels | Accept rate | Paired old/new |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for role in roles:
        for row in role.get('players', []):
            totals = row['totals']
            rate = totals['distinct_accept_rate']
            values = [row['player'], totals['act_origins'], totals['distinct_scored'], totals['distinct_accepted'],
                totals['distinct_new_pixels'], f'{rate:.1%}' if rate is not None else 'not measured',
                totals['paired_comparisons']]
            lines.append('| ' + ' | '.join(map(str, values)) + ' |')
        if 'players' not in role:
            lines.append('\n' + role['role'] + ': ' + role['status'])
    lines.extend(['', 'Hourly bins are in the JSON and retain separate player/epoch identities.',
        'Parsed-caption totals, format faults, no-caption acts and generated tokens are not present in this ledger.',
        'They remain unknown here, not zero; this is not the complete tokens-normalized game measurement.'])
    output.with_suffix('.md').write_text('\n'.join(lines) + '\n')
    print(json.dumps(dict(path=str(output.relative_to(repository)),
        players=sum(len(role.get('players', [])) for role in roles),
        errors=[role['role'] for role in roles if 'players' not in role])))


if __name__ == '__main__':
    if sys.argv[1:] == ['--fleet']:
        collect_fleet()
    else:
        print(json.dumps(collect(json.load(sys.stdin)), sort_keys=True))
