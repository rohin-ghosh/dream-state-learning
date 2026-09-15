from copy import deepcopy
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from gpu import orch_r108_guided_seed as seed


def test_fixed_checkpoint_corpus_and_even_rehearsal():
    assert str(seed.CHECKPOINT).endswith('/FULL/checkpoints/000008932')
    assert seed.STATE_SHA == '121655d491bc55ba6bbd8eb732bc4f7a65215a07d3b6b2492f4fa623026f80f1'
    assert seed.rehearsal_indexes() == [0,242,484,726,969,1211,1453,1695,1938,2180,2422,2664,2907,3149,3391,3634]
    assert len(set(seed.rehearsal_indexes())) == 16
    with pytest.raises(ValueError): seed.rehearsal_indexes(3640)


def test_config_seal_survives_json_and_detects_edits():
    document=seed._seal(dict(adapter='fixed',generation=0,options=dict(betas=(.9,.999))))
    serialized=json.loads(json.dumps(document))
    assert seed._seal(serialized)==serialized
    serialized['adapter']='reset'
    assert seed._seal(serialized)!=serialized


def test_once_preserves_existing_evidence(tmp_path):
    path=tmp_path/'receipt.json'
    seed._once(path,dict(preserved=True))
    with pytest.raises(FileExistsError): seed._once(path,dict(preserved=False))
    assert seed.read(path)==dict(preserved=True)


def fixture():
    torch=pytest.importorskip('torch')
    parameters=[torch.nn.Parameter(torch.tensor([[1.,2.],[3.,4.]])),
        torch.nn.Parameter(torch.tensor([[5.,6.],[7.,8.]]))]
    optimizer=torch.optim.AdamW(parameters,lr=3e-5,betas=(.9,.999),eps=1e-8,weight_decay=.01,
        amsgrad=False,foreach=False,fused=False)
    for update in range(4):
        optimizer.zero_grad()
        sum((position+1)*parameter.square().sum() for position,parameter in enumerate(parameters)).backward()
        optimizer.step()
    manifest=[dict(name=f'layer.lora_{name}.default.weight',shape=[2,2],dtype='torch.float32') for name in ('A','B')]
    return torch,parameters,optimizer,manifest


def test_same_shape_reordered_parameters_preserve_moments_and_next_step():
    torch,parameters,optimizer,manifest=fixture()
    state=deepcopy(optimizer.state_dict())
    baseline=seed.optimizer_summary(state,manifest,4)
    assert json.loads(json.dumps(baseline))==baseline
    copies=[torch.nn.Parameter(parameter.detach().clone()) for parameter in parameters]
    resumed=torch.optim.AdamW(list(reversed(copies)),lr=3e-5,betas=(.9,.999),eps=1e-8,
        weight_decay=.01,amsgrad=False,foreach=False,fused=False)
    destination=list(reversed(manifest))
    remapped=seed.remap_optimizer(state,manifest,destination,resumed.state_dict()['param_groups'][0]['params'])
    resumed.load_state_dict(remapped)
    assert seed.optimizer_summary(resumed.state_dict(),destination)==baseline
    for current,values in ((optimizer,parameters),(resumed,copies)):
        current.zero_grad()
        sum((position+1)*parameter.square().sum() for position,parameter in enumerate(values)).backward()
        current.step()
    assert all(torch.equal(before,after) for before,after in zip(parameters,copies))
    assert seed.optimizer_summary(optimizer.state_dict(),manifest,5)==seed.optimizer_summary(resumed.state_dict(),destination,5)


@pytest.mark.parametrize('change',['missing','nan','shape','step','lr','duplicate','negative'])
def test_bad_optimizer_rejected(change):
    torch,parameters,optimizer,manifest=fixture()
    state=deepcopy(optimizer.state_dict())
    if change=='missing': del state['state'][0]
    if change=='nan': state['state'][0]['exp_avg'][0,0]=float('nan')
    if change=='shape': state['state'][0]['exp_avg']=torch.zeros(1)
    if change=='step': state['state'][0]['step'].fill_(0)
    if change=='lr': state['param_groups'][0]['lr']=.5
    if change=='duplicate': state['param_groups'][0]['params']=[0,0]
    if change=='negative': state['state'][0]['exp_avg_sq'][0,0]=-1
    with pytest.raises(ValueError): seed.optimizer_summary(state,manifest)


def test_missing_or_renamed_parameter_cannot_map_by_shape():
    torch,parameters,optimizer,manifest=fixture()
    destination=deepcopy(manifest)
    destination[0]['name']='layer.lora_A.wrong.weight'
    with pytest.raises(ValueError,match='named_parameter'):
        seed.remap_optimizer(optimizer.state_dict(),manifest,destination,[0,1])


@pytest.mark.parametrize('phase',['collection','sealed_readout'])
def test_readonly_phases_cannot_restore(monkeypatch,phase):
    monkeypatch.setattr(seed,'validate',lambda value:value)
    loaded=SimpleNamespace(binding=SimpleNamespace(phase=phase))
    with pytest.raises(ValueError,match='restore_only_sleep'):
        seed.restore(loaded,{})


def test_restore_never_calls_load_training_or_manual_seed(tmp_path,monkeypatch):
    torch=pytest.importorskip('torch')
    model=torch.nn.Module()
    model.layer=torch.nn.Module()
    model.layer.lora_A=torch.nn.ModuleDict({'default':torch.nn.Linear(2,2,bias=False)})
    model.layer.lora_B=torch.nn.ModuleDict({'default':torch.nn.Linear(2,2,bias=False)})
    model.base=torch.nn.Parameter(torch.ones(2),requires_grad=False)
    model.gradient_checkpointing_enable=lambda **kwargs:None
    model.enable_input_require_grads=lambda:None
    model.config=SimpleNamespace(use_cache=True)
    selected={name:parameter for name,parameter in model.named_parameters() if seed.native.is_lora(name)}
    optimizer=torch.optim.AdamW(list(selected.values()),lr=3e-5,betas=(.9,.999),eps=1e-8,
        weight_decay=.01,amsgrad=False,foreach=False,fused=False)
    sum(parameter.square().sum() for parameter in selected.values()).backward(); optimizer.step()
    path=tmp_path/'optimizer.pt'; torch.save(optimizer.state_dict(),path)
    rng=tmp_path/'rng.pt'; torch.save(dict(python=(),numpy=(),torch=torch.tensor([1]),cuda=torch.tensor([2])),rng)
    identity=SimpleNamespace(state_sha256=seed.native.state_hash(selected))
    model.requires_grad_(False)
    document=dict(adapter={},optimizer_path=str(path),optimizer_sha256=seed.sha(path),rng_path=str(rng),
        rng_sha256=seed.sha(rng),optimizer_parameters=seed.parameter_manifest(model),generation=0,binding_sha256='bound')
    document['optimizer_summary']=seed.optimizer_summary(optimizer.state_dict(),document['optimizer_parameters'])
    monkeypatch.setattr(seed,'validate',lambda value:value)
    monkeypatch.setattr(seed.native.bridge.AdapterIdentity,'from_document',lambda value:identity)
    monkeypatch.setattr(seed.native,'observe_adapter',lambda engine,expected:expected)
    never=Mock(side_effect=AssertionError('reset_forbidden'))
    monkeypatch.setattr(seed.native,'load_training',never)
    monkeypatch.setattr(torch,'manual_seed',never)
    restored=Mock(); monkeypatch.setattr(seed.continual,'restore_rng',restored)
    loaded=SimpleNamespace(binding=SimpleNamespace(phase='training'),observed=identity,optimizer=None,
        engine=SimpleNamespace(torch=torch,model=model))
    receipt=seed.restore(loaded,document)
    assert receipt['step']==1 and not receipt['optimizer_reset'] and receipt['rank0_rng_restored']
    assert seed.optimizer_summary(loaded.optimizer.state_dict(),seed.parameter_manifest(model))==document['optimizer_summary']
    assert not model.base.requires_grad and all(parameter.requires_grad for parameter in selected.values())
    assert restored.call_count==1 and not never.called
    with pytest.raises(ValueError,match='overwrite_live_optimizer'): seed.restore(loaded,document)


def test_canonical_encoding_dispatch_without_changing_targets(monkeypatch):
    expected=object(); math=Mock(return_value=[expected])
    monkeypatch.setattr(seed.continual.encoding,'encode_rows',math)
    row=dict(encoding='math',row=dict(student_prefix=[],target='unchanged'))
    original=deepcopy(row)
    assert seed.encoded(row,None) is expected and row==original
    math.assert_called_once_with([row['row']],None)
    with pytest.raises(ValueError,match='alternating_goal_pair'):
        seed.encoded(dict(encoding='terse_route',row=dict(prefix=[],episode_call_index=0)),None)
    with pytest.raises(ValueError): seed.encoded(dict(encoding='parent',row={}),None)


def test_actual_native_document_roundtrip_when_available():
    location=os.environ.get('R108_SEED_DOCUMENT')
    if not location: pytest.skip('native-only immutable seed files')
    document=seed.read(location)
    assert seed.validate(json.loads(json.dumps(document)))==document
    assert document['optimizer_summary']['step']==8932
    assert document['optimizer_summary']['parameter_count']==392
    assert len(seed.rehearsal_rows(document))==16


@pytest.mark.parametrize('phase',['collection','sealed_readout'])
def test_readonly_phases_cannot_save_carry(monkeypatch,phase):
    monkeypatch.setattr(seed,'validate',lambda value:value)
    with pytest.raises(ValueError,match='carry_only_sleep'):
        seed.save_carry(SimpleNamespace(binding=SimpleNamespace(phase=phase)),{},None,None)


def test_carry_saved_moments_rng_and_next_restore(tmp_path,monkeypatch):
    torch,parameters,optimizer,manifest=fixture()
    model=torch.nn.Module()
    model.layer=torch.nn.Module()
    for name,parameter in zip(('lora_A','lora_B'),parameters):
        layer=torch.nn.Module()
        layer.default=torch.nn.Module()
        layer.default.register_parameter('weight',parameter)
        setattr(model.layer,name,layer)
    model.base=torch.nn.Parameter(torch.ones(2),requires_grad=False)
    model.gradient_checkpointing_enable=lambda **kwargs:None
    model.enable_input_require_grads=lambda:None
    model.config=SimpleNamespace(use_cache=True)
    selected={name:parameter for name,parameter in model.named_parameters() if seed.native.is_lora(name)}
    identity=SimpleNamespace(base_sha256=seed.BASE_SHA,state_sha256=seed.native.state_hash(selected))
    identity.document=lambda:dict(state_sha256=identity.state_sha256,base_sha256=identity.base_sha256)
    monkeypatch.setattr(seed.native.bridge.AdapterIdentity,'from_document',lambda value:identity)
    monkeypatch.setattr(seed.native,'observe_adapter',lambda engine,expected:expected)
    monkeypatch.setattr(seed,'validate',lambda value:value)
    rng=dict(python=('saved',),numpy=('saved',),torch=torch.tensor([1],dtype=torch.uint8),
        cuda=torch.tensor([2],dtype=torch.uint8))
    monkeypatch.setattr(seed.continual,'rng_state',lambda runtime:rng)
    document=seed._seal(dict(generation=0,optimizer_summary=seed.optimizer_summary(optimizer.state_dict(),manifest)))
    engine=SimpleNamespace(torch=torch,model=model,verify_base=Mock())
    loaded=SimpleNamespace(binding=SimpleNamespace(phase='training'),engine=engine,optimizer=optimizer,
        process=('cpu-test',42),r108_seed_provenance=dict(binding_sha256=document['binding_sha256']))
    carry=seed.save_carry(loaded,document,identity,tmp_path/'carry')
    roundtrip=seed.read(tmp_path/'carry/CARRY.json')
    assert roundtrip==carry==seed._seal(carry)
    assert seed.read(carry['parent_document']['path'])==document
    assert carry['parent_binding_sha256']==document['binding_sha256'] and carry['generation']==1
    assert carry['source_process']==['cpu-test',42]
    assert carry['optimizer_summary']==document['optimizer_summary']
    engine.verify_base.assert_called_once()
    with pytest.raises(ValueError,match='carry_never_overwrites'):
        seed.save_carry(loaded,document,identity,tmp_path/'carry')
    optimizer.param_groups[0]['params'].reverse()
    with pytest.raises(ValueError,match='carry_live_optimizer_order'):
        seed.save_carry(loaded,document,identity,tmp_path/'wrong-order')
    optimizer.param_groups[0]['params'].reverse()
    model.requires_grad_(False)
    next_loaded=SimpleNamespace(binding=SimpleNamespace(phase='training'),observed=identity,
        engine=engine,optimizer=None)
    restored=Mock(); monkeypatch.setattr(seed.continual,'restore_rng',restored)
    forbidden=Mock(side_effect=AssertionError('reset_forbidden'))
    monkeypatch.setattr(torch,'manual_seed',forbidden)
    monkeypatch.setattr(seed.native,'load_training',forbidden)
    provenance=seed.restore(next_loaded,roundtrip)
    assert provenance['step']==4 and provenance['generation']==1 and not provenance['optimizer_reset']
    restored_rng=restored.call_args.args[1]
    assert restored_rng['python']==rng['python'] and restored_rng['numpy']==rng['numpy']
    assert torch.equal(restored_rng['torch'],rng['torch']) and torch.equal(restored_rng['cuda'],rng['cuda'])
    resumed_parameters=[torch.nn.Parameter(parameter.detach().clone()) for parameter in parameters]
    reference=torch.optim.AdamW(resumed_parameters,lr=3e-5)
    reference.load_state_dict(deepcopy(optimizer.state_dict()))
    for current,values in ((next_loaded.optimizer,parameters),(reference,resumed_parameters)):
        current.zero_grad()
        sum((position+1)*parameter.square().sum() for position,parameter in enumerate(values)).backward()
        current.step()
    assert all(torch.equal(actual,expected) for actual,expected in zip(parameters,resumed_parameters))
    assert seed.optimizer_summary(next_loaded.optimizer.state_dict(),manifest,5)==seed.optimizer_summary(reference.state_dict(),manifest,5)
    assert not forbidden.called


def test_actual_rehearsal_matches_original_native_encoder_when_available():
    location=os.environ.get('R108_SEED_DOCUMENT')
    if not location: pytest.skip('native-only immutable corpus and tokenizer')
    document=seed.read(location)
    rows=seed.rehearsal_rows(document)
    before=deepcopy(rows)
    tokenizer=seed.continual.native.source.native.load_local_tokenizer(document['model_dir'])
    corpus=seed.read(document['corpus_path'])['rows']
    reference=seed.continual.encode_corpus(corpus,tokenizer,{})
    for row,index in zip(rows,document['rehearsal_indices']):
        actual=seed.encoded(row,tokenizer)
        assert actual==reference[index]
        supervised=[label for label in actual.labels if label!=-100]
        assert supervised[-1]==tokenizer.eos_token_id and len(actual.input_ids)<=2048
    assert rows==before
