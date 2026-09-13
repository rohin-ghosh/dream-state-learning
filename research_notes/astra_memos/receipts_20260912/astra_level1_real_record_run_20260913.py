"""Bounded native interactive record formation; Main owns preparation and launch."""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


SELF = Path(__file__).resolve()
SCOPE = 'level1_real_record_formation_only_20260913_v1'
STATES = ('OFF', 'perception_seed0', 'perception_seed1', 'perception_seed2')
EPISODES, CALLS_PER_STATE = 8, 32
MAX_CALLS = 128
ACTION_TOKENS, RECORD_TOKENS = 96, 192
OUTER_SECONDS, STATE_SECONDS, COLLECTION_SECONDS = 1800, 900, 180
GPU_QUERY_SECONDS, CLEANUP_SECONDS, LEASE_MARGIN = 30, 40, 21600
LEVEL1_SHA256 = '6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e'
PUBLIC_SHA256 = '59874c678ce1b36feaa1969721c0dcc761b4fa05072a6231892269991201052c'
CORE_SOURCES = ('organism_v6/rulegame.py', 'organism_v6/rulegame_parenting_diagnostic.py')
ENGINE = dict(max_model_len=16384, tensor_parallel_size=1, seed=0, gpu_memory_utilization=.85,
              enforce_eager=True, enable_lora=True, max_lora_rank=32, enable_prefix_caching=False,
              dtype='bfloat16', trust_remote_code=False)
PARAMS = dict(temperature=0.0, seed=0, top_p=1.0, top_k=-1, n=1, presence_penalty=0.0,
              frequency_penalty=0.0, repetition_penalty=1.0, ignore_eos=False)
CLAIM = ('Interactive actual child-action/world-response/child-record formation only. No parent, fit, write, quiz, '
         'readout-score endpoint, clean ancestry, learning-improvement, closed-loop, P1/H1/H2 or automatic promotion. '
         'Same episode IDs and budgets do not imply identical realized actions or experiences.')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode()


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            checksum.update(block)
    return checksum.hexdigest()


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'duplicate JSON key')
        value[key] = item
    return value


def read(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_object,
                      parse_constant=lambda value: require(False, 'nonfinite JSON'))


def write(path, value):
    path = Path(path)
    temporary = path.with_name(f'.{path.name}.{os.getpid()}.pending')
    with temporary.open('xb') as stream:
        stream.write(encoded(value))
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink()


def failure(path, error):
    if not Path(path).exists():
        write(path, dict(error_type=type(error).__name__, error=str(error), time=time.time(), retry=False))


def tree(root):
    inventory = {}
    for path in sorted(Path(root).rglob('*')):
        require(not path.is_symlink(), 'symlink in artifact tree')
        if path.is_file():
            inventory[str(path.relative_to(root))] = digest(path)
        else:
            require(path.is_dir(), 'special artifact file')
    return inventory


def offline():
    os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_DATASETS_OFFLINE='1',
                      HF_HUB_DISABLE_TELEMETRY='1', VLLM_NO_USAGE_STATS='1', DO_NOT_TRACK='1',
                      VLLM_WORKER_MULTIPROC_METHOD='spawn', PYTHONDONTWRITEBYTECODE='1')
    sys.dont_write_bytecode = True


def pinned(record):
    require(set(record) == {'path', 'sha256'} and Path(record['path']).is_absolute() and
            digest(record['path']) == record['sha256'], 'input file pin differs')


def load_module(record, name):
    pinned(record)
    specification = importlib.util.spec_from_file_location('real_record_' + name, record['path'])
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


def checked_apis(specification):
    require(specification['runner_sha256'] == digest(SELF), 'formation runner pin differs')
    for key in ('core', 'level1_runtime', 'public', 'protocol', 'binding'):
        pinned(specification[key])
    require(specification['level1_runtime']['sha256'] == LEVEL1_SHA256 and
            specification['public']['sha256'] == PUBLIC_SHA256, 'original helper pin differs')
    source = Path(specification['source'])
    require(source.is_absolute() and not (source / '.git').exists() and
            set(CORE_SOURCES).issubset(specification['source_files']) and
            tree(source) == specification['source_files'], 'new pinned core-dependency source snapshot required')
    helper = load_module(specification['level1_runtime'], 'level1')
    probe = load_module(specification['public'], 'public')
    core = load_module(specification['core'], 'core')
    require(probe.GPU_QUERY_SECONDS == GPU_QUERY_SECONDS, 'original XML query budget differs')
    require(tuple(core.STATES) == STATES and core.MAX_OUTPUT_TOKENS == {'wake': ACTION_TOKENS, 'record': RECORD_TOKENS},
            'core states/token-budget contract differs; Main/Parfit must bind the agreed96/192 version')
    require(all(specification['source_files'].get(name) == checksum for name, checksum in core.PINS.items()),
            'core source dependency pins missing/different')
    return core, helper, probe


def upstream_bindings(specification, helper, binding):
    entries = specification['upstream']
    require(type(entries) is list and len(entries) == 3 and all(type(entry['seed']) is int for entry in entries) and
            sorted(entry['seed'] for entry in entries) == [0, 1, 2] and len({entry['root'] for entry in entries}) == 3,
            'exact three distinct completed perception learners required')
    result = {}
    for entry in entries:
        root = Path(entry['root'])
        require(root.is_absolute() and not root.is_symlink() and not (root / 'controller_failure.json').exists(),
                'failed/nonabsolute upstream root forbidden')
        require(digest(root / 'plan.json') == entry['plan_sha256'] and
                digest(root / 'capture_complete.json') == entry['completion_sha256'], 'upstream plan/completion pin differs')
        plan, complete = read(root / 'plan.json'), read(root / 'capture_complete.json')
        require(plan['root'] == str(root) and plan['self_sha256'] == LEVEL1_SHA256 and plan['scope'] == helper.SCOPE and
                plan['skill'] == 'perception' and type(plan['learner_seed']) is int and plan['learner_seed'] == entry['seed'] and
                plan['model'] == specification['model'] and plan['model_files'] == binding['model_files'],
                'upstream learner/base identity differs')
        require(complete['plan_sha256'] == entry['plan_sha256'] and type(complete['calls']) is int and complete['calls'] == 120 and
                complete['scored'] is False and set(complete['stages']) == {'OFF', 'fit', 'post'}, 'upstream incomplete capture')
        previous = plan['specification']
        require(previous['runner_sha256'] == LEVEL1_SHA256 and previous['skill'] == 'perception' and
                previous['learner_seed'] == entry['seed'] and previous['source_files'] and
                all(specification['source_files'].get(name) == checksum for name, checksum in previous['source_files'].items()),
                'upstream material/source provenance differs')
        pinned(entry['collection'])
        collection_path = Path(entry['collection']['path'])
        require(collection_path.name == 'collection.json' and not (collection_path.parent / 'collection_failure.json').exists(),
                'successful upstream native collection required')
        collection = read(collection_path)
        require(collection['completion_sha256'] == entry['completion_sha256'] and
                digest(collection_path.parent / 'scores.json') == collection['scores_sha256'], 'upstream collected bytes differ')
        claim = read(root.with_name(root.name + '.collection_claim.json'))
        require(claim['plan_sha256'] == entry['plan_sha256'] and Path(claim['out']) == collection_path.parent,
                'upstream one-shot collection claim differs')
        adapter = root / 'run/fit/adapter'
        files = helper.check_adapter(adapter, plan['config'])
        require(files == entry['adapter_files'] and all(complete['stages']['fit'].get('adapter/' + name) == checksum
                for name, checksum in files.items()), 'upstream adapter files differ from completed fit')
        fit_path = root / 'run/fit/fit.json'
        require(digest(fit_path) == complete['stages']['fit']['fit.json'], 'upstream fit receipt differs')
        fit = read(fit_path)
        require(fit['adapter'] == str(adapter) and fit['adapter_files'] == files and fit['updates'] == 320 and
                fit['presentations'] == 1280, 'upstream fit custody differs')
        result['perception_seed' + str(entry['seed'])] = dict(adapter=str(adapter), adapter_files=files,
                root=str(root), plan_sha256=entry['plan_sha256'], completion_sha256=entry['completion_sha256'],
                collection=entry['collection'], scores_sha256=collection['scores_sha256'],
                material_pin=previous['material'], protocol_pin=previous['protocol'], source_files=previous['source_files'])
    return result


def route_for(plan, state):
    require(state in STATES, 'unknown formation state')
    if state == 'OFF':
        return None
    entry = plan['upstream'][state]
    require(tree(entry['adapter']) == entry['adapter_files'], 'bound upstream adapter changed')
    return dict(name='real_record_perception', id=1, path=entry['adapter'])


def validate_response(request, response, route):
    native = request['native']
    require(all(response.get(key) == value for key, value in native.items()) and
            response.get('actual_prompt_token_ids') == native['prompt_token_ids'], 'native prompt/token/system drift')
    tokens = response.get('output_token_ids')
    cap = request['params']['max_tokens']
    require(type(tokens) is list and 0 < len(tokens) <= cap and all(type(token) is int and token >= 0 for token in tokens),
            'native output token count differs')
    require(type(response.get('text')) is str and response['text'] == response.get('decoded_output'), 'exact native output bytes differ')
    require(response.get('finish_reason') in ('stop', 'length') and 'stop_reason' in response and
            (response['finish_reason'] != 'length' or len(tokens) == cap), 'invalid native finish reason/token cap')
    require(response.get('lora_request') == route, 'actual adapter route differs')
    require(all(type(response.get(key)) in (int, float) and math.isfinite(response[key]) for key in ('started', 'ended')) and
            response['ended'] >= response['started'], 'invalid generation timing')


class Native:
    def __init__(self, plan, probe, route):
        from vllm import LLM
        from vllm.lora.request import LoRARequest
        self.probe, self.route = probe, route
        self.llm = LLM(model=plan['model'], tokenizer=plan['model'], **ENGINE)
        self.tokenizer = self.llm.get_tokenizer()
        require(self.tokenizer.chat_template == plan['chat_template'], 'native template drift')
        self.lora = None if route is None else LoRARequest(route['name'], route['id'], route['path'])

    def generate(self, request):
        import torch
        from vllm import SamplingParams
        started = time.monotonic()
        with torch.inference_mode():
            outputs = self.llm.generate([request['native']['rendered_prompt']], SamplingParams(**request['params']),
                                       lora_request=self.lora, use_tqdm=False)
        require(len(outputs) == 1 and len(outputs[0].outputs) == 1, 'native generation cardinality differs')
        output = outputs[0].outputs[0]
        return dict(**request['native'], text=output.text, output_token_ids=list(output.token_ids),
                    actual_prompt_token_ids=list(outputs[0].prompt_token_ids), finish_reason=output.finish_reason,
                    stop_reason=output.stop_reason, decoded_output=self.tokenizer.decode(list(output.token_ids), skip_special_tokens=True),
                    started=started, ended=time.monotonic(), lora_request=self.route)

    def close(self):
        shutdown = getattr(self.llm, 'shutdown', None)
        if shutdown is not None:
            shutdown()


@contextlib.contextmanager
def budget(seconds):
    require(seconds > 0, 'no remaining runtime budget')
    def expired(signum, frame):
        raise TimeoutError('formation runtime deadline exceeded')
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def prepare(root, spec_path, spec_sha256, allow_native=False):
    require(allow_native is True, 'Main-only CPU native tokenizer preflight requires --allow-native')
    offline()
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    require(digest(spec_path) == spec_sha256, 'spec pin differs')
    specification = read(spec_path)
    root = Path(root).resolve()
    require(not root.exists(), 'fresh formation root required; no retry')
    require(type(specification['gpu_index']) is int and specification['gpu_index'] >= 0 and
            type(specification['gpu_uuid']) is str and specification['gpu_uuid'].startswith('GPU-'), 'planned GPU identity required')
    require(type(specification['lease_end']) in (int, float) and math.isfinite(specification['lease_end']) and
            specification['lease_end'] > time.time() + OUTER_SECONDS + COLLECTION_SECONDS + LEASE_MARGIN, 'six-hour lease finish margin required')
    protected = [SELF, spec_path, specification['source'], specification['model']]
    protected += [specification[key]['path'] for key in ('core', 'level1_runtime', 'public', 'protocol', 'binding')]
    protected += [entry['root'] for entry in specification['upstream']]
    protected += [str(Path(entry['collection']['path']).parent) for entry in specification['upstream']]
    require(all(Path(path).is_absolute() and root != Path(path).resolve() and root not in Path(path).resolve().parents and
                Path(path).resolve() not in root.parents for path in protected), 'root must be disjoint from every protected input')
    root.mkdir()
    write(root / 'prepare_started.json', dict(spec_sha256=spec_sha256, time=time.time()))
    try:
        core, helper, probe = checked_apis(specification)
        binding = probe.scope_binding(read(specification['binding']['path']), specification['source'], specification['model'],
                                      specification['source_files']['organism_v6/birth_skill_corpus.py'])
        require(binding['source_files'] == {name: specification['source_files'][name] for name in probe.SOURCE_NAMES} and
                binding['model_files'] == probe.model_hashes(specification['model']) and
                binding['native_environment'] == probe.native_environment(), 'native model/source/environment differs')
        upstream = upstream_bindings(specification, helper, binding)
        dependencies = core.load_dependencies(specification['source'])
        contract = core.contract(dependencies)
        episode_ids = list(core.episode_ids())
        require(len(episode_ids) == EPISODES and len(set(episode_ids)) == EPISODES and
                contract['possible_records_per_state'] == 16 and contract['calls_per_episode'] == {'scheduled_wake': 2, 'maximum_record': 2},
                'fixed episode/formation denominator contract differs')
        tokenizer = probe.native_tokenizer(specification['model'])
        initial = []
        for eid in episode_ids:
            messages = [{'role': 'user', 'content': contract['wake_template'].format(eid=eid, tick=1, earlier_transcript=contract['first_history'])}]
            native = probe.render(tokenizer, messages)
            require(len(native['prompt_token_ids']) + ACTION_TOKENS <= ENGINE['max_model_len'], 'initial wake context exceeded')
            initial.append(dict(episode_id=eid, messages=messages, native=native))
        write(root / 'initial_prompts.json', initial)
        plan = dict(scope=SCOPE, claim=CLAIM, root=str(root), specification=specification, spec_sha256=spec_sha256,
                    self_sha256=digest(SELF), python=os.path.abspath(sys.executable), python_sha256=digest(sys.executable),
                    source=specification['source'], model=specification['model'], binding=binding,
                    model_files=binding['model_files'], environment=helper.environment(probe),
                    gpu_index=specification['gpu_index'], gpu_uuid=specification['gpu_uuid'], lease_end=specification['lease_end'],
                    core_contract=contract, episode_ids=episode_ids, states=list(STATES), engine=ENGINE, params=PARAMS,
                    upstream=upstream, chat_template=tokenizer.chat_template, initial_prompts_sha256=digest(root / 'initial_prompts.json'),
                    budget=dict(controller=OUTER_SECONDS, state=STATE_SECONDS, collection=COLLECTION_SECONDS,
                                cleanup_reserve=CLEANUP_SECONDS, calls_per_state=CALLS_PER_STATE, calls_total=MAX_CALLS,
                                wake_tokens=ACTION_TOKENS, record_tokens=RECORD_TOKENS))
        checked_apis(specification)
        write(root / 'plan.json', plan)
        return dict(status='CPU_NATIVE_PREFLIGHT_COMPLETE_NOT_GPU_APPROVAL', plan_sha256=digest(root / 'plan.json'), budget=plan['budget'])
    except BaseException as error:
        failure(root / 'prepare_failure.json', error)
        raise


def verify(root, plan_sha256, native=False):
    root = Path(root).resolve()
    require(digest(root / 'plan.json') == plan_sha256, 'formation plan pin differs')
    plan = read(root / 'plan.json')
    require(plan['root'] == str(root) and plan['scope'] == SCOPE and plan['claim'] == CLAIM and
            plan['self_sha256'] == digest(SELF) and plan['python'] == os.path.abspath(sys.executable) and
            plan['python_sha256'] == digest(sys.executable), 'formation runtime/interpreter identity differs')
    require(plan['states'] == list(STATES) and plan['engine'] == ENGINE and plan['params'] == PARAMS and
            read(root / 'prepare_started.json')['spec_sha256'] == plan['spec_sha256'] and
            not (root / 'prepare_failure.json').exists(), 'prepared state/configuration differs')
    require(digest(root / 'initial_prompts.json') == plan['initial_prompts_sha256'], 'prepared tokenizer evidence differs')
    core, helper, probe = checked_apis(plan['specification'])
    for field in ('source', 'model', 'gpu_index', 'gpu_uuid', 'lease_end'):
        require(plan[field] == plan['specification'][field], 'spec/plan differs: ' + field)
    dependencies = core.load_dependencies(plan['source'])
    require(core.contract(dependencies) == plan['core_contract'] and list(core.episode_ids()) == plan['episode_ids'], 'core contract drift')
    require(upstream_bindings(plan['specification'], helper, plan['binding']) == plan['upstream'], 'upstream provenance changed')
    if native:
        require(helper.environment(probe) == plan['environment'] and probe.model_hashes(plan['model']) == plan['model_files'],
                'native model/environment drift')
    return plan, core, dependencies, probe


class NativeCaptureFailure(BaseException):
    """Abort infrastructure failures instead of letting core record a backend refusal."""


def capture_state(plan, state, core, dependencies, probe):
    directory = Path(plan['root']) / 'run' / state
    route = route_for(plan, state)
    identity = dict(state=state, model=plan['model'], model_files=plan['model_files'], lora_request=route,
                    upstream=None if state == 'OFF' else plan['upstream'][state], engine=ENGINE, params=PARAMS)
    write(directory / 'identity.json', identity)
    backend, requests, responses = None, [], []
    try:
        backend = Native(plan, probe, route)
        def generate(core_request):
            try:
                kind = core_request['kind']
                require(kind in ('wake', 'record') and core_request['state'] == state and
                        core_request['episode_id'] in plan['episode_ids'] and type(core_request['tick']) is int and
                        core_request['tick'] in (1, 2), 'core callback source identity differs')
                cap = ACTION_TOKENS if kind == 'wake' else RECORD_TOKENS
                require(core_request['max_output_tokens'] == cap and type(core_request['max_output_tokens']) is int,
                        'core callback output cap differs')
                require(len(requests) < CALLS_PER_STATE and not any((previous['core_request']['episode_id'], previous['core_request']['tick'],
                        previous['core_request']['kind']) == (core_request['episode_id'], core_request['tick'], kind)
                        for previous in requests), 'extra/duplicate formation call')
                messages = core_request['input_messages']
                native = probe.render(backend.tokenizer, messages)
                require(len(native['prompt_token_ids']) + cap <= ENGINE['max_model_len'], 'dynamic sequential context exceeded')
                request = dict(call_id=f'{len(requests):02d}', core_request=core_request, messages=messages,
                               native=native, params=dict(PARAMS, max_tokens=cap), lora_request=route)
                write(directory / (request['call_id'] + '.request.json'), request)
                requests.append(request)
                response = backend.generate(request)
                write(directory / (request['call_id'] + '.response.json'), response)
                validate_response(request, response, route)
                responses.append(response)
                return dict(request_id=core_request['request_id'], state=state, raw=response['text'],
                            finish_reason=response['finish_reason'], native_response=response)
            except Exception as error:
                raise NativeCaptureFailure(type(error).__name__ + ': ' + str(error)) from error
        capture = core.run_state(state, generate, dependencies=dependencies,
                                 binding=dict(kind='pinned_native_capture', identity=identity))
        require(len(requests) == len(responses) and 16 <= len(requests) <= CALLS_PER_STATE and
                sum(request['core_request']['kind'] == 'wake' for request in requests) == 16,
                'actual formation call accounting differs')
        audit = core.audit_capture(capture, dependencies=dependencies)
        require(audit['calls_replayed'] == len(requests), 'core capture/native call accounting differs')
        write(directory / 'formation.json', capture)
    finally:
        if backend is not None:
            backend.close()
    require(route_for(plan, state) == route, 'upstream adapter changed during formation')
    names = ['identity.json', 'formation.json'] + [request['call_id'] + suffix for request in requests for suffix in ('.request.json', '.response.json')]
    write(directory / 'closed.json', dict(calls=len(requests), wake_calls=16, record_calls=len(requests) - 16,
                files={name: digest(directory / name) for name in names},
                prompt_tokens=sum(len(response['actual_prompt_token_ids']) for response in responses),
                output_tokens=sum(len(response['output_token_ids']) for response in responses),
                generation_seconds=sum(response['ended'] - response['started'] for response in responses)))


def worker(root, plan_sha256, state, allow_gpu=False):
    require(allow_gpu is True and state in STATES and os.getpid() == os.getpgrp(), 'Main-only isolated formation worker required')
    offline()
    plan, core, dependencies, probe = verify(root, plan_sha256, native=True)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == plan['gpu_uuid'] and
            time.time() < plan['lease_end'] - COLLECTION_SECONDS - LEASE_MARGIN, 'worker device/lease differs')
    directory = Path(root) / 'run' / state
    write(directory / 'started.json', dict(pid=os.getpid(), pgid=os.getpgrp(), state=state, plan_sha256=plan_sha256))
    try:
        capture_state(plan, state, core, dependencies, probe)
    except BaseException as error:
        failure(directory / 'failure.json', error)
        raise


def run_state(plan, pin, state, deadline, probe):
    require(deadline - time.monotonic() > GPU_QUERY_SECONDS + CLEANUP_SECONDS, 'insufficient time for vacancy/release')
    require(probe.gpu_state(plan) is True, 'assigned GPU not vacant; no foreign process will be stopped')
    seconds = min(STATE_SECONDS, deadline - time.monotonic() - CLEANUP_SECONDS)
    require(seconds > 0, 'insufficient controller budget')
    directory = Path(plan['root']) / 'run' / state
    directory.mkdir()
    command = [plan['python'], '-B', str(SELF), 'worker', '--root', plan['root'], '--plan-sha256', pin,
               '--state', state, '--allow-gpu']
    process = None
    try:
        with (directory / 'stdout.log').open('xb') as output, (directory / 'stderr.log').open('xb') as errors:
            process = subprocess.Popen(command, env=dict(os.environ, CUDA_VISIBLE_DEVICES=plan['gpu_uuid']),
                                       stdout=output, stderr=errors, start_new_session=True)
            write(directory / 'launch.json', dict(pid=process.pid, pgid=process.pid, state=state, plan_sha256=pin))
            require(process.wait(timeout=seconds) == 0, 'native formation worker failed')
    finally:
        if process is not None:
            try:
                probe.cleanup(process)
                require(not probe.group_alive(process.pid), 'owned process group survived cleanup')
                require(probe.gpu_state(plan) is True, 'GPU release not confirmed')
                write(directory / 'released.json', dict(pid=process.pid, pgid=process.pid))
            except BaseException as error:
                failure(directory / 'cleanup_failure.json', error)
                raise


def validate_completed(plan, pin, core, dependencies):
    root = Path(plan['root'])
    inventory, captures, costs, processes = {}, [], {}, []
    for state in STATES:
        directory = root / 'run' / state
        require(not (directory / 'failure.json').exists() and not (directory / 'cleanup_failure.json').exists(), 'failed formation state')
        started, launch, released = (read(directory / name) for name in ('started.json', 'launch.json', 'released.json'))
        require(type(started['pid']) is int and started['pid'] > 1 and started['pid'] == started['pgid'] == launch['pid'] ==
                launch['pgid'] == released['pid'] == released['pgid'] and started['state'] == launch['state'] == state and
                started['plan_sha256'] == launch['plan_sha256'] == pin, 'fresh state process receipts differ')
        processes.append(started['pid'])
        route = route_for(plan, state)
        identity = read(directory / 'identity.json')
        require(identity == dict(state=state, model=plan['model'], model_files=plan['model_files'], lora_request=route,
                    upstream=None if state == 'OFF' else plan['upstream'][state], engine=ENGINE, params=PARAMS), 'state identity differs')
        closed = read(directory / 'closed.json')
        count = closed['calls']
        require(type(count) is int and 16 <= count <= CALLS_PER_STATE and closed['wake_calls'] == 16 and
                type(closed['record_calls']) is int and closed['record_calls'] == count - 16, 'formation call total differs')
        names = {'identity.json', 'formation.json'} | {f'{index:02d}' + suffix for index in range(count)
                                                      for suffix in ('.request.json', '.response.json')}
        require(set(closed['files']) == names and {path.name for path in directory.glob('*.response.json')} ==
                {f'{index:02d}.response.json' for index in range(count)} and
                {path.name for path in directory.glob('*.request.json')} == {f'{index:02d}.request.json' for index in range(count)},
                'raw formation inventory differs')
        for name, checksum in closed['files'].items():
            require(digest(directory / name) == checksum, 'closed native capture bytes changed')
        capture = read(directory / 'formation.json')
        require(capture['state'] == state and capture['contract'] == plan['core_contract'] and
                capture['binding'] == dict(kind='pinned_native_capture', identity=identity), 'core/native binding differs')
        audit = core.audit_capture(capture, dependencies=dependencies)
        calls = [event for event in capture['events'] if event['kind'] == 'call']
        require(audit['calls_replayed'] == len(calls) == count, 'core/native capture count differs')
        prompt_tokens, output_tokens, seconds, wakes = 0, 0, 0., 0
        for index, event in enumerate(calls):
            request = read(directory / f'{index:02d}.request.json')
            response = read(directory / f'{index:02d}.response.json')
            core_request = request['core_request']
            require(request['call_id'] == f'{index:02d}' and core_request == event['request'] and
                    request['messages'] == core_request['input_messages'] and request['lora_request'] == route,
                    'core/native request join differs')
            cap = ACTION_TOKENS if core_request['kind'] == 'wake' else RECORD_TOKENS
            require(core_request['kind'] in ('wake', 'record') and core_request['max_output_tokens'] == cap and
                    request['params'] == dict(PARAMS, max_tokens=cap), 'recorded generation settings differ')
            require(len(request['native']['prompt_token_ids']) + cap <= ENGINE['max_model_len'], 'recorded dynamic context exceeds cap')
            validate_response(request, response, route)
            require(event['response'] == dict(request_id=core_request['request_id'], state=state, raw=response['text'],
                    finish_reason=response['finish_reason'], native_response=response), 'core output not exact native response')
            prompt_tokens += len(response['actual_prompt_token_ids'])
            output_tokens += len(response['output_token_ids'])
            seconds += response['ended'] - response['started']
            wakes += core_request['kind'] == 'wake'
        require(wakes == 16 and closed['prompt_tokens'] == prompt_tokens and closed['output_tokens'] == output_tokens and
                closed['generation_seconds'] == seconds, 'actual native cost accounting differs')
        costs[state] = {key: closed[key] for key in ('calls', 'wake_calls', 'record_calls', 'prompt_tokens', 'output_tokens', 'generation_seconds')}
        inventory[state] = tree(directory)
        captures.append(capture)
    require(len(set(processes)) == 4 and sum(cost['calls'] for cost in costs.values()) <= MAX_CALLS,
            'four isolated state processes/128-call ceiling required')
    return inventory, captures, costs


def controller(root, plan_sha256, allow_gpu=False):
    require(allow_gpu is True, 'Main-only formation controller requires --allow-gpu')
    offline()
    root = Path(root).resolve()
    write(root / 'controller_started.json', dict(time=time.time(), plan_sha256=plan_sha256))
    deadline = time.monotonic() + OUTER_SECONDS
    try:
        with budget(OUTER_SECONDS - CLEANUP_SECONDS):
            plan, core, dependencies, probe = verify(root, plan_sha256, native=True)
            require(plan['lease_end'] > time.time() + OUTER_SECONDS + COLLECTION_SECONDS + LEASE_MARGIN, 'formation no longer fits lease')
            (root / 'run').mkdir()
            for state in STATES:
                run_state(plan, plan_sha256, state, deadline, probe)
            inventory, captures, costs = validate_completed(plan, plan_sha256, core, dependencies)
            require(time.monotonic() < deadline, 'formation controller exceeded total runtime')
            write(root / 'capture_complete.json', dict(plan_sha256=plan_sha256, stages=inventory,
                    calls=sum(cost['calls'] for cost in costs.values()), possible_records_per_state=16,
                    elapsed_seconds=OUTER_SECONDS - (deadline - time.monotonic()), formation_only=True,
                    upstream_unchanged=True, automatic_pass=False))
        return dict(status='FORMATION_CAPTURE_COMPLETE_NO_LEARNING_CLAIM', completion_sha256=digest(root / 'capture_complete.json'))
    except BaseException as error:
        failure(root / 'controller_failure.json', error)
        raise


def collect(root, plan_sha256, completion_sha256, out):
    offline()
    root, out = Path(root).resolve(), Path(out).resolve()
    require(not out.exists() and root != out and root not in out.parents and out not in root.parents, 'fresh external collection required')
    write(root.with_name(root.name + '.collection_claim.json'), dict(plan_sha256=plan_sha256, out=str(out), retry=False))
    out.mkdir()
    try:
        with budget(COLLECTION_SECONDS):
            plan, core, dependencies, probe = verify(root, plan_sha256)
            require(not (root / 'controller_failure.json').exists() and digest(root / 'capture_complete.json') == completion_sha256,
                    'failed or unbound formation capture cannot collect')
            complete = read(root / 'capture_complete.json')
            require(complete['plan_sha256'] == plan_sha256 and complete['formation_only'] is True, 'completion identity differs')
            inventory, captures, costs = validate_completed(plan, plan_sha256, core, dependencies)
            require(inventory == complete['stages'] and complete['calls'] == sum(cost['calls'] for cost in costs.values()),
                    'completed custody/call total differs')
            comparison = core.compare_states(captures, dependencies=dependencies)
            report = dict(scope=SCOPE, claim=CLAIM, plan_sha256=plan_sha256, completion_sha256=completion_sha256,
                          comparison=comparison, native_capture_custody_checked=True, costs=costs, upstream=plan['upstream'],
                          core=plan['specification']['core'], protocol=plan['specification']['protocol'],
                          source_files=plan['specification']['source_files'], model_files=plan['model_files'],
                          controller_elapsed_seconds=complete['elapsed_seconds'], automatic_pass=False, scientific_pass=None,
                          interpretation='Core CPU replay checks formation consistency; native provenance is separately bound by this wrapper. '
                                         'No model is called during collection, no readout-score endpoint or learning claim.')
            write(out / 'formation_report.json', report)
            write(out / 'collection.json', dict(formation_report_sha256=digest(out / 'formation_report.json'), completion_sha256=completion_sha256))
            return dict(status='COLLECTED_FORMATION_ONLY', out=str(out), formation_report_sha256=digest(out / 'formation_report.json'))
    except BaseException as error:
        failure(out / 'collection_failure.json', error)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare_parser = commands.add_parser('prepare')
    for name in ('root', 'spec-path', 'spec-sha256'):
        prepare_parser.add_argument('--' + name, required=True)
    prepare_parser.add_argument('--allow-native', action='store_true')
    for name in ('controller', 'worker', 'collect'):
        command = commands.add_parser(name)
        command.add_argument('--root', required=True)
        command.add_argument('--plan-sha256', required=True)
        if name != 'collect':
            command.add_argument('--allow-gpu', action='store_true')
        if name == 'worker':
            command.add_argument('--state', choices=STATES, required=True)
        if name == 'collect':
            command.add_argument('--completion-sha256', required=True)
            command.add_argument('--out', required=True)
    arguments = vars(parser.parse_args(argv))
    name = arguments.pop('command')
    result = {'prepare': prepare, 'controller': controller, 'worker': worker, 'collect': collect}[name](**arguments)
    if result is not None:
        print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
