"""Prospective, owner-admitted parent-only R166 successor. No child lifecycle operations."""

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import time
import unicodedata

from gpu import orch_r133_programme_parent as parent
from gpu import orch_r153_community_parents as community
from gpu.orch_r125_stream_journal import _decode, _digest, _encoded, require


SCHEMA = 'R166_PARENT_SUCCESSOR_V1'
SOURCE_FILES = tuple(sorted(set(community.SOURCE_FILES) | {
    'gpu/orch_r166_parent_policy.py', 'gpu/orch_r166_parent_snapshot.py',
    'gpu/orch_r153_community_service.py', 'gpu/orch_r153_community_exchange.py'}))
GRAMMAR = ('Exchange grammar, once: send exactly one JSON object, or one json-fenced object, '
    'with no surrounding prose. Example: {"op":"list_messages","cursor":0}. '
    'Use only the documented operation fields; an attempt is not a successful result.')
MAX_RECEIPT_BYTES = 16 * 1024 * 1024
JUDGMENT_SCOPE = 'PARENT_REPORTED_CONVERSATIONAL_ONLY_NOT_SCIENTIFIC_RETENTION'
PROMPT_POLICY_MARKER = 'ROHIN154_EXISTING_PARENTED_ATTENTION_ALLOCATION_V2'
PRIOR_PROMPT_POLICY_MARKER = 'ROHIN153_EXISTING_PARENTED_LIVE_OBJECT_V1'
PROMPT_POLICY = (
    '\n\n' + PROMPT_POLICY_MARKER + '\n'
    'Newest prospective parent instruction; where earlier task-switching advice conflicts, this governs. '
    'Pick the child\'s LIVE self-chosen object from its actual visible TRAIN work. Keep the SAME object '
    'moving across turns and sleeps; do not manufacture a new world, discard the project, or reset a '
    'mismatch budget at sleep. Every parent turn invite rich re-perception of that object: select a '
    'responsive move such as describing in the child\'s own words, noticing another angle, connecting '
    'earlier experience, exploring why it matters, or predicting what happens next. These are alternatives '
    'to vary with the child\'s activity, NOT a checklist, recurring bullet scaffold, fixed ritual, or '
    'required answer format. Encourage chosen behavior and diversity within the object, not repetitive '
    'scaffolding or novelty for its own sake. Every few turns connect perception to judgment: what '
    'changed the child\'s view, what supports it, and what observation might change it next? '
    'Metacognition means the child\'s judgment of HOW MUCH and HOW to perceive: allocation of '
    'attention, choosing a concrete discriminating observation, and selecting or changing a checking '
    'strategy. It is not introspective prose volume, length, or repetition. At every actual parent '
    'turn, include this attention-allocation behavior in the responsive invitation to re-perceive the '
    'SAME live object. Every few turns ask an explicit, object-grounded question about where to '
    'look more closely, which observation would discriminate, how much checking is enough, or '
    'why a different checking strategy is warranted. Vary the question with the child\'s work; '
    'do not turn these alternatives into recurring bullets, a fixed sequence, or a demand for verbosity. '
    'After roughly three delivered turns on one unresolved mismatch/correction, set THAT repetitive '
    'move aside, leave the mismatch unresolved, and invite a different concrete step within the same '
    'project. The child may choose another object; the parent must not force replacement. '
    'Ground claims about environment outcomes in actual visible Tool receipts; distinguish the child\'s '
    'prediction, attempted action, and received result. No receipt means no verified outcome. '
    'Keep the child\'s own retelling, when the existing pre-sleep interaction arises, anchored to this '
    'live object; never supply its retelling as a target or impose a new sleep routine. '
    'Use English own prose and the existing Astra attribution, provider response schema and 90-word '
    'message cap. Preserve all existing training/masking, frozen/no-training, control and asynchronous '
    'transport rules. Never access evaluation data, solicit sealed scores, or claim scientific retention '
    'from conversation. This changes parent instructions only, not runtime, agents, tasks or leases.\n')


def prompt_policy_bytes(original):
    """Pure append-only policy payload for the existing principles-file transport."""
    require(type(original) is bytes and len(original) <= MAX_RECEIPT_BYTES, 'bounded_original_principles')
    original.decode('utf-8')
    require(not any(marker.encode() in original for marker in
        (PROMPT_POLICY_MARKER, PRIOR_PROMPT_POLICY_MARKER)), 'policy_already_present_no_duplicate_suffix')
    result = original + PROMPT_POLICY.encode('utf-8')
    require(len(result) <= MAX_RECEIPT_BYTES, 'bounded_successor_principles')
    return result


def prompt_only_config(original, *, principles_ref, existing_parented):
    """Read-only staging check; change ONLY principles path/hash. Not activation GO."""
    require(existing_parented is True, 'explicit_existing_parented_scope')
    parent.validate(original)
    old_path = community.local_file(original['principles_path'])
    new_path = community.local_file(principles_ref['path'])
    require(old_path != new_path and old_path.stat().st_size <= MAX_RECEIPT_BYTES
        and new_path.stat().st_size <= MAX_RECEIPT_BYTES, 'new_bounded_principles_file')
    old_raw, new_raw = old_path.read_bytes(), new_path.read_bytes()
    require(hashlib.sha256(old_raw).hexdigest() == original['principles_sha256']
        and hashlib.sha256(new_raw).hexdigest() == principles_ref['sha256']
        and new_raw == prompt_policy_bytes(old_raw), 'exact_append_only_prompt_successor')
    config = copy.deepcopy(original)
    config.update(principles_path=str(new_path), principles_sha256=principles_ref['sha256'])
    parent.validate(config)
    return config


def pinned(reference):
    path = community.local_file(reference['path'])
    require(path.stat().st_size <= MAX_RECEIPT_BYTES, 'bounded_receipt')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == reference['sha256'], 'receipt_pin')
    return _decode(raw)


def export_predecessor(output, snapshot):
    """Read-only R153 handoff proposal, NOT authority; Main must pin these exact bytes.

    R133 heterogeneous/standalone outputs require separately reconciled Main seed.
    An existing R133 INBOX-based DELIVERED label never becomes rendered evidence.
    """
    entries = []
    total = 0
    directories = sorted(Path(output).glob('parent_*'))
    require(len(directories) <= 10000, 'predecessor_attempt_limit')
    for directory in directories:
        require(not directory.is_symlink() and directory.is_dir(), 'regular_attempt_directory')
        source, result = directory/'SOURCE.json', directory/'RESULT.json'
        require(source.exists() and result.exists(), 'unfinished_predecessor_requires_reconciliation')
        refs = {}
        for name, path in (('source', source), ('result', result)):
            require(not path.is_symlink() and path.stat().st_size <= MAX_RECEIPT_BYTES, 'bounded_predecessor')
            total += path.stat().st_size
            require(total <= 128 * 1024 * 1024, 'predecessor_byte_limit')
            refs[name] = dict(path=str(path.resolve()), sha256=parent.sha(path))
        source_doc, result_doc = pinned(refs['source']), pinned(refs['result'])
        require(source_doc['journal_id'] == snapshot['journal_id']
            and result_doc['source_sha256'] == refs['source']['sha256'], 'predecessor_source_binding')
        require(result_doc['status'] in ('PUBLISHED', 'SILENT', 'PROVIDER_FAILED', 'VALIDATION_FAILED'), 'uncertain_predecessor')
        require(not (directory/'PUBLISH_INTENT.json').exists() or result_doc['status'] == 'PUBLISHED',
                'uncertain_predecessor_publish')
        entries.append(dict(source=source_doc, result=result_doc, refs=refs))
    return dict(schema=SCHEMA, journal_id=snapshot['journal_id'], attempts=entries,
        object_delivered_turns={}, last_response_count=0, last_request_count=0,
        prospective_request_count=snapshot['request_count'], credits={}, grammar_delivered=False)


def build_config(original, *, seed_ref, cursor_store, community_learner):
    """Pure prospective config; preserve programme, root, wall and original config hash."""
    parent.validate(original)
    config = copy.deepcopy(original)
    config.update(r166_schema=SCHEMA, predecessor_config_sha256=_digest(original),
        predecessor_seed=seed_ref, cursor_store=str(cursor_store),
        community_learner=community_learner, prospective_label='Rohin150-parent-policy-successor',
        object_turn_limit=3)
    if community_learner:
        require(original.get('community_schema') == community.SCHEMA, 'community_predecessor')
        config.update(cadence_responses=1, cadence_label='SPARSE', schedule_on='response')
    return config


def validate(config):
    parent.validate(config)
    require(config.get('r166_schema') == SCHEMA and config.get('object_turn_limit') == 3,
            'successor_policy')
    require(type(config.get('community_learner')) is bool, 'explicit_community_scope')
    if config['community_learner']:
        require(config['branch'] in community.LEARNERS and config['cadence_responses'] == 1
            and config['schedule_on'] == 'response', 'prospective_community_cadence')
    return config


def memory(seed, attempts, state):
    require(state['split'] == 'TRAIN' and state['journal_id'] == seed['journal_id'], 'same_TRAIN_life')
    result = {key: copy.deepcopy(seed[key]) for key in ('object_delivered_turns',
        'last_response_count', 'last_request_count', 'prospective_request_count', 'credits', 'grammar_delivered')}
    result.update(awaiting_render=False, deliveries=[], relapses=[], responded_audits=[],
                  delivered_next_steps=[])
    seen = set()
    for attempt in seed['attempts'] + attempts:
        source, receipt = attempt['source'], attempt['result']
        require(source['journal_id'] == state['journal_id'], 'same_attempt_journal')
        result['last_response_count'] = max(result['last_response_count'], source['response_count'])
        result['last_request_count'] = max(result['last_request_count'], source.get('request_count', 0))
        require(receipt['status'] in ('PUBLISHED', 'SILENT', 'PROVIDER_FAILED', 'VALIDATION_FAILED'), 'uncertain_publication')
        if receipt['status'] != 'PUBLISHED':
            continue
        publication = receipt['publication']
        require(publication['id'] not in seen, 'duplicate_publication')
        seen.add(publication['id'])
        delivered = state['delivered'].get(publication['id'])
        if delivered is None:
            result['awaiting_render'] = True
            continue
        require(delivered['speaker'] == 'Astra' and delivered['inbox_sha256'] == publication['sha256']
            and delivered['text_sha256'] == hashlib.sha256(receipt['message'].encode()).hexdigest(),
            'exact_rendered_parent')
        object_id = receipt['object_id']
        result['object_delivered_turns'][object_id] = result['object_delivered_turns'].get(object_id, 0) + 1
        result['deliveries'].append(delivered['request_count'])
        result['responded_audits'].extend(receipt.get('relapse_audit_sha256', []))
        if receipt.get('continuity') is not None:
            result['delivered_next_steps'].append(copy.deepcopy(dict(next_task=receipt['next_task'],
                continuity=receipt['continuity'], publication=publication)))
        if receipt.get('grammar_lesson'):
            result['grammar_delivered'] = True
        credit = receipt.get('credit')
        if credit:
            require(credit['id'] not in result['credits'], 'duplicate_credit_id')
            result['credits'][credit['id']] = dict(credit, publication=publication,
                delivered=delivered, audit_sleep_counts=[delivered['sleep_count']+offset for offset in (1, 2, 3)])
    require(state['response_count'] >= result['last_response_count']
        and state['request_count'] >= result['last_request_count'], 'no_cursor_rewind')
    start = result['prospective_request_count']
    require(type(start) is int and 0 <= start <= state['request_count'], 'prospective_frontier')
    result['missed_floor_windows'] = [list(range(end-1, end+1))
        for end in range(start+2, state['request_count']+1)
        if not any(end-1 <= delivery <= end for delivery in result['deliveries'])]
    result['audit_tasks'] = [dict(credit_id=identifier, sleep_count=sleep,
        status='DUE_UNREVIEWED' if state['sleep_count'] >= sleep else 'WAITING_FOR_SLEEP')
        for identifier, credit in result['credits'].items() for sleep in credit['audit_sleep_counts']]
    return result


def bind_watcher_audits(memory_state, references, state):
    """Only externally pinned watcher judgments; never infer retention from substrings."""
    seen = set()
    for reference in references:
        audit = pinned(reference)
        require(audit['journal_id'] == state['journal_id'] and audit['credit_id'] in memory_state['credits'],
                'watcher_credit_binding')
        credit = memory_state['credits'][audit['credit_id']]
        key = (audit['credit_id'], audit['sleep_count'])
        require(key not in seen and audit['sleep_count'] in credit['audit_sleep_counts']
            and audit['sleep_count'] <= state['sleep_count'], 'watcher_three_sleep_window')
        require(audit['verdict'] in ('RETAINED', 'RELAPSE', 'UNRESOLVED')
            and audit['reviewer'] != 'Astra-parent' and bool(audit['reviewer']), 'independent_watcher_verdict')
        evidence = pinned(audit['snapshot'])
        require(evidence['journal_id'] == state['journal_id'] and evidence['split'] == 'TRAIN'
            and evidence['sleep_count'] == audit['sleep_count'], 'watcher_snapshot_binding')
        _quote(audit['evidence'], evidence)
        seen.add(key)
        for task in memory_state['audit_tasks']:
            if (task['credit_id'], task['sleep_count']) == key:
                task.update(status=audit['verdict'], authority=reference, judgment_scope=JUDGMENT_SCOPE)
        if audit['verdict'] == 'RELAPSE' and reference['sha256'] not in memory_state['responded_audits']:
            memory_state['relapses'].append(dict(audit, authority_sha256=reference['sha256']))


def _quote(evidence, state):
    require(type(evidence) is dict and set(evidence) == {'record_index', 'record_sha256', 'quote'},
            'exact_child_quote_schema')
    require(type(evidence['quote']) is str and 0 < len(evidence['quote']) <= 2000, 'bounded_quote')
    require(any(event['actor'] == 'child' and event['record_index'] == evidence['record_index']
        and event['record_sha256'] == evidence['record_sha256'] and evidence['quote'] in event['text']
        for event in state['events']), 'actual_committed_child_quote')


def english_output(message, evidence_quotes):
    """Conservative script check, NOT linguistic proof; exact quoted evidence exempt."""
    prose = message
    for quote in evidence_quotes:
        for opening, closing in (('"', '"'), ('“', '”'), ('`', '`')):
            prose = prose.replace(opening + quote + closing, '')
    require(all(ord(character) < 128 or 'LATIN' in unicodedata.name(character, '')
        or unicodedata.category(character).startswith(('P', 'Z')) for character in prose),
        'English_prose_script_validation_failed_not_language_proof')


def _environment_quote(evidence, state):
    require(type(evidence) is dict and set(evidence) == {
        'record_index', 'record_sha256', 'quote', 'inbox_id', 'inbox_sha256'}, 'environment_receipt_schema')
    require(type(evidence['quote']) is str and 0 < len(evidence['quote']) <= 2000, 'bounded_environment_quote')
    delivered = state['delivered'].get(evidence['inbox_id'])
    require(delivered is not None and delivered['speaker'] == 'Tool'
        and delivered['inbox_sha256'] == evidence['inbox_sha256']
        and delivered['record_index'] == evidence['record_index']
        and delivered['record_sha256'] == evidence['record_sha256'], 'actual_rendered_Tool_receipt')
    require(any(event['actor'] == 'environment' and event.get('speaker') == 'Tool'
        and event['record_index'] == evidence['record_index']
        and event['record_sha256'] == evidence['record_sha256']
        and evidence['quote'] in event['text']
        and hashlib.sha256(event['text'].encode()).hexdigest() == delivered['text_sha256']
        for event in state['events']), 'environment_quote_binding')


def _continuity(details, message, state, memory_state):
    continuity = details.get('continuity')
    require(type(continuity) is dict and set(continuity) == {
        'chosen_object', 'move_kind', 'progress_basis', 'environment_receipts'}, 'same_chosen_object_continuity')
    chosen = continuity['chosen_object']
    previous = memory_state['delivered_next_steps']
    if not any(chosen == step['continuity']['chosen_object'] for step in previous):
        _quote(chosen, state)
    require(chosen['quote'] in details['next_task']
        and re.search(r'\b(keep|continue|stay with|within)\b', message, re.I), 'preserve_chosen_object_in_next_step')
    require(continuity['move_kind'] in ('perception', 'judgment', 'test', 'chosen_behavior'), 'responsive_move_kind')
    receipts = continuity['environment_receipts']
    require(type(receipts) is list and len(receipts) <= 4, 'bounded_environment_receipts')
    for evidence in receipts:
        _environment_quote(evidence, state)
    basis = 'RENDERED_TOOL_OBSERVATION' if receipts else 'UNVERIFIED_NEXT_STEP'
    require(continuity['progress_basis'] == basis, 'no_invented_environment_progress')
    if not receipts:
        require('not yet verified' in message.lower(), 'unverified_step_explicit')
    repeated = [step for step in previous if ' '.join(step['next_task'].casefold().split())
                == ' '.join(details['next_task'].casefold().split())]
    old_receipts = {(evidence['inbox_id'], evidence['inbox_sha256']) for step in repeated
                    for evidence in step['continuity']['environment_receipts']}
    require(not repeated or any((evidence['inbox_id'], evidence['inbox_sha256']) not in old_receipts
        for evidence in receipts), 'repeated_move_without_new_environment_evidence')
    return [chosen['quote']] + [evidence['quote'] for evidence in receipts]


def decision(response, state, memory_state):
    response = community.response_schema(json.dumps(response))
    if not response['speak']:
        return None
    details = json.loads(response['rationale'])
    require(set(details) - {'continuity'} == {'object_id', 'source_records', 'disposition', 'next_task',
        'perception', 'credit', 'relapse_credit_id'}, 'policy_evidence_schema')
    legacy = {key: details[key] for key in ('object_id', 'source_records', 'disposition')}
    community.decision(dict(response, rationale=json.dumps(legacy)), state, memory_state)
    message = response['message']
    _quote(details['perception'], state)
    quotes = [details['perception']['quote']]
    if details['disposition'] == 'set_aside':
        require(re.search(r'\bunresolved\b', message, re.I) and type(details['next_task']) is str
            and len(details['next_task'].split()) >= 3 and details['next_task'] in message,
            'unresolved_and_next_concrete_step')
        quotes.extend(_continuity(details, message, state, memory_state))
    else:
        require(details['next_task'] is None and details.get('continuity') is None, 'no_unbound_task')
    credit = details['credit']
    require(('CREDIT:' in message) == (credit is not None), 'credit_marker_and_ledger_together')
    if credit is not None:
        require(set(credit) == {'id', 'step', 'evidence'} and type(credit['id']) is str
            and re.fullmatch('[a-z0-9_-]{1,96}', credit['id'])
            and credit['id'] not in memory_state['credits'] and type(credit['step']) is str
            and 0 < len(credit['step']) <= 500, 'structured_own_step_credit')
        _quote(credit['evidence'], state)
        quotes.append(credit['evidence']['quote'])
    english_output(message, quotes)
    relapse = details['relapse_credit_id']
    if memory_state['relapses']:
        require(relapse in {audit['credit_id'] for audit in memory_state['relapses']}, 'respond_to_credit_relapse')
    if relapse is not None:
        require(relapse in {audit['credit_id'] for audit in memory_state['relapses']}
            and 'NOTICE' in message and re.search(r'\bwhy\b', message, re.I)
            and re.search(r'\b(repeated|again|same correction)\b', message, re.I), 'NOTICE_repeated_correction_why')
    return details


def prompt(config, state, memory_state):
    instruction, unused = parent.prompt(config, dict(schema='R133_TRAIN_PARENT_SNAPSHOT_V1', events=state['events']))
    instruction += ('\nProspective Rohin150 with newest R152 steering: English only, Astra attribution. '
        'Preserve and progress the SAME self-chosen object/project, not a new world each sleep. '
        'object_id is the existing stable unresolved mismatch/correction-move budget key, NOT a project '
        'expiration counter. Keep its three delivered turns maximum; on turn three leave that mismatch '
        'unresolved and set the repetitive correction aside, NOT the child\'s project. Propose a different '
        'concrete step within the same child-chosen object, naming its exact child quote in next_task. '
        'Keep prior object IDs/counts intact across sleeps; never rename a mismatch to reset its budget. '
        'Let the child choose behavior; vary perception, judgment, small tests and metacognition in response '
        'to observations, not ritual or novelty for its own sake. A project change requires the child\'s '
        'own choice, never a sleep boundary or exhausted correction budget. '
        'Ground environmental progress claims in actual shown rendered Tool receipts, not child narration, '
        'a publication attempt, or imagined success. Without such evidence label the proposed step '
        '"not yet verified"; do not claim demonstrated progress. '
        'Include a responsive perception/judgment move grounded in a shown child quote, '
        'not an endless fixed child ritual. Credit an actual child step with CREDIT: and a private ledger '
        'record, not a claim of tool success or retention. For watcher-confirmed relapse ask the child to '
        'NOTICE the repeated correction and why. Do not request a fixed response format. '
        'Private rationale must be JSON with object_id, source_records, disposition (continue/set_aside), '
        'next_task (null or exact same-project next-step text in message), perception ({record_index,record_sha256,quote}), '
        'credit (null or {id,step,evidence:{record_index,record_sha256,quote}}), relapse_credit_id (null or '
        'watcher-confirmed credit id). For set_aside also supply continuity: '
        '{chosen_object:{record_index,record_sha256,quote},move_kind:perception/judgment/test/chosen_behavior,'
        'progress_basis:RENDERED_TOOL_OBSERVATION/UNVERIFIED_NEXT_STEP,environment_receipts:[]}. '
        'chosen_object must be a shown committed child choice (or a previously delivered continuity anchor). '
        'Use keep/continue/stay with/within in the message to preserve that object. '
        'Each optional environment_receipts entry is {record_index,record_sha256,quote,inbox_id,inbox_sha256} '
        'bound to an actual Tool delivery shown below; maximum four. Repeating the identical next step '
        'needs a new rendered environment receipt, not just another sleep. For continue omit continuity '
        'or use null. These fields are private parent metadata, NEVER a fixed child ritual. '
        'No synthetic reviews, scores or invented observations. '
        'Speak your own prose in English. Accented Latin names are permitted; non-Latin source text '
        'may appear only as an exact bounded evidence.quote in double quotes or backticks. '
        'The script check is not proof of language. RETAINED is only a parent-reported conversational '
        'watcher judgment, never sealed or fresh-process scientific retention. '
        'Silence requires empty message and rationale.')
    lesson = config['community_learner'] and not memory_state['grammar_delivered']
    word_budget = 90 - len(GRAMMAR.split()) if lesson else 90
    instruction += f' Your message limit is {word_budget} whitespace-separated words.'
    if lesson:
        instruction += (' The transport will append this authorized one-time lesson verbatim; do not '
            'repeat it yourself. The combined publication is capped at 90 words: ' + GRAMMAR)
    instruction += PROMPT_POLICY
    return instruction, json.dumps(dict(events=state['events'], memory=memory_state,
        environment_deliveries={identifier: receipt for identifier, receipt in state['delivered'].items()
                                if receipt['speaker'] == 'Tool'}), ensure_ascii=False)


def local_attempts(output):
    attempts = []
    directories = sorted(Path(output).glob('parent_*'))
    require(len(directories) <= 10000, 'attempt_limit')
    for directory in directories:
        source_path, result_path = directory/'SOURCE.json', directory/'RESULT.json'
        require(result_path.exists(), 'unfinished_attempt_no_replay')
        require(source_path.stat().st_size <= MAX_RECEIPT_BYTES
            and result_path.stat().st_size <= MAX_RECEIPT_BYTES, 'bounded_attempt')
        source = pinned(dict(path=str(source_path.resolve()), sha256=parent.sha(source_path)))
        result = pinned(dict(path=str(result_path.resolve()), sha256=parent.sha(result_path)))
        require(result['source_sha256'] == parent.sha(source_path), 'attempt_source_pin')
        attempts.append(dict(source=source, result=result))
    return attempts


def tick(repository, config, output, seed, state):
    """One parent-only dispatch. Caller owns gate/lock; never waits on the child."""
    validate(config)
    if not state['caught_up']:
        return dict(status='VERIFIED_BOOTSTRAP_IN_PROGRESS', source_bytes=state['source_bytes'])
    memory_state = memory(seed, local_attempts(output), state)
    bind_watcher_audits(memory_state, config.get('watcher_audits', []), state)
    status = dict(memory=memory_state, observed_unix=time.time(), journal_head=state['head_sha256'])
    if memory_state['awaiting_render']:
        return dict(status, status='AWAITING_RENDER')
    clock = 'request_count' if config['community_learner'] or config.get('schedule_on') == 'request' else 'response_count'
    baseline = memory_state['last_request_count' if clock == 'request_count' else 'last_response_count']
    if state[clock] < baseline + config['cadence_responses'] or not any(event['actor'] == 'child' for event in state['events']):
        return dict(status, status='WAITING_FOR_NEW_CHILD_BOUNDARY')
    directory = Path(output)/f"parent_{state['request_count']:012d}"
    directory.mkdir(mode=0o700)
    community.write(directory/'SOURCE.json', state)
    instruction, payload = prompt(config, state, memory_state)
    community.write(directory/'PROMPT.json', dict(instruction=instruction, payload=payload))
    community.write(directory/'DISPATCH_INTENT.json', dict(request_count=state['request_count']))
    result = dict(status='PROVIDER_FAILED', source_sha256=parent.sha(directory/'SOURCE.json'))
    try:
        response, model, usage = parent.strong(payload, directory, config['hard_end_unix'], instruction,
                                              reasoning_effort=config.get('parent_reasoning_effort', 'low'))
        result.update(model=model, usage=usage, status='VALIDATION_FAILED')
        details = decision(response, state, memory_state)
        if details is None:
            result['status'] = 'SILENT'
        else:
            message = response['message']
            lesson = config['community_learner'] and not memory_state['grammar_delivered']
            if lesson:
                message += '\n\n' + GRAMMAR
            require(len(message.split()) <= 90 and len(message.encode()) <= 4096
                and time.time() < config['hard_end_unix'], 'bounded_timely_publication')
            result.update(details, message=message, grammar_lesson=lesson, status='PUBLICATION_UNKNOWN',
                relapse_audit_sha256=[audit['authority_sha256'] for audit in memory_state['relapses']
                    if audit['credit_id'] == details['relapse_credit_id']])
            community.write(directory/'PUBLISH_INTENT.json', dict(message=message, speaker='Astra'))
            result['publication'] = parent.publish(repository, config, message)
            result['status'] = 'PUBLISHED'
    except Exception as error:
        result.update(error_type=type(error).__name__, error=str(error)[:500])
    community.write(directory/'RESULT.json', result)
    return dict(status, status=result['status'])


def verify_gate(config, repository, output, gate):
    validate(config)
    require(gate['schema'] == SCHEMA and gate['status'] == 'MAIN_GO'
        and gate['confirmed_by'] == 'Main' and gate['config_sha256'] == _digest(config)
        and gate['output'] == str(Path(output).resolve()) and gate['parented_scope'] is True,
        'exact_Main_successor_GO')
    require(time.time() < gate['expires_unix'] <= config['hard_end_unix'], 'unexpired_parent_gate')
    require(gate['custody']['predecessor_terminal'] is True and gate['custody']['no_competing_parent'] is True
        and gate['custody']['pending_reconciled'] is True, 'owner_clean_handoff')
    for reference in (gate['custody']['receipt'], gate['cpu_receipt'], gate['intake']):
        pinned(reference)
    cpu = pinned(gate['cpu_receipt'])
    require(cpu['status'] == 'PASS' and cpu['execution_kind'] == 'CPU_ONLY'
        and cpu['source_pins'] == gate['source_pins'], 'CPU_provenance_bound_to_source')
    require({'tests/test_orch_r166_parent_policy.py', 'tests/test_orch_r166_parent_snapshot.py'}
        <= cpu['test_pins'].keys(), 'owned_regression_pins')
    for name, expected in cpu['test_pins'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts
            and parent.sha(community.local_file(Path(repository)/name)) == expected, 'CPU_test_pin')
    seed = pinned(config['predecessor_seed'])
    for entry in seed['attempts']:
        require(pinned(entry['refs']['source']) == entry['source']
            and pinned(entry['refs']['result']) == entry['result'], 'unchanged_predecessor_evidence')
    required = set(SOURCE_FILES) | {'gpu/'+config['node']+'_ssh.sh'}
    require(required <= gate['source_pins'].keys() and required <= gate['remote_source_pins'].keys(), 'source_closure')
    for name, expected in gate['source_pins'].items():
        path = Path(name)
        require(not path.is_absolute() and '..' not in path.parts, 'relative_source_pin')
        require(parent.sha(community.local_file(Path(repository)/path)) == expected, 'local_source_pin')
    for name, expected in gate['remote_source_pins'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts
            and re.fullmatch('[0-9a-f]{64}', expected), 'remote_source_pin')
    for name in SOURCE_FILES:
        require(gate['source_pins'][name] == gate['remote_source_pins'][name], 'identical_tested_parent_transport')
    require(Path(__file__).resolve() == Path(repository).resolve()/'gpu/orch_r166_parent_policy.py', 'executed_source')
    return seed


def serve(config_ref, repository, output, gate_ref, *, once=False):
    config, gate = pinned(config_ref), pinned(gate_ref)
    repository, output = Path(repository).resolve(), Path(output).resolve()
    seed = verify_gate(config, repository, output, gate)
    with community.parent_lock(output):
        binding = dict(config=config_ref, gate=gate_ref)
        binding_path = output/'BINDING.json'
        if binding_path.exists():
            require(_decode(binding_path.read_bytes()) == binding, 'immutable_successor_binding')
        else:
            community.write(binding_path, binding)
        script = ('import json; from pathlib import Path; from gpu.orch_r133_programme_parent import sha; '
            'root=Path('+repr(config['source_root'])+'); pins='+repr(gate['remote_source_pins'])+'; '
            'assert all(sha(root/name)==value for name,value in pins.items()); print(json.dumps({"verified":True}))')
        require(parent.remote(repository, config, script) == {'verified': True}, 'remote_closure')
        polls = sorted(output.glob('POLL_*.json'))
        reference = _decode(polls[-1].read_bytes())['reference'] if polls else None
        sequence = len(polls)
        while time.time() < min(config['hard_end_unix'], gate['expires_unix']):
            require(sequence < 100000, 'parent_poll_receipt_limit')
            script = ('import json; from gpu.orch_r166_parent_snapshot import stored_poll; '
                'print(json.dumps(stored_poll('+repr(config['root'])+','+repr(config['cursor_store'])+','+repr(reference)+')))')
            observed = parent.remote(repository, config, script)
            community.write(output/f'POLL_{sequence:08d}.json', observed)
            reference = observed['reference']
            status = tick(repository, config, output, seed, observed['snapshot'])
            community.write(output/f'STATUS_{sequence:08d}.json', status)
            sequence += 1
            if once:
                return status
            time.sleep(config.get('poll_interval_seconds', 5))
        community.write(output/'TERMINAL.json', dict(status='PARENT_WALL_COMPLETE', observed_unix=time.time()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'config-sha256', 'gate', 'gate-sha256', 'repository', 'output'):
        parser.add_argument('--'+name, required=True)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    serve(dict(path=args.config, sha256=args.config_sha256), args.repository, args.output,
          dict(path=args.gate, sha256=args.gate_sha256), once=args.once)


if __name__ == '__main__':
    main()
