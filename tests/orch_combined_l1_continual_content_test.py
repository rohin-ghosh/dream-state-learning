"""Real content-v2 packet regressions; no historical label mutations."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from gpu import orch_combined_l1_continual_content as content
from organism_v6 import orch_combined_l1_continual as policy


def packet_fixture():
    root = Path(__file__).resolve().parents[1] / 'research_notes/analysis/orch_combined_l1_continual_20260915_attempt1'
    folder = root / 'CONTENT_QUEUE/math_content_readmission473_20260915'
    if not folder.exists():
        pytest.skip('experiment packet not present in source-only checkout')
    return root, json.loads((folder / 'BOUND_PACKET.json').read_text()), json.loads((folder / 'EXCLUSIONS.json').read_text())


def test_all473_exact_rows_and_false_historical_labels_preserved():
    root, packet, exclusions = packet_fixture()
    before = deepcopy(packet)
    state = policy.initial_state(json.loads((root / 'PACKET/ADMITTED_ROWS.json').read_text()), 'initial')
    result = content.append(state, packet, exclusions)
    assert result['ingested'][-1]['added'] == 473
    assert packet == before
    assert any(not entry['row']['admitted'] for entry in result['rows'][2394:])
    assert [entry['row'] for entry in result['rows'][2394:]] == [entry['row'] for entry in packet['rows']]
    assert content.append(result, packet, exclusions) is result


def test_content_policy_not_historical_register_or_length_gates():
    root, packet, exclusions = packet_fixture()
    selected = [entry for entry in packet['rows'] if entry['eligibility']['length_tag'] in ('under150', 'over400')]
    assert len(selected) == 285
    for entry in selected:
        content.validate_entry(entry, exclusions)


def test_content_true_eligibility_is_recomputed_not_trusted():
    root, packet, exclusions = packet_fixture()
    entry = deepcopy(packet['rows'][0])
    entry['row']['review']['grounded_operations'] = False
    with pytest.raises(AssertionError, match='eligibility'):
        content.validate_entry(entry, exclusions)


def test_content_held_id_and_question_hash_rejected():
    root, packet, exclusions = packet_fixture()
    entry = packet['rows'][0]
    for key, value in (('held_math', entry['row']['task_id']), ('held_question_hashes', entry['question_sha256'])):
        changed = dict(exclusions, **{key: exclusions[key] + [value]})
        with pytest.raises(AssertionError):
            content.validate_entry(entry, changed)


def test_content_parenting_quarantine():
    root, packet, exclusions = packet_fixture()
    packet['parenting_experience'] = True
    with pytest.raises(AssertionError):
        content.append(policy.initial_state([], 'initial'), packet, exclusions)
