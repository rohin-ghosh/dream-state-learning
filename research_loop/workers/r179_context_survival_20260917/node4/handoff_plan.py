"""Bounded, read-only NODE4 metadata staging; never signals or starts a life."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import time


ROLES = {0: 'kernel0', 1: 'raw_unparented', 3: 'raw_parented', 4: 'kernel_parented'}
SOURCE_FILES = {
    'native': 'gpu/orch_r125_continual_native.py',
    'stream': 'organism_v6/orch_r125_continual_stream.py',
    'history': 'organism_v6/orch_r124_train_history.py',
    'presentation': 'organism_v6/orch_r125_plain_context.py',
}
DEFAULT_CENSUS = 'research_loop/workers/rohin162_context_console_20260917/SOURCE_CENSUS_1789663949490665603.json'
DEFAULT_ROSTER = 'research_loop/workers/r171_forward_roster_20260917/CURRENT_LEARNER_ROSTER.json'
WORKSPACE = 'research_loop/workers/r179_context_survival_20260917/node4'
MAX_BYTES = 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def metadata_bytes(path):
    path = Path(path)
    require(not set(path.parts).intersection({'stream', 'records', 'readouts', 'sealed', 'journals'}),
            'journal and sealed paths are outside this read-only probe')
    require(not path.is_symlink() and path.resolve() == path, 'metadata path must be canonical and not a symlink')
    before = path.stat()
    require(stat.S_ISREG(before.st_mode) and before.st_size <= MAX_BYTES, 'bounded regular metadata/source file required')
    raw = path.read_bytes()
    after = path.stat()
    require((before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns), 'metadata changed while reading')
    return raw


def metadata_json(path):
    raw = metadata_bytes(path)
    return json.loads(raw), {'path': str(path), 'sha256': digest(raw)}


def identity(process_id):
    require(type(process_id) is int and process_id > 1, 'explicit registered PID required')
    process = Path('/proc') / str(process_id)
    before = process.joinpath('stat').read_text().rsplit(')', 1)[1].split()
    raw = process.joinpath('cmdline').read_bytes()
    require(len(raw) <= 32768, 'bounded command line')
    after = process.joinpath('stat').read_text().rsplit(')', 1)[1].split()
    require(before[19] == after[19] and after[0] not in ('Z', 'X'), 'registered process must remain live')
    return dict(pid=process_id, start_ticks=after[19], state=after[0], parent_pid=int(after[1]),
                process_group=int(after[2]), session=int(after[3]), uid=process.stat().st_uid,
                cwd=os.readlink(process / 'cwd'), argv_sha256=digest(raw),
                argv=raw.rstrip(b'\0').decode().split('\0'),
                cgroup_sha256=digest(process.joinpath('cgroup').read_bytes()))


def selected_rows(census, roster, roster_raw):
    require(census['schema'] == 'ROHIN162_READONLY_SOURCE_CENSUS_V1', 'expected R162 census')
    require(census['roster_ref']['sha256'] == digest(roster_raw), 'roster bytes must match supplied census')
    census_rows = [entry for node in census['nodes'] if node['node'] == 'a40r' for entry in node['rows']]
    live = [row for row in roster['rows'] if row['node'] == 'a40r' and row['status'] == 'LIVE']
    require(len(census_rows) == len(live) == 4, 'exactly four current NODE4 learning lives')
    require({row['physical'] for row in live} == set(ROLES), 'only physical 0, 1, 3, 4; no new caption lanes or retirees')
    census_by_root = {row['life_root']: row for row in census_rows}
    require(len(census_by_root) == 4 and set(census_by_root) == {row['life_root'] for row in live}, 'census/roster life closure')
    output = []
    for row in sorted(live, key=lambda entry: entry['physical']):
        require(len(row['natives']) == 1 and row['training']['training_enabled'] is True, 'one registered learning native per life')
        native = row['natives'][0]
        source = census_by_root[row['life_root']]
        require(native['module'] == 'gpu.orch_r125_continual_guard' and native['plan_ref'] == source['plan_ref'], 'expected guarded native and exact plan')
        require(row['current_source_root'] == source['plan']['source_root'], 'exact registered source root')
        output.append(dict(role=ROLES[row['physical']], physical=row['physical'], node='a40r',
                           life_root=row['life_root'], source_root=row['current_source_root'],
                           registered_identity=native['identity'], guard_ref=native['config_ref'],
                           plan_ref=native['plan_ref'], census_source=source['source']))
    return output


def checkpoint_metadata(root):
    directories = [path for path in (Path(root) / 'checkpoints').iterdir()
                   if re.fullmatch(r'sleep_[0-9]{6}', path.name) and path.is_dir() and not path.is_symlink()]
    require(len(directories) <= 10000, 'bounded checkpoint directory census')
    for directory in sorted(directories, reverse=True):
        commit_path = directory / 'COMMIT.json'
        if not commit_path.exists():
            continue
        commit, reference = metadata_json(commit_path)
        require(commit['adapter_path'] == str(directory / 'adapter') and
                commit['optimizer_rng_path'] == str(directory / 'optimizer_rng.pt'), 'same-life checkpoint paths')
        require(set(commit['checkpoint_sha256']) == {'adapter', 'optimizer', 'rng'} and
                commit['checkpoint_sha256']['optimizer'] == commit['checkpoint_sha256']['rng'], 'shared optimizer/RNG bundle declaration')
        require(digest(canonical(commit['adapter_files'])) == commit['checkpoint_sha256']['adapter'], 'adapter inventory declaration hash')
        payloads = []
        for name, declared_sha in commit['adapter_files'].items():
            require(Path(name).name == name and name not in ('.', '..'), 'adapter basename only')
            path = directory / 'adapter' / name
            info = path.stat()
            require(not path.is_symlink() and stat.S_ISREG(info.st_mode), 'regular adapter artifact')
            payloads.append(dict(path=str(path), declared_sha256=declared_sha, bytes=info.st_size, mtime_ns=info.st_mtime_ns))
        optimizer = Path(commit['optimizer_rng_path'])
        info = optimizer.stat()
        require(not optimizer.is_symlink() and stat.S_ISREG(info.st_mode), 'regular optimizer/RNG artifact')
        payloads.append(dict(path=str(optimizer), declared_sha256=commit['checkpoint_sha256']['optimizer'], bytes=info.st_size, mtime_ns=info.st_mtime_ns))
        return dict(commit_ref=reference, cycle=int(directory.name.split('_')[1]),
                    optimizer_steps=commit['optimizer_steps'], adapter_state_sha256=commit['adapter_state_sha256'],
                    checkpoint_sha256=commit['checkpoint_sha256'], base_sha256=commit['base_sha256'],
                    created_unix=commit['created_unix'], payloads=payloads,
                    payload_bytes_read=False, payload_hashes_verified=False,
                    exact_saved_boundary_captured=False,
                    limitation='COMMIT metadata only: not a journal-head or full-state handoff admission')
    raise ValueError('no committed sleep checkpoint metadata found')


def remote_probe(rows):
    require(len(rows) == 4 and {row['physical'] for row in rows} == set(ROLES), 'four-life remote allowlist')
    deadline = time.monotonic() + 45
    output = []
    for row in rows:
        item = dict(role=row['role'], physical=row['physical'], life_root=row['life_root'], observed_unix=time.time())
        try:
            require(time.monotonic() < deadline, 'read-only probe deadline')
            actor = identity(row['registered_identity']['pid'])
            for field in ('pid', 'start_ticks', 'uid', 'cwd', 'argv_sha256', 'parent_pid'):
                require(actor[field] == row['registered_identity'][field], 'registered native identity changed: ' + field)
            require(actor['argv'][-3:] == ['native', '--config', row['guard_ref']['path']], 'exact guarded-native arguments')
            guard, guard_ref = metadata_json(Path(row['guard_ref']['path']))
            plan, plan_ref = metadata_json(Path(row['plan_ref']['path']))
            require(guard_ref == row['guard_ref'] and plan_ref == row['plan_ref'], 'guard/plan bytes changed')
            require(guard['plan_path'] == plan_ref['path'] and guard['plan_sha256'] == plan_ref['sha256'], 'guard-to-plan binding')
            require(plan['root'] == row['life_root'] and plan['source_root'] == row['source_root'] and
                    plan['physical'] == row['physical'], 'same-life source/device plan')
            parent = identity(actor['parent_pid'])
            launch, launch_ref = metadata_json(Path(guard['attempt_dir']) / 'LAUNCH.json')
            require(parent['pid'] == actor['process_group'] == parent['process_group'] == launch['pid'] and
                    str(launch['parent_start_ticks']) == parent['start_ticks'] and launch['guard_sha256'] == guard_ref['sha256'],
                    'exact owned timeout/supervisor group')
            require(parent['uid'] == actor['uid'] and parent['cgroup_sha256'] == actor['cgroup_sha256'], 'owned UID and cgroup')
            source = {}
            for label, relative in SOURCE_FILES.items():
                require(time.monotonic() < deadline, 'source probe deadline')
                path = Path(row['source_root']) / relative
                value = digest(metadata_bytes(path))
                require(value == row['census_source'][label]['sha256'] == guard['source_pins'][relative], 'source pins changed: ' + label)
                source[label] = dict(path=str(path), sha256=value)
            policy = guard.get('device_containment', {})
            item.update(status='METADATA_VERIFIED', actor={key: value for key, value in actor.items() if key != 'argv'},
                        parent={key: value for key, value in parent.items() if key != 'argv'},
                        guard_ref=guard_ref, plan_ref=plan_ref, launch_ref=launch_ref,
                        plan={key: plan.get(key) for key in ('root', 'source_root', 'physical', 'gpu_uuid', 'hard_end_unix',
                                                           'context_limit', 'segment_tokens', 'segments_per_sleep', 'presleep_variant',
                                                           'presentation_version', 'seed', 'adapter_rank')},
                        source=source, source_pins_sha256=digest(canonical(guard['source_pins'])),
                        device_containment={key: policy.get(key) for key in ('unit', 'minor', 'uid', 'gid')},
                        checkpoint=checkpoint_metadata(row['life_root']))
            final_actor = identity(actor['pid'])
            require(final_actor['start_ticks'] == actor['start_ticks'] and final_actor['argv_sha256'] == actor['argv_sha256'],
                    'native identity changed during metadata probe')
        except (OSError, KeyError, ValueError, IndexError) as error:
            item.update(status='METADATA_BLOCKED', error=str(error))
        output.append(item)
    return dict(schema='R179_NODE4_READONLY_METADATA_V1', observed_unix=time.time(), rows=output,
                signals_sent=0, processes_started=0, journal_reads=0, journal_writes=0, sealed_reads=0,
                GPU_calls=0, source_mutations=0, checkpoint_payload_reads=0)


def write_once(path, payload):
    with Path(path).open('x') as stream:
        json.dump(payload, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def prepare(census_path, roster_path, output):
    workspace = Path(WORKSPACE).resolve()
    output = Path(output).resolve()
    require(output.is_relative_to(workspace) and output != workspace and not output.exists(), 'fresh NODE4-local output directory required')
    census_raw, roster_raw = Path(census_path).read_bytes(), Path(roster_path).read_bytes()
    census, roster = json.loads(census_raw), json.loads(roster_raw)
    rows = selected_rows(census, roster, roster_raw)
    script = Path(__file__).resolve()
    command = 'python3 -B -c ' + shlex.quote(script.read_text()) + ' --probe-stdin'
    process = subprocess.run(['bash', 'gpu/a40r_ssh.sh', command], input=json.dumps(rows),
                             text=True, capture_output=True, timeout=75, check=False)
    require(process.returncode == 0, 'read-only NODE4 SSH probe failed: ' + process.stderr[-1000:])
    report = json.loads(process.stdout)
    ready = len(report['rows']) == 4 and all(row['status'] == 'METADATA_VERIFIED' for row in report['rows'])
    output.mkdir(parents=True, exist_ok=False)
    write_once(output / 'READONLY_METADATA.json', report)
    plan = dict(schema='R179_NODE4_BOUNDED_HANDOFF_PLAN_V1', node='a40r', prepared_unix=time.time(),
                status='METADATA_VERIFIED_USE_NODE4_ROLLOUT' if ready else 'BLOCKED_METADATA_MISMATCH',
                owner_scope=list(ROLES.values()),
                census_ref=dict(path=str(Path(census_path).resolve()), sha256=digest(census_raw)),
                roster_ref=dict(path=str(Path(roster_path).resolve()), sha256=digest(roster_raw)),
                operator_ref=dict(path=str(script), sha256=digest(script.read_bytes())),
                metadata_ref=dict(path=str(output / 'READONLY_METADATA.json'), sha256=digest((output / 'READONLY_METADATA.json').read_bytes())),
                lives=report['rows'], execution_armed=False, main_tested_patch_go_required=False,
                existing_authority='research_loop/workers/r179_context_survival_20260917/BUILDER_SCOPE.json',
                sealed_reads_permitted=False, journal_mutation_permitted=False,
                bounds=dict(probe_seconds=75, metadata_max_age_seconds=120, boundary_wait_seconds=600,
                            completion_wait_seconds=600, shutdown_wait_seconds=10, wall_safety_seconds=120,
                            maximum_handoffs_per_life=1, implicit_retries=0, new_leases=0),
                preserved=['same life_root and identity', 'frozen base', 'adapter bytes and parameter order',
                           'optimizer state/steps', 'Python/CPU/CUDA RNG', 'full saved history and masks',
                           'presentation/visible context at handoff', 'replay and request-consumption state',
                           'readout dispatch identities', 'nominal budgets and actual counters', 'walls and device confinement'],
                steps=[
                    'Use existing Main READY/GO and node4_rollout.py for actual-source staging and bounded handoff.',
                    'Recheck exact native/timeout PID+start_ticks, plan, guard, source family, cgroup and device ownership.',
                    'Stage a new frozen source/control candidate with only Main-approved source changes; preserve original sources.',
                    'Wait at most 600 seconds for a new COMPLETE SLEEP_COMPLETE saved boundary; never choose an older convenient checkpoint.',
                    'After receiving CPU/provenance, hold exact owned processes at the saved boundary and recheck no state advancement.',
                    'Use completion metadata only; do not read sealed outputs. Wait for dispatched readout completion and no active child.',
                    'Verify record/envelope/full-history hashes and R152-style adapter inventory plus optimizer/RNG file hashes and parameter order.',
                    'Require exact stream-state equality across source relocation, including complete history, masks, counters, pending requests and presentation.',
                    'Only after successful admission stop the exact owned old native, then launch once with resume=True on the same root/device/wall.',
                    'Verify LOADED equality before generation, optimizer/RNG/history continuity and no replayed consumed requests; preserve every receipt.',
                    'If any pre-stop check fails, release a held owner and keep the old life; no reset, tail rollback, replay recovery or automatic retry.',
                ],
                missing_before_cutover=['fresh exact saved boundary and full-state admission',
                                       'actual adapter/optimizer/RNG payload hash verification at that boundary'],
                existing_machinery_not_directly_executable=['R157 is node5/runtime-extension-specific; unchanged-source gate is incompatible with this patch.',
                                                          'R152 is retired a40r7/sleep31-specific; unsaved-generation recovery/replay is forbidden here.'])
    write_once(output / 'HANDOFF_PLAN.json', plan)
    print(json.dumps(dict(status=plan['status'], plan=str(output / 'HANDOFF_PLAN.json'),
                          metadata=str(output / 'READONLY_METADATA.json'), signals_sent=0, execution_armed=False), sort_keys=True))
    return 0 if ready else 2


def validate_scope(scope_path):
    scope = json.loads(Path(scope_path).read_bytes())
    require(scope['schema'] == 'R179_BUILDER_CONTEXT_POLICY_SCOPE_V1', 'existing_R179_scope')
    require(scope['policy']['sha256'] == 'b36949c2d93662b876b6519eee9dddba0e5af94a294e1f570f37685cd9604a2b',
            'exact_Main_context_policy')
    require(scope['cpu']['passed'] == 108 and scope['cpu']['subtests_passed'] == 145, 'Main_CPU_READY')
    for name in ('directive', 'policy', 'tests', 'cpu'):
        reference = scope[name]
        require(digest(Path(reference['path']).read_bytes()) == reference['sha256'], 'exact_Main_bytes:' + name)
    print(json.dumps(dict(status='EXISTING_MAIN_READY_GO_VERIFIED', execution_performed=False,
        operator='research_loop/workers/r179_context_survival_20260917/node4/node4_rollout.py',
        still_required='actual-source CPU, existing confinement and exact saved-boundary admission'), sort_keys=True))
    return 0


def main(argv=None):
    if '--probe-stdin' in (sys.argv[1:] if argv is None else argv):
        print(json.dumps(remote_probe(json.load(sys.stdin)), sort_keys=True))
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    stage = commands.add_parser('prepare')
    stage.add_argument('--census', default=DEFAULT_CENSUS)
    stage.add_argument('--roster', default=DEFAULT_ROSTER)
    stage.add_argument('--output', required=True)
    check = commands.add_parser('validate-scope')
    check.add_argument('--scope', default='research_loop/workers/r179_context_survival_20260917/BUILDER_SCOPE.json')
    args = parser.parse_args(argv)
    try:
        return prepare(args.census, args.roster, args.output) if args.action == 'prepare' else validate_scope(args.scope)
    except (OSError, ValueError, KeyError, IndexError, subprocess.TimeoutExpired) as error:
        parser.error(str(error))


if __name__ == '__main__':
    raise SystemExit(main())
