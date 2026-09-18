import json
from pathlib import Path
import shutil
import tarfile

import pytest

from gpu import orch_route_adversary_reduce as reducer


@pytest.fixture
def evidence(tmp_path):
    published = Path(__file__).resolve().parents[1] / 'research_notes/analysis/orch_route_adversary_20260914_attempt1/revision2'
    for name in ('PREPARE.json', 'REFERENCE.json'):
        shutil.copyfile(published / name, tmp_path / name)
    with tarfile.open(published / 'native_evidence.tar.gz') as archive:
        for member in archive.getmembers():
            relative = Path(member.name)
            assert not relative.is_absolute() and '..' not in relative.parts
            target = tmp_path / relative
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                assert member.isfile()
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.extractfile(member) as source, target.open('xb') as output:
                    shutil.copyfileobj(source, output)
    return tmp_path


def test_terminal_reduction_replays_all_cases_and_raw_calls(evidence):
    result = reducer.reduce(evidence)
    assert result['replayed_cases'] == result['case_denominator'] == 72
    assert result['actual_native_calls'] == result['native_call_cap'] == 144
    assert result['terminal_models'] == result['model_denominator'] == 3
    assert result['fits'] == result['updates'] == 0


def test_raw_call_tamper_rejected(evidence):
    path = evidence / 'FULL_TARGET/CALL_000.json'
    document = json.loads(path.read_text())
    document['response']['raw'] = 'tampered'
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match='native_artifact_inventory_drift'):
        reducer.reduce(evidence)


def test_summary_tamper_rejected(evidence):
    path = evidence / 'FULL_TARGET/RESULT.json'
    document = json.loads(path.read_text())
    document['summary']['REFERENCE']['complete_correct'] = 999
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match='prospective_metric_replay_drift'):
        reducer.reduce(evidence)
