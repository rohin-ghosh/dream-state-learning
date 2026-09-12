"""Trained-record acquisition check: 24 requests, 48 forwards, zero generations.

CPU prepare freezes actual JSON bytes/contexts, foils and native masks. Main alone
launches three fresh scoring processes. No fits, gym selection or dose escalation.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import math
import os
from pathlib import Path
import re
import secrets
import sys
import time


SELF = Path(__file__).resolve()
READOUT = Path('/tmp/astra_rulegame_record_readout_20260912.py')
READOUT_SHA = '120e260a76395586736d47e4f8a55c425b090f9f8654208dcfbef7eac5cccbde'
WRITE_PLAN_SHA = '48effd1ba154f497e5946d308f990624ada63bd905c198e0abfdf668131a8ee4'
VERSION = 'rulegame-trained-record-acquisition-v1'
CELLS = ('OFF', 'P', 'A')
CONTEXTS = ('FULL', 'MAPPING_SENTENCE_REMOVED')
EXTRA_SOURCES = ('semantic_carrier_diagnostic.py', 'conditional_behavior_readout.py',
    'conditional_behavior_corpus.py', 'fundamental_teaching_corpus.py', 'fundamental_teaching_readout.py',
    'writer_interface_calibration.py', 'multikey_writer_gateway_simple.py')


def load_runtime():
    import hashlib
    payload = READOUT.read_bytes()
    if hashlib.sha256(payload).hexdigest() != READOUT_SHA:
        raise ValueError('frozen runtime changed')
    name = 'acquisition_runtime_' + READOUT_SHA
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, READOUT)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        exec(compile(payload, str(READOUT), 'exec'), module.__dict__)
    return sys.modules[name]


runtime = load_runtime()
require, read, write_json, digest = runtime.require, runtime.read, runtime.write_json, runtime.digest


def modules(source):
    diagnostic = runtime.diagnostic_module(source)
    conditional = importlib.import_module('organism_v6.conditional_behavior_readout')
    carrier = importlib.import_module('organism_v6.semantic_carrier_diagnostic')
    require(all(Path(module.__file__).resolve().parents[1] == Path(source) for module in (conditional, carrier)),
        'scorer source root differs')
    return diagnostic, conditional, carrier


def scoring_pins(source):
    paths = [Path(source) / 'organism_v6' / name for name in EXTRA_SOURCES] + [SELF, READOUT]
    return {str(path): digest(path) for path in paths}


def protocol():
    return dict(version=VERSION, cells=list(CELLS), contexts=list(CONTEXTS), records=['P0', 'P1', 'A0', 'A1'],
        order='record then context within each OFF/P/A process', requests=24, candidate_forwards=48, generations=0,
        candidates=['truth', 'foil'], max_len=4096, eos=True, target='entire unchanged raw JSON plus EOS',
        primary_likelihood='full-target summed logprob', descriptive_likelihood='full-target mean logprob',
        margin='truth full-target sum minus foil full-target sum',
        own_record_acquisition='each adapter: both own records individually improve sum AND margin versus OFF, per context',
        stronger_P_specific='both P-owned records individually improve sum AND margin versus OFF AND A, per context',
        report_all_cross_arm=True, strict_improvement=True,
        ablation='remove exactly one LF plus RELATION_DEFINITION; other schema/action/outcome remain',
        interpretation='trained-record conditional acquisition; not heldout learning/parenting/P1/H1/H2 or pre-TRY skill',
        ablation_limit='prompt length/positions change; sensitivity to ablation, not unique semantic mechanism',
        controller_seconds=1800, worker_seconds=600, cleanup_seconds=140, lease_margin_seconds=21600)


def foil(raw):
    parsed = runtime.unique_object
    import json
    obj = json.loads(raw, object_pairs_hook=parsed)
    require(set(obj) == {'try', 'observed', 'predicted', 'relation'} and type(obj['predicted']) is bool
        and type(obj['observed']) is bool, 'exact record schema and nonnull Boolean prediction required')
    expected = 'matched' if obj['predicted'] == obj['observed'] else 'mismatched'
    require(obj['relation'] == expected, 'truth relation differs from prediction/outcome')
    matches = list(re.finditer(r'"relation"\s*:\s*"(matched|mismatched)"', raw))
    require(len(matches) == 1 and matches[0].group(1) == expected, 'one exact unescaped relation span required')
    start, end = matches[0].span(1)
    wrong = 'mismatched' if expected == 'matched' else 'matched'
    other = raw[:start] + wrong + raw[end:]
    require(json.loads(other, object_pairs_hook=parsed) == {**obj, 'relation': wrong}, 'foil changes another field')
    return dict(text=other, truth_span=[start, end], foil_span=[start, start+len(wrong)],
        truth_byte_span=[len(raw[:start].encode()), len(raw[:end].encode())],
        foil_byte_span=[len(raw[:start].encode()), len((raw[:start]+wrong).encode())],
        original_relation=expected, foil_relation=wrong)


def remove_mapping(text, diagnostic):
    needle = '\n' + diagnostic.RELATION_DEFINITION
    require(text.count(needle) == 1, 'exact mapping sentence must occur once with its LF')
    offset = text.index(needle)
    return text[:offset] + text[offset+len(needle):]


def decode(tokenizer, ids):
    return tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)


def encode_candidate(tokenizer, context, prefix, raw, span):
    """Carrier offset/mask checks, generalized only from compiler lines to JSON."""
    eos = tokenizer.eos_token_id
    require(type(eos) is int and eos >= 0, 'native EOS required')
    text = context + raw
    encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
    ids = list(encoded['input_ids'])
    offsets = [list(pair) for pair in encoded['offset_mapping']]
    require(len(ids) == len(offsets) and len(ids) > len(prefix) > 0, 'candidate token length differs')
    cursor, labels = 0, []
    for token, (start, end) in zip(ids, offsets):
        require(type(token) is int and token >= 0 and start == cursor and start < end <= len(text), 'exact offset coverage required')
        require(not start < len(context) < end, 'context/target boundary straddle')
        labels.append(-100 if end <= len(context) else token)
        cursor = end
    require(cursor == len(text) and decode(tokenizer, ids) == text, 'native complete-text roundtrip differs')
    target = tokenizer.encode(raw, add_special_tokens=False)
    require(ids == prefix + target and labels == [-100]*len(prefix) + target, 'candidate-dependent prefix/token join')
    require(target and eos not in target and decode(tokenizer, target) == raw, 'raw target/EOS roundtrip differs')
    require(len(ids)+1 <= 4096, 'no truncation: overlength candidate')
    positions = list(range(len(prefix), len(ids)+1))
    char_offsets = offsets + [[len(text), len(text)]]
    byte_offsets = [[len(text[:start].encode()), len(text[:end].encode())] for start, end in char_offsets]
    relation_positions = [index for index, (start, end) in enumerate(offsets)
        if start < len(context)+span[1] and end > len(context)+span[0]]
    require(relation_positions and min(relation_positions) >= len(prefix), 'relation outside target labels')
    return dict(text=raw, input_ids=ids+[eos], labels=labels+[eos], response_ids=target+[eos],
        token_offsets_char=char_offsets, token_offsets_utf8=byte_offsets, label_positions=positions,
        predictor_positions=[index-1 for index in positions], relation_char_span=span,
        relation_label_positions=relation_positions, eos_position=len(ids), terminal_eos_zero_width=True)


def records_from_write(plan, tokenizer):
    writer = runtime.load_driver(plan['write_driver'])
    root, written, diagnostic, exporter, _ = writer.checked_plan(plan['write_root'], plan['write_plan_sha256'])
    writer.verify_inputs(written, diagnostic)
    capture = Path(written['formation_root']) / 'formation/data'
    decision = diagnostic.read(written['main_audit_path'])
    selection = diagnostic.read(written['fixed_selection_path']) if written.get('fixed_selection_path') else decision['fixed_selection']
    replay = diagnostic.check_capture(capture, diagnostic.expected_identity(written), 'interaction_v3')
    pair = exporter.build_record_pair(capture, decision, selection, tokenizer, 4096, replay_verified_capture=replay)
    rows = []
    for arm in ('P', 'A'):
        require(pair['corpora'][arm] == read(root / 'material/corpora' / (arm+'.json'))
            and pair['source_receipts'][arm] == read(root / 'material/provenance' / (arm+'.sources.json')), 'original material/source map differs')
        training = read(root / 'material/provenance' / (arm+'.tokens.json'))
        for ordinal, (item, source) in enumerate(zip(pair['corpora'][arm]['corpus'], pair['source_receipts'][arm])):
            request = read(capture / 'calls' / (source['call_id']+'.request.json'))['request']
            require(request['protocol'] == 'interaction_v3', 'formation protocol differs')
            context, raw = item['spans'][0][0], item['spans'][1][0]
            contrast = foil(raw)
            removed_prompt = remove_mapping(request['prompt'], diagnostic)
            removed_context = remove_mapping(context, diagnostic)
            require(tokenizer.apply_chat_template([dict(role='user', content=removed_prompt)],
                tokenize=False, add_generation_prompt=True) == removed_context, 'ablation changes rendered bytes beyond one sentence')
            rows.append(dict(record_id=arm+str(ordinal), origin_arm=arm, ordinal=ordinal,
                source=source, raw=raw, foil=contrast, prompt=request['prompt'], context=context,
                removed_prompt=removed_prompt, removed_context=removed_context,
                training_ids=training['rows'][ordinal]['input_ids'], training_labels=training['rows'][ordinal]['labels']))
    require([row['record_id'] for row in rows] == ['P0', 'P1', 'A0', 'A1'], 'all four originally selected records required')
    return rows


def requests_from_records(records, tokenizer):
    requests = []
    for record in records:
        for condition in CONTEXTS:
            context = record['context'] if condition == 'FULL' else record['removed_context']
            prompt = record['prompt'] if condition == 'FULL' else record['removed_prompt']
            prefix = tokenizer.encode(context, add_special_tokens=False)
            require(prefix and decode(tokenizer, prefix) == context, 'input-only native prefix differs')
            candidates = [dict(candidate_id=name, **encode_candidate(tokenizer, context, prefix, raw, span))
                for name, raw, span in (('truth', record['raw'], record['foil']['truth_span']),
                                       ('foil', record['foil']['text'], record['foil']['foil_span']))]
            target = candidates[0]
            if condition == 'FULL':
                require(target['input_ids'] == record['training_ids'] and target['labels'] == record['training_labels'],
                    'FULL truth differs from actually trained V3 tokens/mask/EOS')
            else:
                require(target['response_ids'] == requests[-1]['candidates'][0]['response_ids'], 'ablation changes target tokenization')
            require(candidates[0]['response_ids'] != candidates[1]['response_ids'], 'foil tokenization not distinct')
            requests.append(dict(call_id=f'{len(requests):04d}', version=VERSION, operation='score_raw_record_relation',
                record_id=record['record_id'], origin_arm=record['origin_arm'], context_condition=condition,
                prompt=prompt, rendered_prompt=context, payload=dict(prompt_input_ids=prefix), candidates=candidates))
    require(len(requests) == 8, 'exactly eight scoring requests per cell')
    return requests


def prepare(write_root, write_plan_sha256, write_driver, out, deadline, lease_end):
    require(write_plan_sha256 == WRITE_PLAN_SHA, 'only the fixed attempt2 write plan is accepted')
    writer = runtime.load_driver(write_driver)
    root, written, diagnostic, _, _ = writer.checked_plan(write_root, write_plan_sha256)
    writer.verify_inputs(written, diagnostic)
    output = writer.local_path(out, fresh=True)
    require(output.parent == root.parent and output != root, 'fresh sibling acquisition root required')
    for protected in (written['model'], written['source_root'], written['formation_root'], written['main_audit_path'], write_driver, SELF):
        require(not writer.overlaps(output, Path(protected).resolve()), 'output overlaps protected input')
    end, lease = runtime.timestamp(deadline), runtime.timestamp(lease_end)
    require(time.time()+1800 < end <= lease-21600, '1800s work window and real lease six-hour margin required')
    require(runtime.absolute_python(sys.executable) == written['python'], 'use unchanged absolute native venv interpreter')
    modules(written['source_root'])
    plan = dict(version=VERSION, out=str(output), write_root=str(root), write_plan_sha256=write_plan_sha256,
        write_driver=str(Path(write_driver).resolve()), write_driver_sha256=digest(write_driver),
        source_root=written['source_root'], source_pins=written['implementation'],
        scoring_pins=scoring_pins(written['source_root']), model=written['model'], model_files=written['model_files'],
        device=written['device'], python=written['python'], deadline=end, supplied_lease_end=lease, lease_cutoff=lease-21600,
        protocol=protocol(), self_path=str(SELF), self_sha256=digest(SELF))
    plan['lineage'] = runtime.accepted_writes(plan)
    tokenizer = diagnostic.native_tokenizer(plan['model'])
    plan['records'] = records_from_write(plan, tokenizer)
    plan['requests'] = requests_from_records(plan['records'], tokenizer)
    require(runtime.accepted_writes(plan) == plan['lineage'] and scoring_pins(plan['source_root']) == plan['scoring_pins'],
        'lineage/source changed during native preparation')
    require(time.time()+1800 < end, 'preparation exhausted deadline')
    output.mkdir()
    write_json(output / 'plan.json', plan)
    pin = digest(output / 'plan.json')
    write_json(output / 'plan.sha256.json', dict(sha256=pin))
    return dict(status='PREPARED_NATIVE_SCORING_ONLY', root=str(output), plan_sha256=pin, requests=24, candidate_forwards=48, generations=0)


def check_sources(plan):
    require(all(digest(path) == checksum for path, checksum in {**plan['source_pins'], **plan['scoring_pins']}.items()), 'source/scorer bytes changed')
    require(digest(SELF) == plan['self_sha256'], 'acquisition sidecar changed')


def checked_plan(root, plan_sha256, tokenizer=None):
    root = Path(root).expanduser().resolve(strict=True)
    require(digest(root / 'plan.json') == plan_sha256 == read(root / 'plan.sha256.json')['sha256'], 'acquisition plan changed')
    plan = read(root / 'plan.json')
    require(plan['out'] == str(root) and plan['self_path'] == str(SELF) and plan['version'] == VERSION
        and plan['protocol'] == protocol() and plan['write_plan_sha256'] == WRITE_PLAN_SHA, 'prospective protocol/root differs')
    require(plan['deadline'] <= plan['lease_cutoff'] == plan['supplied_lease_end']-21600, 'lease cutoff differs')
    require(runtime.absolute_python(sys.executable) == plan['python'], 'native venv interpreter differs')
    require(digest(plan['write_driver']) == plan['write_driver_sha256'], 'write driver changed')
    check_sources(plan)
    diagnostic, conditional, carrier = modules(plan['source_root'])
    require(runtime.accepted_writes(plan) == plan['lineage'], 'fit/material/base/adapter lineage changed')
    if tokenizer is not None:
        require(records_from_write(plan, tokenizer) == plan['records'] and requests_from_records(plan['records'], tokenizer) == plan['requests'],
            'actual record/native token preparation differs')
    return root, plan, diagnostic


def forward_inputs(request):
    length = max(len(candidate['input_ids']) for candidate in request['candidates'])
    return [dict(input_ids=[candidate['input_ids']+[candidate['response_ids'][-1]]*(length-len(candidate['input_ids']))],
        attention_mask=[[1]*length], position_ids=[list(range(length))], use_cache=False) for candidate in request['candidates']]


def validate_scores(request, response):
    require(request['version'] == VERSION and request['operation'] == 'score_raw_record_relation'
        and [row['candidate_id'] for row in request['candidates']] == ['truth', 'foil'], 'acquisition protocol/candidates differ')
    values = response['token_logprobs']
    require(len(values) == 2 and response['native_forwards'] == forward_inputs(request), 'two exact native candidate forwards required')
    for candidate, scores in zip(request['candidates'], values):
        require(len(scores) == len(candidate['response_ids']) and all(type(value) in (int, float) and math.isfinite(value) and value <= 0
            for value in scores), 'incomplete/nonfinite candidate logprobs')
    require(sum(math.exp(sum(scores)) for scores in values) <= 1+1e-6, 'disjoint EOS candidate probability mass exceeds one')
    common = 0
    for left, right in zip(request['candidates'][0]['response_ids'], request['candidates'][1]['response_ids']):
        if left != right:
            break
        common += 1
    require(all(abs(values[0][index]-values[1][index]) <= 1e-6 for index in range(common)), 'shared earlier target-prefix scores differ')


class NativeScorer:
    """Reuse HF loader/close and carrier.score; never conditional assay routing."""
    def __init__(self, spec):
        _, conditional, self.carrier = modules(spec['source_root'])
        self.core = conditional.HFScorer(spec)
        model = self.core.model
        try:
            parameters = list(model.named_parameters())
            require(parameters and all(not parameter.requires_grad for _, parameter in parameters)
                and model.training is False and model.config.use_cache is False, 'scoring model must be frozen eval/no-cache')
            count = len(getattr(model, 'peft_config', {}))
            require(count == (0 if spec['adapter'] is None else 1), 'wrong scoring adapter count')
            base = model.get_base_model() if count else model
            require(Path(base.name_or_path).resolve() == Path(spec['model']), 'loaded base path differs')
            self.receipt = dict(loader='conditional_behavior_readout.HFScorer', scorer='semantic_carrier_diagnostic.score',
                training=False, trainable_parameters=0, adapter_count=count, use_cache=False,
                parameter_count=sum(parameter.numel() for _, parameter in parameters),
                dtypes=sorted({str(parameter.dtype) for _, parameter in parameters}),
                load_dtype='bf16', attention='eager', generation=False)
        except BaseException:
            self.core.close()
            raise

    def score(self, request):
        seen = []
        def capture(model, args, kwargs):
            require(not args and set(kwargs) == {'input_ids', 'attention_mask', 'position_ids', 'use_cache'}, 'native LM arguments differ')
            row = {name: kwargs[name].detach().cpu().tolist() for name in ('input_ids', 'attention_mask', 'position_ids')}
            row['use_cache'] = kwargs['use_cache']
            expected = forward_inputs(request)
            require(len(seen) < 2 and row == expected[len(seen)], 'native LM input/mask/positions differ')
            seen.append(row)
        hook = self.core.model.register_forward_pre_hook(capture, with_kwargs=True)
        try:
            result = self.carrier.score(self.core.torch, self.core.model, request)
        finally:
            hook.remove()
        response = dict(**result, native_forwards=seen)
        validate_scores(request, response)
        return response

    def close(self):
        return self.core.close()


def identity(spec):
    return dict(version=VERSION, backend='HF teacher-forced score; not vLLM generation', model=spec['model'],
        model_files=spec['model_files'], adapter=spec['adapter'], adapter_files=spec['adapter_files'],
        scorer_pins=spec['scoring_pins'], model_authentication_certified=False)


SPEC_KEYS = {'version', 'cell', 'data', 'model', 'model_files', 'adapter', 'adapter_files', 'device', 'python',
    'source_root', 'source_pins', 'scoring_pins', 'self_sha256', 'protocol', 'requests', 'hard_end', 'nonce'}


def worker_spec(root, plan, cell, hard_end):
    fit = plan['lineage']['fits'][cell] if cell != 'OFF' else None
    return dict(version=VERSION, cell=cell, data=str(root / 'run' / cell / 'data'), model=plan['model'],
        model_files=plan['model_files'], adapter=fit['adapter'] if fit else None, adapter_files=fit['files'] if fit else {},
        device=plan['device'], python=plan['python'], source_root=plan['source_root'], source_pins=plan['source_pins'],
        scoring_pins=plan['scoring_pins'], self_sha256=plan['self_sha256'], protocol=plan['protocol'],
        requests=plan['requests'], hard_end=hard_end, nonce=secrets.token_hex(16))


def worker(spec, spec_sha256, allow_gpu=False):
    require(allow_gpu, '--allow-gpu required before scoring worker work')
    spec_path = Path(spec).resolve(strict=True)
    require(digest(spec_path) == spec_sha256, 'worker spec changed')
    spec = read(spec_path)
    require(set(spec) == SPEC_KEYS and spec['version'] == VERSION and spec['protocol'] == protocol() and spec['cell'] in CELLS,
        'worker protocol/extra context differs')
    require((spec['adapter'] is None and spec['adapter_files'] == {}) if spec['cell'] == 'OFF'
        else bool(spec['adapter'] and spec['adapter_files']), 'OFF/P/A adapter role differs')
    require(runtime.absolute_python(sys.executable) == spec['python'] and os.environ.get('CUDA_VISIBLE_DEVICES') == spec['device'],
        'worker venv/device differs')
    require(time.time() < spec['hard_end']-140, 'worker cleanup window exhausted')
    stage, data = spec_path.parent / spec['cell'], Path(spec['data'])
    require(spec_path.name == spec['cell']+'.spec.json' and data == stage / 'data' and not data.exists(), 'fresh fixed worker path required')
    diagnostic, _, _ = modules(spec['source_root'])
    with runtime.owning_process(stage, spec['hard_end']):
        check_sources(spec)
        require(diagnostic.model_hashes(spec['model']) == spec['model_files'] and
            (spec['adapter'] is None or diagnostic.tree_hashes(spec['adapter']) == spec['adapter_files']), 'worker base/adapter changed')
        tokenizer = diagnostic.native_tokenizer(spec['model'])
        for request in spec['requests']:
            require(tokenizer.apply_chat_template([dict(role='user', content=request['prompt'])], tokenize=False,
                add_generation_prompt=True) == request['rendered_prompt'], 'native rendered context differs')
            prefix = tokenizer.encode(request['rendered_prompt'], add_special_tokens=False)
            require(request['payload'] == dict(prompt_input_ids=prefix), 'prompt prefix contains target or differs')
            for candidate in request['candidates']:
                expected = dict(candidate_id=candidate['candidate_id'], **encode_candidate(tokenizer, request['rendered_prompt'],
                    prefix, candidate['text'], candidate['relation_char_span']))
                require(candidate == expected, 'native token/mask/EOS/offset audit differs')
        require(len(spec['requests']) == 8, 'eight requests per worker required')
        data.mkdir()
        (data / 'calls').mkdir()
        write_json(data / 'identity.json', identity(spec))
        write_json(data / 'isolation.json', dict(pid=os.getpid(), pgid=os.getpgrp(), parent_pid=os.getppid(), spec_sha256=spec_sha256,
            generations=0, training=False, scope='fresh supervised process; no prior cell scores/model state'))
        backend = None
        try:
            backend = NativeScorer(spec)
            write_json(data / 'backend.ready.json', dict(pid=os.getpid(), ready=time.monotonic(), runtime=backend.receipt))
            for request in spec['requests']:
                stem = data / 'calls' / request['call_id']
                write_json(str(stem)+'.request.json', dict(request=request, started=time.monotonic(), identity=identity(spec),
                    request_sha256=diagnostic.value_hash(request)))
                response = backend.score(request)
                write_json(str(stem)+'.response.json', dict(response=response, ended=time.monotonic(), response_sha256=diagnostic.value_hash(response)))
                validate_scores(request, response)
            write_json(data / 'native_audit.json', dict(ok=True, requests=8, candidate_forwards=16, generations=0,
                native_prefix_offsets_masks_eos=True, native_forward_inputs=True, protocol=VERSION))
        except BaseException as error:
            write_json(data / 'failure.json', dict(error=type(error).__name__+': '+str(error)))
            raise
        finally:
            closed, error = False, None
            try:
                closed = backend.close() if backend is not None else True
            except Exception as failure:
                error = str(failure)
            write_json(data / 'backend.cleanup.json', dict(closed=closed, error=error))
            require(closed is True, 'scoring backend cleanup unverified')
        check_sources(spec)
        require(diagnostic.model_hashes(spec['model']) == spec['model_files'] and
            (spec['adapter'] is None or diagnostic.tree_hashes(spec['adapter']) == spec['adapter_files']), 'base/adapter changed while scoring')
        require(digest(spec_path) == spec_sha256, 'worker spec changed while scoring')
        diagnostic.capture_manifest(data)
        return dict(status='CAPTURED_SCORES', cell=spec['cell'])


def replay(root, plan, cell):
    diagnostic = runtime.diagnostic_module(plan['source_root'])
    data, spec_path = root / 'run' / cell / 'data', root / 'run' / (cell+'.spec.json')
    spec = read(spec_path)
    expected_spec = worker_spec(root, plan, cell, read(root / 'run/controller.json')['hard_end'])
    expected_spec['nonce'] = spec['nonce']
    require(spec == expected_spec, 'scoring worker/adapter spec differs')
    require(read(data / 'manifest.json')['files'] == diagnostic.tree_hashes(data, ('manifest.json',)), 'score capture seal changed')
    require(not (data / 'failure.json').exists() and read(data / 'backend.cleanup.json')['closed'] is True, 'failed score capture/cleanup')
    require(read(data / 'identity.json') == identity(spec), 'native score backend/adapter identity differs')
    require(read(data / 'native_audit.json') == dict(ok=True, requests=8, candidate_forwards=16, generations=0,
        native_prefix_offsets_masks_eos=True, native_forward_inputs=True, protocol=VERSION), 'native audit differs')
    require({path.name for path in (data / 'calls').iterdir()} == {request['call_id']+suffix for request in plan['requests']
        for suffix in ('.request.json', '.response.json')}, 'missing/extra score calls')
    rows, previous = [], 0.0
    costs = dict(requests=0, candidate_forwards=0, generations=0, scored_target_tokens=0, native_input_tokens=0,
        padded_forward_tokens=0, call_seconds=0.0)
    for request in plan['requests']:
        stem = data / 'calls' / request['call_id']
        sent, returned = read(str(stem)+'.request.json'), read(str(stem)+'.response.json')
        response = returned['response']
        require(sent['request'] == request and sent['identity'] == identity(spec) and
            sent['request_sha256'] == diagnostic.value_hash(request) and returned['response_sha256'] == diagnostic.value_hash(response), 'native score byte custody differs')
        require(all(type(value) in (int, float) and math.isfinite(value) for value in (sent['started'], returned['ended']))
            and previous <= sent['started'] <= returned['ended'], 'score timing differs')
        previous = returned['ended']
        validate_scores(request, response)
        values = {}
        for candidate, scores in zip(request['candidates'], response['token_logprobs']):
            values[candidate['candidate_id']] = dict(sum_logprob=sum(scores), mean_logprob=sum(scores)/len(scores),
                scored_tokens=len(scores), token_logprobs=scores)
        rows.append(dict(record_id=request['record_id'], origin_arm=request['origin_arm'], context_condition=request['context_condition'],
            truth=values['truth'], foil=values['foil'], truth_foil_margin=values['truth']['sum_logprob']-values['foil']['sum_logprob']))
        costs['requests'] += 1
        costs['candidate_forwards'] += 2
        costs['scored_target_tokens'] += sum(len(candidate['response_ids']) for candidate in request['candidates'])
        costs['native_input_tokens'] += sum(len(candidate['input_ids']) for candidate in request['candidates'])
        costs['padded_forward_tokens'] += 2*max(len(candidate['input_ids']) for candidate in request['candidates'])
        costs['call_seconds'] += returned['ended']-sent['started']
    return dict(cell=cell, rows=rows, costs=costs, capture_sha256=digest(data / 'manifest.json'))


def summarize(captures):
    require(set(captures) == set(CELLS), 'all cells required; no partial aggregate')
    indexed = {cell: {(row['record_id'], row['context_condition']): row for row in captures[cell]['rows']} for cell in CELLS}
    expected = {(record, context) for record in ('P0', 'P1', 'A0', 'A1') for context in CONTEXTS}
    require(all(len(captures[cell]['rows']) == 8 and set(indexed[cell]) == expected for cell in CELLS), 'all cross-arm records required')
    def gain(left, right, key):
        candidate, control = indexed[left][key], indexed[right][key]
        require(candidate['truth']['scored_tokens'] == control['truth']['scored_tokens'], 'cross-cell target counts differ')
        return dict(sum_logprob_delta=candidate['truth']['sum_logprob']-control['truth']['sum_logprob'],
            mean_logprob_delta=candidate['truth']['mean_logprob']-control['truth']['mean_logprob'],
            margin_delta=candidate['truth_foil_margin']-control['truth_foil_margin'],
            both_improve=candidate['truth']['sum_logprob'] > control['truth']['sum_logprob']
                and candidate['truth_foil_margin'] > control['truth_foil_margin'])
    comparisons, conditions = [], {}
    for record, context in [(record, context) for record in ('P0', 'P1', 'A0', 'A1') for context in CONTEXTS]:
        comparisons.append(dict(record_id=record, context_condition=context, P_vs_OFF=gain('P', 'OFF', (record, context)),
            A_vs_OFF=gain('A', 'OFF', (record, context)), P_vs_A=gain('P', 'A', (record, context))))
    for context in CONTEXTS:
        own = {arm: all(gain(arm, 'OFF', (arm+str(index), context))['both_improve'] for index in range(2)) for arm in ('P', 'A')}
        stronger = all(gain('P', control, ('P'+str(index), context))['both_improve'] for index in range(2) for control in ('OFF', 'A'))
        shared_P_records = all(gain(arm, 'OFF', ('P'+str(index), context))['both_improve'] for arm in ('P', 'A') for index in range(2))
        conditions[context] = dict(own_record_acquisition_vs_OFF=own, stronger_P_specific_selective_carriage=stronger,
            both_adapters_gain_on_P_records=shared_P_records,
            interpretation='shared/nonselective acquisition; stronger P-specific criterion not met' if all(own.values()) and shared_P_records and not stronger
                else 'report own-record acquisition separately from stronger P-specific criterion')
    sensitivity = {}
    for arm in ('P', 'A'):
        full = conditions['FULL']['own_record_acquisition_vs_OFF'][arm]
        removed = conditions['MAPPING_SENTENCE_REMOVED']['own_record_acquisition_vs_OFF'][arm]
        sensitivity[arm] = 'both' if full and removed else 'FULL_only' if full else 'MAPPING_SENTENCE_REMOVED_only' if removed else 'neither_demonstrated'
    return dict(contexts=conditions, all_record_comparisons=comparisons, own_acquisition_context_pattern=sensitivity,
        acquisition_is_not_heldout_learning=True, stronger_P_criterion_not_required_for_parameter_acquisition=True,
        mapping_ablation_limit=protocol()['ablation_limit'], conditional_prefix_limit='Earlier correct target fields precede relation autoregressively; not cognition or pre-TRY selection.')


def run(root, plan_sha256, allow_gpu=False):
    require(allow_gpu, '--allow-gpu required before controller work')
    started_wall, started = time.time(), time.monotonic()
    root, plan, diagnostic = checked_plan(root, plan_sha256)
    hard_end = min(started_wall+1800, plan['deadline'], plan['lease_cutoff'])
    stage = root / 'run'
    stage.mkdir()
    completed = {}
    try:
        with runtime.work_window(hard_end):
            tokenizer = diagnostic.native_tokenizer(plan['model'])
            checked_plan(root, plan_sha256, tokenizer)
            write_json(stage / 'controller.json', dict(plan_sha256=plan_sha256, started_wall=started_wall, hard_end=hard_end,
                pid=os.getpid(), cleanup_reserve=140, requests=24, candidate_forwards=48, generations=0))
            for cell in CELLS:
                checked_plan(root, plan_sha256)
                require(time.time() < hard_end-140, 'next cell lacks cleanup reserve')
                path = stage / (cell+'.spec.json')
                write_json(path, worker_spec(root, plan, cell, hard_end))
                pin = digest(path)
                command = [plan['python'], '-B', str(SELF), '_worker', '--spec', str(path), '--spec-sha256', pin, '--allow-gpu']
                with runtime.supervised_window(hard_end):
                    supervision = diagnostic.supervise(root, dict(model=plan['model'], device=plan['device'], lease_end=hard_end),
                        stage / cell, command, stage / cell / 'data/calls')
                require(supervision['ok'] and supervision['reservation_release_verified'], 'scoring supervision/release unverified')
                require(time.time() < hard_end-140 and digest(path) == pin, 'worker spec changed or controller work window exhausted')
                completed[cell] = replay(root, plan, cell)
                write_json(stage / cell / 'reduction.json', completed[cell])
            checked_plan(root, plan_sha256, tokenizer)
            require(all(replay(root, plan, cell) == completed[cell] for cell in CELLS), 'prior scoring capture changed')
            summary = summarize(completed)
        require(time.monotonic()-started <= 1800 and time.time() <= hard_end, 'inclusive controller cap exceeded')
        result = dict(status='COMPLETE_TRAINED_RECORD_ACQUISITION_CHECK', cells=completed, summary=summary,
            requests=24, candidate_forwards=48, generations=0, controller_seconds=time.monotonic()-started,
            claim_boundary=protocol()['interpretation'], model_authentication_certified=False, semantic_nonleakage_certified=False)
        write_json(stage / 'result.json', result)
        return result
    except BaseException as error:
        write_json(stage / 'failure.json', dict(error=type(error).__name__+': '+str(error), completed_cells=list(completed),
            aggregate=None, retry=False, controller_seconds=time.monotonic()-started))
        raise


def main(argv=None):
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    prep = sub.add_parser('prepare')
    for name in ('write-root', 'write-plan-sha256', 'write-driver', 'out', 'deadline', 'lease-end'):
        prep.add_argument('--'+name, required=True)
    command = sub.add_parser('run')
    command.add_argument('--root', required=True)
    command.add_argument('--plan-sha256', required=True)
    command.add_argument('--allow-gpu', action='store_true')
    child = sub.add_parser('_worker')
    child.add_argument('--spec', required=True)
    child.add_argument('--spec-sha256', required=True)
    child.add_argument('--allow-gpu', action='store_true')
    args = vars(parser.parse_args(argv))
    action = args.pop('action')
    print(json.dumps({'prepare': prepare, 'run': run, '_worker': worker}[action](**args), sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
