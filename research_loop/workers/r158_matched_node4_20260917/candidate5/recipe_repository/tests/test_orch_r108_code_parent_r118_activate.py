from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r108_code_parent_r118_activate as activation


def test_strict_admission_requires_privileged_clear_exact_uuid_and_minor():
    plan={'gpu_uuid':'OWN'}
    snapshot=dict(clear=True,scanner_euid=0,gpu={'uuid':'OWN'},device_minor=6,blocking_reasons=[])
    assert activation.admitted(snapshot,plan)
    for change in [dict(clear=False),dict(scanner_euid=2524),dict(gpu={'uuid':'FOREIGN'}),
        dict(blocking_reasons=['open_target_fd'])]:
        assert not activation.admitted(dict(snapshot,**change),plan)
    del snapshot['device_minor']
    assert not activation.admitted(snapshot,plan)


def test_carry_driver_restores_exact_latest_settings_without_replaying(tmp_path,monkeypatch):
    settings=dict(effective_max_new_tokens=512,status='BOUND_FOR_LANE_DECODER')
    saved=dict(schema='R118_CODE_CARRY_V1',reflection_settings=settings,
        reflection_source_id='LAST_SILENT',old_experience_replayed=False)
    path=tmp_path/'carry.json';activation.run.write_new(path,saved)
    activation.run.write_new(tmp_path/'R118_SHARED_HANDOFF_BRANCH.json',
        dict(carry=dict(path=str(path),sha256=activation.run.sha(path))))

    def initial(self,root,engine,session):
        self.root=root;self.settings={'effective_max_new_tokens':4096};self.cycle_sources={}

    monkeypatch.setattr(activation.client.Driver,'__init__',initial)
    actor=activation.CarryDriver(tmp_path,None,None)
    assert actor.settings==settings and actor.cycle_sources=={}
    assert activation.run.read(tmp_path/'R118_CARRY_RESTORED.json')['prior_experience_replayed'] is False


def test_preparation_cannot_run_without_actual_main_initialization(tmp_path,monkeypatch):
    root=tmp_path/'root';source=tmp_path/'source';root.mkdir();source.mkdir()
    activation.run.write_new(root/'PLAN.json',{'physical':2})
    monkeypatch.setattr(activation,'handoff_document',lambda root:dict(branch='F3'))
    with pytest.raises(FileNotFoundError):
        activation.prepare(root,tmp_path/'absent_MAIN_INITIALIZED.json',source)
    assert not (root/'SHARED_ACTIVATION.json').exists()


def test_frozen_runnable_entry_uses_carry_overlay_without_source_mutation(monkeypatch,tmp_path):
    seen=[]
    monkeypatch.setattr(activation,'validate_activation',lambda root:None)
    original=activation.lifecycle.native
    marker=SimpleNamespace(Driver=object)
    namespace={'client':marker,'seen':seen}
    exec('def target(root):\n seen.append(client.Driver)\n',namespace)
    monkeypatch.setattr(activation.lifecycle,'native',namespace['target'])
    activation.native(tmp_path)
    assert seen==[activation.CarryDriver] and marker.Driver is object
    assert original.__module__=='gpu.orch_r108_code_parent_r116_shared_run'


def test_prepare_preserves_bounds_calls_and_exact_main_reference(tmp_path):
    write=activation.run.write_new
    root=tmp_path/'life';source=tmp_path/'overlay/source';source.mkdir(parents=True)
    plan=dict(physical=2,started_unix=1,hard_deadline_unix=100,lease_end_unix=30000,
        native_cap=8192,parent_cap=1000,cycles=100)
    write(root/'PLAN.json',plan)
    write(root/'reservations/OLD.json',dict(status='FAILED'))
    bounds={key:plan[key] for key in activation.client.BOUND_FIELDS}
    released=dict(root=str(root),branch='F3',bounds=bounds,predecessors=[{'pid':999999999}],
        preserved_files={'PLAN.json':activation.run.sha(root/'PLAN.json'),
            'reservations/OLD.json':activation.run.sha(root/'reservations/OLD.json')})
    write(root/'R118_SHARED_HANDOFF_BRANCH.json',released)
    common=tmp_path/'common'
    adoption=dict(schema='R118_SHARED_ADOPTION_V1',no_lifetime_reset=True,
        branch_bounds={'F3':bounds},checkpoint={'reference':'frozen'},initial_history={'F1':['old']})
    write(common/'ADOPTION.json',adoption)
    write(common/'CONFIG.json',dict(owner='F1',initial_checkpoint=adoption['checkpoint'],
        initial_history=adoption['initial_history']))
    binding=dict(branch='F3',root=str(common),config_sha256=activation.run.sha(common/'CONFIG.json'),
        adoption_path=str(common/'ADOPTION.json'),adoption_sha256=activation.run.sha(common/'ADOPTION.json'))
    write(common/'INITIALIZED.json',dict(schema='R118_SHARED_INITIALIZED_V1',bindings={'F3':binding}))
    write(source/'cpu_fixture.py',{'fixture':True})
    write(source.parent/'SOURCE_SHA256.json',{'cpu_fixture.py':activation.run.sha(source/'cpu_fixture.py')})
    write(source.parent/'CPU_TESTS.json',dict(passed=True,cuda_initialized=False,
        source_manifest_sha256=activation.run.sha(source.parent/'SOURCE_SHA256.json')))
    before=(root/'PLAN.json').read_bytes()
    result=activation.prepare(root,common/'INITIALIZED.json',source)
    assert result['shared_learner']==binding and result['inherited_bounds']==bounds
    assert result['previous_reservations']=={'OLD.json':released['preserved_files']['reservations/OLD.json']}
    assert (root/'PLAN.json').read_bytes()==before
    assert not (root/'R118_SHARED_NATIVE_LAUNCH.json').exists()
