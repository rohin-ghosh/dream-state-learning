"""Observational correction ledger; no execution, persistence, or causal claims.

Main calls update_ledger once per completed ACT, then persists the returned JSON
state. completed_sleeps is the counter BEFORE that ACT, not a scheduled sleep.
raw_think accepts a string, a list of raw THINK strings, or None. execution is
the unmodified R184/R153 CPU outcome (including its actual result), not child
prose. Receipt authenticity remains the caller's responsibility; this helper
only checks supplied provenance joins and never reads files or runs code.

raw_code_glyphs checks only fullwidth ASCII U+FF01..U+FF5E and the explicitly
included ideographic space U+3000 in the raw first code block, including its
literals/comments. Other Unicode is not a fault under this guard. Neither
presence nor absence is a Python syntax, equation, or reasoning verdict.

Optional child_evidence is a list of explicit, caller-extracted child statements:
    {'fault_id': 'raw_code_glyphs',
     'noticed': {'value': True, 'source': 'THINK', 'index': 0, 'quote': '...'},
     'chosen': {'value': True, 'source': 'ACT', 'quote': '...'}}
Quotes must occur verbatim in the designated raw response. These are attributed
self-reports, not semantic verification. Missing/ambiguous evidence is UNKNOWN;
ordinary keywords never establish noticing, choosing, reasoning, or equations.
Child evidence remains explicitly UNADJUDICATED; quote binding is not adjudication.

parent_interventions covers ALL inputs since the preceding ACT, including
LEARN/THINK. None means unrecorded; [] confirms none. To classify an intervention,
Main supplies reminder: bool and, for reminders, fault_ids: list[str]. Unscoped
or unclassified interventions are UNKNOWN, never assumed unrelated from prose.

Every supplied cycle retains its observations, including UNKNOWN measurements.
A correction opportunity exists only if the immediately preceding ACT cycle
showed that fault YES, or current explicit bound child evidence says NOTICED.
Current fault absence then establishes ENACTED, without inferring NOTICED/CHOSEN.
counts.observed_by_fault counts cycle measurements; counts.by_fault and
counts.opportunities count only admitted correction opportunities.
HELD requires absence on the immediately following cycle AND the first later
ACT after a completed sleep, with no same-fault reminder or unknown interval.
One ACT can witness both conditions. HELD is a finite observed window, not a
claim of permanent retention, sleep effects, or correctness. Unknown/custom
faults (including equations/reasoning) have no automatic absence detector.
"""

from copy import deepcopy
import hashlib
import json
import re

from gpu import orch_r153_code_blocks as blocks


SCHEMA = 'R197_CORRECTION_LEDGER_V1'
STAGES = ('NOTICED', 'CHOSEN', 'ENACTED', 'HELD')
UNKNOWN = 'UNKNOWN'
FAULTS = ('raw_code_glyphs', 'execution_failure', 'import_error')


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _sha(raw):
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _is_sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def _raw_check(raw_act):
    if raw_act is None:
        return dict(fault_present=UNKNOWN, reason='RAW_ACT_UNRECORDED')
    report = blocks.extract(raw_act)
    original = report['raw_source']
    check = dict(fault_present=UNKNOWN, reason=report['reason'],
                 raw_text_sha256=report['raw_text_sha256'])
    if original is not None:
        codepoints = sorted({f'U+{ord(character):04X}' for character in original
                             if '\uff01' <= character <= '\uff5e' or character == '\u3000'})
        check.update(fault_present='YES' if codepoints else 'NO',
            raw_source_sha256=report['raw_source_sha256'], span_start=report['span_start'],
            span_end=report['span_end'], scope='FULLWIDTH_ASCII_U+FF01..U+FF5E_PLUS_U+3000'
                                             '_INCLUDING_LITERALS_AND_COMMENTS',
            fullwidth_codepoints=codepoints)
    return check


def _execution_check(execution, raw_act, source):
    check = dict(provenance=UNKNOWN, reason='NO_MATCHED_ACTUAL_RESULT',
                 execution_failure=UNKNOWN, import_error=UNKNOWN,
                 receipt_authentication='CALLER_RESPONSIBILITY')
    if not execution or raw_act is None:
        return check
    result = execution.get('result')
    if type(result) is not dict:
        return check
    origin = result.get('origin')
    if type(origin) is not dict:
        return check
    transformation = origin.get('code_transformation')
    if type(transformation) is not dict:
        return check
    policy = transformation.get('policy')
    if policy not in (blocks.POLICY, blocks.NFKC_POLICY):
        return check
    expected = blocks.extract(raw_act, policy=policy)
    reference = (source or {}).get('response')
    if reference is not None and (type(reference) is not dict
            or reference.get('record_sha256') != origin.get('record_sha256')):
        check['reason'] = 'RESPONSE_REFERENCE_MISMATCH'
        return check
    if not (execution.get('schema') == 'R153_CPU_DELIVERY_V1'
            and execution.get('status') == 'PUBLISHED'
            and result.get('schema') == 'R125_CPU_EXPERIMENT_RESULT_V1'
            and _is_sha(execution.get('result_sha256'))
            and type(execution.get('request_id')) is str and execution['request_id']
            and execution['request_id'] == result.get('request_id')
            and execution.get('origin') == origin
            and origin.get('child_generated') is True
            and _is_sha(origin.get('record_sha256'))
            and type(origin.get('journal_id')) is str and origin['journal_id']
            and execution.get('journal_id') == origin['journal_id']
            and expected['raw_source'] is not None
            and all(transformation.get(key) == expected.get(key) for key in
                    ('raw_text_sha256', 'raw_source_sha256', 'source_sha256'))
            and execution.get('source_sha256') == result.get('source_sha256')
            == expected.get('source_sha256')
            and execution.get('executed') is result.get('launch_attempted')
            and type(result.get('launch_attempted')) is bool
            and execution.get('result_status') == result.get('status')):
        return check
    check.update(provenance='MATCHED_SUPPLIED_RECEIPT', reason='BOUND_RESULT',
                 result_sha256=execution['result_sha256'], policy=policy,
                 execution_source_sha256=result['source_sha256'],
                 raw_source_sha256=expected['raw_source_sha256'])
    returncode = result.get('returncode')
    if result['launch_attempted'] and type(returncode) is int:
        if returncode != 0:
            check['execution_failure'] = 'YES'
        elif result.get('status') == 'COMPLETE':
            check.update(execution_failure='NO', import_error='NO')
        stderr = result.get('stderr')
        if returncode != 0 and type(stderr) is str:
            trace = re.search(r'^Traceback \(most recent call last\):\r?$', stderr, re.MULTILINE)
            terminal = re.search(r'^(?:ModuleNotFoundError|ImportError):[^\r\n]*\s*\Z',
                                 stderr, re.MULTILINE)
            if trace and terminal and trace.start() < terminal.start():
                check['import_error'] = 'YES'
    return check


def _statement(entries, key, raw_think, raw_act):
    candidates = [entry[key] for entry in entries if key in entry]
    if len(candidates) != 1 or type(candidates[0]) is not dict:
        return UNKNOWN
    evidence = candidates[0]
    if type(evidence.get('value')) is not bool:
        return UNKNOWN
    if evidence.get('source') == 'ACT':
        raw = raw_act
    elif evidence.get('source') == 'THINK':
        index = evidence.get('index', 0)
        raw = (raw_think[index] if type(index) is int and 0 <= index < len(raw_think)
               else None)
    else:
        raw = None
    quote = evidence.get('quote')
    if type(quote) is not str or not quote.strip() or raw is None or quote not in raw:
        return UNKNOWN
    return 'YES' if evidence['value'] else 'NO'


def _reminder(interventions, fault_id):
    if interventions is None:
        return UNKNOWN
    status = 'NO'
    for intervention in interventions:
        if intervention.get('reminder') is False:
            continue
        faults = intervention.get('fault_ids')
        if (intervention.get('reminder') is not True or type(faults) is not list
                or not faults or any(type(fault) is not str or not fault for fault in faults)):
            status = UNKNOWN
        elif fault_id in faults:
            return 'YES'
    return status


def _follow_up(opportunity, record):
    if opportunity['ENACTED'] != 'YES' or opportunity['HELD'] in ('YES', 'NO'):
        return
    window = opportunity['hold_window']
    cycle = record['cycle']
    present = record['faults'].get(opportunity['fault_id'], UNKNOWN)
    reminder = _reminder(record['parent_interventions'], opportunity['fault_id'])
    witness = dict(cycle=cycle, completed_sleeps=record['completed_sleeps'],
                   fault_present=present, reminder=reminder)
    window['observations'].append(witness)
    if cycle == opportunity['cycle'] + 1:
        window['following_action'] = deepcopy(witness)
    if (record['completed_sleeps'] > opportunity['completed_sleeps']
            and window['after_sleep'] is None):
        window['after_sleep'] = deepcopy(witness)
    if present == 'YES' or reminder == 'YES':
        opportunity['HELD'] = 'NO'
    elif (window['following_action'] is not None and window['after_sleep'] is not None
          and all(item['fault_present'] == 'NO' and item['reminder'] == 'NO'
                  for item in window['observations'])
          and [item['cycle'] for item in window['observations']]
          == list(range(opportunity['cycle'] + 1, cycle + 1))):
        opportunity['HELD'] = 'YES'


def _counts(opportunities, cycles):
    observations = {}
    for record in cycles:
        for fault_id, present in record['faults'].items():
            counts = observations.setdefault(fault_id, dict(cycles=0, failures=0, measured=0, unknown=0))
            counts['cycles'] += 1
            counts['failures'] += present == 'YES'
            counts['measured'] += present != UNKNOWN
            counts['unknown'] += present == UNKNOWN
    faults = {fault_id: dict(opportunities=0, failures=0, measured=0, unknown=0,
              stages={stage: dict(YES=0, NO=0, UNKNOWN=0) for stage in STAGES})
              for fault_id in observations}
    for opportunity in opportunities:
        counts = faults[opportunity['fault_id']]
        counts['opportunities'] += 1
        counts['failures'] += opportunity['fault_present'] == 'YES'
        counts['measured'] += opportunity['fault_present'] != UNKNOWN
        counts['unknown'] += opportunity['fault_present'] == UNKNOWN
        for stage in STAGES:
            counts['stages'][stage][opportunity[stage]] += 1
    return dict(cycles=len(cycles), observed_by_fault=observations,
                opportunities=len(opportunities), by_fault=faults)


def update_ledger(state, *, life_id, cycle, raw_think, raw_act, completed_sleeps,
                  execution=None, parent_interventions=None, child_evidence=None, source=None):
    """Return detached state; identical retries are idempotent, conflicting ones fail.

    Cycles increase strictly; gaps and missing evidence cannot establish HELD.
    source may carry the R191 source object; response.record_sha256, when supplied,
    must match the receipt origin. Other source metadata is retained verbatim.

    state is None for a new life or a prior returned dict restored from JSON.
    raw_think is str/list[str]/None; raw_act is str/None. completed_sleeps counts
    completed sleeps before this ACT. Optional execution is the actual R153
    outcome wrapper; missing/unbound receipts remain UNKNOWN. Parent inputs
    and quoted child evidence follow the module-level contract. The returned
    dict contains cycles, opportunities, counts, and raw source hashes. counts
    separates observed_by_fault from correction-only by_fault denominators. The
    raw_code_glyphs detector covers only U+FF01..U+FF5E plus U+3000; it never
    treats all non-ASCII text as a fault. Main owns config gating and persistence.
    """
    _require(type(life_id) is str and bool(life_id), 'nonempty_life_id')
    _require(type(cycle) is int and cycle >= 1, 'positive_cycle')
    _require(type(completed_sleeps) is int and completed_sleeps >= 0, 'completed_sleep_counter')
    _require(raw_act is None or type(raw_act) is str, 'raw_ACT_string_or_none')
    _require(raw_think is None or type(raw_think) is str
             or (type(raw_think) is list and all(type(raw) is str for raw in raw_think)),
             'raw_THINK_strings_or_none')
    _require(execution is None or type(execution) is dict, 'execution_object_or_none')
    _require(source is None or type(source) is dict, 'source_object_or_none')
    for name, entries in (('parent_interventions', parent_interventions), ('child_evidence', child_evidence)):
        _require(entries is None or (type(entries) is list and all(type(entry) is dict for entry in entries)),
                 name + '_objects_or_none')
    supplied = dict(life_id=life_id, cycle=cycle, raw_think=raw_think, raw_act=raw_act,
        completed_sleeps=completed_sleeps, execution=execution, parent_interventions=parent_interventions,
        child_evidence=child_evidence, source=source)
    json.dumps(supplied, ensure_ascii=False, allow_nan=False)
    if state is None:
        ledger = dict(schema=SCHEMA, life_id=life_id, cycles=[], opportunities=[],
                      causality_claimed=False, retained_in_weights=UNKNOWN)
    else:
        _require(type(state) is dict and state.get('schema') == SCHEMA
                 and state.get('life_id') == life_id, 'same_ledger_schema_and_life')
        ledger = deepcopy(state)
    for previous in ledger['cycles']:
        if previous['cycle'] == cycle:
            _require(previous['input'] == supplied, 'conflicting_cycle_retry')
            return ledger
    previous = ledger['cycles'][-1] if ledger['cycles'] else None
    if previous is not None:
        _require(cycle > previous['cycle'], 'increasing_cycle')
        _require(completed_sleeps >= previous['completed_sleeps'], 'nondecreasing_completed_sleeps')
    thinks = [] if raw_think is None else [raw_think] if type(raw_think) is str else raw_think
    raw_check = _raw_check(raw_act)
    execution_check = _execution_check(execution, raw_act, source)
    evidence = child_evidence or []
    fault_ids = set(FAULTS) | (set(previous['faults']) if previous is not None else set())
    fault_ids.update(entry['fault_id'] for entry in evidence
                     if type(entry.get('fault_id')) is str and entry['fault_id'])
    faults = {fault: UNKNOWN for fault in fault_ids}
    faults.update(raw_code_glyphs=raw_check['fault_present'],
                  execution_failure=execution_check['execution_failure'], import_error=execution_check['import_error'])
    record = dict(cycle=cycle, completed_sleeps=completed_sleeps, input=deepcopy(supplied),
        raw_think_sha256=[_sha(raw) for raw in thinks],
        raw_act_sha256=None if raw_act is None else _sha(raw_act),
        raw_check=raw_check, execution_check=execution_check, faults=faults,
        parent_interventions=deepcopy(parent_interventions))
    for opportunity in ledger['opportunities']:
        _follow_up(opportunity, record)
    for fault_id in sorted(fault_ids):
        entries = [entry for entry in evidence if entry.get('fault_id') == fault_id]
        noticed = _statement(entries, 'noticed', thinks, raw_act)
        chosen = _statement(entries, 'chosen', thinks, raw_act)
        prior_fault = (previous is not None and previous['cycle'] == cycle - 1
                       and previous['faults'].get(fault_id) == 'YES')
        if not prior_fault and noticed != 'YES':
            continue
        present = faults[fault_id]
        enacted = 'YES' if present == 'NO' else 'NO' if present == 'YES' else UNKNOWN
        ledger['opportunities'].append(dict(life_id=life_id, cycle=cycle,
            completed_sleeps=completed_sleeps, fault_id=fault_id, fault_present=present,
            NOTICED=noticed, CHOSEN=chosen, ENACTED=enacted, HELD=UNKNOWN,
            opportunity_basis=dict(prior_fault_cycle=previous['cycle'] if prior_fault else None,
                                   explicit_noticed=noticed == 'YES'),
            child_evidence=deepcopy(entries), child_evidence_adjudication='UNADJUDICATED',
            hold_window=dict(following_action=None, after_sleep=None, observations=[])))
    ledger['cycles'].append(record)
    ledger['counts'] = _counts(ledger['opportunities'], ledger['cycles'])
    return ledger
