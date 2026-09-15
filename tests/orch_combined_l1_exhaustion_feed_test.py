"""New registry is explicit; old publisher and training controls are unchanged."""

import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from gpu import orch_combined_l1_exhaustion_feed as feed
from gpu.orch_combined_l1_exhaustion_node import existing
from gpu.orch_combined_l1_native_feed_watch import pending


def blob(value):
    raw = json.dumps(value).encode()
    return base64.b64encode(raw).decode(), hashlib.sha256(raw).hexdigest()


def binding(monkeypatch):
    entry = dict(purpose='L1_RICHNESS_GENERATION', family='math', allowed_shards=list(range(1, 8)),
        generator_state_sha256=feed.INITIAL, generator_base_sha256=feed.BASE,
        source_purpose='L1_EXTERNAL_GENERATION', parenting_experience=False,
        checkpoint_derived_allowed=False, teacher_targets_allowed=False, L2_allowed=False)
    registry = dict(adapter_sha256=feed.ADAPTER_SHA, source_generation_policy_sha256=feed.GENERATION_SHA,
                    sources={feed.SOURCE: entry})
    source_blob, source_sha = blob(registry)
    publisher = dict(source_registry_sha256=source_sha, batching_rule='MIXED_STEERING_SAME_37EC',
        causal_prompt_comparison=False, BASE_stream_registered=False, no_L2=True, no_checkpoint=True, no_teacher=True)
    publisher_blob, publisher_sha = blob(publisher)
    monkeypatch.setattr(feed, 'SOURCE_REGISTRY_SHA', source_sha)
    monkeypatch.setattr(feed, 'REGISTRY_SHA', publisher_sha)
    return dict(source_registry=source_blob, publisher_registry=publisher_blob), registry, publisher


def test_exact_separate_registry(monkeypatch):
    proof, registry, _ = binding(monkeypatch)
    assert feed.registries(proof) == registry['sources'][feed.SOURCE]
    from gpu import orch_combined_l1_native_feed as old
    assert old.ROOT != feed.ROOT


@pytest.mark.parametrize('key,value', [('allowed_shards', list(range(8))),
    ('generator_state_sha256', 'BASE'), ('generator_base_sha256', 'other'),
    ('checkpoint_derived_allowed', True), ('teacher_targets_allowed', True), ('L2_allowed', True),
    ('parenting_experience', True), ('source_purpose', 'PARENTING')])
def test_wrong_source_rejected_even_with_new_hash(monkeypatch, key, value):
    proof, registry, publisher = binding(monkeypatch)
    registry['sources'][feed.SOURCE][key] = value
    proof['source_registry'], digest = blob(registry)
    monkeypatch.setattr(feed, 'SOURCE_REGISTRY_SHA', digest)
    publisher['source_registry_sha256'] = digest
    proof['publisher_registry'], digest = blob(publisher)
    monkeypatch.setattr(feed, 'REGISTRY_SHA', digest)
    with pytest.raises(AssertionError):
        feed.registries(proof)


def test_registry_byte_rebinding_rejected(monkeypatch):
    proof, _, _ = binding(monkeypatch)
    proof['source_registry'] = blob({'changed': True})[0]
    with pytest.raises(AssertionError, match='source_blob_hash'):
        feed.registries(proof)


def test_discovery_waits_actual_accepted_manifest(monkeypatch, tmp_path):
    proof, _, _ = binding(monkeypatch)
    for name, key in [('PUBLISHER_REGISTRY.json', 'publisher_registry'), ('SOURCE_REGISTRY.json', 'source_registry')]:
        (tmp_path / name).write_bytes(base64.b64decode(proof[key]))
    folder = tmp_path / 'orch_continual_exhaustion_feed_batch_000'
    folder.mkdir()
    (folder / 'CANDIDATES.json').write_text('[]')
    assert feed.discover(tmp_path) == []
    manifest = dict(batch_author_accepted=False)
    (folder / 'MANIFEST.json').write_text(json.dumps(manifest))
    assert feed.discover(tmp_path) == []
    manifest = dict(batch_author_accepted=True, batch_id='orch_continual_exhaustion_segment1_000', row_count=62)
    (folder / 'MANIFEST.json').write_text(json.dumps(manifest))
    assert feed.discover(tmp_path)[0]['row_count'] == 62


@pytest.mark.parametrize('batch_id', ['orch_continual_batch_segment2_native_027', '../bad',
                                    'orch_continual_exhaustion_segment2_000'])
def test_receiver_rejects_foreign_namespace(tmp_path, batch_id):
    with pytest.raises(AssertionError):
        existing(tmp_path, batch_id, 'sha')


def test_pending_idempotence_failed_hash_and_rebinding():
    entry = dict(batch_id='orch_continual_exhaustion_segment1_002', number=2, manifest_sha256='sha')
    assert pending([entry], dict(entries=[]), set()) == [entry]
    assert pending([entry], dict(entries=[]), {'sha'}) == []
    assert pending([entry], dict(entries=[dict(entry, area='CONTENT_QUEUE')]), set()) == []
    with pytest.raises(ValueError, match='rebound'):
        pending([dict(entry, manifest_sha256='new')], dict(entries=[dict(entry, area='CONTENT_QUEUE')]), set())


def test_future_labels_and_targets_preserved():
    wrapped = dict(row=dict(target='exact', admitted=False, semantic_status='UNREVIEWED',
        target_sha256='sha', provenance=dict(instruction_regime='STEERED', steering_degree=3)),
        eligibility=dict(eligible=True, **{key: None for key in feed.common.REPORTING_FIELDS}))
    before = deepcopy(wrapped)
    projected = feed.common.project(wrapped, 'orch_continual_exhaustion_segment1_002', 0)
    assert wrapped == before and projected['row'] == before['row']


def test_live_receiver_default_remains_original():
    import inspect
    from gpu.orch_combined_l1_continual_receive import receive
    assert inspect.signature(receive).parameters['native_validator'].default is None


def test_original_watcher_defaults_remain_original():
    import inspect
    from gpu.orch_combined_l1_native_feed_watch import main
    assert inspect.signature(main).parameters['receiver_module'].default == 'gpu.orch_combined_l1_native_feed_node'
