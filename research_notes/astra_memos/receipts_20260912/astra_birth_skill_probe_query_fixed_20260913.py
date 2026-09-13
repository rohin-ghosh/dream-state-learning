#!/usr/bin/env python3
"""Bounded OFF-only DEV12 paired elicitation. Main owns native execution."""
from __future__ import annotations

import argparse
from collections.abc import Mapping
import contextlib
import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import threading
import time
import xml.etree.ElementTree as ET

ANCHOR = ('Keep observations, prior predictions, and later outcomes distinct. '
          'Report only what the public record supports. Do not invent a prediction '
          'when none was stated. Compare an explicit prediction with its matching '
          'outcome; do not infer a hidden rule. Follow the requested record format.')
REVISION = 'a09a35458c702b33eeacc393d103063234e8bc28'
MODEL_NAME = 'Qwen/Qwen2.5-7B-Instruct'
SCOPE = 'perception_DEV12_anchor_NO_FIT'
CONDITIONS = ('absent', 'present')
SOURCE_NAMES = ('organism_v6/birth_skill_corpus.py',
                'organism_v6/rulegame_parenting_diagnostic.py')
PARAMS = dict(temperature=0.0, seed=0, max_tokens=192, top_p=1.0,
              top_k=-1, n=1, presence_penalty=0.0, frequency_penalty=0.0,
              repetition_penalty=1.0, ignore_eos=False)
ENGINE = dict(max_model_len=16384, tensor_parallel_size=1, seed=0,
              gpu_memory_utilization=0.85, enforce_eager=True,
              enable_lora=False, enable_prefix_caching=False, dtype='bfloat16',
              trust_remote_code=False)
LIMITS = ('Diagnostic n=1 public-record elicitation only. Not learned skills, '
          'persistence, H1/H2, L2, a scientific pass, or exact-wording/paraphrase evidence.')
CONTROLLER_SECONDS = 900
COLLECT_SECONDS = 180
RELEASE_RESERVE = 20
GPU_QUERY_SECONDS = 30


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                       separators=(',', ':')) + '\n').encode()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def read(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_object)


def write(path, value):
    path = Path(path)
    temporary = path.with_name(f'.{path.name}.{os.getpid()}.pending')
    created = False
    try:
        with temporary.open('xb') as stream:
            created = True
            stream.write(encoded(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        if created and temporary.exists():
            temporary.unlink()


def tree(root):
    root = Path(root)
    result = {}
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink(), 'archive/source tree symlink')
        if path.is_file():
            result[str(path.relative_to(root))] = digest(path)
        else:
            require(path.is_dir(), 'special file rejected')
    return result


def model_hashes(model):
    model = Path(model)
    files = {str(path.relative_to(model)): digest(path)
             for path in sorted(model.rglob('*')) if path.is_file()}
    require(files and not any('adapter' in name.lower() for name in files),
            'model-only base required; adapter material rejected')
    require('config.json' in files and 'tokenizer_config.json' in files and
            any(name.endswith('.safetensors') for name in files), 'incomplete local base')
    require(read(model / 'config.json').get('model_type') == 'qwen2', 'wrong base type')
    return files


def native_environment():
    return dict(python=str(Path(sys.executable).resolve()), python_sha256=digest(sys.executable),
                version=sys.version, packages={name: importlib.metadata.version(name) for name in
                ('vllm', 'torch', 'transformers', 'tokenizers', 'safetensors', 'huggingface-hub')})


def offline():
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
                      HF_DATASETS_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1',
                      VLLM_NO_USAGE_STATS='1', DO_NOT_TRACK='1',
                      VLLM_WORKER_MULTIPROC_METHOD='spawn', PYTHONDONTWRITEBYTECODE='1')
    sys.dont_write_bytecode = True


def disjoint(first, second):
    first, second = Path(first).resolve(), Path(second).resolve()
    return first != second and first not in second.parents and second not in first.parents


def stdout_outside(root):
    for descriptor in (1, 2):
        target = os.readlink(f'/proc/self/fd/{descriptor}')
        if target.startswith('/'):
            require(disjoint(root, target.removesuffix(' (deleted)')), 'stdout/stderr inside root')


def load_corpus(source):
    path = Path(source) / SOURCE_NAMES[0]
    spec = importlib.util.spec_from_file_location('public_birth_probe_corpus', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixed_rows(corpus):
    variants = corpus.build_variants('perception', split='dev', system_anchor=ANCHOR)
    rows = {name: variants['supplied' if name == 'present' else name]['rows']
            for name in CONDITIONS}
    require(all(len(value) == 12 for value in rows.values()), 'DEV12 only')
    require(len({row['row_id'] for row in rows['absent']}) == 12, 'duplicate public row')
    for absent, present in zip(rows['absent'], rows['present'], strict=True):
        require(absent['skill'] == present['skill'] == 'perception', 'wrong skill')
        require(absent['input_messages'] == [absent['input_messages'][0]] and
                absent['input_messages'][0]['role'] == 'user', 'baseline input scope')
        require(present['input_messages'] == [{'role': 'system', 'content': ANCHOR}]
                + absent['input_messages'], 'anchor-only variation required')
        require({key: value for key, value in absent.items() if key not in
                 ('input_messages', 'input_sha256')} ==
                {key: value for key, value in present.items() if key not in
                 ('input_messages', 'input_sha256')}, 'paired source/target drift')
    return rows


def render(tokenizer, messages):
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    template_tokens = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
    if isinstance(template_tokens, Mapping):
        template_tokens = template_tokens.get('input_ids')
    require(isinstance(template_tokens, (list, tuple)) and template_tokens and
            all(type(token) is int and token >= 0 for token in template_tokens),
            'invalid template token vector')
    tokens = list(template_tokens)
    encoded_tokens = tokenizer.encode(text, add_special_tokens=False)
    require(isinstance(encoded_tokens, (list, tuple)) and encoded_tokens and
            all(type(token) is int and token >= 0 for token in encoded_tokens),
            'invalid encoded token vector')
    require(tokens == list(encoded_tokens), 'template/token disagreement')
    require(tokens and len(tokens) + 192 <= ENGINE['max_model_len'], 'native context exceeded')
    match = re.match(r'\A<\|im_start\|>system\n(.*?)<\|im_end\|>\n', text, re.S)
    require(match is not None, 'cannot identify actual Qwen system segment')
    return dict(rendered_prompt=text, prompt_token_ids=tokens,
                actual_system_text=match[1], actual_system_segment=match[0])


def native_tokenizer(model):
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(model, local_files_only=True, trust_remote_code=False)


def validate_binding(binding, corpus_hash):
    require(set(binding) == {'schema', 'scope', 'visibility', 'model_name', 'revision',
                            'model_files', 'source_files', 'native_environment', 'approved_by'},
            'binding fields/scope: no adapter, training, or legacy normalization accepted')
    require(binding['schema'] == 1 and binding['scope'] == SCOPE and
            binding['visibility'] == 'model-only-public' and binding['approved_by'] == 'Main',
            'Main public model-only binding required')
    require(binding['model_name'] == MODEL_NAME and binding['revision'] == REVISION,
            'frozen base revision differs')
    require(set(binding['source_files']) == set(SOURCE_NAMES) and
            binding['source_files'][SOURCE_NAMES[0]] == corpus_hash and
            re.fullmatch('[0-9a-f]{64}', corpus_hash), 'actual final corpus/source pin differs')
    require(isinstance(binding['model_files'], dict) and binding['model_files'], 'model manifest missing')
    require(not any('adapter' in name.lower() for name in binding['model_files']), 'adapter forbidden')


def public_model_files(receipt, model):
    require(set(receipt) == {'checked_utc', 'clean_lineage_certified', 'elapsed_seconds', 'file_count',
                            'files', 'historical_receipts_changed', 'limitation', 'metadata_sha256',
                            'metadata_url', 'model', 'repository', 'revision', 'status'},
            'public model-only receipt fields differ')
    require(receipt['status'] == 'PUBLIC_REVISION_FILES_MATCHED_PROSPECTIVE_BINDING' and
            receipt['repository'] == MODEL_NAME and receipt['revision'] == REVISION and
            Path(receipt['model']).resolve() == Path(model).resolve(), 'public model binding differs')
    require(receipt['file_count'] == len(receipt['files']) == 14, '14 public matched files required')
    files = {}
    for name, entry in receipt['files'].items():
        require(entry['public_match'] in ('GIT_BLOB_SHA1', 'LFS_SHA256') and
                re.fullmatch('[0-9a-f]{64}', entry['sha256']) and 'adapter' not in name.lower(),
                'unmatched/adapter public file')
        files[name] = entry['sha256']
    return files


def scope_binding(receipt, source, model, corpus_hash):
    if 'source_files' in receipt:
        binding = receipt
    else:
        binding = dict(schema=1, scope=SCOPE, visibility='model-only-public', approved_by='Main',
                       model_name=MODEL_NAME, revision=REVISION,
                       model_files=public_model_files(receipt, model),
                       source_files={name: digest(Path(source) / name) for name in SOURCE_NAMES},
                       native_environment=native_environment())
    validate_binding(binding, corpus_hash)
    return binding


def prepare(root, source, model, binding_path, binding_sha256, corpus_sha256,
            gpu_uuid, gpu_index, lease_end, log_dir):
    offline()
    root, source, model, log_dir = map(lambda path: Path(path).resolve(),
                                      (root, source, model, log_dir))
    stdout_outside(root)
    require(not root.exists(), 'new immutable run directory required')
    require(all(disjoint(root, path) for path in (source, model, log_dir, binding_path)),
            'root overlaps protected input/logs')
    require(log_dir.is_dir(), 'existing external log directory required')
    require(re.fullmatch(r'GPU-[0-9a-fA-F-]{36}', gpu_uuid) and type(gpu_index) is int
            and gpu_index >= 0, 'single physical GPU UUID and index required')
    require(math.isfinite(lease_end) and lease_end > time.time() + 1100, 'insufficient lease')
    require(digest(binding_path) == binding_sha256, 'Main receipt hash differs')
    binding = scope_binding(read(binding_path), source, model, corpus_sha256)
    require(binding['source_files'] == {name: digest(source / name) for name in SOURCE_NAMES},
            'source snapshot drift')
    require(binding['model_files'] == model_hashes(model), 'model drift')
    require(binding['native_environment'] == native_environment(), 'native environment drift')
    rows = fixed_rows(load_corpus(source))
    tokenizer = native_tokenizer(str(model))
    calls = {condition: [dict(call_id=f'{index:02d}', row_id=row['row_id'],
             messages=row['input_messages'], native=render(tokenizer, row['input_messages']))
             for index, row in enumerate(rows[condition])] for condition in CONDITIONS}
    require(all(call['native']['actual_system_text'] == ANCHOR for call in calls['present']),
            'supplied anchor changed by template')
    plan = dict(schema=1, scope=SCOPE, adapter=None, fit=False, model=str(model),
                revision=REVISION, source=str(source), binding=binding,
                binding_sha256=binding_sha256, corpus_sha256=corpus_sha256,
                gpu_uuid=gpu_uuid, gpu_index=gpu_index, lease_end=lease_end,
                log_dir=str(log_dir), driver_sha256=digest(__file__),
                params=PARAMS, engine=ENGINE, calls=calls, conditions=list(CONDITIONS),
                controller_seconds=CONTROLLER_SECONDS, collect_seconds=COLLECT_SECONDS,
                claim_limits=LIMITS, chat_template=tokenizer.chat_template)
    root.mkdir()
    with (root / 'binding.json').open('xb') as stream:
        stream.write(Path(binding_path).read_bytes())
    require(digest(root / 'binding.json') == binding_sha256, 'receipt changed while copying')
    for name in SOURCE_NAMES:
        destination = root / 'source' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as stream:
            stream.write((source / name).read_bytes())
    write(root / 'rows.json', rows)
    plan['rows_sha256'] = digest(root / 'rows.json')
    require(binding['source_files'] == {name: digest(root / 'source' / name) for name in SOURCE_NAMES},
            'source changed while copying')
    write(root / 'plan.json', plan)
    return dict(plan_sha256=digest(root / 'plan.json'), root=str(root))


def verify(root, plan_sha256, native=False):
    root = Path(root)
    require(digest(root / 'plan.json') == plan_sha256, 'plan hash differs')
    plan = read(root / 'plan.json')
    require(plan['scope'] == SCOPE and plan['adapter'] is None and plan['fit'] is False and
            plan['revision'] == REVISION and plan['params'] == PARAMS and plan['engine'] == ENGINE and
            plan['conditions'] == list(CONDITIONS) and plan['controller_seconds'] == 900 and
            plan['collect_seconds'] == 180 and plan['claim_limits'] == LIMITS, 'scope/parameters drift')
    validate_binding(plan['binding'], plan['corpus_sha256'])
    require(digest(root / 'binding.json') == plan['binding_sha256'], 'Main receipt bytes differ')
    receipt = read(root / 'binding.json')
    if 'source_files' in receipt:
        require(receipt == plan['binding'], 'scoped receipt differs')
    else:
        require(public_model_files(receipt, plan['model']) == plan['binding']['model_files'],
                'public receipt model manifest differs')
    require(plan['driver_sha256'] == digest(__file__), 'driver drift')
    for source in (Path(plan['source']), root / 'source'):
        require(plan['binding']['source_files'] == {name: digest(source / name) for name in SOURCE_NAMES},
                'source drift')
    require(digest(root / 'rows.json') == plan['rows_sha256'], 'row metadata drift')
    rows = fixed_rows(load_corpus(root / 'source'))
    require(rows == read(root / 'rows.json'), 'fixed public rows drift')
    for condition in CONDITIONS:
        calls = plan['calls'][condition]
        require(len(calls) == 12, 'call count differs')
        for index, (call, row) in enumerate(zip(calls, rows[condition], strict=True)):
            require(set(call) == {'call_id', 'row_id', 'messages', 'native'} and
                    call['call_id'] == f'{index:02d}' and call['row_id'] == row['row_id'] and
                    call['messages'] == row['input_messages'], 'input visibility/selection drift')
    if native:
        require(plan['binding']['model_files'] == model_hashes(plan['model']), 'model drift')
        require(plan['binding']['native_environment'] == native_environment(), 'native environment drift')
    return plan


class Native:
    def __init__(self, plan):
        from vllm import LLM
        self.llm = LLM(model=plan['model'], tokenizer=plan['model'], **ENGINE)
        self.tokenizer = self.llm.get_tokenizer()
        require(self.tokenizer.chat_template == plan['chat_template'], 'native chat template drift')

    def generate(self, messages):
        import torch
        from vllm import SamplingParams
        native = render(self.tokenizer, messages)
        started = time.monotonic()
        with torch.inference_mode():
            outputs = self.llm.generate([native['rendered_prompt']], SamplingParams(**PARAMS),
                                        lora_request=None, use_tqdm=False)
        require(len(outputs) == 1 and len(outputs[0].outputs) == 1, 'native output cardinality')
        output = outputs[0].outputs[0]
        return dict(**native, text=output.text, output_token_ids=list(output.token_ids),
                    actual_prompt_token_ids=list(outputs[0].prompt_token_ids),
                    finish_reason=output.finish_reason, stop_reason=output.stop_reason,
                    started=started, ended=time.monotonic(),
                    decoded_output=self.tokenizer.decode(list(output.token_ids), skip_special_tokens=True))

    def close(self):
        shutdown = getattr(self.llm, 'shutdown', None)
        if shutdown is not None:
            shutdown()


def validate_response(call, response):
    require(all(response.get(key) == value for key, value in call['native'].items()),
            'native rendered input/token/system drift')
    require(response.get('actual_prompt_token_ids') == call['native']['prompt_token_ids'],
            'actual native prompt tokens drift')
    tokens = response.get('output_token_ids')
    require(type(tokens) is list and 0 < len(tokens) <= 192 and
            all(type(token) is int and token >= 0 for token in tokens), 'output tokens missing/over budget')
    require(isinstance(response.get('text'), str) and
            response['text'] == response.get('decoded_output'), 'output text/token audit differs')
    require(response.get('finish_reason') in ('stop', 'length') and 'stop_reason' in response,
            'missing/failed termination')
    require(response['finish_reason'] != 'length' or len(tokens) == 192, 'weak length termination')
    require(all(type(response.get(key)) in (int, float) and math.isfinite(response[key])
                for key in ('started', 'ended')) and response['ended'] >= response['started'], 'invalid timing')


def capture(plan, condition, directory, factory=Native):
    directory = Path(directory)
    directory.mkdir()
    identity = dict(model=plan['model'], revision=REVISION, adapter=None, params=PARAMS,
                    engine=ENGINE, binding=plan['binding'], driver_sha256=plan['driver_sha256'],
                    pid=os.getpid(), pgid=os.getpgrp(), condition=condition)
    write(directory / 'identity.json', identity)
    backend = None
    try:
        backend = factory(plan)
        for call in plan['calls'][condition]:
            write(directory / (call['call_id'] + '.request.json'),
                  dict(messages=call['messages'], native=call['native'], params=PARAMS,
                       started=time.monotonic()))
            response = backend.generate(call['messages'])
            write(directory / (call['call_id'] + '.response.json'), response)
            validate_response(call, response)
    finally:
        if backend is not None:
            backend.close()
    write(directory / 'closed.json', dict(calls=12, ended=time.monotonic()))


@contextlib.contextmanager
def budget(seconds):
    def expired(signum, frame):
        raise TimeoutError('bounded controller/collection deadline')
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def gpu_state(plan):
    result = subprocess.run(['nvidia-smi', '-i', str(plan['gpu_index']), '-q', '-x'],
                            capture_output=True, text=True, timeout=GPU_QUERY_SECONDS)
    require(result.returncode == 0, 'GPU identity/release query failed')
    devices = ET.fromstring(result.stdout).findall('gpu')
    require(len(devices) == 1 and devices[0].findtext('uuid') == plan['gpu_uuid'], 'GPU UUID/index drift')
    processes = devices[0].find('processes')
    return processes is not None and not (processes.text or '').strip() and not list(processes)


def group_alive(group):
    for path in Path('/proc').glob('[0-9]*/stat'):
        try:
            fields = path.read_text().rsplit(')', 1)[1].split()
            if int(fields[2]) == group and fields[0] not in ('Z', 'X'):
                return True
        except FileNotFoundError:
            continue
    return False


def cleanup(process):
    require(process.pid > 1 and process.pid != os.getpgrp(), 'not an owned isolated group')
    for action in (signal.SIGTERM, signal.SIGKILL):
        if not group_alive(process.pid):
            break
        try:
            os.killpg(process.pid, action)
        except ProcessLookupError:
            pass
        deadline = time.monotonic() + 2
        while group_alive(process.pid) and time.monotonic() < deadline:
            time.sleep(.05)
    process.wait(timeout=2)
    return not group_alive(process.pid)


def wait_worker(process, deadline):
    while process.poll() is None:
        require(time.monotonic() < deadline, 'controller timeout')
        time.sleep(.1)
    require(process.returncode == 0, f'worker failed rc={process.returncode}')


def worker(root, plan_sha256, condition):
    offline()
    root = Path(root).resolve()
    stdout_outside(root)
    receipt_path = root / f'{condition}.process.json'
    parent = os.getppid()
    until = time.monotonic() + 5
    while not receipt_path.exists() and time.monotonic() < until:
        require(os.getppid() == parent > 1, 'controller disappeared before ownership receipt')
        time.sleep(.05)
    receipt = read(receipt_path)
    require(receipt['pid'] == os.getpid() == os.getpgrp() and
            receipt['parent_pid'] == os.getppid() > 1, 'controller ownership required')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == receipt['gpu_uuid'], 'worker GPU drift')
    remaining = receipt['deadline_monotonic'] - time.monotonic()
    require(remaining > 0, 'worker deadline already passed')
    stop = threading.Event()

    def watch_owner():
        while not stop.wait(.1):
            if os.getppid() != parent or time.monotonic() >= receipt['deadline_monotonic']:
                os.killpg(os.getpgrp(), signal.SIGKILL)
                return

    watcher = threading.Thread(target=watch_owner, daemon=True)
    watcher.start()
    try:
        with budget(remaining):
            plan = verify(root, plan_sha256, native=True)
            require(plan['gpu_uuid'] == receipt['gpu_uuid'], 'ownership device differs')
            capture(plan, condition, root / condition)
    finally:
        stop.set()
        watcher.join()


def validate_captures(root, plan):
    for condition in CONDITIONS:
        directory = Path(root) / condition
        closure = read(directory / 'closed.json')
        require(closure['calls'] == 12, 'all captures must close before scoring')
        identity = read(directory / 'identity.json')
        process = read(Path(root) / f'{condition}.process.json')
        require(identity == dict(model=plan['model'], revision=REVISION, adapter=None, params=PARAMS,
                engine=ENGINE, binding=plan['binding'], driver_sha256=plan['driver_sha256'],
                pid=process['pid'], pgid=process['pid'], condition=condition), 'capture identity drift')
        for call in plan['calls'][condition]:
            request = read(directory / (call['call_id'] + '.request.json'))
            require(request['messages'] == call['messages'] and request['native'] == call['native'] and
                    request['params'] == PARAMS, 'request drift')
            response = read(directory / (call['call_id'] + '.response.json'))
            validate_response(call, response)
            require(type(request['started']) in (int, float) and math.isfinite(request['started']) and
                    request['started'] <= response['started'] <= response['ended'] <= closure['ended'],
                    'capture lifecycle timing differs')
        require(len(list(directory.glob('*.response.json'))) == 12 and
                len(list(directory.glob('*.request.json'))) == 12, 'extra/missing calls')
        release = read(Path(root) / f'{condition}.release.json')
        require(release['ok'] is True and release['returncode'] == 0 and
                release['owned_group_empty'] is True and release['gpu_processes_absent'] is True and
                release['gpu_uuid'] == plan['gpu_uuid'] and release['pid'] == process['pid'],
                'unverified release or weak success')
    require(read(Path(root) / 'absent.process.json')['pid'] !=
            read(Path(root) / 'present.process.json')['pid'], 'fresh condition processes required')


def controller(root, plan_sha256, allow_gpu=False):
    require(allow_gpu, 'Main must explicitly allocate GPU and pass --allow-gpu')
    offline()
    root = Path(root).resolve()
    stdout_outside(root)
    with budget(CONTROLLER_SECONDS):
        started = time.monotonic()
        deadline = started + CONTROLLER_SECONDS - RELEASE_RESERVE
        write(root / 'controller.started.json', dict(started=started, pid=os.getpid()))
        plan = verify(root, plan_sha256, native=True)
        require(plan['lease_end'] > time.time() + CONTROLLER_SECONDS + COLLECT_SECONDS,
                'lease insufficient for controller plus collection')
        for condition in CONDITIONS:
            require(gpu_state(plan) is True, 'GPU occupied or unverifiable; no launch')
            require(time.monotonic() < deadline, 'controller timeout before launch')
            environment = os.environ.copy()
            environment.update(CUDA_VISIBLE_DEVICES=plan['gpu_uuid'], PYTHONNOUSERSITE='1')
            log = Path(plan['log_dir']) / f'{root.name}.{condition}.stdout.log'
            require(disjoint(root, log), 'stdout inside root')
            process, error, released, empty, status = None, None, False, False, None
            try:
                with log.open('xb') as stream:
                    command = [sys.executable, '-B', str(Path(__file__).resolve()), '_worker',
                               '--root', str(root), '--plan-sha256', plan_sha256, '--condition', condition]
                    process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT,
                                               env=environment, start_new_session=True)
                    write(root / f'{condition}.process.json', dict(pid=process.pid, parent_pid=os.getpid(),
                          gpu_uuid=plan['gpu_uuid'], deadline_monotonic=deadline, command=command))
                    wait_worker(process, deadline)
                    status = process.returncode
            except BaseException as failure:
                error = f'{type(failure).__name__}: {failure}'
            finally:
                try:
                    if process is not None:
                        released = cleanup(process)
                    empty = gpu_state(plan) is True
                except BaseException as failure:
                    error = error or f'cleanup {type(failure).__name__}: {failure}'
                write(root / f'{condition}.release.json', dict(ok=error is None and released and empty,
                      error=error, returncode=status, pid=None if process is None else process.pid,
                      owned_group_empty=released, gpu_processes_absent=empty, gpu_uuid=plan['gpu_uuid']))
            require(error is None and released and empty, 'worker failed/release unverified: ' + str(error))
            with (root / condition / 'stdout.closed.log').open('xb') as stream:
                stream.write(log.read_bytes())
        verify(root, plan_sha256, native=True)
        validate_captures(root, plan)
        write(root / 'release.json', dict(ok=True, calls_closed=24, gpu_uuid=plan['gpu_uuid'],
              owned_groups_empty=True, gpu_processes_absent=True, ended=time.monotonic(),
              elapsed=time.monotonic() - started))
        write(root / 'archive.json', dict(schema=1, plan_sha256=plan_sha256, files=tree(root)))
        return dict(archive_sha256=digest(root / 'archive.json'), plan_sha256=plan_sha256)


def collect(root, out, plan_sha256, archive_sha256):
    root, out = Path(root).resolve(), Path(out).resolve()
    require(disjoint(root, out) and not out.exists(), 'new disjoint immutable collection directory required')
    stdout_outside(root)
    stdout_outside(out)
    out.mkdir()
    with budget(COLLECT_SECONDS):
        require(digest(root / 'archive.json') == archive_sha256, 'archive digest differs')
        archive = read(root / 'archive.json')
        actual = tree(root)
        actual.pop('archive.json')
        require(actual == archive['files'] and archive['plan_sha256'] == plan_sha256,
                'full archive hashes/file set differ')
        plan = verify(root, plan_sha256, native=True)
        require(all(disjoint(out, path) for path in (plan['model'], plan['source'], plan['log_dir'])),
                'collection overlaps protected inputs/logs')
        validate_captures(root, plan)
        release = read(root / 'release.json')
        require(release['ok'] is True and release['calls_closed'] == 24 and
                release['owned_groups_empty'] is True and release['gpu_processes_absent'] is True and
                release['gpu_uuid'] == plan['gpu_uuid'] and 0 <= release['elapsed'] <= 900,
                'full capture/release required before scoring')
        corpus = load_corpus(root / 'source')
        rows = read(root / 'rows.json')
        scores = {condition: [corpus.score_response(row, read(root / condition /
                   f'{index:02d}.response.json')['text']) for index, row in enumerate(rows[condition])]
                   for condition in CONDITIONS}
        require(all(type(score['passed']) is bool and score['score_kind'] == 'public_record_parser'
                    for values in scores.values() for score in values), 'unsupported score kind')
        counts = {condition: sum(score['passed'] for score in scores[condition]) for condition in CONDITIONS}
        report = dict(scope=SCOPE, claim_limits=LIMITS, science_pass=None, learned_skill_claim=False,
                      archive_sha256=archive_sha256, plan_sha256=plan_sha256, scores=scores,
                      passed_counts=counts, present_minus_absent=counts['present'] - counts['absent'],
                      pairs=[dict(row_id=row['row_id'], absent=scores['absent'][index]['passed'],
                                  present=scores['present'][index]['passed'])
                             for index, row in enumerate(rows['absent'])])
        require(tree(root) == dict(archive['files'], **{'archive.json': archive_sha256}),
                'archive changed during scoring')
        write(out / 'report.json', report)
        return dict(report_sha256=digest(out / 'report.json'), out=str(out))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    for name in ('root', 'source', 'model', 'binding', 'binding-sha256', 'corpus-sha256', 'gpu-uuid', 'log-dir'):
        prep.add_argument('--' + name, required=True)
    prep.add_argument('--gpu-index', type=int, required=True)
    prep.add_argument('--lease-end', type=float, required=True)
    for name in ('controller', '_worker', 'collect'):
        command = commands.add_parser(name)
        command.add_argument('--root', required=True)
        command.add_argument('--plan-sha256', required=True)
        if name == 'controller':
            command.add_argument('--allow-gpu', action='store_true')
        elif name == '_worker':
            command.add_argument('--condition', choices=CONDITIONS, required=True)
        else:
            command.add_argument('--out', required=True)
            command.add_argument('--archive-sha256', required=True)
    args = vars(parser.parse_args(argv))
    name = args.pop('command')
    if name == 'prepare':
        args['binding_path'] = args.pop('binding')
    result = {'prepare': prepare, 'controller': controller, '_worker': worker, 'collect': collect}[name](**args)
    if result is not None:
        print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
