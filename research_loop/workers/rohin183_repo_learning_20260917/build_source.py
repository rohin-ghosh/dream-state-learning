"""Freeze canonical native sources and a narrow truthful owned guard adapter."""

import ast
import json
from pathlib import Path

from research_loop.workers.rohin183_repo_learning_20260917.safe_snapshot import write,digest,require


OWN='research_loop/workers/rohin183_repo_learning_20260917'
TESTS=['tests/test_orch_r125_stream_journal.py','tests/test_orch_r125_continual_native.py',
    'tests/test_orch_r125_continual_stream.py','tests/test_orch_r127_pilot_console.py',
    OWN+'/test_runtime.py']


def adapt_guard(raw):
    text=raw.decode()
    before="and allocation['builder_entry_pushed'] is True, 'posted_allocation_and_CPU_provenance')"
    after="and allocation['builder_entry_logged'] is True\n        and child.sha(allocation['cpu_receipt_path']) == allocation['cpu_receipt_sha256']\n        and child.read(allocation['cpu_receipt_path'])['passed'] is True, 'posted_allocation_and_CPU_provenance')"
    require(text.count(before)==1,'exact_legacy_pushed_metadata_clause')
    text=text.replace(before,after)
    before="report = json.loads(subprocess.check_output(command, text=True, timeout=100))"
    after="bound = child.read(attempt/'PRE_SERVICE_ADMISSION.json')\n        child.require(bound['guard_sha256'] == child.sha(config_path)\n            and 0 <= time.time()-bound['verified_unix'] <= 120, 'fresh_bound_privileged_preservice_scan')\n        report = bound['report']"
    require(text.count(before)==1,'exact_scanner_invocation_in_supervise')
    return text.replace(before,after).encode()


def dependencies(repository,entries):
    pending=list(entries)
    found={}
    while pending:
        name=pending.pop()
        if name in found:
            continue
        path=repository/name
        require(path.is_file() and not path.is_symlink(),'regular_runtime_source:'+name)
        raw=path.read_bytes()
        found[name]=raw
        tree=ast.parse(raw,filename=name)
        packages=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                packages.extend(alias.name for alias in node.names)
            elif isinstance(node,ast.ImportFrom):
                prefix=node.module or ''
                if node.level:
                    parents=Path(name).parent.parts
                    prefix='.'.join((*parents[:len(parents)-node.level+1],*prefix.split('.'))).strip('.')
                packages.append(prefix)
                packages.extend(prefix+'.'+alias.name for alias in node.names if alias.name!='*')
        for package in packages:
            if package.split('.')[0] not in ('gpu','organism_v6','research_loop','tests'):
                continue
            candidate=Path(*package.split('.'))
            for relative in (candidate.with_suffix('.py'),candidate/'__init__.py'):
                if (repository/relative).is_file():
                    pending.append(str(relative))
        for parent in Path(name).parents:
            init=parent/'__init__.py'
            if (repository/init).is_file():
                pending.append(str(init))
    return found


def build(repository,destination):
    require(not destination.exists(),'immutable_runtime_source')
    entries=['gpu/orch_r125_continual_guard.py','gpu/orch_r125_continual_native.py',
        'gpu/orch_r125_continual_readout.py',OWN+'/broker.py',OWN+'/confinement.py',*TESTS]
    files=dependencies(repository,entries)
    originals={name:digest(raw) for name,raw in files.items()}
    files['gpu/orch_r125_continual_guard.py']=adapt_guard(files['gpu/orch_r125_continual_guard.py'])
    for name,raw in files.items():
        write(destination/name,raw)
    write(destination/'STARTUP.md',(repository/OWN/'STARTUP.md').read_bytes())
    return dict(schema='R183_RUNTIME_SOURCE_V1',source_pins={name:digest(raw) for name,raw in files.items()},
        original_pins=originals,main_journal_sha256=originals['gpu/orch_r125_stream_journal.py'],
        canonical_native_sha256=originals['gpu/orch_r125_continual_native.py'],
        guard_delta='truthful_logged_builder_CPU_binding_and_fresh_bound_preservice_privileged_scan',
        optional_working_state_implemented=False)


if __name__=='__main__':
    repository=Path(__file__).resolve().parents[3]
    output=repository/OWN
    print(json.dumps(write(output/'SOURCE_BUILD.json',build(repository,output/'runtime_source')),sort_keys=True))
