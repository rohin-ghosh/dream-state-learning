"""Prospective outcome-filtered actual trajectories; never repair old source.

Pure replay is not native actor attestation. Native callers bind all original
receipts and new calls. Rows contain actual public prefixes and child responses;
failed sources, paired episodes and original all-or-none statuses remain evidence.
"""

from copy import deepcopy
from types import SimpleNamespace

from organism_v6 import experienced_event_goal_scale as scale


hop = scale.breadth.goal.hop
lesson = scale.breadth.goal.lesson
require = hop.require
same = lesson._same
document_sha256 = hop.document_sha256
SCHEMA = 'DEV_GOAL_QUALITY_COLLECTION_V1'
UNITS = (0, 1, 4, 6)
REUSED_SHARDS = (2, 3, 5, 7)
UNIT_WORLDS = {0: 7, 1: 8, 4: 7, 6: 7}
UNIT_CAPS = {unit: count * 24 for unit, count in UNIT_WORLDS.items()}
MAX_NEW_CALLS = 696
MAX_ROWS = 1452
UNAVAILABLE = 'MEMORY UNAVAILABLE'
CLAIM = 'NEW_OUTCOME_FILTERED_EXPOSED_DEV_DATASET_NOT_V1_RECOVERY_OR_UNBIASED_SAMPLE'


def runtime(shard):
    return SimpleNamespace(**scale.runtime(shard))


def source_plan(exposures):
    require(type(exposures) in (list, tuple) and len(exposures) == 8, 'all_eight_original_exposures_required')
    eligible, excluded, probes = [], [], []
    for shard, exposure in enumerate(exposures):
        goal = runtime(shard)
        collections = exposure['collections']
        require(tuple(item['master'] for item in collections) == goal.MASTERS, 'original_eighty_world_order_required')
        for world_index, collection in enumerate(collections):
            verified = goal.replay_collection(collection)
            bad = [dict(record_index=index, event=record['edge']['event'], error=deepcopy(record['error']))
                   for index, record in enumerate(verified['records']) if not record['accepted']]
            entry = dict(shard=shard, world_index=world_index, master=verified['master'],
                collection_sha256=verified['collection_sha256'], source_ready=verified['ready'], rejected_records=bad)
            if verified['master'] in goal.TRAIN_MASTERS:
                (eligible if verified['ready'] else excluded).append(entry)
            else:
                entry.update(world=deepcopy(verified['world']), text={record['edge']['event']:
                    record['event']['raw'] if record['accepted'] else UNAVAILABLE for record in verified['records']})
                probes.append(entry)
    units = [dict(unit=unit, masters=[entry['master'] for entry in eligible if entry['shard'] == unit],
                  max_native_calls=UNIT_CAPS[unit]) for unit in UNITS]
    require(len(eligible) == 61 and len(excluded) == 3 and len(probes) == 16
            and sum(len(entry['rejected_records']) for entry in excluded + probes) == 4,
            'fixed_original_316_of_320_source_population_required')
    require(all(len(unit['masters']) == UNIT_WORLDS[unit['unit']] for unit in units), 'fixed_29_untaught_worlds_required')
    return hop._seal(dict(schema=SCHEMA, eligible_train=eligible, excluded_train=excluded, probes=probes, units=units,
        original_train_worlds=64, source_eligible_train_worlds=61, original_train_tasks=256, source_eligible_train_tasks=244,
        source_excluded_train_tasks=12, original_train_pairs=128, source_eligible_train_pairs=122,
        probe_worlds=16, probe_goals=64, probe_pairs=32, source_events_accepted=316, source_events_total=320,
        original_exposure_calls=640, max_new_calls=MAX_NEW_CALLS, claim=CLAIM), 'plan_sha256')


def _world_quality(shard, collection, captures, episodes, origin, evidence_sha, original_ready=None):
    goal = runtime(shard)
    master = collection['master']
    require(master in goal.TRAIN_MASTERS and collection['ready'], 'eligible_train_world_only')
    require([entry['task_index'] for entry in episodes] == [0, 1, 2, 3], 'all_four_task_attempts_required')
    summary = goal.summarize_pairs(collection, [entry['episode'] for entry in episodes])
    admitted, pairs = set(), []
    for indexes, score in zip(goal.GOAL_PAIRS, summary['pairs']):
        accepted = all(episodes[index]['complete'] for index in indexes) and score['correct']
        if accepted:
            admitted.update(indexes)
        pairs.append(dict(task_indexes=list(indexes), admitted=accepted,
            reason=None if accepted else 'both_source_grounded_six_turn_episodes_required',
            failed_tasks=[index for index in indexes if not episodes[index]['complete']]))
    rows = []
    for task_index in range(4):
        if task_index not in admitted:
            continue
        actual = [capture for capture in captures if capture['task_index'] == task_index]
        require([capture['episode_call_index'] for capture in actual] == list(range(6)), 'six_actual_child_targets_required')
        for capture in actual:
            prefix = deepcopy(capture['student_prefix'])
            require(all(lesson.PARENT_GUIDANCE not in message['content'] for message in prefix), 'parent_free_student_prefix_required')
            require(capture['error'] is None, 'native_error_cannot_be_target')
            rows.append(hop._seal(dict(schema=SCHEMA, row_index=len(rows), shard=shard,
                world_index=goal.TRAIN_MASTERS.index(master), master=master, task_index=task_index,
                episode_call_index=capture['episode_call_index'], prefix=prefix, assistant=capture['response']['raw'],
                source_collection_sha256=collection['collection_sha256'], origin=origin,
                source_evidence_sha256=evidence_sha, call_index=capture['call_index'], call_sha256=capture['call_sha256'],
                target_eot=lesson.TARGET_EOT, loss_policy=deepcopy(lesson.LOSS_POLICY)), 'row_sha256'))
    return hop._seal(dict(schema=SCHEMA, shard=shard, master=master, origin=origin,
        source_collection_sha256=collection['collection_sha256'], source_evidence_sha256=evidence_sha,
        original_all_or_none_ready=original_ready, captures=deepcopy(captures), episodes=deepcopy(episodes),
        pairs=pairs, rows=rows, admitted_pairs=sum(pair['admitted'] for pair in pairs), attempted_tasks=4,
        native_error_calls=sum(capture['error'] is not None for capture in captures)), 'quality_sha256')


def reused_quality(exposures, teachings):
    require(set(teachings) == set(REUSED_SHARDS), 'reuse_exactly_shards_2_3_5_7')
    worlds = []
    for shard in REUSED_SHARDS:
        goal, document = runtime(shard), teachings[shard]
        goal.replay_lessons(document)
        same(document['collections'], exposures[shard]['collections'][:8], 'reused_teaching_source_join')
        for collection in document['collections']:
            master = collection['master']
            worlds.append(_world_quality(shard, collection,
                [capture for capture in document['captures'] if capture['master'] == master],
                [entry for entry in document['episodes'] if entry['master'] == master],
                'REUSED_ORIGINAL_TEACH', document['lesson_sha256'], document['ready']))
    rows = _ordered_rows(worlds)
    require(len(rows) == 756 and sum(document['model_calls'] for document in teachings.values()) == 768,
            'fixed_original_756_candidates_768_calls_required')
    return hop._seal(dict(schema=SCHEMA, worlds=worlds, rows=rows, reused_calls=768, new_calls=0,
        original_statuses=[dict(shard=shard, ready=teachings[shard]['ready'], original_rows=len(teachings[shard]['rows']))
                           for shard in REUSED_SHARDS], claim=CLAIM), 'reuse_sha256')


def _ordered_rows(worlds):
    rows = sorted((deepcopy(row) for world in worlds for row in world['rows']),
                  key=lambda row: (row['shard'], row['world_index'], row['task_index'], row['episode_call_index']))
    for index, row in enumerate(rows):
        row.pop('row_sha256')
        row['row_index'] = index
        row.update(hop._seal(row, 'row_sha256'))
    return rows


def _collect_world(shard, collection, invoke, offset):
    goal = runtime(shard)
    collection = goal.replay_collection(collection)
    require(collection['ready'] and collection['master'] in goal.TRAIN_MASTERS, 'complete_train_source_required')
    store = goal.exact_text_store(collection)
    captures, episodes = [], []
    for case in goal.build_cases(collection)['cases']:
        plan, episode_call = case['plan'], 0

        def actor(student):
            nonlocal episode_call
            require(episode_call < 6 and len(captures) < 24, 'quality_world_call_cap')
            metadata = dict(master=collection['master'], task_index=case['task_index'], episode_call_index=episode_call)
            guided = lesson._coached_messages(student, plan[episode_call], store)
            outcome = invoke(deepcopy(guided), metadata)
            capture = hop._seal(dict(call_index=offset + len(captures), student_prefix=deepcopy(student),
                messages=guided, **metadata, **deepcopy(outcome)), 'call_sha256')
            captures.append(capture)
            episode_call += 1
            require(capture['error'] is None, 'quality_callback_error')
            response = capture['response']
            if type(response) is dict:
                if 'messages' in response:
                    same(response['messages'], guided, 'quality_native_prompt_drift')
                if 'token_ids' in response:
                    require(type(response['token_ids']) is list and 0 < len(response['token_ids']) <= 160
                            and all(type(token) is int and token >= 0 for token in response['token_ids']), 'quality_token_cap')
                if 'prompt_tokens' in response:
                    require(type(response['prompt_tokens']) is int and 0 < response['prompt_tokens'] <= 2048, 'quality_context_cap')
                return {key: deepcopy(response[key]) for key in ('raw','terminal','truncated') if key in response}
            return deepcopy(response)

        episode = goal.run_episode(collection['world'], case['task'], actor, store.__getitem__)
        actual = [trace for trace in episode['traces'] if trace['kind'] == 'actor']
        matches = len(actual) == 6 and all(trace['error'] is None and type(trace['response']) is dict
            and type(trace['response'].get('raw')) is str and trace['response']['raw'].rstrip('\n') == step['command']
            for trace, step in zip(actual, plan))
        complete = (matches and episode['reached_goal'] and episode['terminal_reason'] == 'reached_goal'
                    and episode['route_calls'] == 2 and episode['memory_calls'] == 4)
        episodes.append(dict(master=collection['master'], task_index=case['task_index'], plan=plan, episode=episode,
            complete=complete, failure=None if complete else ('actual_commands_differ_from_plan' if episode['reached_goal'] else episode['terminal_reason'])))
    evidence = hop._seal(dict(shard=shard, collection=collection, captures=captures, episodes=episodes), 'evidence_sha256')
    return dict(evidence=evidence, quality=_world_quality(shard,collection,captures,episodes,'NEW_QUALITY_TEACH',evidence['evidence_sha256']))


def _collect_unit(exposures, plan, unit, invoke):
    require(type(unit) is int and unit in UNITS, 'fixed_quality_unit_required')
    planned = next(item for item in plan['units'] if item['unit'] == unit)
    collections = [item for item in exposures[unit]['collections'] if item['master'] in planned['masters']]
    require([item['master'] for item in collections] == planned['masters'], 'ordered_untaught_worlds_required')
    documents, count = [], 0
    for collection in collections:
        document = _collect_world(unit, collection, invoke, count)
        count += len(document['evidence']['captures'])
        documents.append(document)
    require(count <= UNIT_CAPS[unit], 'quality_unit_call_cap')
    worlds = [document['quality'] for document in documents]
    return hop._seal(dict(schema=SCHEMA, unit=unit, plan_sha256=plan['plan_sha256'], documents=documents,
        rows=_ordered_rows(worlds), model_calls=count, max_native_calls=UNIT_CAPS[unit], attempts_complete=True,
        attempted_tasks=4*len(worlds), admitted_pairs=sum(world['admitted_pairs'] for world in worlds),
        rejected_pairs=sum(2-world['admitted_pairs'] for world in worlds),
        native_error_calls=sum(world['native_error_calls'] for world in worlds), fits=0, claim=CLAIM), 'unit_sha256')


def collect_unit(exposures, unit, generate):
    plan = source_plan(exposures)
    return _collect_unit(exposures,plan,unit,
        lambda messages, metadata: hop._invoke(lambda prompt: generate(prompt, **metadata), messages))


def replay_unit(exposures, document):
    plan = source_plan(exposures)
    captures = iter(capture for world in document['documents'] for capture in world['evidence']['captures'])

    def invoke(messages, metadata):
        capture = next(captures,None)
        require(capture is not None, 'missing_quality_capture')
        same(capture['messages'], messages, 'quality_capture_prompt_drift')
        require(all(capture[key] == value for key,value in metadata.items()), 'quality_capture_metadata_drift')
        return dict(response=capture['response'],error=capture['error'])

    verified = _collect_unit(exposures,plan,document['unit'],invoke)
    require(next(captures,None) is None, 'extra_quality_capture')
    same(verified,document,'quality_unit_replay_drift')
    return verified


def assemble(exposures, teachings, units):
    plan, reused = source_plan(exposures), reused_quality(exposures,teachings)
    require([unit['unit'] for unit in units] == list(UNITS), 'all_four_ordered_quality_units_required')
    units = [replay_unit(exposures,unit) for unit in units]
    worlds = reused['worlds'] + [world['quality'] for unit in units for world in unit['documents']]
    rows = _ordered_rows(worlds)
    require(len(worlds) == 61 and len(rows) <= MAX_ROWS and len(rows) % 12 == 0, 'bounded_paired_quality_dataset_required')
    return hop._seal(dict(schema=SCHEMA, source_plan=plan, original_exposures=deepcopy(exposures),
        original_teachings=[dict(shard=shard,document=deepcopy(teachings[shard])) for shard in REUSED_SHARDS],
        reused=reused, units=units, rows=rows, row_count=len(rows), admitted_pairs=len(rows)//12,
        rejected_eligible_pairs=122-len(rows)//12, original_train_pairs=128, eligible_train_pairs=122,
        reused_calls=768, new_calls=sum(unit['model_calls'] for unit in units), max_new_calls=MAX_NEW_CALLS,
        fits=0, trainingAllowed=False, claim=CLAIM), 'capsule_sha256')
