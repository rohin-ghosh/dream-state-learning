"""Contingent Candidate A data only; no runtime, model, fit or outcome selection."""
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
from types import SimpleNamespace

from organism_v6 import birth_conditional_corpus as birth
from organism_v6 import conditional_behavior_corpus as legacy
from organism_v6 import rulegame, rulegame_parenting_diagnostic as spec
from organism_v6 import rulegame_process_material as process
from organism_v6 import train_adapter_v3 as trainer

SCHEMA = 'birth-protocol-overlay-A-v1-20260913'
ORIGIN = 'SOURCE_AUTHORED_PROTOCOL_OVERLAY_NOT_OWN_WAKE_NOT_CLEAN'
ARMS = ('BRIDGE_AUTH', 'BRIDGE_DERANGED')
GROUP_SIZE, MAX_LEN = 8, 512
PROBE_FILE = Path('/tmp/astra_birth_protocol_probe_material_20260913.py')
PROBE_SHA = '2799efda619f7686db88d7990b203a3c7ad39eb8577228a26402037de16cc66b'
FROZEN = {'birth_conditional_corpus.py': '43bf074938e8c4e3a995e43d747ff24f2c6cf70252359cb35134391ff88da74b',
          'conditional_behavior_corpus.py': 'a0ea3717508f05b751935fa3070792d33fe4a21dd46d8a2a93dadb6c2a8b606a',
          'rulegame.py': '88304996b00837ad1855e8a6661aad39e64f3beb0c0ab4491b63119e797226f3',
          'rulegame_parenting_diagnostic.py': 'e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526',
          'rulegame_process_material.py': 'a060f11165e68baa9baaf50433e157e2b3d348a3577e4fbc8ba540d269c24168'}
require = birth.require
digest = birth.digest


def _file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _probe():
    data = PROBE_FILE.read_bytes()
    require(hashlib.sha256(data).hexdigest() == PROBE_SHA, 'frozen probe changed')
    module = importlib.util.module_from_spec(importlib.util.spec_from_file_location('overlay_frozen_probe', PROBE_FILE))
    exec(compile(data, str(PROBE_FILE), 'exec'), module.__dict__)
    return module


def _sources():
    files = [Path(module.__file__) for module in (birth, legacy, rulegame, spec, process, trainer)] + [PROBE_FILE, Path(__file__)]
    hashes = {path.name: _file_hash(path) for path in files}
    require(all(hashes[name] == pin for name, pin in FROZEN.items()) and hashes[PROBE_FILE.name] == PROBE_SHA, 'frozen source changed')
    return hashes


def training_recipe():
    return birth.training_recipe(learning_rate=1e-4, seed=0, epochs=4)


def _exclusions(probe):
    triples = {tuple(row['public']['values']) for row in probe['cases'] if 'values' in row['public']}
    triples.update(tuple(values) for row in probe['cases'] for values in row['source'].get('revealed_triples', []))
    return triples


def _bridges(probe_module, fixed):
    excluded = _exclusions(fixed)
    available = [values for values in itertools.product(range(10), repeat=3) if values not in excluded]
    used, pairs = set(available[:4]), []

    def case(pair, side, family, public, source):
        identifier = f'overlay-A-pair-{pair}-side-{side}'
        public = dict(public, id=identifier, family=family)
        return dict(id=identifier, family=family, pair=pair, public=public, context=probe_module._context(public),
            auth_example_target=probe_module._target(public), source=source, scaffolded=True,
            derivation=dict(basis='supplied scaffold or exact public execution only', hidden_rule_inference=False,
                informative_choice=False, source_event_id='source-'+identifier, outcome_based_selection=False))

    for pair, values in enumerate(available[:4]):
        pairs.append([case(pair, side, 'try_serialization', dict(values=list(values), supplied_forecast=forecast,
            remaining_tries=3, revealed=False), dict(kind='supplied_forecast_scaffold', rule_index=None,
            functions=['parse_action', 'process.validate_wake'], values=list(values), forecast=forecast))
            for side, forecast in enumerate((True, False))])
    for pair, rules, prediction in ((4, (6, 7), True), (5, (8, 9), None)):
        values = next(values for values in available if values not in used and
            rulegame.RULES[rules[0]][1](*values) != rulegame.RULES[rules[1]][1](*values))
        used.add(values)
        rows = []
        for side, rule in enumerate(rules):
            eid = f'rule{rule}/birth-protocol-next-A-v1/record-{pair}-{side}'
            action = 'TRY '+','.join(map(str, values))
            wake = ('PREDICT: T\n' if prediction is not None else '')+'ACT: '+action
            reward, outcome = rulegame.RuleGame().evaluate(SimpleNamespace(eid=eid), action)
            rows.append(case(pair, side, 'record', dict(values=list(values), previous_wake=wake, outcome=outcome,
                remaining_tries=2, revealed=False), dict(kind='generator_authored_public_observation', eid=eid,
                rule_index=rule, action=action, previous_wake=wake, reward=reward, outcome=outcome,
                functions=['RuleGame.evaluate', 'parse_action', 'record_prompt', 'judge_record'])))
        pairs.append(rows)
    rows = []
    for side, rule, labels in ((0, 6, 'TTFFTF'), (1, 7, 'FFTTFT')):
        eid = f'rule{rule}/birth-protocol-next-A-v1/quiz-{side}'
        game = rulegame.RuleGame()
        reward, outcome = game.evaluate(SimpleNamespace(eid=eid), 'QUIZ ?')
        triples = [list(values) for values in game.quiz_triples(eid)]
        require(not excluded.intersection(map(tuple, triples)), 'fixed quiz source overlaps probe; no resampling')
        rows.append(case(6, side, 'quiz_format', dict(revealed=True, remaining_tries=0, reveal_outcome=outcome,
            supplied_labels=list(labels)), dict(kind='generator_reveal_supplied_labels', eid=eid, rule_index=rule,
            action='QUIZ ?', reward=reward, outcome=outcome, revealed_triples=triples, labels_are_scaffolded=True,
            functions=['RuleGame.evaluate', 'RuleGame.quiz_triples', 'parse_action'])))
    pairs.append(rows)
    pairs.append([case(7, side, 'quiz_format', dict(revealed=False, remaining_tries=0),
        dict(kind='reveal_state_scaffold', rule_index=None, functions=['parse_action', 'play_task'])) for side in (0, 1)])
    return pairs


def build_candidate():
    sources = _sources()
    probe_module = _probe()
    fixed, original = probe_module.build_candidate(), birth.build_candidate(root=0)
    probe_module.check_candidate(fixed)
    birth.audit_candidate(original)
    rows = deepcopy(original['train']['AUTH'])
    pairs = _bridges(probe_module, fixed)
    replacements, swap = [], list(range(256))
    for pair, cases in enumerate(pairs):
        group = 4*pair
        indices = [8*group+order+(pair % 2) for order in (4, 6)]
        if pair != 7:
            swap[indices[0]], swap[indices[1]] = indices[1], indices[0]
        for index, case in zip(indices, cases, strict=True):
            old = rows[index]
            operation = {'try_serialization': 'PROTOCOL_TRY', 'record': 'PROTOCOL_RECORD',
                         'quiz_format': 'PROTOCOL_QUIZ' if case['public']['revealed'] else 'PROTOCOL_REVEAL'}[case['family']]
            rows[index] = dict(id=case['id'], semantic_id=case['id'], instance_id=case['id'], split='train',
                operation=operation, template='frozen_protocol_practice_v1', context=case['context'],
                response=case['auth_example_target'], group=old['group'], order=old['order'], origin=ORIGIN,
                source_event_ids=[case['derivation']['source_event_id']])
            replacements.append(dict(index=index, pair=pair, removed=old, bridge_case=case))
    required_sources = {identifier for row in rows+original['dev'] for identifier in row['source_event_ids']}
    records = [deepcopy(row) for row in original['source_records'] if row['id'] in required_sources]
    records += [dict(id=case['derivation']['source_event_id'], origin=ORIGIN, split='train',
                     public=case['public'], source=case['source'], derivation=case['derivation']) for cases in pairs for case in cases]
    return dict(schema=SCHEMA, origin=ORIGIN, status='CONTINGENT_CPU_DATA_NOT_SELECTED_FOR_FIT', source_sha256=sources,
        original_candidate_sha256=birth.digest(original), fixed_probe_sha256=probe_module.digest(fixed),
        fixed_probe_call_map_sha256=probe_module.digest(probe_module.call_map(fixed)),
        train={ARMS[0]: rows, ARMS[1]: [dict(deepcopy(row), response=rows[swap[index]]['response']) for index, row in enumerate(rows)]},
        dev=deepcopy(original['dev']), dev_twins=deepcopy(original['twins']['dev']), source_records=records,
        replacements=replacements, swap=swap, recipe=training_recipe(),
        partition=dict(generator_rules=[6, 7, 8, 9], excluded_rules=list(range(6)), excluded_probe_tuples=[list(values) for values in sorted(_exclusions(fixed))],
            shared_probe_tuples=[], global_novelty_claim=False, selected_from_live_outputs=False),
        dose=dict(rows=256, groups=32, epochs=4, updates=128, unchanged_rows=240, replaced_rows=16,
            nontrivial_swaps=14, common_reveals=2, conditional_presentations=512,
            anchor_presentations_per_family=224, prior_anchor_presentations_per_family=256,
            bridge_presentations=64, equal_original_anchor_dose=False, equal_original_token_dose=False),
        limitations=['AUTH conditional background in BOTH new arms; original DERANGED map is not used',
            'Inherited scaffold prompt grammar/priority ambiguity is unchanged; not a remedy for harness ambiguity',
            'No rule induction, child experience, selective retention, fit authorization or efficacy claim'])


def audit_candidate(candidate):
    require(candidate == build_candidate(), 'overlay/source/partition/targets changed from fixed Candidate A')
    original, probe_module = birth.build_candidate(root=0), _probe()
    indices = {entry['index'] for entry in candidate['replacements']}
    auth, deranged = (candidate['train'][arm] for arm in ARMS)
    require(len(auth) == len(deranged) == 256 and len(indices) == 16, 'overlay counts')
    require(all(row == original['train']['AUTH'][index] for index, row in enumerate(auth) if index not in indices), '240-row background changed')
    for index, (left, right) in enumerate(zip(auth, deranged, strict=True)):
        require({key: value for key, value in left.items() if key != 'response'} == {key: value for key, value in right.items() if key != 'response'}, 'arm inputs differ')
        require(right['response'] == auth[candidate['swap'][index]]['response'], 'whole-target map differs')
    for offset in range(0, 256, GROUP_SIZE):
        block = auth[offset:offset+GROUP_SIZE]
        require(len({row['group'] for row in block}) == 1 and [row['order'] for row in block] == list(range(8)), 'optimizer group changed')
        require(Counter(row['response'] for row in block) == Counter(row['response'] for row in deranged[offset:offset+8]), 'batch target multiset differs')
    for entry in candidate['replacements']:
        case, index = entry['bridge_case'], entry['index']
        require(probe_module.validate_output(case, auth[index]['response'])['instruction_compliant'], 'AUTH bridge control failed')
        require(probe_module.validate_output(case, deranged[index]['response'])['public_contract_correct'] == (entry['pair'] == 7), 'nontrivial control/shared reveal differs')
    require(candidate['dev'] == original['dev'] and candidate['dev_twins'] == original['twins']['dev'], 'original dev changed')
    require(all(not {row[key] for row in auth} & {row[key] for row in candidate['dev']} for key in ('id', 'context')), 'train/dev overlap')
    return dict(status='OVERLAY_CPU_SPEC_VERIFIED_NATIVE_PENDING', candidate_sha256=digest(candidate),
        train_counts=dict(Counter(row['operation'] for row in auth)), dev_rows=128, **candidate['dose'])


def train_items(candidate, arm, render_context=None):
    audit_candidate(candidate)
    require(arm in ARMS, 'new overlay arm required, not original AUTH/DERANGED')
    render_context = render_context or (lambda text: text)
    return [dict(spans=[[render_context(row['context']), False, 'context'], [row['response'], True, 'authored_birth_target']],
        group=row['group'], order=row['order'], view=row['operation'], category='authored_birth_target',
        meta=dict(case_id=row['id'], source_event_ids=list(row['source_event_ids']), origin=row['origin'], split='train'))
        for row in candidate['train'][arm]]


def audit_tokenizer(candidate, tokenizer, *, recipe=None):
    audit_candidate(candidate)
    recipe = training_recipe() if recipe is None else recipe
    require(recipe == training_recipe(), 'fixed seed0/LR1e-4/epochs4 birth recipe required')
    eos, pad = tokenizer.eos_token_id, tokenizer.pad_token_id
    require(type(eos) is int and type(pad) is int and eos >= 0 and pad >= 0 and eos != pad, 'distinct EOS/PAD required')
    render = lambda text: tokenizer.apply_chat_template([dict(role='user', content=text)], tokenize=False, add_generation_prompt=True)
    corpora = {arm: train_items(candidate, arm, render) for arm in ARMS}
    segments, records, mismatches = {}, {}, []
    for arm in ARMS:
        segments[arm], records[arm] = [], []
        for index, item in enumerate(trainer.normalize_items(corpora[arm])):
            prefix = tokenizer.encode(item['spans'][0][0], add_special_tokens=False)
            target = tokenizer.encode(item['spans'][1][0], add_special_tokens=False)
            require(prefix and target and eos not in target and pad not in target, 'empty/special target')
            require(all(type(token) is int and token >= 0 for token in prefix+target), 'invalid token IDs')
            ids, labels = prefix+target+[eos], [-100]*len(prefix)+target+[eos]
            require(len(ids) <= MAX_LEN, 'overlay overflow: no drops/splits/truncation permitted')
            encoded = trainer.encode_item_segments(item, tokenizer, MAX_LEN, False, True, index, overflow='truncate')
            require(len(encoded) == 1, 'missing/split row')
            segment = encoded[0]
            require(segment.ids == ids and segment.labels == labels and segment.n_target == len(target)+1
                and segment.context_dropped == segment.target_dropped == 0 and segment.n_splits == 1, 'target mask/EOS/boundary mismatch')
            segments[arm].append(segment)
            records[arm].append(dict(case_id=item['meta']['case_id'], rendered_context=item['spans'][0][0], prefix_ids=prefix,
                input_ids=ids, labels=labels, context_tokens=len(prefix), input_tokens=len(ids), target_tokens=segment.n_target,
                supervised_eos_position=len(ids)-1, operation=item['view'], group=item['group'], order=item['order']))
    for index, swapped in enumerate(candidate['swap']):
        left, right = records[ARMS[0]][swapped], records[ARMS[1]][index]
        require(records[ARMS[0]][index]['prefix_ids'] == right['prefix_ids'], 'paired input prefixes differ')
        require([token for token in left['labels'] if token != -100] == [token for token in right['labels'] if token != -100], 'complete native target/EOS swap differs')
        if len(left['prefix_ids']) != len(right['prefix_ids']):
            mismatches.append(dict(kind='swap_prefix_length', index=index, swapped=swapped))
    schedules, costs = [], {arm: [] for arm in ARMS}
    for epoch in range(recipe['epochs']):
        orders = {arm: trainer.epoch_order(trainer.pack_by_group(segments[arm], MAX_LEN, False), recipe['seed'], epoch, True) for arm in ARMS}
        for offset in range(0, 256, GROUP_SIZE):
            summaries, indices = {}, {}
            for arm in ARMS:
                packs = orders[arm][offset:offset+GROUP_SIZE]
                require(len(packs) == 8 and all(len(pack) == 1 for pack in packs) and len({pack[0].group for pack in packs}) == 1
                    and [pack[0].order for pack in packs] == list(range(8)), 'actual shuffled group/order mismatch')
                batch = trainer.collate(packs, pad)
                width = max(len(pack[0].ids) for pack in packs)
                for position, (segment,) in enumerate(packs):
                    padding = width-len(segment.ids)
                    require(batch['input_ids'][position] == segment.ids+[pad]*padding
                        and batch['labels'][position] == segment.labels+[-100]*padding
                        and batch['position_ids'][position] == list(range(len(segment.ids)))+[0]*padding
                        and batch['segment_ids'][position] == [0]*len(segment.ids)+[-1]*padding, 'actual collator mask/padding/position mismatch')
                indices[arm] = [pack[0].item_index for pack in packs]
                actual = [pack[0] for pack in packs]
                inputs, targets = sum(len(row.ids) for row in actual), sum(row.n_target for row in actual)
                require(batch['n_tokens'] == inputs and batch['n_target'] == targets, 'actual collator exposure mismatch')
                summaries[arm] = dict(joint=sorted((len(row.ids)-row.n_target, row.n_target, len(row.ids), len(row.ids)-1) for row in actual),
                    targets=Counter(tuple(token for token in row.labels if token != -100) for row in actual),
                    input_tokens=Counter(token for row in actual for token in row.ids), padded=8*width)
                costs[arm].append(dict(epoch=epoch, update_index=len(costs[arm]), group=actual[0].group, row_indices=indices[arm],
                    context_tokens=inputs-targets, input_tokens=inputs, target_tokens=targets, eos_tokens=8,
                    padded_input_tokens=8*width, padding_tokens=8*width-inputs))
            require(indices[ARMS[0]] == indices[ARMS[1]], 'arm optimizer schedules differ')
            if summaries[ARMS[0]] != summaries[ARMS[1]]:
                mismatches.append(dict(kind='batch_exposure', epoch=epoch, batch=offset//8))
            schedules.append(indices[ARMS[0]])
    totals = {arm: {key: sum(row[key] for row in costs[arm]) for key in
        ('context_tokens', 'input_tokens', 'target_tokens', 'eos_tokens', 'padded_input_tokens', 'padding_tokens')} for arm in ARMS}
    return dict(schema=SCHEMA+'-token-audit', status='OVERLAY_CALLBACK_AUDITED_NOT_NATIVE', candidate_sha256=digest(candidate),
        source_sha256=_sources(), recipe=recipe, corpora=corpora, rows=records, group_costs=costs, totals=totals,
        optimizer_update_rows=schedules, updates=128, rows_per_arm=256, group_size=8,
        paired_exposure_equal=not mismatches, exposure_mismatches=mismatches, no_truncation=True,
        loss_bearing_padding=False, native=False, ready_for_native_export=False, no_fit_authorization=True)


def audit_native(candidate, model_path, expected_file_hashes, *, recipe=None):
    """Callable offline tokenizer audit only; no model weights, fitting or runtime."""
    audit_candidate(candidate)
    directory = Path(model_path).expanduser().resolve(strict=True)
    required = {'config.json', 'tokenizer.json', 'tokenizer_config.json'}
    required |= {name for name in ('vocab.json', 'merges.txt', 'special_tokens_map.json', 'added_tokens.json',
        'chat_template.jinja', 'chat_template.json') if (directory/name).exists()}
    require(not (directory/'chat_templates').exists(), 'external chat_templates unbound')
    require(isinstance(expected_file_hashes, dict) and required <= set(expected_file_hashes), 'missing local tokenizer pins')
    for name, pin in expected_file_hashes.items():
        require(Path(name).name == name and _file_hash(directory/name) == pin, 'local tokenizer pin mismatch')
    require(json.loads((directory/'config.json').read_bytes())['model_type'] == 'qwen2', 'Qwen2 base required')
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(directory), local_files_only=True, trust_remote_code=False)
    report = audit_tokenizer(candidate, tokenizer, recipe=recipe)
    require(all(_file_hash(directory/name) == pin for name, pin in expected_file_hashes.items()), 'tokenizer changed during audit')
    require(report['source_sha256'] == _sources(), 'source changed during audit')
    matched = report['paired_exposure_equal']
    report.update(status='NATIVE_OVERLAY_TOKEN_MATCH_VERIFIED' if matched else 'NATIVE_OVERLAY_EXPOSURE_MISMATCH_NOT_READY',
        native=True, ready_for_native_export=matched, tokenizer_path=str(directory), tokenizer_file_hashes=deepcopy(expected_file_hashes),
        eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.pad_token_id)
    return report


def export_native(candidate, report, arm):
    """In-memory v3 JSON export from this overlay's matching native audit, not a fit."""
    audit_candidate(candidate)
    require(arm in ARMS, 'new overlay arm required')
    require(report['schema'] == SCHEMA+'-token-audit' and report['candidate_sha256'] == digest(candidate)
        and report['source_sha256'] == _sources() and report['recipe'] == training_recipe()
        and report['native'] is True and report['status'] == 'NATIVE_OVERLAY_TOKEN_MATCH_VERIFIED'
        and report['ready_for_native_export'] is True and report['paired_exposure_equal'] is True
        and not report['exposure_mismatches'], 'matching native overlay audit required; callbacks/old schemas/mismatches cannot export')
    items = report['corpora'][arm]
    expected = train_items(candidate, arm)
    require(len(items) == len(report['rows'][arm]) == len(expected) == 256, 'partial native export')
    for item, original, row in zip(items, expected, report['rows'][arm], strict=True):
        original['spans'][0][0] = row['rendered_context']
        require(item == original and row['case_id'] == item['meta']['case_id'], 'native corpus/row/target join mismatch')
    return {'corpus': deepcopy(items)}
