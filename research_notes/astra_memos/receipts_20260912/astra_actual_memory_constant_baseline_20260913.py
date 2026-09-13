import collections
import datetime
import hashlib
import json
from pathlib import Path
import tarfile
from types import ModuleType


REPO = Path('/data/home/rohing/dream-state')
ARCHIVE = REPO / 'gpu_artifacts_local/actual_record_memory_20260913_attempt1/evidence.tar'
ARCHIVE_SHA256 = '3ed6579e7e885139d78faf3457eb3bec254215d36b533558ef22f8199ff6a003'
FROZEN = REPO / 'gpu_artifacts_local/real_record_20260913/astra_actual_record_frozen_sources_20260913.tar'
MEMORY_SHA256 = '2c5538f5b63cbb4e592f40822561b4d62595ab3c9d7d193f084b91f9a064e8ef'
CORE_SHA256 = 'b023a4321d0a20e465c96914316a730fbb2dd897c11369a9eb62d2d8f1248ef5'
CORE_PATH = Path('/tmp/astra_level1_real_record_core_20260913_v2.py')
OUTPUT = Path('/tmp/astra_actual_memory_constant_baseline_20260913')
FIELDS = ('try', 'observed', 'predicted', 'relation')


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def require(condition, text):
    if not condition:
        raise AssertionError(text)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def source_fields(execution):
    return dict(try_value=execution['values'], observed=execution['observed'],
                predicted=execution['predicted'], relation='unavailable' if execution['predicted'] is None
                else 'matched' if execution['predicted'] == execution['observed'] else 'mismatched')


def record_fields(execution):
    result = source_fields(execution)
    result['try'] = result.pop('try_value')
    return result


def content_key(parsed):
    if not isinstance(parsed, dict) or any(field not in parsed for field in FIELDS):
        return None
    return canonical({field: parsed[field] for field in FIELDS})


def counter_rows(counter):
    return [dict(value=value, count=count) for value, count in sorted(counter.items(), key=lambda pair: (-pair[1], pair[0]))]


def counts(scores):
    return dict(full_source_correct=sum(score['score']['content_correct'] for score in scores),
                production_eligible=sum(score['score']['production_eligible'] for score in scores),
                strict_canonical=sum(score['score']['strict_canonical'] for score in scores),
                exact_target_bytes=sum(score['exact_target_bytes'] for score in scores),
                fields={field: sum(score['score']['field_correct'][field] for score in scores) for field in FIELDS})


def main():
    require(not OUTPUT.with_suffix('.json').exists() and not OUTPUT.with_suffix('.md').exists(), 'output already exists')
    with ARCHIVE.open('rb') as stream:
        require(hashlib.file_digest(stream, 'sha256').hexdigest() == ARCHIVE_SHA256, 'memory archive changed')
    with tarfile.open(FROZEN, 'r:') as frozen:
        core_payload = frozen.extractfile('astra_level1_real_record_core_20260913_v2.py').read()
        require(sha(core_payload) == CORE_SHA256 == sha(CORE_PATH.read_bytes()), 'frozen/local core pin')
    core = ModuleType('constant_alternative_frozen_core')
    exec(compile(core_payload, str(CORE_PATH), 'exec'), core.__dict__)
    dependencies = core.load_dependencies(str(REPO))
    with tarfile.open(ARCHIVE, 'r:') as archive:
        payload = archive.extractfile('astra_real_record_memory_core_20260913.py').read()
        require(sha(payload) == MEMORY_SHA256, 'memory scorer pin')
        memory = ModuleType('constant_alternative_frozen_memory')
        exec(compile(payload, 'archived/astra_real_record_memory_core_20260913.py', 'exec'), memory.__dict__)
        result = dict(schema='astra_actual_memory_constant_alternative_20260913_v1',
                      created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                      scope='SEQ153 evaluator-only constant-record alternative; no executed baseline or causal proof',
                      archive=dict(path=str(ARCHIVE), sha256=ARCHIVE_SHA256),
                      script_sha256=sha(Path(__file__).read_bytes()),
                      source_hashes=dict(memory=MEMORY_SHA256, formation_core=CORE_SHA256,
                                         dependencies=dependencies.manifest['full_source_sha256']),
                      design=dict(candidate_set='each distinct exact raw_target among all admitted training rows, per seed',
                                  constant_policy='one unchanged candidate response for every admitted row in a seed/view',
                                  oracle_selection='maximize frozen full source/content correctness on these same evaluated rows',
                                  assumed_finish_reason='stop for evaluator alternatives; observed finish reason for actual WRITE',
                                  primary='content_correct from frozen original-execution scorer',
                                  no_target_normalization=True, all_admitted_rows_retained=True,
                                  variants=['exact', 'paraphrase'], excluded_records='remain excluded by original admission, not newly filtered',
                                  not_executed=True, no_model_or_tokenizer_or_native_or_collector=True), seeds=[])
        for seed in range(3):
            root = f'real_record_memory_seed{seed}_20260913_attempt1'
            def read(name):
                return json.loads(archive.extractfile(root + '/' + name).read())
            dataset = read('dataset.json')
            capture = read('capture.json')
            plan = read('plan.json')
            calls = read('calls.json')
            archived_scores = json.load(archive.extractfile(root + '_collected/scores.json'))
            require(memory.project_capture(capture, core_path=str(CORE_PATH), source_root=str(REPO)) == dataset,
                    'frozen projection differs from original dataset')
            for name in ['dataset.json', 'capture.json', 'calls.json']:
                require(sha(archive.extractfile(root + '/' + name).read()) == plan['input_hashes'][name], 'input pin ' + name)
            executions = {turn['execution']['execution_id']: turn['execution']
                          for episode in capture['episodes'] for turn in episode['turns'] if turn['execution']}
            rows = dataset['rows']
            expected = {row['row_id']: record_fields(executions[row['row_id']]) for row in rows}
            repertoire = {canonical(fields) for fields in expected.values()}
            targets = {}
            for row in rows:
                require(sha(row['raw_target'].encode()) == row['target_sha256'], 'raw target hash')
                targets.setdefault(row['target_sha256'], dict(target_sha256=row['target_sha256'], raw_target=row['raw_target'],
                                   originating_row_ids=[], semantic_content=content_key(json.loads(row['raw_target']))))['originating_row_ids'].append(row['row_id'])
            for index, candidate in enumerate(targets.values()):
                candidate['candidate_id'] = f'T{index+1}'
            seed_result = dict(seed=seed, denominator=len(rows), original_counts=dataset['counts'],
                               expected_source_distribution=counter_rows(collections.Counter(canonical(value) for value in expected.values())),
                               expected_triple_distribution=counter_rows(collections.Counter(canonical(value['try']) for value in expected.values())),
                               targets=list(targets.values()), input_hashes=plan['input_hashes'],
                               admitted_rows=[dict(row_id=row['row_id'], source=row['source'], target_sha256=row['target_sha256'],
                                                   execution_fields=expected[row['row_id']]) for row in rows],
                               original_refused_slots=dataset['refused'], variants={})
            def score(row, raw, finish, variant):
                messages = row['input_messages'] if variant == 'exact' else row['paraphrase_input_messages']
                return memory.score_readback(capture, row['row_id'], raw, finish, input_messages=messages,
                                              variant=variant, core_path=str(CORE_PATH), source_root=str(REPO))
            for variant in ['exact', 'paraphrase']:
                baselines = []
                for candidate in targets.values():
                    scored = [score(row, candidate['raw_target'], 'stop', variant) for row in rows]
                    baselines.append(dict(candidate_id=candidate['candidate_id'], target_sha256=candidate['target_sha256'],
                                          counts=counts(scored), correct_row_ids=[row['row_id'] for row, entry in zip(rows, scored)
                                                                               if entry['score']['content_correct']],
                                          row_scores=scored))
                best = max(entry['counts']['full_source_correct'] for entry in baselines)
                oracle = [entry for entry in baselines if entry['counts']['full_source_correct'] == best]
                planned = [call for call in calls if call['panel'] == variant]
                require([call['row_id'] for call in planned] == [row['row_id'] for row in rows], 'row/call order')
                actual = []
                raw_distribution = collections.Counter()
                parsed_distribution = collections.Counter()
                triple_distribution = collections.Counter()
                confusion = collections.Counter()
                for row, call, prior in zip(rows, planned, archived_scores['cells']['WRITE'][variant]):
                    response_path = root + '/run/WRITE_readout/' + call['call_id'] + '.response.json'
                    payload = archive.extractfile(response_path).read()
                    response = json.loads(payload)
                    evaluated = score(row, response['text'], response['finish_reason'], variant)
                    require(evaluated == prior['score'] and sha(payload) == prior['response_sha256'], 'actual frozen score or response pin mismatch')
                    parsed = evaluated['score']['parsed']
                    semantic = content_key(parsed)
                    truth = canonical(expected[row['row_id']])
                    in_repertoire = semantic in repertoire
                    correct = evaluated['score']['content_correct']
                    triple = canonical(parsed['try']) if isinstance(parsed, dict) and 'try' in parsed else '<missing-or-unparseable>'
                    raw_distribution[response['text']] += 1
                    parsed_distribution[semantic if semantic is not None else '<missing-fields-or-unparseable>'] += 1
                    triple_distribution[triple] += 1
                    confusion[(truth, semantic)] += 1
                    actual.append(dict(row_id=row['row_id'], source=row['source'], expected=expected[row['row_id']],
                                       raw_response=response['text'], finish_reason=response['finish_reason'],
                                       response_sha256=sha(payload), semantic_content=semantic,
                                       raw_is_any_training_target=response['text'] in {item['raw_target'] for item in targets.values()},
                                       semantic_is_any_training_content=in_repertoire,
                                       wrong_key_in_repertoire=in_repertoire and not correct,
                                       score=evaluated))
                actual_counts = counts([row['score'] for row in actual])
                correct_ids = {row['row_id'] for row in actual if row['score']['score']['content_correct']}
                unique_actual = len(raw_distribution)
                actual_versus_constant = []
                for baseline in oracle:
                    constant_ids = set(baseline['correct_row_ids'])
                    actual_versus_constant.append(dict(candidate_id=baseline['candidate_id'],
                                                       both_correct=sorted(correct_ids & constant_ids),
                                                       actual_only=sorted(correct_ids - constant_ids),
                                                       constant_only=sorted(constant_ids - correct_ids),
                                                       neither=[row['row_id'] for row in rows if row['row_id'] not in correct_ids | constant_ids]))
                paired_changes = []
                by_episode = collections.defaultdict(list)
                for row in actual:
                    by_episode[row['source']['task_id']].append(row)
                for episode, pair in by_episode.items():
                    if len(pair) == 2 and pair[0]['expected'] != pair[1]['expected']:
                        paired_changes.append(dict(task_id=episode, row_ids=[row['row_id'] for row in pair],
                                                   truth_changes=True, output_content_changes=pair[0]['semantic_content'] != pair[1]['semantic_content'],
                                                   both_full_source_correct=all(row['score']['score']['content_correct'] for row in pair)))
                variant_result = dict(constant_candidates=baselines, oracle_best_full_source_correct=best,
                                      oracle_best_candidate_ids=[entry['candidate_id'] for entry in oracle],
                                      actual_counts=actual_counts, actual_minus_oracle=actual_counts['full_source_correct'] - best,
                                      actual_unique_raw_responses=unique_actual, actual_unique_content_records=len(parsed_distribution),
                                      actual_raw_distribution=counter_rows(raw_distribution), actual_content_distribution=counter_rows(parsed_distribution),
                                      actual_triple_distribution=counter_rows(triple_distribution),
                                      actual_training_target_byte_matches=sum(row['raw_is_any_training_target'] for row in actual),
                                      actual_training_repertoire_matches=sum(row['semantic_is_any_training_content'] for row in actual),
                                      actual_wrong_key_in_repertoire=sum(row['wrong_key_in_repertoire'] for row in actual),
                                      actual_confusion=[dict(expected=truth, emitted=emitted, count=count)
                                                        for (truth, emitted), count in confusion.items()],
                                      actual_vs_oracle_row_overlap=actual_versus_constant,
                                      eligible_two_turn_episode_changes=paired_changes, actual_rows=actual)
                seed_result['variants'][variant] = variant_result
                print('SEED',seed,variant,'CONSTANT',best,'WRITE',actual_counts,'UNIQUE_RAW',unique_actual,
                      'UNIQUE_CONTENT',len(parsed_distribution),'WRONG_KEY_IN_REPERTOIRE',variant_result['actual_wrong_key_in_repertoire'],flush=True)
            exact = seed_result['variants']['exact']
            paraphrase = seed_result['variants']['paraphrase']
            seed_result['same_row_exact_paraphrase'] = dict(
                identical_raw=sum(left['raw_response'] == right['raw_response'] for left, right in zip(exact['actual_rows'], paraphrase['actual_rows'])),
                identical_content=sum(left['semantic_content'] == right['semantic_content'] for left, right in zip(exact['actual_rows'], paraphrase['actual_rows'])),
                denominator=len(rows))
            result['seeds'].append(seed_result)
        result['limits'] = [
            'Oracle chooses one admitted raw training target after seeing the same evaluation executions; not trained, generated, or prospectively executed.',
            'Hypothetical constants use finish_reason=stop; this is an evaluator alternative, not a model behavior probability.',
            'All originally admitted rows are retained; no new selection or target rewriting. Original refusals are preserved as metadata but have no native memory readout.',
            'A constant can explain an aggregate count without reproducing varying row-level outputs; equal counts do not prove a constant mechanism.',
            'Exceeding the best constant rules out only a single fixed response on this finite panel, not heuristic cue use, repertoire memorization, or general binding failure.',
            'Outputs from the training repertoire at the wrong execution ID demonstrate repertoire availability without correct key-to-field assignment on those rows.',
            'No ID permutation, counterfactual cue intervention, novel record set, fresh generation, retention reanalysis, or causal mechanism test was performed.',
            'The original frozen memory scorer necessarily audits saved capture/projected rows; no collector, tokenizer, model, or native runner is imported or called.',
            'This evaluator-only alternative is not a scientific claim revision or authorization; Main owns scientific claims.'
        ]
        with OUTPUT.with_suffix('.json').open('x') as stream:
            json.dump(result, stream, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write('\n')
        write_markdown(result)


def write_markdown(result):
    lines = ['# SEQ153 — constant-record alternative to keyed memory binding', '',
             '**Descriptive evaluator-only diagnostic. No executed baseline, new model output, causal proof, or claim revision.**', '',
             '## Main comparison', '',
             'The oracle selects one unchanged admissible raw training target per seed and emits it hypothetically for every admitted execution. All choices are evaluated with the exact frozen memory/core scorer and hypothetical `finish_reason="stop"`. Actual WRITE outputs retain their observed finish reasons. Full source correctness is frozen `content_correct`; production eligibility is reported separately. Exact and paraphrase are never pooled.', '',
             '| Seed | Rows | Raw targets / content records / triples | View | Best constant | WRITE full source | WRITE production | Difference | Unique WRITE raw / content | Wrong-key repertoire outputs |',
             '| --- | ---: | --- | --- | ---: | ---: | ---: | ---: | --- | ---: |']
    for seed in result['seeds']:
        for variant, stats in seed['variants'].items():
            lines.append(f"| {seed['seed']} | {seed['denominator']} | {len(seed['targets'])} / {len(seed['expected_source_distribution'])} / {len(seed['expected_triple_distribution'])} | {variant} | {stats['oracle_best_full_source_correct']} | {stats['actual_counts']['full_source_correct']} | {stats['actual_counts']['production_eligible']} | {stats['actual_minus_oracle']:+d} | {stats['actual_unique_raw_responses']} / {stats['actual_unique_content_records']} | {stats['actual_wrong_key_in_repertoire']} |")
    lines += ['', '## Interpretation', '']
    for seed in result['seeds']:
        exact = seed['variants']['exact']
        difference = exact['actual_minus_oracle']
        conclusion = ('exceeds the best single constant by ' + str(difference) + ' rows; this fixed-output alternative cannot attain the observed exact count' if difference > 0 else
                      'does not exceed the oracle-best constant; its aggregate exact count is attainable without any ID-dependent response')
        lines.append(f"- **Seed {seed['seed']}:** WRITE exact {exact['actual_counts']['full_source_correct']}/{seed['denominator']} versus constant {exact['oracle_best_full_source_correct']}/{seed['denominator']} {conclusion}. Actual exact emits {exact['actual_unique_content_records']} distinct content records; aggregate equivalence is not a claim that its behavior is literally constant.")
    lines += ['', 'A repertoire of remembered record contents is not sufficient evidence of correct key binding. The row-level distributions and confusion tables below distinguish content availability from the assignment to the requested execution. A positive finite-panel difference from a constant does not distinguish episodic ID binding from simpler task/turn-pattern heuristics; neither ID dependence nor a causal mechanism is established without a counterfactual cue test.', '']
    for seed in result['seeds']:
        lines += [f"## Seed {seed['seed']} — targets and output assignments", '',
                  f"All {seed['denominator']} admitted rows retained; original refusals: {seed['original_counts']['refused_slots']}/16. No original target byte was changed. Candidate IDs follow first occurrence in the original row order; all maximizing ties remain in the JSON.", '',
                  '### Raw training-target distribution', '',
                  '| Candidate | Training occurrences | Exact raw target | SHA256 |', '| --- | ---: | --- | --- |']
        for target in seed['targets']:
            raw = canonical(target['raw_target'])
            lines.append(f"| {target['candidate_id']} | {len(target['originating_row_ids'])} | `{raw}` | `{target['target_sha256']}` |")
        lines += ['', 'The displayed target is a JSON string literal: escapes expose original whitespace; the JSON result also preserves each original raw string directly. This display encoding is not supplied to the scorer.', '',
                  '### Constant candidate scores', '', '| Candidate | Full source / rows | Production / rows | Exact target bytes / rows |', '| --- | --- | --- | --- |']
        for candidate in seed['variants']['exact']['constant_candidates']:
            stats = candidate['counts']; denominator = seed['denominator']
            lines.append(f"| {candidate['candidate_id']} | {stats['full_source_correct']}/{denominator} | {stats['production_eligible']}/{denominator} | {stats['exact_target_bytes']}/{denominator} |")
        lines += ['', 'The constant scores are also calculated separately for paraphrase and have the same source-scoring basis. The JSON contains every candidate-by-row score in both views.', '',
                  '### Expected source-content distribution', '']
        for entry in seed['expected_source_distribution']:
            lines.append(f"- {entry['count']} × `{entry['value']}`")
        for variant, stats in seed['variants'].items():
            lines += ['', f'### WRITE {variant}', '',
                      f"Frozen field correctness /{seed['denominator']}: " + ', '.join(f'{field} {count}' for field, count in stats['actual_counts']['fields'].items()) + '.',
                      f"Any raw training-target byte match: {stats['actual_training_target_byte_matches']}/{seed['denominator']}; any semantic training-content match: {stats['actual_training_repertoire_matches']}/{seed['denominator']}; repertoire content at the wrong key: {stats['actual_wrong_key_in_repertoire']}/{seed['denominator']}.", '',
                      '**Output triple distribution:**']
            for entry in stats['actual_triple_distribution']:
                lines.append(f"- {entry['count']} × `{entry['value']}`")
            lines += ['', '**Output content distribution (parsed for description only):**']
            for entry in stats['actual_content_distribution']:
                lines.append(f"- {entry['count']} × `{entry['value']}`")
            lines += ['', '**Every raw response variant:**']
            for entry in stats['actual_raw_distribution']:
                lines.append(f"- {entry['count']} × `{canonical(entry['value'])}`")
            lines += ['', '**Assignment by original row (admission order, no filtering):**', '',
                      '| Task suffix / turn | Expected triple / observed / predicted / relation | Emitted triple / observed / predicted / relation | Full source | Wrong-key repertoire |',
                      '| --- | --- | --- | --- | --- |']
            for row in stats['actual_rows']:
                expected = row['expected']; parsed = row['score']['score']['parsed']
                render = lambda value: ' / '.join(canonical(value.get(field)) for field in FIELDS) if isinstance(value, dict) else '<unparsed>'
                label = row['source']['task_id'].replace('real-record-dev-', '') + '#t' + str(row['source']['tick'])
                lines.append(f"| `{label}` | `{render(expected)}` | `{render(parsed)}` | {row['score']['score']['content_correct']} | {row['wrong_key_in_repertoire']} |")
            for overlap in stats['actual_vs_oracle_row_overlap']:
                lines.append(f"\nAgainst oracle candidate {overlap['candidate_id']}: both correct {len(overlap['both_correct'])}; WRITE-only {len(overlap['actual_only'])}; constant-only {len(overlap['constant_only'])}; neither {len(overlap['neither'])}. Exact row IDs are retained in JSON.")
            paired = stats['eligible_two_turn_episode_changes']
            if paired:
                lines.append(f"\nAmong {len(paired)} episodes with both turns admitted and different source contents, output content changes in {sum(item['output_content_changes'] for item in paired)}; both records are source-correct in {sum(item['both_full_source_correct'] for item in paired)}. Nonrandomized turn patterns are not a causal binding test.")
        pair = seed['same_row_exact_paraphrase']
        lines.append(f"\nSame-row exact/paraphrase outputs: {pair['identical_raw']}/{pair['denominator']} identical raw bytes; {pair['identical_content']}/{pair['denominator']} identical parsed content.")
    lines += ['', '## Evidence and limits', '', f"- Memory archive SHA256: `{ARCHIVE_SHA256}`.",
              f"- Frozen memory scorer SHA256: `{MEMORY_SHA256}`.", f"- Frozen formation core SHA256: `{CORE_SHA256}`.",
              f"- This analysis script SHA256: `{result['script_sha256']}`.",
              f"- Complete JSON SHA256: `{sha(OUTPUT.with_suffix('.json').read_bytes())}`.",
              '- The two dependency hashes, all prepared input pins, target hashes, raw response hashes, per-row execution fields and frozen scorer results are in the JSON.',
              '- Actual WRITE exact/paraphrase frozen scorer results reproduce the stored results exactly. No retention panels, LR0 scores, archive inventory audit, or full training pipeline were rerun.']
    lines += ['- ' + limit for limit in result['limits']]
    lines += ['', 'Outputs are confined to this analysis script and its same-stem `.json` and `.md` files in `/tmp`. No targets were sent to a model, fed back into training, or used to change the repository, protocols, original artifacts or scientific claims.', '']
    with OUTPUT.with_suffix('.md').open('x') as stream:
        stream.write('\n'.join(lines))


if __name__ == '__main__':
    main()
