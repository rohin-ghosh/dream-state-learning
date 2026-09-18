"""Sparse, asynchronous Astra parents for Main-bound C1..C5 TRAIN streams."""

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import time

from gpu import orch_r127_pilot_transcript as transcript
from gpu import orch_r133_programme_parent as parent
from gpu.orch_route_parent_campaign_providers import response_schema


SCHEMA = 'R153_COMMUNITY_PARENT_V1'
GATE_SCHEMA = 'R153_COMMUNITY_PARENT_GATE_V1'
SNAPSHOT_SCHEMA = 'R153_COMMITTED_TRAIN_SNAPSHOT_V1'
LEARNERS = ('C1', 'C2', 'C3', 'C4', 'C5')
SOURCE_FILES = (
    'gpu/orch_r153_community_parents.py',
    'gpu/orch_r133_programme_parent.py',
    'gpu/orch_route_parent_campaign_providers.py',
    'gpu/orch_route_parent_campaign_parent.py',
    'gpu/orch_l2_long_backend.py',
    'gpu/orch_l2_shared_run.py',
    'gpu/orch_r127_pilot_transcript.py',
    'gpu/orch_r127_pilot_console.py',
    'gpu/orch_r125_stream_console.py',
    'gpu/orch_r125_stream_journal.py',
    'organism_v6/orch_guided_bridge.py',
    'organism_v6/orch_route_parent_campaign.py',
    'organism_v6/orch_r124_train_history.py',
    'organism_v6/orch_r125_continual_stream.py',
    'organism_v6/orch_r125_plain_context.py',
)
IDENTICAL_TRANSPORT_FILES = (
    'gpu/orch_r153_community_parents.py',
    'gpu/orch_r133_programme_parent.py',
    'gpu/orch_r127_pilot_transcript.py',
    'gpu/orch_r125_stream_console.py',
    'gpu/orch_r127_pilot_console.py',
)


def write(path, document):
    parent.write(path, document)
    descriptor = os.open(Path(path).parent, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def local_file(path):
    path = Path(path)
    parent.require(path.is_absolute() and path == path.resolve() and path.is_file(),
                   'canonical_regular_input')
    parent.require(not any(re.search(r'(^|[_ .-])(held|final|readout|sealed)([_ .-]|$)',
        part, re.IGNORECASE) for part in path.parts), 'no_evaluation_input')
    return path


def build_config(template, *, learner_id, node, root, source_root, hard_end_unix):
    """Return an R133-compatible config; no files, transport, or provider calls."""
    config = {name: template[name] for name in (
        'programme_path', 'programme_sha256', 'principles_path', 'principles_sha256')}
    config.update(schema='R133_PROGRAMME_PARENT_V1', community_schema=SCHEMA,
        programme='raw_parented', branch=learner_id, node=node, root=str(root),
        source_root=str(source_root), hard_end_unix=hard_end_unix,
        cadence_responses=3, cadence_label='SPARSE', schedule_on='response',
        parent_reasoning_effort='low', parent_style='Sparse, responsive English guidance',
        start_after_response_count=0, poll_interval_seconds=5, object_turn_limit=3)
    return validate(config)


def validate(config):
    parent.validate(config)
    parent.require(config.get('community_schema') == SCHEMA and config['branch'] in LEARNERS,
                   'new_community_only')
    parent.require('r153' in config['root'].lower() and 'r127' not in config['root'].lower(),
                   'R127_protected_new_R153_root')
    parent.require(config['cadence_responses'] == 3 and config['cadence_label'] == 'SPARSE'
        and config['schedule_on'] == 'response' and config['parent_reasoning_effort'] == 'low'
        and config.get('object_turn_limit') == 3, 'fixed_sparse_low_effort_budget')
    parent.require(not config.get('predecessor_output'), 'no_old_life_parent_inheritance')
    for name in ('programme_path', 'principles_path'):
        local_file(config[name])
    return config


def remote_source_pins(gate, node):
    sources = gate['source_pins']
    if 'remote_source_pins' not in gate:
        return sources
    remote = gate['remote_source_pins']
    nodes = {binding['node'] for binding in gate['parents'].values()}
    parent.require(type(remote) is dict and set(remote) == nodes and node in nodes,
                   'exact_remote_source_nodes')
    required = set(SOURCE_FILES) | {'gpu/'+name+'_ssh.sh' for name in nodes}
    parent.require(required <= set(sources), 'complete_parent_source_gate')
    for pins in remote.values():
        parent.require(type(pins) is dict and set(pins) == set(sources), 'same_remote_source_closure_names')
        parent.require(all(type(value) is str and re.fullmatch(r'[0-9a-f]{64}', value)
            for value in pins.values()), 'exact_remote_source_hashes')
        parent.require(all(pins[name] == sources[name] for name in IDENTICAL_TRANSPORT_FILES),
                       'identical_parent_reader_and_transport_sources')
    return remote[node]


def verify_gate(config_path, repository, output, gate_path, gate_sha256):
    """Read a Main-supplied immutable gate before any remote/provider operation."""
    config_path, gate_path = local_file(config_path), local_file(gate_path)
    parent.require(parent.sha(gate_path) == gate_sha256, 'exact_Main_gate_pin')
    gate = json.loads(gate_path.read_text())
    parent.require(gate.get('schema') == GATE_SCHEMA and gate.get('status') == 'MAIN_BOUND',
                   'Main_exact_roots_and_source_gate_required')
    config = validate(json.loads(config_path.read_text()))
    bindings = gate['parents']
    parent.require(set(bindings) == set(LEARNERS), 'exact_five_parent_bindings')
    parent.require(len({entry['root'] for entry in bindings.values()}) == 5
        and len({entry['output'] for entry in bindings.values()}) == 5, 'independent_roots_and_state')
    binding = bindings[config['branch']]
    parent.require(binding == dict(root=config['root'], node=config['node'],
        source_root=config['source_root'], config_sha256=parent.sha(config_path),
        output=str(Path(output).resolve())), 'exact_parent_binding')
    repository = Path(repository).resolve()
    sources = gate['source_pins']
    required = set(SOURCE_FILES) | {'gpu/'+config['node']+'_ssh.sh'}
    parent.require(required <= set(sources), 'complete_parent_source_gate')
    for name, expected in sources.items():
        path = Path(name)
        parent.require(not path.is_absolute() and '..' not in path.parts, 'relative_source_pin')
        parent.require(parent.sha(local_file(repository/path)) == expected, 'pinned_parent_source')
    remote_source_pins(gate, config['node'])
    parent.require(Path(__file__).resolve() == repository/'gpu/orch_r153_community_parents.py',
                   'executed_parent_source_binding')
    return config, gate


def read_train_snapshot(root):
    """Read only numbered journal records; expose committed TRAIN text and receipts."""
    stats = dict(source_bytes=0, journal_id=None, head_sha256=None)
    inbox, delivered, events = {}, {}, []
    pending, response, count, sleeps = None, None, 0, 0
    for record, unused_mtime, unused_hash in transcript._records(root, stats,
            transcript.MAX_RECORDS, transcript.MAX_RECORD_BYTES, transcript.MAX_TOTAL_BYTES):
        kind, document = record['kind'], record['document']
        evidence = dict(record_index=record['index'], record_sha256=record['sha256'])
        if kind == 'INBOX':
            entry = transcript._inbox(document)
            parent.require(entry['inbox_id'] not in inbox, 'unique_inbox_id')
            inbox[entry['inbox_id']] = dict(entry, **evidence)
        elif kind == 'REQUEST':
            parent.require(pending is None and document.get('split') == 'TRAIN', 'TRAIN_request_only')
            parent.require(document.get('render_receipt', {}).get('all_history_tokens_masked') is True,
                           'external_context_never_loss_targets')
            visible, unused_ambiguous = transcript._visible(document['messages'], inbox)
            for identifier in sorted(visible - delivered.keys()):
                entry = inbox[identifier]
                delivered[identifier] = dict(speaker=entry['speaker'],
                    inbox_sha256=entry['inbox_source_sha256'], text_sha256=hashlib.sha256(
                        entry['text'].encode()).hexdigest(), **evidence)
                events.append(dict(actor=entry['actor'], speaker=entry['speaker'],
                    text=entry['text'], **evidence))
            pending = dict(request_sha256=transcript._digest({key: value for key, value in
                document.items() if key != 'resume_state'}), segment=document['segment'])
        elif kind == 'RESPONSE':
            parent.require(pending is not None and response is None
                and document['request_sha256'] == pending['request_sha256'], 'bound_TRAIN_response')
            response = dict(document=document, evidence=evidence)
        elif kind == 'COMMITTED' and pending is not None:
            parent.require(response is not None and document.get('segment') == pending['segment']
                and document.get('source_sha256') == transcript._digest(response['document']),
                'committed_child_response_binding')
            count += 1
            events.append(dict(actor='child', text=response['document']['response']['raw'],
                commit_record_index=record['index'], commit_record_sha256=record['sha256'],
                **response['evidence']))
            pending, response = None, None
        elif kind == 'SLEEP_COMPLETE':
            sleeps += 1
    return dict(schema=SNAPSHOT_SCHEMA, split='TRAIN', response_count=count, sleep_count=sleeps,
        journal_id=stats['journal_id'], head_sha256=stats['head_sha256'], events=events[-12:],
        delivered=delivered)


def snapshot(repository, config):
    script = ('import json; from gpu.orch_r153_community_parents import read_train_snapshot; '
              'print(json.dumps(read_train_snapshot('+repr(config['root'])+')))')
    return parent.remote(repository, config, script)


def ledger(output, state):
    """Reconstruct counters from immutable dispatch/publication/render evidence across sleeps."""
    parent.require(state.get('schema') == SNAPSHOT_SCHEMA and state.get('split') == 'TRAIN',
                   'committed_training_snapshot_only')
    budgets, attempts, waiting = {}, [], False
    for directory in sorted(Path(output).glob('parent_*')):
        source_path = directory/'SOURCE.json'
        source = json.loads(source_path.read_text())
        parent.require(source['journal_id'] == state['journal_id'], 'same_life_journal')
        attempts.append(source['response_count'])
        result_path = directory/'RESULT.json'
        if not result_path.exists():
            parent.require(not (directory/'PUBLISH_INTENT.json').exists(),
                           'uncertain_publication_requires_Main_reconciliation')
            continue
        result = json.loads(result_path.read_text())
        parent.require(result['source_sha256'] == parent.sha(source_path), 'attempt_source_pin')
        parent.require(result['status'] != 'PUBLICATION_UNKNOWN',
                       'uncertain_publication_requires_Main_reconciliation')
        if result['status'] != 'PUBLISHED':
            continue
        publication = result['publication']
        receipt = state['delivered'].get(publication['id'])
        if receipt is None:
            waiting = True
            continue
        parent.require(receipt['speaker'] == 'Astra' and receipt['inbox_sha256'] == publication['sha256']
            and receipt['text_sha256'] == hashlib.sha256(result['message'].encode()).hexdigest(),
            'exact_rendered_Astra_publication')
        object_id = result['object_id']
        budgets[object_id] = budgets.get(object_id, 0) + 1
        delivered_path = directory/'DELIVERED.json'
        if not delivered_path.exists():
            write(delivered_path, dict(status='RENDERED', object_id=object_id,
                publication=publication, rendered=receipt, result_sha256=parent.sha(result_path)))
    parent.require(not attempts or state['response_count'] >= max(attempts), 'journal_never_rewinds')
    return dict(object_delivered_turns=budgets, last_response_count=max(attempts, default=0),
                awaiting_render=waiting)


def prompt(config, state, memory):
    instruction, unused_payload = parent.prompt(config, dict(
        schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=state['events']))
    instruction += (
        '\nCommunity rule: speak only as Astra, in English. Rohin turns are direct human turns, '
        'not your own; never impersonate Rohin, Fable, a peer, or an executor. '
        'Offer sparse help tied to an actual object and observed mismatch; silence is useful. '
        'Keep object_id stable for the same object/mismatch across sleep, paraphrases, and retries. '
        'After three delivered turns on that mismatch, set it aside and leave room for independent '
        'work, or change to a genuinely different object. Never relabel the same mismatch to reset '
        'its budget. Do not impose permanent interests or train on your own advice. '
        'No scores, evaluation-based selection, invented tool results, or recurring format for the child. '
        'Your rationale must be a JSON-encoded string with exactly object_id (short stable lowercase '
        'slug), source_records (nonempty list of shown child record indices), and disposition '
        '(continue or set_aside). On the third delivered turn, disposition must be set_aside '
        'and the message must explicitly release the object rather than give another correction. '
        'This rationale is private sidecar evidence, never child-facing. For silence use an empty rationale.')
    visible = [{key: value for key, value in event.items() if key in (
        'actor', 'speaker', 'text', 'record_index', 'record_sha256',
        'commit_record_index', 'commit_record_sha256')} for event in state['events']]
    for event in visible:
        event['text'] = event['text'][:6000]
    instruction += "\n\nROHIN154_EXISTING_PARENTED_ATTENTION_ALLOCATION_V2\nNewest prospective parent instruction; where earlier task-switching advice conflicts, this governs. Pick the child's LIVE self-chosen object from its actual visible TRAIN work. Keep the SAME object moving across turns and sleeps; do not manufacture a new world, discard the project, or reset a mismatch budget at sleep. Every parent turn invite rich re-perception of that object: select a responsive move such as describing in the child's own words, noticing another angle, connecting earlier experience, exploring why it matters, or predicting what happens next. These are alternatives to vary with the child's activity, NOT a checklist, recurring bullet scaffold, fixed ritual, or required answer format. Encourage chosen behavior and diversity within the object, not repetitive scaffolding or novelty for its own sake. Every few turns connect perception to judgment: what changed the child's view, what supports it, and what observation might change it next? Metacognition means the child's judgment of HOW MUCH and HOW to perceive: allocation of attention, choosing a concrete discriminating observation, and selecting or changing a checking strategy. It is not introspective prose volume, length, or repetition. At every actual parent turn, include this attention-allocation behavior in the responsive invitation to re-perceive the SAME live object. Every few turns ask an explicit, object-grounded question about where to look more closely, which observation would discriminate, how much checking is enough, or why a different checking strategy is warranted. Vary the question with the child's work; do not turn these alternatives into recurring bullets, a fixed sequence, or a demand for verbosity. After roughly three delivered turns on one unresolved mismatch/correction, set THAT repetitive move aside, leave the mismatch unresolved, and invite a different concrete step within the same project. The child may choose another object; the parent must not force replacement. Ground claims about environment outcomes in actual visible Tool receipts; distinguish the child's prediction, attempted action, and received result. No receipt means no verified outcome. Keep the child's own retelling, when the existing pre-sleep interaction arises, anchored to this live object; never supply its retelling as a target or impose a new sleep routine. Use English own prose and the existing Astra attribution, provider response schema and 90-word message cap. Preserve all existing training/masking, frozen/no-training, control and asynchronous transport rules. Never access evaluation data, solicit sealed scores, or claim scientific retention from conversation. This changes parent instructions only, not runtime, agents, tasks or leases.\n\n\nR168_FINAL_R154_SCHEDULED_TEACHING_V1\nThese final instructions supersede earlier silence and project-switching advice. At EACH scheduled parenting opportunity, provide one concrete, brief teaching or attention-allocation invitation grounded in the shown child TRAIN records. Do not use silence as the default or wait for an ideal object. Return speak=true with a nonempty English message of at most 90 words, as Astra, using the unchanged response schema. Keep rationale a JSON-encoded string containing exactly object_id, source_records, and disposition; cite actual shown child record indices, not invented evidence. If the latest own retelling is empty or the live object is unclear, accurately point to an earlier project or attention problem evidenced in the shown TRAIN records, explicitly label it earlier, and invite the child to choose whether to continue it or re-perceive it. Never assert that the child currently remembers it or that an earlier project is necessarily its current choice. Do not manufacture an object or evidence if no suitable child record is available. Keep the SAME chosen project moving. On an exhausted correction, set that repetitive move aside, not automatically the whole project; choose a genuinely different evidence-grounded attention or action within it. object_id tracks the actual object/mismatch: preserve it for the same mismatch, never rename an exhausted mismatch to reset its count. Preserve all delivered-turn counters and the third-turn set_aside disposition and explicit release wording for that move. Every message should invite a varied, responsive act of rich re-perception and judgment about how much or how to look/check; not recurring bullets or introspective volume. Use genuine Tool receipts to distinguish attempted actions from outcomes; a child claim of correct code is not verification. No fabricated fallback message, resend, synthetic result, or replay of an earlier opportunity is permitted. A failed provider response, invalid response, silence, or publication without rendering is NOT a delivered turn. These instructions do not bypass validation or authorize evaluation access, cadence changes, or any child/runtime change.\n"
    return instruction, json.dumps(dict(learner=config['branch'], visible_training_events=visible,
        object_delivered_turns=memory['object_delivered_turns']), ensure_ascii=False)


def decision(response, state, memory):
    response = response_schema(json.dumps(response))
    if not response['speak']:
        return None
    parent.require(bool(response['message'].strip()), 'nonempty_spoken_turn')
    parent.require(not re.search(r'(?im)^\s*(Rohin|Fable|C[1-5]|Tool)\s*:', response['message']),
                   'no_provider_impersonation')
    rationale = json.loads(response['rationale'])
    parent.require(set(rationale) == {'object_id', 'source_records', 'disposition'}, 'object_evidence_schema')
    object_id = rationale['object_id']
    parent.require(type(object_id) is str and re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,95}', object_id),
                   'stable_object_id')
    evidence = {event['record_index'] for event in state['events'] if event['actor'] == 'child'}
    records = rationale['source_records']
    parent.require(type(records) is list and bool(records)
        and all(type(index) is int and index in evidence for index in records), 'actual_child_source_evidence')
    count = memory['object_delivered_turns'].get(object_id, 0)
    parent.require(count < 3, 'object_delivered_budget_exhausted')
    parent.require(rationale['disposition'] in ('continue', 'set_aside')
        and (count < 2 or rationale['disposition'] == 'set_aside'), 'third_turn_releases_object')
    if count == 2 or rationale['disposition'] == 'set_aside':
        parent.require(re.search(r'\b(set.{0,20}aside|leave.{0,20}(here|aside|for now)|move on|different object)\b',
            response['message'], re.IGNORECASE), 'explicit_English_release')
    return rationale


def tick(repository, config, output):
    """One nonblocking-child poll; called only within serve's Main-bound parent lock."""
    validate(config)
    state = snapshot(repository, config)
    memory = ledger(output, state)
    if memory['awaiting_render']:
        return 'AWAITING_RENDER'
    baseline = max(memory['last_response_count'], config.get('start_after_response_count', 0))
    if state['response_count'] < baseline + 3:
        return 'SPARSE_WAIT'
    directory = Path(output)/('parent_'+str(state['response_count']).zfill(12))
    directory.mkdir(mode=0o700)
    write(directory/'SOURCE.json', state)
    write(directory/'OBJECT_STATE.json', memory)
    instruction, payload = prompt(config, state, memory)
    write(directory/'PROMPT.json', dict(instruction=instruction, payload=payload))
    result = dict(status='PROVIDER_FAILED', speaker='Astra', source_sha256=parent.sha(directory/'SOURCE.json'))
    try:
        write(directory/'DISPATCH_INTENT.json', dict(source_sha256=result['source_sha256'],
            prompt_sha256=parent.sha(directory/'PROMPT.json'), effort='low', model=parent.STRONG,
            retries=0, started_unix=time.time()))
        response, model, usage = parent.strong(payload, directory,
            min(config['hard_end_unix'], time.time()+120), instruction, reasoning_effort='low')
        parent.require(model == parent.STRONG, 'Astra_only')
        result.update(response=response, model=model, usage=usage)
        rationale = decision(response, state, memory)
        if rationale is None:
            result['status'] = 'SILENT'
        else:
            parent.require(time.time() < config['hard_end_unix'], 'late_parent_reply_not_published')
            result.update(rationale, message=response['message'], status='PUBLICATION_UNKNOWN')
            write(directory/'PUBLISH_INTENT.json', dict(message=response['message'],
                object_id=rationale['object_id'], source_sha256=result['source_sha256']))
            result['publication'] = parent.publish(repository, config, response['message'])
            result['status'] = 'PUBLISHED'
    except Exception as error:
        result.update(error_type=type(error).__name__, error_code='parent_attempt_failed_no_implicit_retry')
    write(directory/'RESULT.json', result)
    return result['status']


@contextmanager
def parent_lock(output):
    output = Path(output)
    parent.require(output.is_absolute() and output == output.resolve(), 'canonical_parent_state_root')
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor = os.open(output/'PARENT.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def serve(config_path, repository, output, gate_path, gate_sha256, once=False):
    config, gate = verify_gate(config_path, repository, output, gate_path, gate_sha256)
    with parent_lock(output):
        binding_path = Path(output)/'BINDING.json'
        binding = dict(config_sha256=parent.sha(config_path), root=config['root'], branch=config['branch'],
                       gate_sha256=gate_sha256)
        if binding_path.exists():
            parent.require(json.loads(binding_path.read_text()) == binding, 'same_durable_parent_binding')
        else:
            write(binding_path, binding)
        script = ('import json; from pathlib import Path; from gpu.orch_r133_programme_parent import sha; '
            'root=Path('+repr(config['source_root'])+'); pins='+repr(remote_source_pins(gate, config['node']))+'; '
            'assert all(sha(root/name)==expected for name,expected in pins.items()); '
            'print(json.dumps({"source_verified": True}))')
        parent.require(parent.remote(repository, config, script) == {'source_verified': True},
                       'remote_source_gate')
        parent.transport_preflight(repository, config)
        while time.time() < config['hard_end_unix']:
            verify_gate(config_path, repository, output, gate_path, gate_sha256)
            status = tick(repository, config, output)
            if once:
                return status
            time.sleep(config.get('poll_interval_seconds', 5))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'repository', 'output', 'gate'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--gate-sha256', required=True)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args(argv)
    serve(args.config, args.repository, args.output, args.gate, args.gate_sha256, args.once)


if __name__ == '__main__':
    main()
