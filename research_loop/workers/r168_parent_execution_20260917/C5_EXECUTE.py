"""C5-only parent handoff after Main-pinned actual recovery; no child operations."""

import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import time

from gpu import orch_r133_programme_parent as parent
from gpu import orch_r153_community_parents as community
from gpu import orch_r167_parent_takeover as files
from gpu import orch_r168_c5_parent_recovery_gate as recovery
from gpu import orch_r168_parent_rollout as transaction


STAGE=Path(__file__).resolve().parent
ROOT=STAGE.parents[2]
OUTPUT=STAGE/'C5_RECOVERED_PARENT_HANDOFF'
CONTINUITY=ROOT/'research_loop/workers/r166_retelling_handoff_20260917/C5_RECOVERY2_CONTINUITY.json'
OPERATOR=STAGE/'ROLLOUT/EXECUTE.py'


def ref(path):
    return dict(path=str(path.resolve()),sha256=files.sha(path))


def main():
    OUTPUT.mkdir(mode=0o700)
    tests=['tests/test_orch_r168_c5_parent_recovery_gate.py','tests/test_orch_r168_parent_rollout.py',
        'tests/test_orch_r167_parent_takeover.py','tests/test_orch_r167_parent_watchdog.py',
        'tests/test_orch_r168_manual_parent_turn.py','tests/test_orch_r168_community_prompt_patch.py']
    names=tests+['gpu/orch_r168_c5_parent_recovery_gate.py','gpu/orch_r168_parent_rollout.py',
        'gpu/orch_r167_parent_takeover.py','gpu/orch_r167_parent_watchdog.py','gpu/orch_r168_manual_parent_turn.py',
        'gpu/orch_r168_community_prompt_patch.py',str(OPERATOR),str(Path(__file__))]
    pins={name:files.sha(ROOT/name) for name in names}
    result=subprocess.run(['uv','run','--with','pytest','--with','pytest-subtests','python','-m','pytest','-q',*tests],
        cwd=ROOT,capture_output=True,text=True,timeout=60,
        env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES=''))
    (OUTPUT/'CPU_OUTPUT.txt').write_text(result.stdout+result.stderr)
    assert result.returncode==0 and all(files.sha(ROOT/name)==expected for name,expected in pins.items())
    community.write(OUTPUT/'CPU_GATE.json',dict(status='PASS',execution_kind='CPU_ONLY',pins=pins,
        output=ref(OUTPUT/'CPU_OUTPUT.txt'),finished_unix=time.time()))
    continuity=json.loads(files.read_file(CONTINUITY))
    child=recovery.child_binding(continuity)
    community.write(OUTPUT/'MAIN_CONDITION_MET.json',dict(authority='Main',recorded_unix=time.time(),
        instruction='C5 recovery now confirmed: C5_RECOVERY2_CONTINUITY.json status ACTUAL_LOADED_SAVED28_CONTINUITY_VERIFIED, native4018497 ticks17068304, LOADED2900 resume=true2478steps. Verify current custody and proceed previously approved C5 parent-only final-policy migration; no child restart.',
        original_authority=ref(STAGE/'ROLLOUT/MAIN_GO.json'),actual_paths_confirmation=ref(STAGE/'MAIN_CONFIRMATION_0845.json'),
        continuity=ref(CONTINUITY),child=child,scope='C5_PARENT_ONLY',no_native_restart=True))
    original_index=json.loads(files.read_file(STAGE/'INDEX.json'))
    old_start=json.loads(files.read_file(original_index['candidates']['C5']['predecessor_start']['path']))
    old_config=json.loads(files.read_file(old_start['config']['path']))
    script='''import hashlib,json,time
from pathlib import Path
from gpu.orch_r125_stream_journal import _decode,_digest
child=CHILD
process=Path('/proc')/str(child['pid']);fields=(process/'stat').read_text().rsplit(')',1)[1].split()
argv=(process/'cmdline').read_bytes().rstrip(b'\\0').decode().split('\\0')
assert fields[19]==child['start_ticks'] and fields[0] not in ('Z','X','T','t')
assert argv==child['argv'] and str((process/'cwd').resolve())==child['cwd']
for key in ('config_ref','plan_ref','loaded_ref'):
 entry=child[key];path=Path(entry['path']);assert not path.is_symlink() and path.stat().st_size<16777216
 assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256']
record=_decode(Path(child['loaded_ref']['path']).read_bytes())
assert record['kind']=='LOADED' and record['index']==2900 and record['sha256']==child['loaded_ref']['record_sha256']
assert _digest({key:value for key,value in record.items() if key!='sha256'})==record['sha256']
assert record['document']['pid']==child['pid'] and record['document']['resume'] is True and record['document']['optimizer_steps']==2478
print(json.dumps(dict(status='CURRENT_RECOVERED_C5_VERIFIED',child=child,observed_unix=time.time(),state=fields[0],no_mutations=True)))
'''.replace('CHILD',repr(child))
    observed=parent.remote(ROOT,old_config,script)
    community.write(OUTPUT/'CURRENT_RECOVERY_VERIFIED.json',observed)
    specification=importlib.util.spec_from_file_location('r168_original_rollout_operator',OPERATOR)
    module=importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    tree=ast.parse(files.read_file(OPERATOR))
    class_node=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='Operations')
    original=next(node for node in class_node.body if isinstance(node,ast.FunctionDef) and node.name=='preflight')
    modified=copy.deepcopy(original)
    scope=[node for node in ast.walk(modified) if isinstance(node,ast.Tuple)
        and all(isinstance(entry,ast.Constant) for entry in node.elts)
        and [entry.value for entry in node.elts]==['C2','C3','C4']]
    assert len(scope)==1
    scope[0].elts=[ast.Constant(value='C5')]
    assignments=[node for node in modified.body if isinstance(node,ast.Assign)
        and any(isinstance(target,ast.Name) and target.id=='child' for target in node.targets)]
    assert len(assignments)==1
    original_assignment=copy.deepcopy(assignments[0].value)
    assignments[0].value=ast.parse(repr(child),mode='eval').body
    check=copy.deepcopy(modified)
    check_scope=next(node for node in ast.walk(check) if isinstance(node,ast.Tuple)
        and len(node.elts)==1 and isinstance(node.elts[0],ast.Constant) and node.elts[0].value=='C5')
    check_scope.elts=[ast.Constant(value=value) for value in ('C2','C3','C4')]
    next(node for node in check.body if isinstance(node,ast.Assign)
        and any(isinstance(target,ast.Name) and target.id=='child' for target in node.targets)).value=original_assignment
    assert ast.dump(check)==ast.dump(original)
    namespace=dict(vars(module))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[modified],type_ignores=[])),str(OPERATOR)+'#C5-preflight','exec'),namespace)
    operations=module.Operations('C5')
    operations.preflight=namespace['preflight'].__get__(operations,type(operations))
    community.write(OUTPUT/'OPERATOR_BINDING.json',dict(original_operator=ref(OPERATOR),
        delta='preflight allowlist narrowed to C5 and child identity replaced only by verified recovery binding',
        otherwise_preflight_AST_identical=True,no_running_parent_source_changes=True,child=child,
        cpu_gate=ref(OUTPUT/'CPU_GATE.json')))
    with (ROOT/'research_loop/COORDINATION.md').open('a') as stream:
        stream.write('\n[Builder] 2026-09-17 '+time.strftime('%H:%M:%S',time.gmtime())+' UTC — R168 C5 recovered-parent migration ONLY: '
            'Main continuity condition independently rechecked live native4018497/ticks17068304+exactGUARD/PLAN/LOADED2900 bytes; '
            'resume=True2478steps, same life. '+str(OUTPUT/'CURRENT_RECOVERY_VERIFIED.json')+' SHA'+files.sha(OUTPUT/'CURRENT_RECOVERY_VERIFIED.json')+
            '. Fresh own CPU '+str(OUTPUT/'CPU_GATE.json')+' SHA'+files.sha(OUTPUT/'CPU_GATE.json')+
            ' PASS before parent signals. Existing reviewed gate/source/config, no child restart, no C1 resend; '
            'watchdog/settled-rendered-ledger/lock/executable transport preflight preserved.\n')
    try:
        transaction.handoff(operations)
        community.write(OUTPUT/'STARTED_REF.json',dict(started=ref(STAGE/'ROLLOUT/C5/STARTED.json'),
            no_native_changes=True,observed_unix=time.time()))
    except BaseException as error:
        community.write(OUTPUT/'DEFERRED_OR_FAILED.json',dict(error_type=type(error).__name__,error=str(error)[:2000],
            observed_unix=time.time(),no_implicit_retry=True))
        raise


if __name__=='__main__':
    def interrupted(signum,frame):
        raise InterruptedError('C5_parent_operator_interrupted')
    signal.signal(signal.SIGTERM,interrupted)
    main()
