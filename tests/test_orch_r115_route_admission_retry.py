import json

import pytest

from gpu import orch_r115_route_admission_retry as retry


def fixture(tmp_path):
    campaign = tmp_path / 'root/recovery/campaign'
    campaign.mkdir(parents=True)
    (campaign / 'parent_queue').mkdir()
    (tmp_path / 'proc').mkdir()
    (campaign.parent.parent / 'RESERVATIONS.jsonl').write_text('unchanged\n')
    documents = {'TERMINAL.json': dict(status='FAILED'),
        'GUARDIAN_FAILED.json': dict(error=dict(type='ValueError', message='strict_privileged_clear')),
        'RELEASE.json': dict(clear=False), 'ADMISSION_000.json': dict(clear=False),
        'RECOVERY.json': dict(old_reservations_sha256=retry.sha(campaign.parent.parent / 'RESERVATIONS.jsonl'))}
    for name, document in documents.items():
        (campaign / name).write_text(json.dumps(document))
    return campaign


def test_preserves_evidence_and_does_not_change_recipe(tmp_path):
    campaign = fixture(tmp_path)
    before = retry.sha(campaign / 'RECOVERY.json')
    result = retry.preserve(campaign, tmp_path / 'proc')
    assert result['preserved_files'] == 4 and result['recipe_sha256'] == before
    assert (campaign / 'admission_retry_r115_1034/TERMINAL.json').exists()
    assert not (campaign / 'TERMINAL.json').exists()


@pytest.mark.parametrize('name', ['LAUNCH.json', 'ACTOR_READY.json', 'native.log'])
def test_never_retries_after_native_launch(tmp_path, name):
    campaign = fixture(tmp_path)
    (campaign / name).write_text('{}')
    with pytest.raises(ValueError):
        retry.preserve(campaign, tmp_path / 'proc')
    assert (campaign / 'TERMINAL.json').exists()


def test_rejects_active_recovery_guard(tmp_path):
    campaign = fixture(tmp_path)
    process = tmp_path / 'proc/123'
    process.mkdir()
    (process / 'cmdline').write_bytes(b'python\0-m\0gpu.orch_r111_route_recovery\0guard\0--root\0'
        + str(campaign.parent.parent).encode())
    with pytest.raises(ValueError, match='still_alive'):
        retry.preserve(campaign, tmp_path / 'proc')


def test_rejects_new_charges(tmp_path):
    campaign = fixture(tmp_path)
    (campaign.parent.parent / 'RESERVATIONS.jsonl').write_text('new calls\n')
    with pytest.raises(ValueError, match='unchanged_charges'):
        retry.preserve(campaign, tmp_path / 'proc')


def test_scanner_subprocess_failure_still_requires_fresh_admission(tmp_path):
    campaign = fixture(tmp_path)
    failure = dict(type='CalledProcessError', message="gpu.orch_r109_route_scan 'scan' "
        + str(campaign.parent.parent / 'SERVICE_IDENTITY.json'))
    (campaign / 'GUARDIAN_FAILED.json').write_text(json.dumps(dict(error=failure)))
    assert retry.preserve(campaign, tmp_path / 'proc')['charges_unchanged']


def test_other_failure_not_reclassified_as_admission_only(tmp_path):
    campaign = fixture(tmp_path)
    (campaign / 'GUARDIAN_FAILED.json').write_text(json.dumps(dict(error=dict(type='ValueError', message='model failed'))))
    with pytest.raises(ValueError, match='exact_admission_failure'):
        retry.preserve(campaign, tmp_path / 'proc')
