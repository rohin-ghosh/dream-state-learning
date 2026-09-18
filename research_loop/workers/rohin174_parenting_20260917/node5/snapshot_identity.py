"""Recover exact inbox identity from a bound, byte-reproduced TRAIN REQUEST render."""

import copy
import hashlib
import json
from pathlib import Path

from gpu import orch_r166_parent_snapshot as snapshot
from gpu.orch_r125_stream_journal import _digest, require
from organism_v6 import orch_r124_train_history as history_module
from organism_v6 import orch_r125_plain_context as plain
from organism_v6.orch_r125_continual_stream import SCHEMA as STREAM_SCHEMA


PINS = {
    'gpu/orch_r166_parent_snapshot.py': '116aa1158735fbf28bcba14e270ea23e901b4553878815ee2101ae9b4b347003',
    'organism_v6/orch_r124_train_history.py': '0c336e3c9d3f5fbcfa3446287b24f554052cd57ec5330fb1d4a84f5e0894dd91',
    'organism_v6/orch_r125_plain_context.py': 'dcfd1f7f5584867e39356f336f53bb7222aeb535da87d5ecb8f1f0bb59f72feb',
}


class CapturedRender(Exception):
    def __init__(self, messages):
        self.messages = messages


def reconstructed_messages(history, presentation):
    def capture_before_tokenization(messages):
        raise CapturedRender(messages)

    try:
        history.render(capture_before_tokenization, 0, presentation=presentation)
    except CapturedRender as captured:
        return captured.messages
    raise ValueError('render_capture_required_no_fabricated_token_count')


def exact_visible(document, inbox):
    require(document.get('split') == 'TRAIN' and
            document.get('render_receipt', {}).get('all_history_tokens_masked') is True, 'bound_masked_TRAIN_request')
    checkpoint = document.get('resume_state')
    require(type(checkpoint) is dict and set(checkpoint) == {'state', 'sha256'},
            'ambiguous_delivery_requires_bound_checkpoint')
    state = checkpoint['state']
    require(checkpoint['sha256'] == _digest(state) and state['schema'] == STREAM_SCHEMA,
            'stream_checkpoint_integrity')
    require(state['pending'] == _digest({key: value for key, value in document.items() if key != 'resume_state'}),
            'checkpoint_pending_binds_exact_request')
    history_checkpoint = state['history']
    require(_digest(history_checkpoint) == document['history_sha256'], 'request_binds_exact_history')
    history = history_module.TrainHistory.restore(history_checkpoint)
    presentation = state.get('presentation')
    require(type(presentation) is dict and presentation['version'] == plain.VERSION,
            'exact_known_plain_presentation_required')
    messages = reconstructed_messages(history, presentation)
    require(messages == document['messages'], 'byte_exact_full_render_reproduction')
    selected = set()
    by_event = {entry['actor'] + ':inbox:' + identifier: identifier for identifier, entry in inbox.items()}
    for event in history.events[history.visible_frontier.event_count:]:
        if event.event_id not in by_event:
            continue
        identifier = by_event[event.event_id]
        entry = inbox[identifier]
        require(event.actor == entry['actor'] and event.split == 'TRAIN' and
                event.source_id == entry['inbox_source_id'] and event.source_sha256 == entry['inbox_source_sha256'] and
                event.text == entry['visible_text'], 'exact_history_event_inbox_source_binding')
        rendered = plain.event_message(event)
        if rendered is not None:
            require(rendered['role'] == 'user' and rendered in messages[2:], 'actual_rendered_external_event')
            selected.add(identifier)
    proof = dict(schema='NODE5_EXACT_RENDER_IDENTITY_V1', checkpoint_sha256=checkpoint['sha256'],
        history_sha256=document['history_sha256'], messages_sha256=_digest(messages),
        visible_frontier=history.visible_frontier.event_count, exact_visible_ids=sorted(selected),
        method='restore_bound_history_and_reproduce_all_messages_before_token_counter',
        token_count_recomputed=False, model_calls=0)
    return selected, proof


def install():
    root = Path(snapshot.__file__).resolve().parents[1]
    for name, expected in PINS.items():
        require(hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, 'bound_original_reader_and_renderer')
    original_reduce = snapshot._reduce
    require(Path(original_reduce.__code__.co_filename).resolve() == root / 'gpu/orch_r166_parent_snapshot.py',
            'one_explicit_install_on_original_reducer')

    def reduce_with_identity(state, record):
        if record['kind'] != 'REQUEST' or state['pending'] is not None:
            return original_reduce(state, record)
        document = record['document']
        if document.get('split') != 'TRAIN' or document.get('render_receipt', {}).get('all_history_tokens_masked') is not True:
            return original_reduce(state, record)
        original_visible = snapshot.transcript._visible
        visible, ambiguous = original_visible(document['messages'], state['inbox'])
        if not ambiguous:
            return original_reduce(state, record)
        exact, proof = exact_visible(document, state['inbox'])
        require(visible <= exact, 'no_conflicting_existing_render_proof')

        def bound_visibility(messages, inbox):
            require(messages is document['messages'] and inbox is state['inbox'], 'exact_single_request_consumer')
            return exact, set()

        snapshot.transcript._visible = bound_visibility
        try:
            result = original_reduce(state, record)
        finally:
            snapshot.transcript._visible = original_visible
        previous = state.get('exact_render_identity', dict(count=0, chain_sha256='0' * 64))
        proof.update(record_index=record['index'], record_sha256=record['sha256'],
                     text_only_ambiguous_ids=sorted(ambiguous))
        state['exact_render_identity'] = dict(count=previous['count'] + 1,
            chain_sha256=_digest(dict(previous=previous['chain_sha256'], proof=proof)), latest=proof)
        return result

    snapshot._reduce = reduce_with_identity
    return original_reduce


def stored_poll(root, store, reference=None):
    observed = snapshot.stored_poll(root, store, reference)
    cursor_path = Path(observed['reference']['path'])
    raw = cursor_path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == observed['reference']['sha256'], 'own_cursor_proof_pin')
    cursor = json.loads(raw)
    observed['exact_render_identity'] = cursor.get('exact_render_identity', dict(count=0))
    return observed
