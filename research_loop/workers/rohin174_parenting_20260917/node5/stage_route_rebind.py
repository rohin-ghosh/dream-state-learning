"""Freeze route-only successors and start them using the tested parent custody helper."""

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import time

from activate_parent import identity, read, reference, require, sha, write
from build_activation import add_copy
from rebind_parent import terminal_parent_receipt


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def stage(label, effort=False, examples=False):
    status_path = sorted(HERE.glob('BASELINE_STATUS_*.json'))[-1]
    row = next(row for row in read(status_path)['rows'] if row['label'] == label)
    manifest = read(row['manifest']['path'])
    old = Path(row['current_output'])
    route_active = sorted(HERE.glob('ROUTE_' + label + '_*/parent/ACTIVE_PARENT.json'))
    previous_binding = None
    if route_active:
        old = route_active[-1].parent
        previous_binding = read(old.parent / 'BINDING.json')
    dead = False
    if label == 'repo_reader' and not (old / 'ACTIVE_PARENT.json').exists():
        require(not row['operator_live'], 'old_reader_waiter_must_be_terminal')
        old = Path(manifest['predecessor']['output_path'])
        owner = dict(identity(manifest['predecessor']['pid']), label=label)
        config_path = Path(manifest['predecessor']['config']['path'])
    else:
        active = read(old / 'ACTIVE_PARENT.json')
        owner = dict(active['identity'], label=label)
        try:
            require(identity(owner['pid'])['start_ticks'] == owner['start_ticks'], 'exact_current_parent')
        except FileNotFoundError:
            terminal_parent_receipt(old)
            dead = True
        config_path = old / 'CONFIG.json'
    original = read(config_path)
    if examples:
        require(label != 'run1', 'R188_run1_sole_Main_turn_not_automatic_parent')
        require(not (old / 'WITHDRAWAL_COMPLETE.json').exists(), 'R188_fixed_withdrawal_not_restarted')
        statuses = sorted(old.glob('STATUS_*.json'))
        require(not statuses or read(statuses[-1]).get('status') != 'WITHDRAWAL_NO_NEW_PARENT_OR_PEER',
                'R188_existing_withdrawal_window_excluded')
    root = HERE / ('ROUTE_' + label + '_' + str(time.time_ns()))
    source = root / 'source'
    source.mkdir(parents=True)
    for name, expected in manifest['source_pins'].items():
        origin = Path(manifest['source']) / name
        require(sha(origin) == expected, 'unchanged_tested_arm_source')
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['cp','--',str(origin),str(target)], check=True)
        require(sha(target) == expected, 'byte_exact_unchanged_source_copy')
    extras = ('rebind_parent.py', 'console_baseline.py', 'provider_route.py', 'retry_prepublication.py',
              'r184_parent_effort.py', 'test_r184_parent_effort.py',
              'test_provider_route.py', 'test_rebind_parent.py', 'test_console_baseline.py','test_retry_prepublication.py')
    for name in extras:
        add_copy(source / name, (HERE / name).read_bytes())
    if effort:
        from r184_parent_effort import SCHEMA
        fixed = REPO / 'research_notes/analysis/R184_FIXED_FIRST_COMPARISON_2026-09-17.md'
        add_copy(source / 'R184_FIXED_FIRST_COMPARISON.md', fixed.read_bytes())
        write(source / 'R184_EFFORT_PHASE.json', dict(schema=SCHEMA, label=label,
            fixed_plan_sha256=sha(fixed), observed_unix=time.time(), no_baseline=True,
            treatment='private_effort_questions_both_directions_at_existing_next_due_boundary',
            unchanged=['arm','cadence','word_limit','withdrawal_clock','pending_publications','child']))
        extras += ('R184_FIXED_FIRST_COMPARISON.md', 'R184_EFFORT_PHASE.json')
    if examples:
        module = REPO / 'gpu/orch_r188_parent_examples.py'
        add_copy(source / 'gpu/orch_r188_parent_examples.py', module.read_bytes())
        write(source / 'R188_EXAMPLES_PHASE.json', dict(label=label,main_module_sha256=sha(module),
            reported_source='Rohin188 relayed by Fable; not fabricated transcripts',observed_unix=time.time(),
            no_baseline=True,run1_Main_owned=True,C2_excluded=True))
        extras += ('gpu/orch_r188_parent_examples.py', 'R188_EXAMPLES_PHASE.json')
    tests = [str(source / name) for name in extras if name.startswith('test_') and name != 'test_console_baseline.py']
    command = ['uv','run','--offline','--no-project','--with','pytest','--python','/usr/bin/python3',
        'python','-B','-m','pytest','-q','-p','no:cacheprovider','-c','/dev/null','--basetemp',str(root/'CPU_TMP'),*tests]
    result = subprocess.run(command, capture_output=True, text=True,
        env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(source)))
    (root / 'CPU.stdout').write_text(result.stdout)
    (root / 'CPU.stderr').write_text(result.stderr)
    require(result.returncode == 0, 'focused_route_and_existing_custody_regressions')
    pins = [reference(source / name) for name in list(manifest['source_pins']) + list(extras)]
    cpu_path = root / 'CPU.json'
    write(cpu_path, dict(status='PASS', execution='CPU_ONLY', stdout=reference(root/'CPU.stdout'),
        source_pins=pins, inherited_arm_CPU=manifest['cpu_receipt'], no_learner_signals=True,
        observed_unix=time.time(), builder='[Builder] Non-material working-route bind plus pending-publication custody carry'))
    remote = '/localhome/local-rohing/orch_r175_node5_' + root.name.lower()
    archive = root / 'SOURCE.tar'
    names = list(manifest['source_pins']) + list(extras)
    subprocess.run(['tar','-cf',str(archive),'-C',str(source),*names], check=True)
    with archive.open('rb') as stream:
        transferred = subprocess.run(['bash',str(REPO/'gpu/ovx3_ssh.sh'),
            'test ! -e '+shlex.quote(remote)+' && mkdir -p '+shlex.quote(remote+'/source')+
            ' && tar -xf - -C '+shlex.quote(remote+'/source')], stdin=stream, capture_output=True, timeout=40)
    require(transferred.returncode == 0, 'source_transport')
    successor = dict(original)
    if 'r175_arm' not in successor:
        import sys
        sys.path.insert(0, str(REPO))
        from gpu import orch_r175_parent_arms as arms
        successor = arms.configure(original, manifest['arm'])
        successor.update(r166_schema='R166_PARENT_SUCCESSOR_V1', object_turn_limit=3, community_learner=False)
    successor.update(source_root=remote+'/source', cursor_store=remote+'/cursor')
    successor_path = root / 'SUCCESSOR_CONFIG.json'
    write(successor_path, successor)
    fable_path = sorted(HERE.glob('FABLE_RECONCILIATION_*.json'))[-1]
    fable = next(row for row in read(fable_path)['rows'] if row['label'] == label)
    require(fable['messages'], 'existing_Fable_baseline_bound_no_new_baseline')
    eligible = set(previous_binding['eligible_publication_ids']) if previous_binding and 'eligible_publication_ids' in previous_binding else set()
    initial_output = Path(row['current_output'])
    for attempt in list(old.glob('parent_*/RESULT.json')) + list(initial_output.glob('parent_*/RESULT.json')):
        result = read(attempt)
        if result.get('status') == 'PUBLISHED' and 'publication' in result:
            eligible.add(result['publication']['id'])
    first_path = old / 'FIRST_RENDERED_REQUEST.json'
    first = read(first_path) if first_path.exists() else None
    if first and first['publication']['id'] not in eligible:
        first = None
    legacy_binding = manifest['predecessor'].get('binding')
    binding_path = root / 'BINDING.json'
    write(binding_path, dict(label=label, owner=owner, old_output=str(old), config=str(config_path),
        successor_config=str(successor_path), source=str(source), output=str(root/'parent'),
        remote_source=remote+'/source', remote_cursor=remote+'/cursor',
        fable_ids=[entry['id'] for entry in fable['messages']], first_exposure=first,
        eligible_publication_ids=sorted(eligible), terminal_parent_recovery=dead,
        legacy_without_lock=label == 'repo_reader' and not (old / 'PARENT.lock').exists(),
        legacy_binding=legacy_binding['path'] if legacy_binding else None,
        legacy_source_sha256=manifest['predecessor']['source_on_disk']['sha256'],
        original_manifest=row['manifest'], cpu=reference(cpu_path),
        pins=pins+[reference(config_path),reference(successor_path),reference(cpu_path),reference(fable_path)]))
    write(root / 'START_ONCE.json', dict(binding=reference(binding_path), observed_unix=time.time(),
        authority='R188 Main reported examples, eligible ordinary parents only' if examples else
        'R184 fixed effort-both-directions prospective parent-only phase' if effort else
        'Rohin179/181 exact working-route parent-only repair; no common-baseline publication'))
    with (root / 'OPERATOR.log').open('x') as stream:
        process = subprocess.Popen(['/usr/bin/python3','-B',str(source/'rebind_parent.py'),'--binding',str(binding_path),
            '--sha256',sha(binding_path)], cwd=source, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT,
            start_new_session=True, close_fds=True, env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(source)))
    write(root / 'STARTED.json', dict(pid=process.pid, identity=identity(process.pid), binding=reference(binding_path),
        observed_unix=time.time(), status='STARTED_NOT_TAKEOVER_OR_PUBLICATION'))
    print(json.dumps(dict(label=label, root=str(root), pid=process.pid, binding=reference(binding_path), cpu=reference(cpu_path))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', choices=('repo_reader','C1','C3','C4','C5','run1','pilot'), required=True)
    parser.add_argument('--effort', action='store_true')
    parser.add_argument('--examples', action='store_true')
    args = parser.parse_args()
    stage(args.label, args.effort or args.examples, args.examples)
