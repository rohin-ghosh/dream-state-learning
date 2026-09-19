import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from gpu import orch_r119_route_final_premodel as repair


@pytest.mark.parametrize('name',['RESERVATIONS.jsonl','DISPATCH.json','ADMISSION.json','FINISHED.json',
                               'TIMEOUT.json','sealed_final_readouts'])
def test_any_input_or_ledger_even_empty_stops_proposal(tmp_path,name):
    path=tmp_path/name
    path.write_text('')
    with pytest.raises(ValueError,match='any_input_or_dispatch'):
        repair.zero_input(tmp_path)
    assert path.exists()


def test_failed_premodel_receipts_are_not_deleted(tmp_path):
    for name in ('ATTEMPT.json','FAILED.json'):
        (tmp_path/name).write_text('original')
    assert repair.zero_input(tmp_path)['model_inputs_charged']==0
    assert (tmp_path/'FAILED.json').read_text()=='original'


def test_no_execute_without_explicit_permission(tmp_path):
    with pytest.raises(ValueError,match='Main_launch_permission'):
        repair.execute({'launch_authorized':False},{},None)


def test_changed_source_reference_is_rejected(tmp_path):
    path=tmp_path/'source'
    path.write_text('{}')
    with pytest.raises(ValueError,match='immutable_reference'):
        repair.bound(dict(path=str(path),sha256='wrong'))


def test_combined_scan_reuses_exact_function_with_only_window_and_plan_binding(tmp_path,monkeypatch):
    calls=[]
    def validate_window(request):
        raise AssertionError('expired_TRAIN_window_must_not_be_reused')
    namespace=dict(validate_window=validate_window,Path=Path)
    exec("def original_scan(request,lifecycle):\n    validate_window(request)\n    return dict(clear=True,physical=lifecycle.verify_plan(Path(request['root']))['physical'])\n",namespace)
    original_scan=namespace['original_scan']
    config=dict(root=str(tmp_path),end_unix=200)
    final=SimpleNamespace(window=lambda *args:calls.append(args),read=lambda p:dict(physical=4))
    monkeypatch.setattr(repair,'verify',lambda *args:(config,{}))
    monkeypatch.setattr(repair,'bound',lambda reference:{})
    monkeypatch.setattr(repair,'load',lambda *args:SimpleNamespace(scan=original_scan))
    monkeypatch.setattr(repair.os,'geteuid',lambda:0)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','')
    result=repair.scan(dict(scanner_source_map={},scanner={},scanner_import_root=str(tmp_path),
        directory=str(tmp_path),scanner_dependencies={}),final)
    assert result['physical']==4 and len(calls)==1
