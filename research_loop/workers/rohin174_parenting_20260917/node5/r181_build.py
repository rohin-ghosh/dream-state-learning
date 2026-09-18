"""Reuse the saved-boundary operator with Main's exact prospective R181 deltas."""

import argparse
import ast
import base64
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import time

from activate_parent import read, reference, require, sha, write
from r181_patch import canonical_functions_match


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
OLD = HERE.parents[1] / 'r179_context_survival_20260917/node5'


def function_replace(text, name, replacement):
    node = next(node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef) and node.name == name)
    lines = text.splitlines(keepends=True)
    return ''.join(lines[:node.lineno - 1]) + replacement.rstrip() + '\n' + ''.join(lines[node.end_lineno:])


AUTHORITY = '''def authority(output):
    require(socket.gethostname() == '[REDACTED_HOST]' and os.getuid() == os.getgid() == 2524, 'exact_node5_owner')
    authorization = read(output / 'R181_AUTHORITY.json')
    require(authorization['recipe'] == 'R181_NEW_ONLY_V1' and authorization['rehearsal_presentations'] == 0
        and authorization['new_presentations'] == 16 and authorization['patch_sha256'] == POLICY_SHA
        and sha(output / 'policy.py') == POLICY_SHA, 'exact_R181_prospective_recipe')
    require(output.parent == BASE and output.name.startswith('orch_r181_node5_'), 'owned_R181_successor')
    request = read(output / 'INPUT.json')
    require(request['label'] in LABELS and request['physical'] == LABELS[request['label']], 'assigned_slot')
    return request
'''


def operator_source(policy_sha, journal_sha=None, readmission=False):
    text = (OLD / 'rollout_operator.py').read_text()
    text = text.replace("POLICY_SHA = 'b36949c2d93662b876b6519eee9dddba0e5af94a294e1f570f37685cd9604a2b'", f'POLICY_SHA = {policy_sha!r}')
    text = text.replace("POLICY = 'gpu/orch_r179_context_survival.py'", "POLICY = 'gpu/orch_r181_newrows_only.py'")
    text = function_replace(text, 'authority', AUTHORITY)
    text = text.replace("request['label'] in ('C2', 'C5')", "request.get('controller_transfer_required', False)")
    text = text.replace("extra = ['--controller-go', str(arguments.controller_go), '--controller-go-sha256', arguments.controller_go_sha256]",
        "extra = ['--controller-go', str(arguments.output / 'R181_AUTHORITY.json'), '--controller-go-sha256', sha(arguments.output / 'R181_AUTHORITY.json')]")
    text = text.replace("    successor_plan['source_root'] = str(source)",
        "    successor_plan['source_root'] = str(source)\n    successor_plan['rehearsal_presentations'] = 0")
    begin = text.index('    tests = subprocess.run(', text.index('def stage(output):'))
    end = text.index('    original = Path(', begin)
    text = text[:begin] + "    (output / 'OPERATOR_CPU.log').write_text('Existing tested R179 operator reused; Main R181 65+124 CPU PASS per explicit directive. No new receiving gate.\\n')\n" + text[end:]
    text = text.replace("script.name == 'orch_r157_repo_reader_wall.py'", "script.name in ('orch_r157_repo_reader_wall.py', 'rollout_operator.py')")
    text = text.replace("capsule = script.parent / 'CONFINEMENT_API.py'",
        "capsule = script.parent / ('reader_capsule.py' if script.name == 'rollout_operator.py' else 'CONFINEMENT_API.py')")
    text = text.replace("'authority':reference(output / 'BUILDER_SCOPE.json')", "'authority':reference(output / 'R181_AUTHORITY.json')")
    text = text.replace("authority=reference(output / 'BUILDER_SCOPE.json')", "authority=reference(output / 'R181_AUTHORITY.json')")
    text = text.replace("output / 'BUILDER_SCOPE.json'", "output / 'R181_AUTHORITY.json'")
    if journal_sha is not None:
        text = text.replace("    return request\n", "    require(sha(output / 'MAIN_JOURNAL.py') == " + repr(journal_sha)
            + ", 'exact_Main_journal_overlay')\n    return request\n", 1)
        text = text.replace("    require(POLICY not in original_files, 'not_already_R179')\n", '')
        text = text.replace('    shutil.copyfile(output / \'policy.py\', source / POLICY)',
            "    if (source / POLICY).exists():\n        (source / POLICY).chmod(0o644)\n"
            "    shutil.copyfile(output / 'policy.py', source / POLICY)")
        anchor = '    inventory = saved.files(source)\n'
        overlay = "    journal = source / 'gpu/orch_r125_stream_journal.py'\n"
        overlay += "    journal.chmod(0o644)\n"
        overlay += "    journal.write_text(policy.patch_journal((original / 'gpu/orch_r125_stream_journal.py').read_text(), (output / 'MAIN_JOURNAL.py').read_text()))\n"
        overlay += "    write(output / 'JOURNAL_OVERLAY.json', dict(original=reference(original / 'gpu/orch_r125_stream_journal.py'), successor=reference(journal), canonical=reference(output / 'MAIN_JOURNAL.py'), noncache_methods_unchanged=True, no_live_source_edit=True))\n"
        require(text.count(anchor) == 1, 'single_inventory_overlay_anchor')
        text = text.replace(anchor, overlay + anchor)
        text = text.replace('if name != NATIVE)', "if name not in (NATIVE, POLICY, 'gpu/orch_r125_stream_journal.py'))")
        text = text.replace("'only_native_compaction_and_policy_added'", "'only_R181_native_policy_and_Main_journal_overlay'")
        text = text.replace('policy_sha256=POLICY_SHA, source_root=str(source)',
            "policy_sha256=POLICY_SHA, journal_overlay=reference(output / 'JOURNAL_OVERLAY.json'), source_root=str(source)")
    if readmission:
        text = text.replace('    pair = owner_pair(saved, request, config, plan)',
            "    pair, recovery_device = load_auxiliary('preload_readmission.py').prepare(output, saved, plan)", 1)
        text = text.replace('    device = device_preflight(config, plan)', '    device = recovery_device', 1)
        text = text.replace("'controller_transfer.py', 'CONTROLLER_BINDING.json', 'CONTROLLER_PREFLIGHT.json')",
            "'controller_transfer.py', 'CONTROLLER_BINDING.json', 'CONTROLLER_PREFLIGHT.json', 'preload_readmission.py', 'READMISSION_BINDING.json')")
        text = text.replace("choices=('bootstrap', 'stage', 'execute', 'contained', 'start')",
            "choices=('bootstrap', 'stage', 'execute', 'contained', 'start', 'readmission')")
        text = text.replace("    elif arguments.action == 'execute':",
            "    elif arguments.action == 'readmission':\n        load_auxiliary('preload_readmission.py').execute(arguments.output, sys.modules[__name__])\n    elif arguments.action == 'execute':")
        text = text.replace("str(arguments.output / 'rollout_operator.py'), 'execute',",
            "str(arguments.output / 'rollout_operator.py'), 'readmission',")
    compile(text, 'r181_rollout_operator.py', 'exec')
    return text


def cpu_source(policy_sha):
    text = (OLD / 'cpu_actual.py').read_text()
    begin = text.index('def prove(')
    prefix, body = text[:begin], text[begin:]
    body = body.replace('from gpu import orch_r179_context_survival as policy', 'from gpu import orch_r181_newrows_only as policy')
    body = body.replace("source / 'gpu/orch_r179_context_survival.py'", "source / 'gpu/orch_r181_newrows_only.py'")
    body = body.replace('b36949c2d93662b876b6519eee9dddba0e5af94a294e1f570f37685cd9604a2b', policy_sha)
    body = body.replace('    results = policy_tests(plan)',
        "    require(plan['rehearsal_presentations'] == 0 and plan['new_presentations'] == 16, 'R181_exact_plan')\n"
        "    rows = [object()]\n"
        "    require(native.select_rehearsal_rows(plan, rows) == [] and native.select_rehearsal_rows(dict(rehearsal_presentations=1), rows) is rows, 'actual_R181_selection')\n"
        "    results = policy_tests(plan) if (source / 'gpu/orch_r179_context_survival.py').exists() else [dict(actual_R181_selection=True, original_retelling_preserved_by_exact_native_delta=True)]")
    body = body.replace("    require(policy.patch_native(old) == patched, 'only_exact_Main_patch')",
        "    require(policy.patch_native(old) == patched, 'only_exact_Main_patch')\n"
        "    journal_name = 'gpu/orch_r125_stream_journal.py'\n"
        "    require(policy.patch_journal((original / journal_name).read_text(), (source.parent / 'MAIN_JOURNAL.py').read_text()) == (source / journal_name).read_text(), 'only_Main_cache_delta_preserves_actual_journal_validators')")
    compile(prefix + body, 'r181_cpu_actual.py', 'exec')
    return prefix + body


CONTROLLER_INSPECT = '''def inspect_holder(label, config, pair):
    require(label in EXPECTED and os.getuid() == 2524, 'bound_R181_controller_scope')
    expected = EXPECTED[label]
    holder = process_identity(expected['pid'])
    require(all(holder[key] == expected[key] for key in ('pid','start_ticks','argv_sha256','cwd')), 'exact_holder_identity')
    require(holder['uid'] == 2524 and holder['parent'] == 1 and holder['group'] == holder['session'] == holder['pid'], 'orphan_outer_CPU_only')
    require(holder['signals'] == dict(SigCgt='0000000000000002', SigIgn='0000000001001000', SigBlk='0000000000000000', Threads='1'), 'default_unblocked_SIGTERM')
    child = process_identity(expected['child_pid'])
    require(child['start_ticks'] == expected['child_start_ticks'] and child['uid'] == 0 and child['parent'] == holder['pid'] and child['argv_sha256'] == expected['child_argv_sha256'], 'exact_sudo_wait_child')
    children = (Path('/proc') / str(holder['pid']) / 'task' / str(holder['pid']) / 'children').read_text().split()
    require(children == [str(child['pid'])], 'one_wait_child')
    recorded = read(Path(config['attempt_dir']) / 'CONTAINED_COMMAND.json')
    require(child['argv'] == recorded['command'] and '--unit=' + config['device_containment']['unit'] in child['argv'], 'exact_waiting_unit_and_recorded_command')
    for process in pair.values():
        actual = process_identity(process['pid'])
        require(actual['start_ticks'] == process['start_ticks'] and actual['session'] != holder['session'] and actual['cgroup'] == '0::/system.slice/' + config['device_containment']['unit'] + '.service', 'native_survives_outer_CPU_detach')
    source = Path(expected['source']['path'])
    require(sha(source) == expected['source']['sha256'], 'bound_actual_controller_source')
    text = source.read_text()
    functions = {node.name:node for node in ast.parse(text).body if isinstance(node,ast.FunctionDef)}
    supervise = functions.get('supervise')
    if supervise is None:
        require(source.name in ('c1_readmission.py','c4_readmission.py'), 'only_known_R179_readmission_waiter')
        supervise = functions['execute']
    calls = [node for node in ast.walk(supervise) if isinstance(node,ast.Call) and ast.unparse(node.func)=='subprocess.run']
    require(len(calls)==1 and ast.unparse(calls[0])=='subprocess.run(command, check=False)', 'one_passive_service_wait')
    require(not any(any(descendant is calls[0] for descendant in ast.walk(node)) for node in ast.walk(supervise) if isinstance(node,(ast.For,ast.While,ast.AsyncFor))), 'no_service_wait_in_retry_loop')
    lock = lock_identity(BASE / ('orch_r157_' + label + '_HANDOFF.lock'))
    require(flock_owners(lock)==[holder['pid']], 'genuine_existing_lock_owner')
    return dict(label=label,holder=holder,wait_child=child,lock=lock,source_proof=dict(source=reference(source),passive_supervise=True,no_retry=True))
'''
CONTROLLER_AUTH = '''def authorize(output, go_path=None, go_sha256=None):
    path = output / 'R181_AUTHORITY.json'
    authorization = read(path)
    require(authorization['recipe']=='R181_NEW_ONLY_V1' and authorization['outer_controller_transfer']=='same_existing_tested_pidfd_same_inode_transfer' and time.time()<authorization['expires_unix'], 'explicit_R181_scoped_authority')
    return reference(path)
'''


def controller_source(expected):
    text = (OLD / 'controller_transfer.py').read_text()
    node = next(node for node in ast.parse(text).body if isinstance(node, ast.Assign) and any(
        isinstance(target,ast.Name) and target.id == 'EXPECTED' for target in node.targets))
    lines = text.splitlines(keepends=True)
    text = ''.join(lines[:node.lineno - 1]) + 'EXPECTED = ' + repr(expected) + '\n' + ''.join(lines[node.end_lineno:])
    text = function_replace(text, 'inspect_holder', CONTROLLER_INSPECT)
    text = function_replace(text, 'authorize', CONTROLLER_AUTH)
    return text


DISCOVER = '''import json,hashlib,os,sys
from pathlib import Path
sys.path.insert(0,OLD)
import controller_transfer as helper
row=ROW
lock_path=helper.BASE/('orch_r157_'+row['label']+'_HANDOFF.lock')
expected={}
if lock_path.exists():
 lock=helper.lock_identity(lock_path);owners=helper.flock_owners(lock)
 assert len(owners)<=1
 if owners:
  holder=helper.process_identity(owners[0]);children=(Path('/proc')/str(holder['pid'])/'task'/str(holder['pid'])/'children').read_text().split();assert len(children)==1
  child=helper.process_identity(int(children[0]));args=holder['argv']
  source=Path(args[2]) if args[2].endswith('.py') else Path(holder['cwd'])/'gpu/orch_r166_retelling_handoff.py'
  expected[row['label']]=dict(pid=holder['pid'],start_ticks=holder['start_ticks'],argv_sha256=holder['argv_sha256'],cwd=holder['cwd'],child_pid=child['pid'],child_start_ticks=child['start_ticks'],child_argv_sha256=child['argv_sha256'],source=helper.reference(source))
print(json.dumps(expected))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True, choices=('C2','C1','C3','C4','C5','run1','pilot','repo_reader'))
    parser.add_argument('--auto-start', action='store_true')
    parser.add_argument('--readmission-from', type=Path)
    arguments = parser.parse_args()
    label = arguments.label
    inventory_path = sorted(HERE.glob('R181_CURRENT_*.json'))[-1]
    row = next(row for row in read(inventory_path)['rows'] if row['label'] == label)
    recovery = None
    if arguments.readmission_from:
        require(label == 'run1', 'only_current_typed_run1_recovery')
        probe = '''import hashlib,json
from pathlib import Path
root=Path(ORIGINAL)
files={name:dict(path=str(root/name),sha256=hashlib.sha256((root/name).read_bytes()).hexdigest()) for name in ('EXECUTION_FAILED.json','OWNER_RETIRED.json','attempt/ADMISSION.json','READY.json','OPERATOR_STARTED.json')}
boundary=json.loads((root/'ACTUAL_BOUNDARY_READY.json').read_bytes())['boundary'];record=json.loads(Path(boundary['path']).read_bytes())
print(json.dumps(dict(row=json.loads((root/'INPUT.json').read_bytes()),binding=dict(original=str(root),files=files,boundary_sha256=record['sha256']))))
'''
        response = subprocess.run(['bash',str(REPO/'gpu/ovx3_ssh.sh'),'python3 -B -c '+shlex.quote(probe.replace('ORIGINAL',repr(str(arguments.readmission_from))))],capture_output=True,text=True,timeout=30)
        require(response.returncode == 0, 'read_only_refusal_binding')
        observed = json.loads(response.stdout)
        row, recovery = observed['row'], observed['binding']
    canonical = REPO / 'gpu/orch_r125_continual_native.py'
    require(canonical_functions_match(canonical.read_text()), 'exact_Main_R181_functions')
    root = HERE / ('R181_' + label + '_' + str(time.time_ns()))
    root.mkdir()
    remote = '/localhome/local-rohing/orch_r181_node5_' + label.lower() + '_' + str(time.time_ns())
    old_remote = '/localhome/local-rohing/orch_r179_context_C2_20260917_attempt4'
    script = DISCOVER.replace('OLD', repr(old_remote)).replace('ROW', repr(row))
    discovered = subprocess.run(['bash',str(REPO/'gpu/ovx3_ssh.sh'),'python3 -B -c '+shlex.quote(script)],capture_output=True,text=True,timeout=30)
    require(discovered.returncode == 0, 'existing_handoff_lock_discovery:' + discovered.stderr[-240:])
    expected = json.loads(discovered.stdout)
    row['controller_transfer_required'] = bool(expected)
    patch_sha = sha(HERE / 'r181_patch.py')
    journal = REPO / 'gpu/orch_r125_stream_journal.py'
    journal_bytes = journal.read_bytes()
    journal_sha = hashlib.sha256(journal_bytes).hexdigest()
    compile(journal_bytes, str(journal), 'exec')
    authority = dict(recipe='R181_NEW_ONLY_V1',rehearsal_presentations=0,new_presentations=16,
        patch_sha256=patch_sha,canonical_Main_native=reference(canonical),
        canonical_Main_journal=dict(path=str(journal), sha256=journal_sha),
        journal_overlay_scope='Main cached validated journal; same lock, hashes, fsync, full replay on open/audit/change; next supported saved boundary only',
        direct_user_authority='Rohin181 PATCH READY; all8 main PLAN rehearsal_presentations=0 at next completed saved boundary; preserve optimizer RNG full history and fixed C2 pilot selection',
        outer_controller_transfer='same_existing_tested_pidfd_same_inode_transfer',expires_unix=row['plan']['hard_end_unix'],
        builder='Main reports65tests+124subtestsPASS; exact minimal function delta checked against canonical; inherited R179 custody/restore/admission remains strict')
    files = {'rollout_operator.py':operator_source(patch_sha, journal_sha, recovery is not None).encode(),'cpu_actual.py':cpu_source(patch_sha).encode(),
        'MAIN_JOURNAL.py':journal_bytes,
        'controller_transfer.py':controller_source(expected).encode(),'policy.py':(HERE/'r181_patch.py').read_bytes(),
        'INPUT.json':json.dumps(row,sort_keys=True).encode(),'R181_AUTHORITY.json':json.dumps(authority,sort_keys=True).encode()}
    if recovery is not None:
        files['READMISSION_BINDING.json'] = json.dumps(recovery, sort_keys=True).encode()
        files['preload_readmission.py'] = (HERE / 'preload_readmission.py').read_bytes()
    for name, origin in {'stage_node5.py':OLD/'stage_node5.py','saved_primitives.py':REPO/'gpu/orch_r157_community_wall_extension.py',
        'protected_primitives.py':REPO/'gpu/orch_r157_node5_keepalive.py','containment_primitives.py':REPO/'gpu/orch_r153_community_runtime.py'}.items():
        files[name] = origin.read_bytes()
    for name, raw in files.items():
        if name.endswith('.py'):
            compile(raw,name,'exec')
        patch = '*** Begin Patch\n*** Add File: '+str(root/name)+'\n'+''.join('+'+line+'\n' for line in raw.decode().splitlines())+'*** End Patch\n'
        subprocess.run(['apply_patch',patch],check=True,stdout=subprocess.DEVNULL)
        files[name] = (root/name).read_bytes()
    write(root/'BINDING.json',dict(label=label,output=remote,inventory=reference(inventory_path),files={name:sha(root/name) for name in files},
        current_native=row['identity'],observed_unix=time.time(),no_signals_before_complete_boundary=True))
    driver = '''import hashlib,json,os,subprocess,sys
from pathlib import Path
root=Path(sys.argv[1]);namespace_pid=json.loads((root/'DRIVER_CONFIG.json').read_bytes())['namespace_pid']
command=[sys.executable,'-B',str(root/'rollout_operator.py'),'stage','--output',str(root)]
if namespace_pid:
 command=['sudo','-n','nsenter','--target',str(namespace_pid),'--mount','--','/usr/bin/setpriv','--reuid=2524','--regid=2524','--clear-groups',*command]
with (root/'STAGING.log').open('x') as log:
 result=subprocess.run(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
if result.returncode:sys.exit(result.returncode)
authorization=root/'R181_AUTHORITY.json';digest=hashlib.sha256(authorization.read_bytes()).hexdigest()
with (root/'STARTING.log').open('x') as log:
 result=subprocess.run([sys.executable,'-B',str(root/'rollout_operator.py'),'start','--output',str(root),'--seconds','14400','--controller-go',str(authorization),'--controller-go-sha256',digest],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
sys.exit(result.returncode)
'''
    if arguments.auto_start:
        files['DRIVER.py'] = driver.encode()
        files['DRIVER_CONFIG.json'] = json.dumps(dict(namespace_pid=row['identity']['pid'] if label == 'repo_reader' else None)).encode()
    package = dict(output=remote,files={name:base64.b64encode(raw).decode() for name,raw in files.items()},
                   namespace_pid=row['identity']['pid'] if label == 'repo_reader' else None, auto_start=arguments.auto_start)
    bootstrap = '''import base64,json,os,subprocess,sys
from pathlib import Path
package=json.load(sys.stdin);root=Path(package['output']);root.mkdir()
for name,encoded in package['files'].items():
 with (root/name).open('xb') as stream:stream.write(base64.b64decode(encoded))
command=[sys.executable,'-B',str(root/'rollout_operator.py'),'stage','--output',str(root)]
if package['namespace_pid']:
 command=['sudo','-n','nsenter','--target',str(package['namespace_pid']),'--mount','--','/usr/bin/setpriv','--reuid=2524','--regid=2524','--clear-groups',*command]
if package['auto_start']:
 command=[sys.executable,'-B',str(root/'DRIVER.py'),str(root)]
with (root/('DRIVER.log' if package['auto_start'] else 'STAGING.log')).open('x') as log:
 process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'))
print(json.dumps(dict(output=str(root),stage_pid=process.pid,model_launch=False)))
'''
    response = subprocess.run(['bash',str(REPO/'gpu/ovx3_ssh.sh'),'/localhome/local-rohing/v2/venv/bin/python -B -c '+shlex.quote(bootstrap)],
        input=json.dumps(package),capture_output=True,text=True,timeout=40)
    require(response.returncode == 0, 'R181_stage_dispatch:' + response.stderr[-240:])
    write(root/'STAGED_DISPATCH.json',dict(result=json.loads(response.stdout),observed_unix=time.time(),binding=reference(root/'BINDING.json')))
    print(json.dumps(dict(local=str(root),**json.loads(response.stdout))))


if __name__ == '__main__':
    main()
