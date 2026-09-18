"""One-shot synthetic HF profile; never imports a live child or loads its state."""

import argparse
import ast
from dataclasses import dataclass
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import signal
import socket
import stat
import subprocess
import time
from types import SimpleNamespace
from uuid import UUID


SCHEMA = 'R177_SYNTHETIC_GENERATION_PROFILE_V1'
MODEL_ID = 'Qwen/Qwen2.5-7B-Instruct'
REVISION = 'a09a35458c702b33eeacc393d103063234e8bc28'
GPU_UUID = 'GPU-06b31c8f-7a96-d812-23f3-df3444d95397'
HOST_SHA256 = 'e376292376f9f56a83e1255021f5b1a4249f1afdff42b5aed3cad36a9635834b'
LEASE = Path('/localhome/local-rohing/orch_rich_hot_node1_20260915_attempt1/LEASE.json')
LEASE_SHA256 = 'ac20665cb03ba0e2f8eebb0f7e441383334fbbf20b4a4e7125757ce7413ea8e6'
HARD_END = 1789754400
PYTHON = '/localhome/local-rohing/v2/venv/bin/python'
MODEL = Path('/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots') / REVISION
SCOPE = Path('research_loop/workers/r177_caption_game_stage1_20260917/generation_profile')
SEED = 170171
DECODER = dict(temperature=0.7, top_p=0.95, repetition_penalty=1.05, no_repeat_ngram_size=16)
SOURCE_FILES = (
    'gpu/ny_caption_generation_profile.py',
    'tests/test_ny_caption_generation_profile.py',
    'gpu/orch_r125_continual_native.py',
    'gpu/orch_r125_stream_journal.py',
    'gpu/astra_pchain2_native.py',
    'organism_v6/orch_r124_train_history.py',
    'organism_v6/orch_r125_continual_stream.py',
    'organism_v6/orch_r125_plain_context.py',
)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def file_hash(path):
    hasher = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b''):
            hasher.update(chunk)
    return hasher.hexdigest()


def immutable(path, value):
    raw = encoded(value) + b'\n'
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o444)
    with os.fdopen(descriptor, 'wb') as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    parent = os.open(Path(path).parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(parent)
    finally:
        os.close(parent)
    return hashlib.sha256(raw).hexdigest()


def receipt(root, name, **fields):
    return immutable(root / name, dict(schema=SCHEMA, observed_unix=time.time(), **fields))


def scoped_root(path):
    root = Path(path).absolute()
    components = root.parts
    scope_parts = SCOPE.parts
    within_scope = any(components[index:index + len(scope_parts)] == scope_parts for index in range(len(components)))
    require(root == root.resolve() and within_scope and root.is_dir(), 'canonical_owned_profile_root')
    return root


def token_counts(rows, prompt_width, eos_ids, pad_id):
    counts = []
    for row in rows:
        continuation = row[prompt_width:]
        stop = next((index + 1 for index, token in enumerate(continuation) if token in eos_ids), None)
        if stop is None:
            stop = len(continuation)
            require(pad_id not in continuation, 'padding_without_EOS_is_ambiguous')
        counts.append(stop)
    return counts


def rates(counts, seconds):
    require(counts and all(type(count) is int and count > 0 for count in counts), 'actual_positive_token_counts')
    require(math.isfinite(seconds) and seconds > 0, 'positive_finite_wall')
    return dict(actual_tokens_per_life=counts, per_life_tokens_per_second=[count / seconds for count in counts],
                aggregate_tokens_per_second=sum(counts) / seconds, seconds=seconds)


def cuda_identity(value):
    raw = value.bytes
    require(isinstance(raw, (bytes, list, tuple)) and len(raw) == 16 and
            all(type(part) is int and 0 <= part <= 255 for part in raw), 'actual_16_byte_CUDA_UUID')
    normalized = 'GPU-' + str(UUID(bytes=bytes(raw)))
    return dict(raw_text=str(value), raw_bytes=list(raw), normalized_uuid=normalized,
                expected_uuid=GPU_UUID, matches=normalized == GPU_UUID)


def extracted(source, name, *, parent=None, namespace=None, remove_import=False):
    tree = ast.parse(Path(source).read_text())
    container = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == parent) if parent else tree
    node = next(node for node in container.body if getattr(node, 'name', None) == name)
    if remove_import:
        node.body = [part for part in node.body if not isinstance(part, ast.ImportFrom)]
    module = ast.Module(body=[node], type_ignores=[])
    bindings = dict(namespace or {})
    exec(compile(module, str(source), 'exec'), bindings)
    return bindings[name]


def prepare(root):
    root = scoped_root(root)
    repository = Path(__file__).resolve().parents[1]
    pins = {}
    for name in SOURCE_FILES:
        source = repository / name
        destination = root / 'source' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as handle:
            handle.write(source.read_bytes())
        destination.chmod(0o444)
        pins[name] = file_hash(destination)
    receipt(root, 'SOURCE_PINS.json', files=pins, model_id=MODEL_ID, model_revision=REVISION,
            input_policy='Public frozen base plus seed-created rank8 fixture only; no existing child data/state reads.')


def verify_sources(root):
    pins = json.loads((root / 'SOURCE_PINS.json').read_text())['files']
    require(set(pins) == set(SOURCE_FILES), 'exact_source_allowlist')
    for name, expected in pins.items():
        require(file_hash(root / 'source' / name) == expected, 'source_pin:' + name)
    return pins


def command(arguments, timeout=30):
    return subprocess.check_output(arguments, text=True, timeout=timeout).strip()


def device_mapping():
    require(hashlib.sha256(socket.gethostname().encode()).hexdigest() == HOST_SHA256, 'exact_node4_host')
    mappings = {}
    for path in Path('/proc/driver/nvidia/gpus').glob('*/information'):
        fields = dict(line.split(':', 1) for line in path.read_text().splitlines() if ':' in line)
        mappings[fields['GPU UUID'].strip()] = int(fields['Device Minor'].strip())
    require(len(mappings) == 8 and GPU_UUID in mappings, 'eight_kernel_UUID_minor_mappings')
    minor = mappings[GPU_UUID]
    metadata = Path('/dev/nvidia' + str(minor)).lstat()
    require(stat.S_ISCHR(metadata.st_mode) and os.major(metadata.st_rdev) == 195 and
            os.minor(metadata.st_rdev) == minor, 'actual_GPU_character_device')
    return minor


def scan_owners(minor):
    require(os.geteuid() == 0, 'privileged_complete_descriptor_scan')
    owners, unreadable = [], []
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            for descriptor in (process / 'fd').iterdir():
                try:
                    metadata = descriptor.stat()
                    if stat.S_ISCHR(metadata.st_mode) and os.major(metadata.st_rdev) == 195 and os.minor(metadata.st_rdev) == minor:
                        owners.append(dict(pid=int(process.name), fd=int(descriptor.name)))
                except FileNotFoundError:
                    continue
        except (FileNotFoundError, ProcessLookupError):
            continue
        except PermissionError:
            unreadable.append(int(process.name))
    require(not unreadable, 'complete_root_proc_scan_required')
    return owners


def admit(root):
    minor = device_mapping()
    require(file_hash(LEASE) == LEASE_SHA256, 'unchanged_existing_lease_authority')
    lease = json.loads(LEASE.read_text())
    require(lease['no_extension_or_new_onboarding'] is True and time.time() + 1200 + 300 < HARD_END,
            'conservative_lease_wall_with_headroom')
    inventory = command(['nvidia-smi', '--query-gpu=index,uuid,memory.total,memory.used,utilization.gpu', '--format=csv,noheader,nounits'])
    row = next(line.split(', ') for line in inventory.splitlines() if GPU_UUID in line)
    require(row[0] == '6' and int(row[2]) >= 45000 and int(row[3]) == 0 and int(row[4]) == 0, 'physical6_idle_capacity')
    apps = command(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid,used_gpu_memory', '--format=csv,noheader'])
    require(GPU_UUID not in apps, 'no_existing_compute_owner')
    owners = scan_owners(minor)
    require(not owners, 'no_existing_UUID_minor_descriptor_owner')
    receipt(root, 'ADMISSION.json', minor=minor, physical=6, gpu_uuid=GPU_UUID, host_sha256=HOST_SHA256,
            inventory=inventory, compute_metadata=apps, owners=owners, scanner_euid=os.geteuid(),
            lease_sha256=LEASE_SHA256, conservative_hard_end_unix=HARD_END, lease_extended=False)
    return minor


def containment_command(root, minor, unit, uid, gid):
    require(type(minor) is int and 0 <= minor <= 7 and uid > 0 and gid > 0, 'nonroot_exact_minor')
    properties = dict(User=str(uid), Group=str(gid), DevicePolicy='strict', NoNewPrivileges='yes',
                      CapabilityBoundingSet='', AmbientCapabilities='', ProtectControlGroups='yes',
                      ProtectSystem='strict', ReadWritePaths=str(root), WorkingDirectory=str(root),
                      RuntimeMaxSec='1100', TimeoutStopSec='5', KillMode='control-group',
                      TasksMax='128', MemoryMax='64G', MemorySwapMax='0')
    devices = ['/dev/null rw', '/dev/zero rw', '/dev/random r', '/dev/urandom r',
               '/dev/nvidiactl rw', '/dev/nvidia-uvm rw', '/dev/nvidia' + str(minor) + ' rw']
    cache = root / 'cache'
    environment = dict(PATH='/usr/bin:/bin', HOME=str(root), PYTHONDONTWRITEBYTECODE='1',
                       PYTHONPATH=str(root / 'source'), CUDA_VISIBLE_DEVICES=GPU_UUID,
                       HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', HF_HOME=str(cache / 'hf'),
                       XDG_CACHE_HOME=str(cache), TORCHINDUCTOR_CACHE_DIR=str(cache / 'inductor'),
                       CUDA_CACHE_PATH=str(cache / 'cuda'), TMPDIR=str(root / 'tmp'),
                       OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', TOKENIZERS_PARALLELISM='false',
                       CUBLAS_WORKSPACE_CONFIG=':4096:8', PROFILE_UNIT=unit)
    return ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe', '--unit=' + unit,
            *['--property=' + key + '=' + value for key, value in properties.items()],
            '--property=DeviceAllow=', *['--property=DeviceAllow=' + device for device in devices],
            '/usr/bin/env', '-i', *[key + '=' + value for key, value in environment.items()],
            PYTHON, '-B', str(root / 'source/gpu/ny_caption_generation_profile.py'), 'run', '--root', str(root)]


def launch(root):
    verify_sources(root)
    gate = json.loads((root / 'BUILDER_GATE.json').read_text())
    require(gate['cpu_tests_passed'] is True and gate['source_pins_sha256'] == file_hash(root / 'SOURCE_PINS.json'),
            'CPU_and_provenance_Builder_gate')
    receipt(root, 'ATTEMPT.json', max_runtime_seconds=1100, max_attempts=1,
            authorization=gate.get('authority', 'Rohin170/171; Main physical6 standalone profile'),
            builder_gate_sha256=file_hash(root / 'BUILDER_GATE.json'))
    command(['sudo', '-n', PYTHON, '-B', str(root / 'source/gpu/ny_caption_generation_profile.py'), 'admit', '--root', str(root)], timeout=60)
    admission = json.loads((root / 'ADMISSION.json').read_text())
    require(0 <= time.time() - admission['observed_unix'] < 60, 'fresh_admission')
    unit = 'r177-caption-profile-' + str(int(time.time()))
    arguments = containment_command(root, admission['minor'], unit, os.getuid(), os.getgid())
    receipt(root, 'LAUNCH.json', unit=unit, command=arguments, source_pins_sha256=file_hash(root / 'SOURCE_PINS.json'))
    with (root / 'SERVICE.log').open('xb') as output:
        result = subprocess.run(arguments, stdout=output, stderr=subprocess.STDOUT, timeout=1140)
    receipt(root, 'SERVICE_EXIT.json', returncode=result.returncode, completed=(root / 'COMPLETE.json').exists())
    require(result.returncode == 0, 'profile_failed_preserve_no_retry')


def verify_confinement(root):
    minor = device_mapping()
    require(os.getuid() > 0 and os.environ.get('CUDA_VISIBLE_DEVICES') == GPU_UUID, 'nonroot_single_UUID')
    unit = os.environ['PROFILE_UNIT']
    require(Path('/proc/self/cgroup').read_text().strip() == '0::/system.slice/' + unit + '.service', 'exact_cgroup')
    settings = command(['systemctl', 'show', unit, '-p', 'DevicePolicy', '-p', 'DeviceAllow', '-p', 'RuntimeMaxUSec', '-p', 'ProtectSystem'])
    require('DevicePolicy=strict' in settings and 'ProtectSystem=strict' in settings, 'actual_strict_device_and_write_policy')
    for descriptor in Path('/proc/self/fd').iterdir():
        try:
            require(not os.readlink(descriptor).startswith('/dev/nvidia'), 'no_inherited_GPU_descriptors')
        except FileNotFoundError:
            continue
    denied = []
    for other in range(8):
        if other == minor:
            continue
        try:
            descriptor = os.open('/dev/nvidia' + str(other), os.O_RDWR | os.O_CLOEXEC)
        except PermissionError:
            denied.append(other)
        else:
            os.close(descriptor)
            raise ValueError('foreign_minor_not_denied')
    descriptor = os.open('/dev/nvidia' + str(minor), os.O_RDWR | os.O_CLOEXEC)
    os.close(descriptor)
    receipt(root, 'CONFINEMENT.json', minor=minor, gpu_uuid=GPU_UUID, denied_foreign_minors=denied,
            actual_systemd_settings=settings, pid=os.getpid(), cvd_is_not_the_confinement=True)


def timed(callback, synchronize=lambda: None):
    synchronize()
    started = time.perf_counter()
    value = callback()
    synchronize()
    return value, time.perf_counter() - started


class ForwardTimer:
    def __init__(self, model, torch):
        self.torch = torch
        self.events = []
        self.handles = [model.register_forward_pre_hook(self.before), model.register_forward_hook(self.after)]

    def before(self, module, arguments):
        start = self.torch.cuda.Event(enable_timing=True)
        end = self.torch.cuda.Event(enable_timing=True)
        start.record()
        self.events.append((start, end))

    def after(self, module, arguments, output):
        self.events[-1][1].record()

    def finish(self):
        for handle in self.handles:
            handle.remove()
        self.torch.cuda.synchronize()
        elapsed = [start.elapsed_time(end) / 1000 for start, end in self.events]
        require(bool(elapsed), 'actual_model_forward_events')
        return dict(prefill_cuda_seconds=elapsed[0], decode_forward_cuda_seconds=sum(elapsed[1:]),
                    forward_calls=len(elapsed), decode_steps=max(0, len(elapsed) - 1),
                    model_forward_cuda_seconds=sum(elapsed), instrumentation='CUDA events; deferred synchronization, no logits retained')


def synthetic_messages(tokenizer, target):
    prefix = [dict(role='system', content='Synthetic throughput fixture. Continue the artificial symbol sequence; no real-world task.'),
              dict(role='user', content='Synthetic symbols:')]
    base = len(tokenizer.apply_chat_template(prefix, tokenize=True, add_generation_prompt=True, return_dict=False))
    prefix[1]['content'] += ' synthetic' * (target - base)
    actual = len(tokenizer.apply_chat_template(prefix, tokenize=True, add_generation_prompt=True, return_dict=False))
    require(actual == target, 'exact_synthetic_prompt_token_budget')
    return prefix


def fixture_hash(model, torch):
    hasher = hashlib.sha256()
    for name, parameter in sorted(model.named_parameters()):
        if '.lora_' in name:
            hasher.update(encoded([name, list(parameter.shape), str(parameter.dtype)]))
            hasher.update(parameter.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes())
    return hasher.hexdigest()


@dataclass(frozen=True)
class EncodedRow:
    input_ids: tuple
    labels: tuple
    target_ids: tuple


def profile(root):
    started = time.perf_counter()
    receipt(root, 'RUN_STARTED.json', pid=os.getpid(), one_attempt=True)

    def deadline(signum, frame):
        raise TimeoutError('bounded_single_profile_deadline')

    signal.signal(signal.SIGALRM, deadline)
    signal.signal(signal.SIGTERM, deadline)
    signal.alarm(1040)
    verify_sources(root)
    verify_confinement(root)
    import torch
    import transformers
    from peft import LoraConfig, get_peft_model
    from organism_v6.orch_r124_train_history import TrainHistory
    from organism_v6.orch_r125_plain_context import VERSION
    from gpu.orch_r125_stream_journal import StreamJournal

    torch.set_num_threads(2)
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    require(torch.cuda.device_count() == 1, 'one_confined_CUDA_device')
    properties = torch.cuda.get_device_properties(0)
    identity = cuda_identity(properties.uuid)
    receipt(root, 'CUDA_IDENTITY.json', **identity)
    require(identity['matches'], 'actual_CUDA_UUID')
    inventory = {}
    index = json.loads((MODEL / 'model.safetensors.index.json').read_text())
    model_files = set(index['weight_map'].values()) | {'config.json', 'generation_config.json', 'tokenizer.json',
                  'tokenizer_config.json', 'vocab.json', 'merges.txt', 'model.safetensors.index.json'}
    for name in sorted(model_files):
        inventory[name] = dict(sha256=file_hash(MODEL / name), size=(MODEL / name).stat().st_size)
        if name.endswith('.safetensors'):
            require(inventory[name]['sha256'] == (MODEL / name).resolve().name, 'public_LFS_content_sha256')
    receipt(root, 'MODEL_PROVENANCE.json', model_id=MODEL_ID, revision=REVISION, files=inventory,
            versions={name: importlib.metadata.version(name) for name in ('torch', 'transformers', 'peft', 'safetensors')},
            physical=6, gpu_uuid=GPU_UUID, dtype='bfloat16', attention='sdpa', seed=SEED, decoder=DECODER,
            quantization=False, compilation=False, tf32=False, warm_KV_reuse=False,
            deterministic_algorithms=torch.are_deterministic_algorithms_enabled(),
            sdpa_backends=dict(flash=torch.backends.cuda.flash_sdp_enabled(),
                               efficient=torch.backends.cuda.mem_efficient_sdp_enabled(), math=torch.backends.cuda.math_sdp_enabled()))
    tokenizer, tokenizer_load = timed(lambda: transformers.AutoTokenizer.from_pretrained(MODEL, local_files_only=True, trust_remote_code=False))
    base, base_load = timed(lambda: transformers.AutoModelForCausalLM.from_pretrained(MODEL, local_files_only=True,
                              trust_remote_code=False, dtype=torch.bfloat16, attn_implementation='sdpa').to('cuda:0'), torch.cuda.synchronize)
    base.requires_grad_(False)
    model = get_peft_model(base, LoraConfig(r=8, lora_alpha=16, lora_dropout=0.0, bias='none',
                               task_type='CAUSAL_LM', target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj']))
    model.requires_grad_(False)
    model.eval()
    initial_hash = fixture_hash(model, torch)
    receipt(root, 'MODEL_LOAD.json', tokenizer_load_seconds=tokenizer_load, base_load_seconds=base_load,
            adapter_sha256=initial_hash, fixture='Seed-created untrained rank8 LoRA; initialized B=0; no saved adapter',
            lora_config=dict(rank=8, alpha=16, dropout=0, target_modules=['q_proj', 'k_proj', 'v_proj', 'o_proj']),
            all_parameters_frozen_for_generation=not any(parameter.requires_grad for parameter in model.parameters()))
    native_source = root / 'source/gpu/orch_r125_continual_native.py'
    tree = ast.parse(native_source.read_text())
    owner = next(node.name for node in tree.body if isinstance(node, ast.ClassDef) and
                 any(getattr(part, 'name', None) == 'generate' for part in node.body))
    native_generate = extracted(native_source, 'generate', parent=owner,
                               namespace=dict(require=require, digest=digest, BASE_SHA256=digest(inventory)))
    encode_own = extracted(native_source, 'encode_own', remove_import=True,
                           namespace=dict(require=require, EncodedRow=EncodedRow))
    life = SimpleNamespace(torch=torch, tokenizer=tokenizer, engine=SimpleNamespace(model=model, transformers=transformers),
            plan=dict(hard_end_unix=time.time() + 900, context_limit=16384, decoder=DECODER),
            adapter_hash=lambda: fixture_hash(model, torch), check=lambda label: require(time.perf_counter() - started < 1030, 'bounded_profile_wall'))
    trials = []
    sleep_fixture = None
    for prompt_size in (2048, 12288):
        messages = synthetic_messages(tokenizer, prompt_size)
        presentation = dict(version=VERSION, system_prompt=messages[0]['content'], birth_prompt=messages[1]['content'])
        history = TrainHistory(system_prompt=messages[0]['content'], birth_prompt=messages[1]['content'])
        for batch_size in (1, 2):
            for phase, budget in (('shape_first', 256), ('excluded_warmup', 8), ('warm', 256), ('shape_first', 512), ('warm', 512)):
                life.check('trial')
                torch.manual_seed(SEED)
                torch.cuda.manual_seed_all(SEED)
                torch.cuda.synchronize()
                wall_started = time.perf_counter()
                rendered, render_seconds = timed(lambda: history.render(
                    lambda items: len(tokenizer.apply_chat_template(items, tokenize=True, add_generation_prompt=True, return_dict=False)),
                    16384 - budget, presentation=presentation))
                require(rendered.messages == messages, 'actual_runtime_render_synthetic_messages')
                token_ids, tokenizer_seconds = timed(lambda: tokenizer.apply_chat_template(rendered.messages,
                    tokenize=True, add_generation_prompt=True, return_dict=False))
                inputs, transfer_seconds = timed(lambda: torch.tensor([token_ids] * batch_size, dtype=torch.long, device='cuda:0'), torch.cuda.synchronize)
                timer = ForwardTimer(model.get_base_model(), torch)
                original_generate = model.generate
                hf_timings = []

                def measured_generate(**arguments):
                    value, seconds = timed(lambda: original_generate(**arguments), torch.cuda.synchronize)
                    hf_timings.append(seconds)
                    return value

                model.generate = measured_generate
                try:
                    if batch_size == 1:
                        response, response_seconds = timed(lambda: native_generate(life, rendered.messages,
                            max_new_tokens=budget, deadline_unix=life.plan['hard_end_unix']), torch.cuda.synchronize)
                        targets = [response['token_ids']]
                        counts = [len(targets[0])]
                    else:
                        config = transformers.GenerationConfig(do_sample=True, num_beams=1, use_cache=True,
                            max_new_tokens=budget, eos_token_id=tokenizer.eos_token_id, pad_token_id=tokenizer.pad_token_id, **DECODER)
                        with torch.inference_mode():
                            generated, response_seconds = timed(lambda: model.generate(input_ids=inputs,
                                attention_mask=torch.ones_like(inputs), generation_config=config), torch.cuda.synchronize)
                        generated_rows = generated.tolist()
                        require(all(row[:len(token_ids)] == token_ids for row in generated_rows), 'batched_prefix_unchanged')
                        counts = token_counts(generated_rows, len(token_ids), {tokenizer.eos_token_id}, tokenizer.pad_token_id)
                        targets = [row[len(token_ids):len(token_ids) + count] for row, count in zip(generated_rows, counts)]
                finally:
                    model.generate = original_generate
                    forward = timer.finish()
                require(len(hf_timings) == 1, 'one_HF_generate_call')
                generation_seconds = hf_timings[0]
                texts, detokenize_seconds = timed(lambda: [tokenizer.decode(target[:-1] if target[-1] == tokenizer.eos_token_id else target,
                    skip_special_tokens=False, clean_up_tokenization_spaces=False) for target in targets])
                unused_hash, adapter_hash_seconds = timed(lambda: fixture_hash(model, torch), torch.cuda.synchronize)
                row = dict(split='TRAIN', actor='child', prefix_loss=False, target_loss=True,
                    prefix=rendered.messages, token_ids=targets[0], terminal=targets[0][-1] == tokenizer.eos_token_id, target=texts[0])
                own, target_encode_seconds = timed(lambda: encode_own(row, tokenizer, 16384))
                serialized, serialize_seconds = timed(lambda: encoded(dict(messages=rendered.messages, targets=targets, texts=texts)))
                trial_name = f'{prompt_size}_{batch_size}_{phase}_{budget}'
                journal = StreamJournal(root / ('journal_' + trial_name), create=True)
                journal_times = []
                try:
                    for depth in range(3):
                        unused_receipt, seconds = timed(lambda: journal.record('PROFILE_SYNTHETIC', dict(
                            depth=depth, messages=rendered.messages, targets=targets, texts=texts)))
                        journal_times.append(seconds)
                finally:
                    journal.close()
                wall = time.perf_counter() - wall_started
                trial = dict(name=trial_name, phase=phase, prompt_tokens_per_life=prompt_size,
                    max_new_tokens=budget, batch_size=batch_size, warmup_excluded=phase == 'excluded_warmup',
                    native_single_generate=batch_size == 1, generation=rates(counts, generation_seconds),
                    response_path_seconds=response_seconds,
                    end_to_end_without_sleep=rates(counts, wall), forward=forward,
                    stages_seconds=dict(render_including_count=render_seconds, tokenizer_only=tokenizer_seconds,
                        input_transfer=transfer_seconds, detokenize=detokenize_seconds, adapter_hash=adapter_hash_seconds,
                        target_encode=target_encode_seconds, serialize=serialize_seconds, journal_by_depth=journal_times),
                    synthetic_payload_bytes=len(serialized), output_token_sha256=digest(targets),
                    peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                    model_forward_fraction_of_generate=forward['model_forward_cuda_seconds'] / generation_seconds)
                receipt(root, 'TRIAL_' + trial_name + '.json', **trial)
                trials.append(trial)
                print(json.dumps(dict(trial=trial_name, tokens=counts, generation_seconds=generation_seconds)), flush=True)
                if prompt_size == 2048 and batch_size == 1 and phase == 'warm' and budget == 256:
                    sleep_fixture = (own, trial)
    require(fixture_hash(model, torch) == initial_hash, 'generation_fixture_unchanged')
    own, selected_trial = sleep_fixture
    parameters = [parameter for name, parameter in model.named_parameters() if '.lora_' in name]
    for parameter in parameters:
        parameter.requires_grad_(True)
    optimizer = torch.optim.AdamW(parameters, lr=3e-5)
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
    model.train()

    def synthetic_sleep():
        optimizer.zero_grad(set_to_none=True)
        inputs = torch.tensor([own.input_ids], dtype=torch.long, device='cuda:0')
        labels = torch.tensor([own.labels], dtype=torch.long, device='cuda:0')
        loss = model(input_ids=inputs, attention_mask=torch.ones_like(inputs), labels=labels, use_cache=False).loss
        require(bool(torch.isfinite(loss)), 'finite_fixture_loss')
        loss.backward()
        require(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all()) for parameter in parameters), 'finite_fixture_gradients')
        optimizer.step()
        return float(loss.detach())

    loss, sleep_seconds = timed(synthetic_sleep, torch.cuda.synchronize)
    model.requires_grad_(False)
    receipt(root, 'SLEEP_MICROBENCHMARK.json', seconds=sleep_seconds, loss=loss, optimizer_steps=1,
            prompt_tokens=2048, target_tokens=len(own.target_ids), seed=SEED,
            meaning='Isolated one-step synthetic target-only LoRA training, not the native multi-presentation/anchor sleep recipe',
            composed_generation_plus_one_step_seconds=selected_trial['end_to_end_without_sleep']['seconds'] + sleep_seconds,
            live_sleep_measured=False, adapter_sha256_after=fixture_hash(model, torch))
    receipt(root, 'COMPLETE.json', measured_trials=[trial['name'] for trial in trials if not trial['warmup_excluded']],
            warmup_trials=[trial['name'] for trial in trials if trial['warmup_excluded']],
            total_profile_seconds=time.perf_counter() - started, live_runtime_modified=False,
            interpretation='Synthetic throughput only; batch shares one fixture, not independent-life adapters. Target >=40 is not guaranteed.')
    signal.alarm(0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('prepare', 'admit', 'launch', 'run'))
    parser.add_argument('--root', required=True)
    options = parser.parse_args()
    root = scoped_root(options.root)
    operations = dict(prepare=prepare, admit=admit, launch=launch, run=profile)
    try:
        operations[options.operation](root)
    except BaseException as error:
        receipt(root, 'FAILURE_' + options.operation + '.json', exception=type(error).__name__, reason=str(error), retry_allowed=False)
        raise


if __name__ == '__main__':
    main()
