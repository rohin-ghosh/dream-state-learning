from copy import deepcopy
import json
from pathlib import Path

import pytest

from gpu import orch_rich_intensity_packet as packet


def qualified_rows():
    first = packet.read(packet.FIRST / 'ADMITTED.json')
    rows = packet.read(packet.ROOT / 'REDUCED_ROWS.json')
    return first, rows


def test_exact_complete_difference_no_task_or_condition_selection():
    first, rows = qualified_rows()
    extra, combined = packet.select(first, rows)
    assert combined[:16] == first and combined[16:] == extra
    assert len(extra) == 10 and len(combined) == 26
    assert packet.membership(extra)['distinct_tasks'] == 3
    assert packet.membership(extra)['conditions'] == dict(control=4, light=3, dense=3)
    assert packet.membership(combined)['distinct_tasks'] == 9
    assert len(packet.membership(combined)['families']) == 4


def test_packet_mutation_fails_instead_of_requalification():
    first, rows = qualified_rows()
    changed = deepcopy(first)
    changed[0]['target'] += '\n'
    with pytest.raises(AssertionError):
        packet.select(changed, rows)


def test_target_duplicate_fails_instead_of_silent_filtering():
    first, rows = qualified_rows()
    changed = deepcopy(rows)
    first_keys = {packet.key(row) for row in first}
    extra = next(row for row in changed if row['admitted'] and packet.key(row) not in first_keys)
    extra['target_sha256'] = first[0]['target_sha256']
    with pytest.raises(AssertionError):
        packet.select(first, changed)


def test_missing_qualified_row_fails_instead_of_cherry_picking():
    first, rows = qualified_rows()
    extra, _ = packet.select(first, rows)
    filtered = [row for row in rows if packet.key(row) != packet.key(extra[0])]
    with pytest.raises(AssertionError):
        packet.select(first, filtered)


def test_export_hashes_refs_raw_copies_and_no_overwrite(tmp_path):
    output = tmp_path / 'packet'
    result = packet.export(output)
    manifest = json.loads((output / 'MANIFEST.json').read_text())
    assert result['packets']['FIRST16'] == packet.FIRST_SHA
    assert manifest['semantic_reviews_added'] == 0 and not manifest['training_authorized']
    for name, entry in manifest['files'].items():
        path = output / name
        assert packet.sha(path.read_bytes()) == entry['sha256']
        assert path.stat().st_mode & 0o222 == 0
    for row in manifest['rows']:
        capture = row['raw_capture']
        assert Path(capture['source']).read_bytes() == (output / capture['frozen']).read_bytes()
    with pytest.raises(AssertionError, match='immutable_destination_already_exists'):
        packet.export(output)
