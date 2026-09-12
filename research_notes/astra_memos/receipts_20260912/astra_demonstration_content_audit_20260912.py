"""Local-only content audit; writes only the assigned Markdown and JSON reports."""
import base64
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import re
import sys
import tarfile

sys.dont_write_bytecode = True
REPO = Path('/data/home/rohing/dream-state')
ROOT = Path('/tmp/astra_demonstration_terminal_20260912')
PREP = ROOT / 'astra_demonstration_preparation_20260912_attempt1'
RUN = ROOT / 'astra_demonstration_20260912_attempt1'
CAPSULE = Path('/tmp/astra_demonstration_terminal_20260912.tgz')
DEST = Path('/tmp/astra_demonstration_content_audit_20260912')
EXPECTED_CAPSULE = 'b2d03d6b41c7211ac0c87ff177e590badb137cb2a9624abca4bc5749ac1d1417'
FAILURES = []
CHECKS = []


def sha(content):
    return hashlib.sha256(content).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode()


def read(path):
    return json.loads(path.read_text())


def verify(condition, description):
    CHECKS.append({'check': description, 'pass': bool(condition)})
    if not condition:
        FAILURES.append(description)


def inventory(root):
    path = root / 'artifact_hashes.json'
    files = read(path)['files']
    for name, expected in files.items():
        target = root / name
        verify(target.is_file() and sha(target.read_bytes()) == expected, f'inventory {root.name}/{name}')
    return sha(path.read_bytes())


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def witness(board, check):
    cells = check['cells']
    shape = (isinstance(cells, list) and len(cells) == 2 and
             all(isinstance(cell, list) and len(cell) == 2 and
                 all(type(value) is int and 1 <= value <= 4 for value in cell) for cell in cells))
    if not shape:
        literal_cells = (isinstance(cells, list) and all(isinstance(cell, list) and len(cell) == 2 and
                         all(type(value) is int and 1 <= value <= 4 for value in cell) for cell in cells))
        values = [board[row-1][column-1] for row, column in cells] if literal_cells else None
        return dict(valid=False, reasons=['coordinate_shape'], actual_values=values)
    first, second = cells
    distinct = first != second
    same = {'row': first[0] == second[0], 'column': first[1] == second[1],
            'box': ((first[0] - 1) // 2, (first[1] - 1) // 2) ==
                   ((second[0] - 1) // 2, (second[1] - 1) // 2)}.get(check['group'], False)
    values = [board[row - 1][column - 1] for row, column in cells]
    reasons = ([] if distinct else ['same_cell']) + ([] if same else ['not_same_named_unit'])
    if values != [check['digit'], check['digit']]:
        reasons.append('claimed_digit_not_at_both_cells')
    return dict(valid=not reasons, reasons=reasons, actual_values=values, same_named_unit=same, distinct=distinct)


def check_key(check):
    return check['group'], check['digit'], tuple(sorted(tuple(cell) for cell in check['cells']))


def independent_score(text, case):
    result = dict(format_valid=False, grounded=0, valid_citations=0, invalid_citations=0,
                  whole_structured_record_clean=False, details=[], schema_reason=None)
    try:
        record = json.loads(text, object_pairs_hook=unique_object)
        if not isinstance(record, dict) or set(record) != {'case_id', 'checks', 'lesson'}:
            raise ValueError('record keys')
        if not isinstance(record['case_id'], str) or not isinstance(record['lesson'], str) or not record['lesson'].strip():
            raise ValueError('case_id/lesson')
        if not isinstance(record['checks'], list) or not 1 <= len(record['checks']) <= 3:
            raise ValueError('checks count')
        for check in record['checks']:
            if not isinstance(check, dict) or set(check) != {'group', 'cells', 'digit'}:
                raise ValueError('check keys')
            if check['group'] not in ('row', 'column', 'box') or type(check['digit']) is not int or not 1 <= check['digit'] <= 4:
                raise ValueError('group/digit')
            detail = witness(case['candidate'], check)
            result['details'].append(dict(citation=check, **detail))
            if detail['reasons'] == ['coordinate_shape']:
                raise ValueError('coordinate_shape: expected exactly two two-integer cells')
    except (ValueError, TypeError, KeyError) as error:
        result['schema_reason'] = str(error)
        return result
    result['format_valid'] = True
    if record['case_id'] != case['case_id']:
        result['schema_reason'] = 'wrong_case_id'
        return result
    seen = set()
    for detail in result['details']:
        if not detail['valid']:
            result['invalid_citations'] += 1
        elif check_key(detail['citation']) not in seen:
            seen.add(check_key(detail['citation']))
    result['valid_citations'] = len(seen)
    result['grounded'] = int(bool(seen))
    result['whole_structured_record_clean'] = len(seen) == len(record['checks'])
    return result


def all_witnesses(board):
    output = []
    for first, second in itertools.combinations(itertools.product(range(1, 5), repeat=2), 2):
        for group in ('row', 'column', 'box'):
            check = dict(group=group, cells=[list(first), list(second)], digit=board[first[0]-1][first[1]-1])
            if witness(board, check)['valid']:
                output.append(check)
    return output


def audit():
    verify(sha(CAPSULE.read_bytes()) == EXPECTED_CAPSULE, 'capsule SHA256 matches supplied anchor')
    archived = 0
    with tarfile.open(CAPSULE, 'r:gz') as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            relative = Path(member.name)
            verify(not relative.is_absolute() and '..' not in relative.parts, f'archive safe member {member.name}')
            target = ROOT / relative
            stream = archive.extractfile(member)
            verify(target.is_file() and sha(target.read_bytes()) == sha(stream.read()), f'archive bytes {member.name}')
            archived += 1
    prep_digest = inventory(PREP)
    config, pairs, preflight = read(PREP/'config.json'), read(PREP/'pairs.json'), read(PREP/'preflight.json')
    completion = read(RUN/'COMPLETED.json')
    verify(len(pairs) == 8 and not config['synthetic'], 'eight native pairs')
    verify(config['protocol']['generation_seed'] == 7101, 'sampler 7101 not optimizer seed')
    verify(config['boundary']['adapter'] is None and not config['boundary']['fit'], 'no adapter / no fit')
    board_evidence = []
    for index, pair in enumerate(pairs):
        for stage, start in [('source', 1851200), ('transfer', 1851300)]:
            case = pair[stage]
            verify(case['episode_id'] == f'rg/mini_sudoku/{start+index}' and case['split'] == 'train', f'{stage} fixed ID {index}')
            parsed = [[0 if item == '_' else int(item) for item in line.split()]
                      for line in case['question'].splitlines() if re.fullmatch(r'[1-4_](?: [1-4_]){3}', line)]
            verify(parsed == case['source_board'] and len(parsed) == 4, f'{case["case_id"]} question/board')
            verify(sha(case['question'].encode()) == case['question_sha256'], f'{case["case_id"]} question hash')
            verify(sha(encoded(parsed)) == case['source_board_sha256'], f'{case["case_id"]} source board hash')
            offset = index + (8 if stage == 'transfer' else 0)
            reconstructed = [[value or 1+(row*2+row//2+column+offset)%4 for column, value in enumerate(values)]
                             for row, values in enumerate(parsed)]
            verify(reconstructed == case['filled_candidate'], f'{case["case_id"]} public deterministic fill')
            for edit in case['program']['edits']:
                row, column = edit['cell']
                verify(reconstructed[row-1][column-1] == edit['before'], f'{case["case_id"]} edit preimage')
                reconstructed[row-1][column-1] = edit['after']
            verify(reconstructed == case['candidate'] and sha(encoded(reconstructed)) == case['candidate_sha256'], f'{case["case_id"]} candidate edits/hash')
            witnesses = all_witnesses(reconstructed)
            verify(bool(witnesses), f'{case["case_id"]} at least one public duplicate')
            board_evidence.append(dict(pair_id=pair['pair_id'], phase=stage, **case, public_witnesses=witnesses))
        example = json.loads(pair['example_text'])['checks'][0]
        verify(sha(pair['example_text'].encode()) == pair['example_sha256'], f'{pair["pair_id"]} example hash')
        verify(witness(pair['source']['candidate'], example)['valid'], f'{pair["pair_id"]} source example factual')
        verify(not witness(pair['transfer']['candidate'], example)['valid'], f'{pair["pair_id"]} copied source witness invalid on transfer')
        verify(witness(pair['transfer']['candidate'], pair['transfer_witness'])['valid'], f'{pair["pair_id"]} target witness factual')
    for key in ['question_sha256', 'candidate_sha256']:
        current = {row[key] for row in board_evidence}
        prior = {row[key] for row in config['prior_content']['records']}
        verify(len(current) == 16 and not current & prior, f'16 unique {key}, no prior metadata overlap')
    prior_actual = []
    for path in [Path('/tmp/astra_constraint_verified_terminal_20260912/astra_constraint_check_preparation_20260912_attempt1'),
                 Path('/tmp/astra_constraint_v2_terminal_20260912/astra_constraint_v2_preparation_20260912_seed7101_attempt1')]:
        digest = inventory(path)
        verify(digest in {row['inventory_sha256'] for row in config['prior_content']['receipts']}, f'prior relocated inventory {path.name}')
        for case in read(path/'cases.json'):
            entry = dict(episode_id=case['episode_id'], question_sha256=sha(case['question'].encode()),
                         candidate_sha256=sha(encoded(case['candidate'])))
            verify(entry in config['prior_content']['records'], f'prior actual content {entry["episode_id"]}')
            prior_actual.append(entry)
    local_source_pins = {}
    for remote, expected in config['sources'].items():
        if '/organism_v6/' in remote:
            local = REPO / 'organism_v6' / remote.split('/organism_v6/')[1]
            actual = sha(local.read_bytes()) if local.is_file() else None
            local_source_pins[str(local)] = dict(expected=expected, actual=actual, match=actual == expected)
    sys.path.insert(0, str(REPO))
    from organism_v6 import constraint_demonstration_diagnostic as demo
    replay = demo.analyze_pair(RUN, PREP)
    verify(all(completion.get(key) == value for key, value in replay.items()), 'existing CPU replay equals terminal fields')
    records, counts, tokens, pids = [], {}, {}, []
    echo_counts = {}
    fields = ['format_valid', 'grounded', 'valid_citations', 'invalid_citations', 'whole_structured_record_clean']
    for arm in ('process', 'format'):
        inventory(RUN/arm)
        result = read(RUN/arm/'results.json')
        runtime = read(RUN/arm/'runtime.json')
        pids.append(runtime['pid'])
        verify(runtime['generation_seed'] == 7101, f'{arm} runtime seed')
        lines = (RUN/arm/'generations.jsonl').read_bytes().splitlines(keepends=True)
        events = [json.loads(line) for line in lines]
        verify([event['kind'] for event in events] == ['request', 'raw_return', 'output']*16, f'{arm} exact 16 calls')
        counts[arm], tokens[arm] = {}, dict(prompt=0, output=0)
        echo_counts[arm] = Counter()
        for position in range(16):
            request, raw, output = events[3*position:3*position+3]
            native = raw['requests'][0]['outputs'][0]
            pair = pairs[position//2]
            phase = 'transfer' if position % 2 else 'source'
            case = pair[phase]
            text = native['text']
            verify(text == output['text'] == result['records'][position]['capture']['text'], f'{arm}/{case["case_id"]} three text copies')
            verify(sha(text.encode()) == output['output_sha256'], f'{arm}/{case["case_id"]} output hash')
            verify(native['finish_reason'] == output['finish_reason'] == 'stop' and
                   len(native['token_ids']) == output['actual_output_tokens'] <= 128, f'{arm}/{case["case_id"]} native stop/tokens')
            verify(request['seed'] == output['generation_seed'] == 7101 and request['max_tokens'] == 128
                   and request['temperature'] == .7, f'{arm}/{case["case_id"]} sampling settings')
            score = independent_score(text, case)
            verify(all(score[key] == result['records'][position]['score'][key] for key in fields), f'{arm}/{case["case_id"]} independent strict score')
            group = counts[arm].setdefault(phase, Counter())
            group.update({key: int(score[key]) for key in fields})
            group['denominator'] += 1
            tokens[arm]['prompt'] += len(raw['requests'][0]['prompt_token_ids'])
            tokens[arm]['output'] += len(native['token_ids'])
            parsed = json.loads(text)
            source_note = None
            if phase == 'source':
                verify(request['example_sha256'] == pair['example_sha256'] and
                       pair['example_text'] in request['prompt'], f'{arm}/{case["case_id"]} common exact example')
                same = any(check_key(detail['citation']) == check_key(json.loads(pair['example_text'])['checks'][0])
                           for detail in score['details'] if detail['valid'])
                nonexample = sum(detail['valid'] and check_key(detail['citation']) != check_key(json.loads(pair['example_text'])['checks'][0])
                                 for detail in score['details']) if score['format_valid'] else 0
                echo_counts[arm].update(dict(exact_example_echo=int(text == pair['example_text']),
                    example_verbatim_substring=int(pair['example_text'] in text), same_example_check=int(same),
                    valid_non_example_citations=nonexample))
            else:
                source_output = events[3*(position-1)+2]
                note = request['note']
                actual = request['prompt'].encode()[note['start_byte']:note['end_byte']]
                verify(actual == source_output['text'].encode() and sha(actual) == note['output_sha256'], f'{arm}/{case["case_id"]} byte-exact source note')
                outside = request['prompt'].encode()[:note['start_byte']] + request['prompt'].encode()[note['end_byte']:]
                verify(request['parent_presentations'] == 0 and request['example_sha256'] is None and
                       b'Parent explanation:' not in outside and b'Shared correct source example:' not in outside,
                       f'{arm}/{case["case_id"]} no direct parent/example outside note')
                source_note = dict(text=source_output['text'], sha256=sha(actual), byte_receipt=note,
                                   source_grounded=result['records'][position-1]['score']['grounded'])
            row = dict(arm=arm, phase=phase, case_id=case['case_id'], episode_id=case['episode_id'], pair_id=pair['pair_id'],
                       request_index=position, raw_file=str(RUN/arm/'generations.jsonl'), raw_return_line=3*position+2,
                       raw_line_sha256=sha(lines[3*position+1]), raw_text_pointer='/requests/0/outputs/0/text',
                       text=text, output_sha256=sha(text.encode()), utf8_bytes=len(text.encode()),
                       utf8_base64=base64.b64encode(text.encode()).decode(),
                       prompt_sha256=request['prompt_sha256'], candidate_sha256=case['candidate_sha256'],
                       candidate=case['candidate'], score=score, own_lesson=parsed['lesson'],
                       lesson_machine_verified=False, training_approved=False, source_note=source_note,
                       native_output_tokens=len(native['token_ids']))
            records.append(row)
        for phase in ('source', 'transfer'):
            verify(counts[arm][phase]['grounded'] == result['counts'][phase]['grounded'] and
                   counts[arm][phase]['format_valid'] == result['counts'][phase]['format_count'], f'{arm}/{phase} aggregate counts')
        verify(dict(echo_counts[arm]) == result['counts']['source_echo'], f'{arm} independent example echo counts')
    verify(len(set(pids)) == 2, 'distinct fresh worker PIDs')
    cleanup = {arm: read(RUN/f'{arm}.cleanup.json') for arm in ('process', 'format')}
    for arm, receipt in cleanup.items():
        verify(receipt['cleanup_error'] is None and receipt['gpu_processes_absent'] and
               receipt['owned_group_empty'] and receipt['reservation_release_verified'], f'{arm} captured cleanup receipt')
    return dict(schema='demonstration-independent-content-audit-v1', status='PASS' if not FAILURES else 'FAIL',
                verification_failures=FAILURES, checks=CHECKS, capsule_sha256=sha(CAPSULE.read_bytes()),
                archive_files_compared=archived, root=str(ROOT), preparation_inventory_sha256=prep_digest,
                protocol=config['protocol'], model_path=config['model_path'], model_file_pins=config['expected_files'],
                native_source_pins=config['sources'], local_source_comparisons=local_source_pins,
                prior_actual_content=prior_actual, counts=counts, echo_counts=echo_counts, tokens=tokens,
                worker_pids=pids, cleanup_receipts=cleanup, main_terminal_observation=read(RUN/'MAIN_TERMINAL_AUDIT.json'),
                elapsed_seconds=completion['elapsed_seconds'], boards=board_evidence, records=records,
                valid_child_records=[row for row in records if row['score']['grounded']],
                explanation_tokens={arm:[row['tokens'] for row in preflight['explanations'][arm]] for arm in ('process','format')},
                boundary=dict(no_normalization=True, training_approved=False, fits=0, new_generations=0,
                              lesson_machine_verified=False, P1_claim=False, internalization_claim=False),
                caveats=['Absolute remote model/package paths not rehashed; captured pins are local-hash provenance, not clean origin.',
                         'Cleanup checked as archived observation, not a fresh process/GPU poll.',
                         'Native token IDs establish counts; tokenizer decode not rerun locally.',
                         'Eight fixed exercise pairs, one generation seed; stages/arms are not independent learner samples.'])


def markdown(report):
    lines = ['# Demonstration content audit — 2026-09-12', '',
             f"**Local verification: {report['status']}; failures: {report['verification_failures']}.** No generation, fit, GPU/network/git action or repo edit.",
             f"Capsule SHA256: `{report['capsule_sha256']}`. Compared {report['archive_files_compared']} extracted files to archived bytes; verified prep/arm inventories, 32 raw returns and original CPU replay.",
             '', '## Recount (strict results unchanged)', '',
             '| Arm / stage | Grounded /8 | Schema /8 | Invalid citations | Whole structured clean /8 |',
             '|---|---:|---:|---:|---:|']
    for arm in ('process','format'):
        for phase in ('source','transfer'):
            row = report['counts'][arm][phase]
            lines.append(f"| {arm} / {phase} | {row['grounded']} | {row['format_valid']} | {row['invalid_citations']} | {row['whole_structured_record_clean']} |")
    lines += ['', 'The two process p01 outputs each name **three cells**, not two: schema failures score 0; no pair extraction/salvage. All other failures are factual citation failures, not numeric strings or JSON syntax. Invalid-citation totals exclude schema-rejected records by the original rule. Schema-valid does not mean board-grounded.',
              '', '## Every raw citation against the actual candidate', '',
              '| Arm | Case | Citation (group; cells; digit) | Observed values | Verdict |', '|---|---|---|---|---|']
    for row in report['records']:
        detail = row['score']['details'][0]
        citation = detail['citation']
        verdict = 'VALID' if row['score']['grounded'] else row['score']['schema_reason'] or ', '.join(detail['reasons'])
        lines.append(f"| {row['arm']} | {row['case_id']} | {citation['group']}; {citation['cells']}; {citation['digit']} | {detail['actual_values']} | {verdict} |")
    lines += ['', '## Exact valid child bytes and ancestry',
              'These are decoded native `RequestOutput.outputs[0].text` UTF-8 bytes, not JSON-reserialized targets. JSON report also stores base64, byte length, full prompt/output hashes, raw-return line/hash and candidate. **Evidence identification only; none is training-approved.**']
    for row in report['valid_child_records']:
        lines += ['', f"### {row['arm']} {row['case_id']} — {row['episode_id']}",
                  f"Raw `{row['raw_file']}` line {row['raw_return_line']}, pointer `{row['raw_text_pointer']}`; request index {row['request_index']}.",
                  f"Output SHA256 `{row['output_sha256']}`; {row['utf8_bytes']} UTF-8 bytes; {row['native_output_tokens']} native output tokens.",
                  f"Candidate SHA256 `{row['candidate_sha256']}`; board `{row['candidate']}`.", '```json', row['text'], '```']
    transfer = next(row for row in report['valid_child_records'] if row['phase'] == 'transfer')
    lines += ['', '**Crucial ancestry:** process s04 repeats the provided example check (different lesson wording); process s07 cites another valid row pair, not the example. Neither source case has a successful transfer. There are zero byte-identical/verbatim-example echoes in either arm. Different valid coordinates do not establish independent discovery.',
              'The sole valid transfer is process **t02**, following **invalid s02**. Its box citation `(3,3),(3,4), digit 1` is true on the new board and differs from both the source example and the erroneous source note. It is also different from the program-planted target row witness. This is one correct new-board response conditioned on a bad self-note—not a verified correct-source-to-application chain.',
              f"The exact s02 note SHA256 is `{transfer['source_note']['sha256']}`; byte span {transfer['source_note']['byte_receipt']['start_byte']}:{transfer['source_note']['byte_receipt']['end_byte']} in t02's UTF-8 user prompt (half-open):", '```json', transfer['source_note']['text'], '```',
              'All 16 transfers retain their own source outputs byte-for-byte, including failures. Direct parent/example content is absent outside the note; transfer is **parent-free but not note-free**, and its ancestry remains externally demonstrated. No child attempted Sudoku ACT or solved board is represented here.',
              '', '## Lesson claims (separate from citation validity)',
              'The three valid records say “Check row for repeated values.”, “Check row for duplicate.” and “Check box members for duplicates.” These are generic checking imperatives; the corresponding single citations support only their local duplicates, not a learned checking habit or universally effective lesson. Imperatives are not additional verified observations. Process s03 says “Check row, column overlap.” despite a false box citation; t03 says “Check column overlap.” while naming a box across different boxes and unequal values. Other generic imperatives accompanying false checks do not repair them. **Free-prose lessons remain unverified and unapproved for training.**',
              '', '## Pairing, cost and verification limits',
              f"Fixed source IDs 1851200..7; transfer IDs 1851300..7. Recomputed public-question parsing, deterministic fills/edits, all candidate/source hashes, 16-way uniqueness and actual relocated v1/v2 prior content. All eight common examples are factual, all eight transfer boards contain witnesses, and all eight copied source checks fail on transfer even with the case ID rebound.",
              f"Sampler 7101 is generation-only; two worker PIDs {report['worker_pids']}. Both arms use eight identical examples, order/caps/temperature and 16 calls. All32 native stops are `stop`, each <=128 tokens; actual prompt-token IDs match recorded counts; no truncation/rewrite.",
              f"Native token totals: process {report['tokens']['process']['prompt']}/{report['tokens']['process']['output']} input/output; format {report['tokens']['format']['prompt']}/{report['tokens']['format']['output']}. Process explanation tokens {report['explanation_tokens']['process']}; format {report['explanation_tokens']['format']}. **Not token- or compute-matched:** same call caps do not equate actual dose; source specificity is part of the intervention. Elapsed controller time {report['elapsed_seconds']:.3f}s is retained from the receipt, not independently timed.",
              'The control has zero valid child records. A later process-valid-only fit versus an empty control would combine material selection, training dose and content quality; it cannot identify a parenting effect. Replaying this one event many times never makes multiple experiences. No P1/H1/generalization/internalization/persistence claim follows.',
              'Remote Qwen2.5-7B-Instruct model/package paths are absolute node paths: file-pin assertions are captured, not locally authenticated model provenance. Matching available local source hashes are reported separately. No remote hash reread or GPU/process inspection was performed. Both cleanup/full-release observations are archived receipts only. Full raw bytes, masks and future model identities must remain bound if another stage is selected.',
              '', '## Recommendation: one bounded event-utility diagnostic, not another production hunt',
              '**Choose the single t02 event only for a technical sleep-utility/no-update comparison.** It is enough to ask whether writing this one verified citation changes behavior beyond a format-only write; it is not enough to test a reliable parent-to-own-lesson internalization process. Treat selection as posthoc, unique experiences=1, source failures retained in the history. Do not combine it with s04/s07 or label any record clean ancestry.',
              'Proposed smallest next comparison (Main selection required): two fresh-base LoRA fits, one fixed optimizer seed distinct in role from sampler 7101, plus a shared no-update baseline. Full condition supervises the exact t02 record structural/citation bytes; active-format condition supervises only structural syntax from the **same raw record**, masking case-ID value and group/cell/digit values. Both mask lesson text and all context. Preserve the original raw sequence, actual transfer prompt and erroneous own source note as provenance/context; no parent explanation/example or parent lesson may enter the sleep corpus or target. Do not rewrite bad s02 into a correct lesson. This is an own-citation write, not an approved whole-lesson sleep.',
              'Use identical span partitions and tokenized input/target sequences, batch/order/steps/base/LoRA initialization for both fits; change only loss flags. A proposed cap is 32 optimizer steps, rank8/alpha16, AdamW LR1e-4, dropout0.05, all existing projection targets, bf16, batch1/accum1; freeze these once, no sweep or continuation. Exact forward/backward token work can be matched this way; supervised-token counts intentionally differ and must be reported, not called identical learning dose. The syntax control still sees citation values through teacher forcing: this isolates citation supervision, not all content exposure. The no-update arm is a no-write reference, not a compute-matched training arm. No synthetic prose, answer padding, invalid control-record training, or hidden corrected target.',
              'Minimum new wiring is a source-bound loss-span selector, not a new trainer: `parent_correction_write.py:raw_span` demonstrates byte binding; `train_adapter_v3.py:normalize_items`, `encode_spans`, `encode_item_segments` provide existing span masks. `parent_correction_write.py:make_corpus`/`command_specs` are **not drop-in**: they hardcode the old event/whole-target mask/32 replays×3 epochs/three recipients. New mask spans need actual-tokenizer verification, nonempty targets, zero truncation and token-boundary accounting before any fit. Parent/lesson exclusion is a corpus property, not a prose whitelist. Do not run the old command helper unchanged.',
              'Evaluate the same eight captured transfer boards **without parent/example/source note**: t02 is a retention/control anchor; the other seven are already exposed development boards, not a new held-out test and not generalization evidence. Freeze exact evaluation prompts and deterministic decode before fitting; measure shared OFF once, and one ON pass per fit (24 evaluation calls total). Score unchanged strict grounded count, invalid citations, schema and per-case transitions; report retention separately from other-seven gain and full-write minus format-write. Current stochastic note-conditioned 1/8 is not the no-note OFF baseline. If no nontraining-case content gain, regression, a format-only gain, or equal active-control gain results, stop and record no demonstrated utility beyond that contrast. Never tune to this panel or collect replacements; no automatic fit promotion or certificates.',
              'This intentionally small question is informative even if negative, but advances only the own-output→write→parent-removed evaluation link. It does not complete P1/integrated parenting. Two fits, one optimizer seed and one selected event give no robustness estimate. Inference cost reference is the captured 32-call/340.549s run; 24 evaluations likely minutes, but fit latency/VRAM is **unmeasured here** and must not be quoted as an observed budget. Hard proposed bounds: 32 steps/fit, 24 evaluation calls, 128 new tokens/call, no automatic continuation; Main must set wall-clock/lease caps before selection.',
              '', '## Why not switch directly to the old nursery runner?',
              'Existing `nursery_dialogue.py:play_task`/`parent_turn` and `rulegame.py:RuleGame.evaluate` supply the stronger eventual child-action→world-feedback→own-note→different-task path. However the current runner is not an already matched clean baseline: parent makes two extra calls; solo makes none; arm names affect episode IDs; notes/prefixes are stripped and truncated; `admitted = post >= pre` is logged but failure branch is `pass`, not a selection veto. `RuleGame.evaluate` TRY reports boolean environment feedback with zero score; quiz score is a different endpoint. Do not equate quiz improvement to lesson truth or launch `nursery_dialogue --phase sleep` unchanged (it invokes the legacy v21 trainer).',
              'If Main wants a substantive integrated-chain test instead of the explicitly narrow utility check, choose a fixed small RuleGame block, not more miniSudoku words/seeds: same task IDs/triples in both arms, active format restatement with equal calls/caps, raw own notes untruncated, real TRY/outcome grounding, explicit selection from predeclared fixed tasks, and one note-/parent-free ON/OFF quiz panel after a modern LoRA-only sleep. Zero material yield stops the block; no rule/source replacement hunt. That requires a separately selected protocol and several hygiene fixes, so it is not the smallest immediate reuse of these terminal bytes. Neither path is implemented or authorized by this audit.',
              '', '## Reproduction',
              '`PYTHONDONTWRITEBYTECODE=1 python3 -B /tmp/astra_demonstration_content_audit_20260912.py`',
              'The script writes only this report and its sibling JSON. It uses a stdlib independent schema/citation witness enumerator plus the existing CPU replay as a cross-check; all comparisons and raw evidence are retained in JSON. No normalization or replacement of original strict scores.']
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    report = audit()
    DEST.with_suffix('.json').write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    DEST.with_suffix('.md').write_text(markdown(report))
    print(json.dumps({key:report[key] for key in ['status','verification_failures','counts','tokens']}, indent=2))
    raise SystemExit(bool(report['verification_failures']))
