"""Fail-closed, operator-admitted Triton add executor; never a host code runner.

Only a bounded, AST-whitelisted Triton function may enter the sandbox. The
trusted driver owns launches, reference computation and timing. A new GPU-profile
gate is mandatory; the R125 CPU gate is deliberately incompatible.
"""

import argparse
import array
import ast
import base64
import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import sys
import time
import zlib

from gpu.orch_r125_bounded_capture import capture
from gpu.orch_r125_cpu_experiment import digest, read_document, read_regular
from organism_v6.orch_r125_experiment_request import make_request as make_cpu_request


SCHEMA = 'R132_KERNEL_REQUEST_V1'
TASK = 'triton_add_f32_v1'
LENGTHS = (1, 1024, 65537, 1048576)
GPU_UUID = 'GPU-35dcea35-12bc-f2f3-d5d2-d2eaa8bacdd8'
GPU_MINOR = 1
MAX_OUTPUT = 1048576
LOCK_PATH = Path('/localhome/local-rohing/.orch_r132_kernel_gpu1.lock')
GATE_CHECKS = frozenset({
    'nonroot_identity', 'zero_capabilities', 'no_new_privileges',
    'network_ipv4_denied', 'network_ipv6_denied', 'network_unix_denied',
    'outside_read_denied', 'outside_write_denied', 'symlink_escape_denied',
    'reference_write_denied', 'input_write_denied', 'host_processes_hidden',
    'host_cgroups_hidden', 'no_inherited_host_fds', 'no_credentials_or_host_home',
    'unassigned_gpu_nodes_hidden', 'unassigned_gpu_device_policy_denied',
    'assigned_gpu_allowed', 'device_bpf_exact', 'resource_limits_verified',
    'timeout_descendants_removed', 'output_limit_enforced', 'memory_limit_enforced',
    'scratch_limit_enforced', 'gpu_context_removed_after_timeout', 'implicit_host_tmp_denied',
})

EXAMPLE_SOURCE = '''@triton.jit
def add_kernel(left, right, output, size: tl.constexpr, BLOCK: tl.constexpr):
    offsets = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)
    mask = offsets < size
    result = tl.load(left + offsets, mask=mask) + tl.load(right + offsets, mask=mask)
    tl.store(output + offsets, result, mask=mask)
'''

HARNESS = r'''import array, base64, importlib.util, json, os, statistics, sys, time, traceback, zlib
os.makedirs('/work/tmp', exist_ok=True)
sys.path.insert(0, '/runtime/site-packages')
phase = 'runtime_import'
try:
    import torch
    import triton
    import triton.language as tl
    task = json.load(open('/input/task.json'))
    assert torch.cuda.is_available() and torch.cuda.device_count() == 1
    torch.set_num_threads(1)
    left_bytes = bytearray(open('/input/left.f32', 'rb').read())
    right_bytes = bytearray(open('/input/right.f32', 'rb').read())
    left_all = torch.frombuffer(left_bytes, dtype=torch.float32).cuda()
    right_all = torch.frombuffer(right_bytes, dtype=torch.float32).cuda()
    def benchmark(operation):
        for repeat in range(3):
            operation()
        torch.cuda.synchronize()
        samples = []
        for repeat in range(20):
            start = torch.cuda.Event(enable_timing=True)
            finish = torch.cuda.Event(enable_timing=True)
            start.record()
            operation()
            finish.record()
            finish.synchronize()
            samples.append(start.elapsed_time(finish))
        return statistics.median(samples)
    phase = 'reference'
    reference_ms = {}
    for size in task['lengths']:
        left, right = left_all[:size], right_all[:size]
        output = torch.empty_like(left)
        reference_ms[str(size)] = benchmark(lambda: torch.add(left, right, out=output))
    phase = 'candidate_import'
    spec = importlib.util.spec_from_file_location('candidate', '/input/kernel.py')
    candidate = importlib.util.module_from_spec(spec)
    candidate.__dict__.update(triton=triton, tl=tl, __builtins__={})
    sys.modules['candidate'] = candidate
    started = time.monotonic()
    spec.loader.exec_module(candidate)
    def launch(left, right, output):
        size = output.numel()
        candidate.add_kernel[(triton.cdiv(size, 256),)](left, right, output, size, 256)
    phase = 'candidate_compile_and_first_launch'
    launch(left_all[:1], right_all[:1], torch.empty_like(left_all[:1]))
    torch.cuda.synchronize()
    first_compile_seconds = time.monotonic() - started
    cases = {}
    for size in task['lengths']:
        phase = 'candidate_launch_' + str(size)
        left, right = left_all[:size].clone(), right_all[:size].clone()
        output = torch.full_like(left, float('nan'))
        launch(left, right, output)
        torch.cuda.synchronize()
        actual = output.cpu().contiguous().numpy().tobytes()
        phase = 'candidate_timing_' + str(size)
        candidate_ms = benchmark(lambda: launch(left, right, output))
        cases[str(size)] = dict(reference_ms=reference_ms[str(size)], candidate_ms=candidate_ms,
            output_zlib_base64=base64.b64encode(zlib.compress(actual)).decode('ascii'))
    print(json.dumps(dict(schema='R132_KERNEL_MEASUREMENTS_V1', status='MEASURED',
        first_compile_seconds=first_compile_seconds, torch_version=torch.__version__,
        triton_version=triton.__version__, cases=cases), allow_nan=False), flush=True)
except BaseException as error:
    print(json.dumps(dict(schema='R132_KERNEL_MEASUREMENTS_V1', status='ERROR', phase=phase,
        error_type=type(error).__name__, error=str(error)[:4096],
        traceback=traceback.format_exc()[-16384:]), allow_nan=False), flush=True)
    sys.exit(1)
'''

BOUNDARY_PROBE = r'''import errno, json, os, pathlib, socket, time
checks = {}
def denied(name, operation):
    try:
        value = operation()
        if hasattr(value, 'close'): value.close()
    except OSError as error:
        checks[name] = error.errno in (errno.EACCES, errno.EPERM, errno.ENOENT, errno.EROFS, errno.ESRCH, errno.EAFNOSUPPORT)
    else:
        checks[name] = False
status = dict(line.split(':', 1) for line in pathlib.Path('/proc/self/status').read_text().splitlines() if ':' in line)
checks['nonroot_identity'] = os.getuid() > 0 and os.getgid() > 0
checks['zero_capabilities'] = all(int(status[key].strip(), 16) == 0 for key in ('CapEff','CapPrm','CapAmb','CapBnd'))
checks['no_new_privileges'] = status['NoNewPrivs'].strip() == '1'
for name, family in [('ipv4',socket.AF_INET),('ipv6',socket.AF_INET6)]:
    denied('network_'+name+'_denied', lambda family=family: socket.socket(family, socket.SOCK_STREAM))
unix_denials = []
for endpoint in (__HOST_SOCKET__, __HOST_ABSTRACT__):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as connection:
        connection.settimeout(0.5)
        try: connection.connect(endpoint)
        except OSError as error: unix_denials.append(error.errno in (errno.EPERM,errno.EACCES,errno.ENOENT,errno.ECONNREFUSED))
        else: unix_denials.append(False)
checks['network_unix_denied'] = all(unix_denials)
outside = __OUTSIDE__
denied('outside_read_denied', lambda: open(outside, 'rb'))
denied('outside_write_denied', lambda: open(outside, 'ab'))
pathlib.Path('/work/link').symlink_to(outside)
denied('symlink_escape_denied', lambda: open('/work/link', 'rb'))
denied('reference_write_denied', lambda: open('/input/task.json', 'ab'))
denied('input_write_denied', lambda: open('/input/left.f32', 'ab'))
denied('host_processes_hidden', lambda: open('/proc/__PEER__/environ', 'rb'))
denied('host_cgroups_hidden', lambda: open('/sys/fs/cgroup/cgroup.procs', 'rb'))
denied('implicit_host_tmp_denied', lambda: open('/tmp/must-not-write','ab'))
descriptors = []
for path in pathlib.Path('/proc/self/fd').iterdir():
    try: target = os.readlink(path)
    except FileNotFoundError: continue
    descriptors.append((int(path.name), target))
checks['no_inherited_host_fds'] = all(number <= 2 or target == '/input/harness.py' for number,target in descriptors)
allowed_env = {'PATH','LANG','LC_CTYPE','HOME','TMPDIR','TRITON_CACHE_DIR','TRITON_LIBCUDA_PATH','CUDA_CACHE_PATH','PYTHONDONTWRITEBYTECODE','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','CUDA_VISIBLE_DEVICES'}
checks['no_credentials_or_host_home'] = set(os.environ) <= allowed_env and os.environ.get('HOME') == '/work' and not pathlib.Path('/localhome').exists()
checks['unassigned_gpu_nodes_hidden'] = sorted(str(path) for path in pathlib.Path('/dev').glob('nvidia[0-9]*')) == ['/dev/nvidia1']
try:
    descriptor = os.open('/input/denied_gpu_fixture', os.O_RDONLY)
except OSError as error:
    checks['unassigned_gpu_device_policy_denied'] = error.errno == errno.EPERM
else:
    os.close(descriptor)
    checks['unassigned_gpu_device_policy_denied'] = False
try:
    descriptor = os.open('/dev/nvidia1', os.O_RDWR)
except OSError:
    checks['assigned_gpu_allowed'] = False
else:
    os.close(descriptor)
    checks['assigned_gpu_allowed'] = True
print(json.dumps({'checks':checks,'passed':all(checks.values())}), flush=True)
time.sleep(4)
'''

RESOURCE_PROBES = {
    'output': 'import os\nwhile True: os.write(1, b"x" * 8192)\n',
    'timeout': 'import os,time\nos.fork()\ntime.sleep(120)\n',
    'memory': 'import time\ntime.sleep(2)\nallocation = bytearray(5 * 1024**3)\n',
    'files': '''import errno,json,pathlib,os,resource
checks = {}
diagnostics = {'file_limit':resource.getrlimit(resource.RLIMIT_FSIZE), 'work_bytes':os.statvfs('/work').f_frsize * os.statvfs('/work').f_blocks}
try:
    with open('/work/large', 'wb') as stream:
        for index in range(65): stream.write(b'x' * 1048576)
except OSError as error:
    checks['file_limit'] = error.errno == errno.EFBIG
else: checks['file_limit'] = False
for directory in ('/work',):
    try:
        for index in range(100):
            pathlib.Path(directory+'/file-'+str(index)).write_bytes(b'x' * 8388608)
    except OSError as error:
        checks[directory+'_limit'] = error.errno == errno.ENOSPC
        diagnostics[directory+'_errno'] = error.errno
        diagnostics[directory+'_files_before_error'] = index
    else: checks[directory+'_limit'] = False
checks['exact_tmpfs_sizes'] = diagnostics['work_bytes'] == 512 * 1024 * 1024
try:
    pathlib.Path('/tmp/must-not-write').write_bytes(b'x')
except OSError as error:
    checks['implicit_tmp_write_denied'] = error.errno in (errno.EACCES,errno.EPERM,errno.EROFS)
else: checks['implicit_tmp_write_denied'] = False
print(json.dumps({'checks':checks,'diagnostics':diagnostics,'passed':all(checks.values())}), flush=True)
''',
    'gpu_context': '''import sys,time,os
os.makedirs('/work/tmp', exist_ok=True)
sys.path.insert(0, '/runtime/site-packages')
import torch
assert torch.cuda.is_available() and torch.cuda.device_count() == 1
allocation = torch.empty(32 * 1024 * 1024, dtype=torch.float32, device='cuda')
allocation.fill_(1)
torch.cuda.synchronize()
print('TRUSTED_GPU_CONTEXT_READY', flush=True)
time.sleep(120)
''',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def environment_schema():
    return dict(schema='R132_KERNEL_ENVIRONMENT_V1', request_schema=SCHEMA,
        requires_verified_gpu_gate=True, task=TASK, reference='torch.add(left, right, out=output)',
        lengths=list(LENGTHS), dtype='float32', layout='contiguous',
        entrypoint='@triton.jit def add_kernel(left, right, output, size: tl.constexpr, BLOCK: tl.constexpr)',
        source_language='AST-whitelisted Triton function only; no imports, module code or child launcher',
        source_contract='R132_BOUNDED_TRITON_AST_V1',
        source_max_utf8_bytes=65536, request_max_bytes=100000,
        request_fields=['schema', 'task', 'source', 'source_sha256', 'origin', 'request_id'],
        origin_kinds=['BUILDER_TEST', 'TRAIN_CHILD_RESPONSE'],
        origin_fields=['kind', 'record_index', 'record_sha256'],
        request_id_encoding='SHA256 of sorted compact ensure_ascii=True UTF-8 JSON excluding request_id',
        gpu_uuid=GPU_UUID, device_minor=GPU_MINOR, output_is_untrusted=True,
        timing_origin='trusted_driver_cuda_events_not_child_reports',
        example_source=EXAMPLE_SOURCE)


def make_request(source, origin):
    request = make_cpu_request(source, origin)
    request.update(schema=SCHEMA, task=TASK)
    request['request_id'] = digest({key: value for key, value in request.items() if key != 'request_id'})
    return parse_request(json.dumps(request, ensure_ascii=False).encode('utf-8'))


def parse_request(raw):
    require(type(raw) is bytes and len(raw) <= 100000, 'bounded_request_bytes_required')
    request = read_document(raw)
    require(set(request) == {'schema', 'task', 'source', 'source_sha256', 'origin', 'request_id'},
        'exact_request_fields_required')
    require(request['schema'] == SCHEMA and request['task'] == TASK, 'fixed_triton_add_task_required')
    validated = make_cpu_request(request['source'], request['origin'])
    require(request['source_sha256'] == validated['source_sha256'], 'source_hash_mismatch')
    require(request['request_id'] == digest({key: value for key, value in request.items() if key != 'request_id'}),
        'request_hash_mismatch')
    validate_kernel_source(request['source'])
    return request


def validate_kernel_source(source):
    """Parse data as AST; never execute/compile a kernel in the supervisor.

The fixed index and mask plus immutable SSA names bound every load/store to
the provided input/output vector. Only pure elementwise value expressions vary.
"""
    require(type(source) is str and 0 < len(source.encode('utf-8')) <= 65536, 'bounded_kernel_source_required')
    try:
        tree = ast.parse(source, mode='exec')
    except (SyntaxError, RecursionError, ValueError) as error:
        raise ValueError('invalid_kernel_AST') from error
    pending = [tree]
    count = 0
    while pending:
        count += 1
        require(count <= 256, 'kernel_AST_node_limit')
        pending.extend(ast.iter_child_nodes(pending.pop()))
    require(len(tree.body) == 1 and type(tree.body[0]) is ast.FunctionDef, 'one_kernel_function_only')
    function = tree.body[0]
    require(function.name == 'add_kernel' and function.returns is None
        and not function.type_comment and not getattr(function, 'type_params', []), 'exact_kernel_function_required')
    decorator = ast.parse('@triton.jit\ndef add_kernel(): pass').body[0].decorator_list[0]
    require(len(function.decorator_list) == 1
        and ast.dump(function.decorator_list[0]) == ast.dump(decorator), 'exact_triton_jit_decorator_required')
    arguments = function.args
    require(not arguments.posonlyargs and not arguments.vararg and not arguments.kwarg
        and not arguments.kwonlyargs and not arguments.defaults and not arguments.kw_defaults,
        'exact_kernel_signature_required')
    require([argument.arg for argument in arguments.args] == ['left', 'right', 'output', 'size', 'BLOCK'],
        'exact_kernel_signature_required')
    constexpr = ast.parse('tl.constexpr', mode='eval').body
    for index, argument in enumerate(arguments.args):
        require(not argument.type_comment, 'no_type_comments')
        require(argument.annotation is None if index < 3 else
            argument.annotation is not None and ast.dump(argument.annotation) == ast.dump(constexpr),
            'exact_constexpr_annotations_required')
    require(3 <= len(function.body) <= 32, 'bounded_kernel_body_required')
    offsets = ast.parse('offsets = tl.program_id(0) * BLOCK + tl.arange(0, BLOCK)').body[0]
    mask = ast.parse('mask = offsets < size').body[0]
    require(ast.dump(function.body[0]) == ast.dump(offsets)
        and ast.dump(function.body[1]) == ast.dump(mask), 'fixed_bounded_offsets_and_mask_required')
    names = {'size', 'BLOCK', 'offsets', 'mask'}

    def expression(node, depth=0):
        require(depth <= 24, 'kernel_expression_depth_limit')
        if type(node) is ast.Name:
            require(node.id in names, 'only_defined_scalar_or_tensor_names')
        elif type(node) is ast.Constant:
            require(type(node.value) in (int, float) and math.isfinite(node.value)
                and abs(node.value) <= 65536, 'bounded_numeric_literals_only')
        elif type(node) is ast.BinOp:
            require(type(node.op) in (ast.Add, ast.Sub, ast.Mult, ast.Div), 'bounded_arithmetic_only')
            expression(node.left, depth + 1)
            expression(node.right, depth + 1)
        elif type(node) is ast.UnaryOp:
            require(type(node.op) in (ast.UAdd, ast.USub), 'numeric_unary_only')
            expression(node.operand, depth + 1)
        elif type(node) is ast.Compare:
            require(len(node.ops) == 1 and type(node.ops[0]) in (ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Eq, ast.NotEq),
                'simple_numeric_comparison_only')
            expression(node.left, depth + 1)
            expression(node.comparators[0], depth + 1)
        elif type(node) is ast.Call:
            require(type(node.func) is ast.Attribute and type(node.func.value) is ast.Name
                and node.func.value.id == 'tl', 'only_allowlisted_tl_calls')
            if node.func.attr == 'load':
                require(len(node.args) == 1, 'one_bounded_load_pointer')
                pointer(node.args[0], {'left', 'right'})
                keywords(node, allow_other=True)
            else:
                require(node.func.attr in ('where', 'minimum', 'maximum') and not node.keywords
                    and len(node.args) == (3 if node.func.attr == 'where' else 2), 'pure_tl_values_only')
                for argument in node.args:
                    expression(argument, depth + 1)
        else:
            raise ValueError('kernel_expression_not_allowlisted')

    def pointer(node, allowed):
        require(type(node) is ast.BinOp and type(node.op) is ast.Add
            and type(node.left) is ast.Name and node.left.id in allowed
            and type(node.right) is ast.Name and node.right.id == 'offsets', 'bounded_pointer_only')

    def keywords(call, allow_other=False):
        values = {keyword.arg: keyword.value for keyword in call.keywords}
        allowed_sets = ({'mask'}, {'mask', 'other'}) if allow_other else ({'mask'},)
        require(len(values) == len(call.keywords) and set(values) in allowed_sets, 'exact_memory_keywords_required')
        require(type(values['mask']) is ast.Name and values['mask'].id == 'mask', 'fixed_mask_required')
        if 'other' in values:
            require(type(values['other']) is ast.Constant and type(values['other'].value) in (int, float)
                and values['other'].value == 0, 'zero_padding_only')

    for statement in function.body[2:-1]:
        require(type(statement) is ast.Assign and len(statement.targets) == 1
            and type(statement.targets[0]) is ast.Name and not statement.type_comment, 'SSA_assignments_only')
        name = statement.targets[0].id
        require(re.fullmatch('[a-z][a-z0-9_]{0,63}', name) and name not in names
            and name not in {'tl', 'triton', 'left', 'right', 'output'}, 'no_shadowing_or_reassignment')
        expression(statement.value)
        names.add(name)
    final = function.body[-1]
    require(type(final) is ast.Expr and type(final.value) is ast.Call, 'one_final_store_required')
    store = final.value
    require(type(store.func) is ast.Attribute and type(store.func.value) is ast.Name
        and store.func.value.id == 'tl' and store.func.attr == 'store' and len(store.args) == 2,
        'one_final_tl_store_required')
    pointer(store.args[0], {'output'})
    expression(store.args[1])
    keywords(store)
    return dict(schema='R132_BOUNDED_TRITON_AST_V1', ast_sha256=digest(ast.dump(tree)),
        source_sha256=hashlib.sha256(source.encode('utf-8')).hexdigest(),
        canonical_source=ast.unparse(tree) + '\n')


def trusted_path(value):
    path = Path(value).absolute()
    require(str(value).startswith('/') and re.fullmatch(r'/[A-Za-z0-9_./-]+', str(path))
        and '..' not in path.parts and path.resolve() == path, 'trusted_absolute_path_required')
    return path


def task_spec():
    return dict(task=TASK, lengths=list(LENGTHS), dtype='little_endian_float32',
        left_formula='((index % 257) - 128) / 8', right_formula='((index % 251) - 125) / 16',
        reference='torch.add(left, right, out=output)', reference_tolerance='exact float32 values',
        warmup=3, repeats=20, statistic='median CUDA event milliseconds; compilation excluded')


def float_bytes(values):
    packed = array.array('f', values)
    require(packed.itemsize == 4, 'float32_host_required')
    if sys.byteorder != 'little':
        packed.byteswap()
    return packed.tobytes()


def expected_output(size):
    return float_bytes(((index % 257) - 128) / 8 + ((index % 251) - 125) / 16
        for index in range(size))


def read_pseudo(path, maximum):
    with path.open('rb') as stream:
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum, 'bounded_kernel_metadata_required')
    return raw


def validate_runtime(runtime_root):
    root = trusted_path(runtime_root)
    manifest_raw = read_regular(root / 'MANIFEST.json', 4194304)
    manifest = read_document(manifest_raw)
    require(set(manifest) == {'schema', 'files'} and manifest['schema'] == 'R132_RUNTIME_MANIFEST_V1',
        'sealed_runtime_manifest_required')
    files = manifest['files']
    require(type(files) is dict and 0 < len(files) <= 50000, 'bounded_runtime_manifest_required')
    require((root / 'site-packages' / 'torch').is_dir()
        and (root / 'site-packages' / 'triton').is_dir(), 'torch_and_triton_runtime_required')
    observed = set()
    for directory, directories, names in os.walk(root, followlinks=False):
        for path in [Path(directory)] + [Path(directory) / name for name in directories + names]:
            metadata = path.lstat()
            require(metadata.st_uid == 0 and metadata.st_mode & 0o022 == 0
                and (stat.S_ISREG(metadata.st_mode) or stat.S_ISDIR(metadata.st_mode)),
                'root_owned_regular_runtime_without_symlinks_required')
        for name in names:
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if relative == 'MANIFEST.json':
                continue
            require(relative in files, 'unmanifested_runtime_file')
            checksum = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1048576), b''):
                    checksum.update(chunk)
            require(checksum.hexdigest() == files[relative], 'runtime_file_hash_mismatch')
            observed.add(relative)
    require(observed == set(files), 'runtime_manifest_set_mismatch')
    return hashlib.sha256(manifest_raw).hexdigest()


def device_identity():
    result = subprocess.run(['nvidia-smi', '--id=' + GPU_UUID,
        '--query-gpu=uuid,index,pci.bus_id', '--format=csv,noheader,nounits'],
        capture_output=True, text=True, timeout=10, check=True)
    fields = [field.strip() for field in result.stdout.strip().split(',')]
    require(len(fields) == 3 and fields[0] == GPU_UUID and fields[1] == '2', 'assigned_uuid_index_mismatch')
    bus = fields[2].lower()[-12:]
    require(re.fullmatch(r'[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]', bus), 'invalid_pci_bus')
    raw = read_pseudo(Path('/proc/driver/nvidia/gpus') / bus / 'information', 16384).decode()
    info = dict((key.strip(), value.strip()) for key, value in
        (line.split(':', 1) for line in raw.splitlines() if ':' in line))
    require(info.get('GPU UUID') == GPU_UUID and info.get('Device Minor') == '1', 'uuid_minor_binding_mismatch')
    nodes = {}
    for name in ('/dev/nvidia1', '/dev/nvidiactl', '/dev/nvidia-uvm'):
        metadata = os.stat(name, follow_symlinks=False)
        require(stat.S_ISCHR(metadata.st_mode), 'real_character_device_required')
        nodes[name] = [os.major(metadata.st_rdev), os.minor(metadata.st_rdev)]
    require(nodes['/dev/nvidia1'] == [195, 1] and nodes['/dev/nvidiactl'] == [195, 255]
        and nodes['/dev/nvidia-uvm'][1] == 0, 'assigned_device_numbers_required')
    return dict(gpu_uuid=GPU_UUID, physical_index=2, nodes=nodes)


def command(root, runtime_root, unit):
    root, runtime = trusted_path(root), trusted_path(runtime_root)
    require(re.fullmatch(r'orch-r132-kernel-[a-f0-9]{32}', unit), 'owned_unit_name_required')
    properties = {
        'DynamicUser': 'yes', 'RootDirectory': str(root / 'rootfs'),
        'BindReadOnlyPaths': f'/usr {runtime}:/runtime {root / "input"}:/input {root / "empty"}:/sys/fs/cgroup {root / "empty"}:/tmp {root / "empty"}:/var/tmp',
        'BindPaths': '/dev/nvidia1 /dev/nvidiactl /dev/nvidia-uvm',
        'PrivateNetwork': 'yes', 'PrivateIPC': 'yes', 'PrivateDevices': 'yes', 'PrivateTmp': 'no', 'MountAPIVFS': 'no',
        'ProtectSystem': 'strict', 'ProtectHome': 'yes', 'ProtectProc': 'invisible', 'ProcSubset': 'pid',
        'NoNewPrivileges': 'yes', 'CapabilityBoundingSet': '', 'AmbientCapabilities': '',
        'ProtectKernelTunables': 'yes', 'ProtectKernelModules': 'yes', 'ProtectKernelLogs': 'yes',
        'ProtectControlGroups': 'yes', 'RestrictNamespaces': 'yes', 'RestrictSUIDSGID': 'yes',
        'RestrictRealtime': 'yes', 'LockPersonality': 'yes', 'MemoryDenyWriteExecute': 'no',
        'InaccessiblePaths': '/sys /run /tmp -/var/tmp', 'WorkingDirectory': '/work',
        'TemporaryFileSystem': '/work:rw,size=512M,mode=1777',
        'ReadWritePaths': '/work', 'MemoryMax': '4G', 'MemorySwapMax': '0',
        'CPUQuota': '200%', 'TasksMax': '64', 'RuntimeMaxSec': '90', 'TimeoutStopSec': '2',
        'KillMode': 'control-group', 'OOMPolicy': 'kill', 'DevicePolicy': 'strict',
        'RestrictAddressFamilies': 'AF_UNIX',
        'SystemCallFilter': '~@mount @privileged @reboot @swap @module @debug',
        'SystemCallErrorNumber': 'EPERM', 'UMask': '0077', 'LimitCORE': '0', 'LimitFSIZE': '67108864',
    }
    device_rules = ['/dev/null rw', '/dev/zero rw', '/dev/random r', '/dev/urandom r',
        '/dev/nvidia1 rw', '/dev/nvidiactl rw', '/dev/nvidia-uvm rw']
    return ['sudo', '-n', 'systemd-run', '--quiet', '--wait', '--pipe', '--unit=' + unit,
        *['--property=' + key + '=' + value for key, value in properties.items()],
        '--property=DeviceAllow=', *['--property=DeviceAllow=' + rule for rule in device_rules],
        '/usr/bin/env', '-i', 'PATH=/usr/bin:/bin', 'LANG=C.UTF-8', 'HOME=/work', 'TMPDIR=/work/tmp',
        'TRITON_CACHE_DIR=/work/triton', 'CUDA_CACHE_PATH=/work/cuda', 'PYTHONDONTWRITEBYTECODE=1',
        'TRITON_LIBCUDA_PATH=/usr/lib/x86_64-linux-gnu',
        'OMP_NUM_THREADS=1', 'OPENBLAS_NUM_THREADS=1', 'CUDA_VISIBLE_DEVICES=' + GPU_UUID,
        '/usr/bin/python3', '-I', '/input/harness.py']


def policy_identity(runtime, runtime_hash, devices):
    placeholder = '/r132-job'
    return dict(executor_sha256=hashlib.sha256(read_regular(Path(__file__), 1048576)).hexdigest(),
        kernel_release=os.uname().release,
        host_tools_sha256={name: hashlib.sha256(read_regular(Path(name).resolve(), 16777216)).hexdigest()
            for name in ('/usr/bin/python3', '/usr/bin/systemd-run')},
        capture_sha256=hashlib.sha256(read_regular(Path(sys.modules[capture.__module__].__file__), 1048576)).hexdigest(),
        cpu_helpers_sha256=hashlib.sha256(read_regular(Path(sys.modules[read_document.__module__].__file__), 1048576)).hexdigest(),
        request_parser_sha256=hashlib.sha256(read_regular(Path(sys.modules[make_cpu_request.__module__].__file__), 1048576)).hexdigest(),
        driver_version_sha256=hashlib.sha256(read_pseudo(Path('/proc/driver/nvidia/version'), 16384)).hexdigest(),
        runtime_manifest_sha256=runtime_hash, devices=devices, task_sha256=digest(task_spec()),
        harness_sha256=hashlib.sha256(HARNESS.encode()).hexdigest(),
        command_template_sha256=digest(command(placeholder, runtime, 'orch-r132-kernel-' + '0' * 32)),
        boot_id_sha256=hashlib.sha256(read_pseudo(Path('/proc/sys/kernel/random/boot_id'), 128)).hexdigest())


def validate_gate(path, identity, now):
    path = trusted_path(path)
    raw = read_regular(path, 1048576)
    gate = read_document(raw)
    require(gate.get('schema') == 'R132_GPU_CONFINEMENT_GATE_V1' and gate.get('passed') is True,
        'new_GPU_profile_gate_required_not_CPU_gate')
    require(gate.get('identity') == identity, 'gate_profile_runtime_device_boot_mismatch')
    require(type(gate.get('observed_unix')) in (int, float) and type(gate.get('expires_unix')) in (int, float)
        and 0 <= now - gate['observed_unix'] <= 3600 and now + 150 < gate['expires_unix'], 'fresh_gate_required')
    checks = gate.get('checks')
    require(type(checks) is dict and set(checks) == GATE_CHECKS, 'complete_GPU_negative_matrix_required')
    for name, check in checks.items():
        require(type(check) is dict and check.get('passed') is True, 'negative_check_failed')
        receipt_path = trusted_path(check['receipt_path'])
        receipt_raw = read_regular(receipt_path, 1048576)
        require(hashlib.sha256(receipt_raw).hexdigest() == check.get('receipt_sha256'), 'negative_receipt_hash_mismatch')
        receipt = read_document(receipt_raw)
        require(receipt.get('identity') == identity and receipt.get('passed') is True
            and receipt.get('checks', {}).get(name) is True,
            'negative_receipt_identity_mismatch')
    return hashlib.sha256(raw).hexdigest()


def validate_admission(path, now):
    raw = read_regular(trusted_path(path), 65536)
    admission = read_document(raw)
    require(admission.get('schema') == 'R132_KERNEL_ADMISSION_V1'
        and admission.get('main_authorized') is True and admission.get('census_clear') is True,
        'Main_custody_and_fresh_census_required')
    require(admission.get('gpu_uuid') == GPU_UUID and type(admission.get('device_minor')) is int
        and admission['device_minor'] == GPU_MINOR, 'exact_assigned_GPU_required')
    for name in ('observed_unix', 'expires_unix', 'hard_wall_unix'):
        require(type(admission.get(name)) in (int, float) and math.isfinite(admission[name]), 'finite_admission_clock_required')
    require(0 <= now - admission['observed_unix'] <= 60
        and now + 150 < min(admission['expires_unix'], admission['hard_wall_unix']), 'fresh_admission_and_wall_required')
    lease_raw = read_regular(trusted_path(admission['lease_receipt_path']), 65536)
    require(hashlib.sha256(lease_raw).hexdigest() == admission['lease_receipt_sha256'], 'lease_receipt_hash_mismatch')
    lease = read_document(lease_raw)
    end = datetime.datetime.fromisoformat(lease['conservative_lease_end_utc'])
    require(end.tzinfo is not None and type(lease['margin_seconds']) is int
        and lease['margin_seconds'] >= 21600, 'conservative_lease_margin_required')
    require(admission['hard_wall_unix'] <= end.timestamp() - lease['margin_seconds'], 'admission_exceeds_lease_wall')
    return hashlib.sha256(raw).hexdigest()


def validate_measurements(raw):
    require(len(raw) <= MAX_OUTPUT, 'bounded_measurements_required')
    result = read_document(raw)
    require(result.get('schema') == 'R132_KERNEL_MEASUREMENTS_V1', 'measurement_schema_required')
    if result.get('status') == 'ERROR':
        return dict(status='KERNEL_ERROR', reported_error=result, correctness_verified=False, speedups=None)
    require(result.get('status') == 'MEASURED' and type(result.get('cases')) is dict
        and set(result['cases']) == {str(size) for size in LENGTHS}, 'all_fixed_shapes_required')
    require(type(result.get('first_compile_seconds')) in (int, float)
        and math.isfinite(result['first_compile_seconds']) and 0 <= result['first_compile_seconds'] <= 120,
        'bounded_compile_time_required')
    cases = {}
    for size in LENGTHS:
        case = result['cases'][str(size)]
        compressed = base64.b64decode(case['output_zlib_base64'], validate=True)
        inflater = zlib.decompressobj()
        actual = inflater.decompress(compressed, size * 4 + 1)
        require(len(actual) == size * 4 and inflater.eof and not inflater.unused_data
            and not inflater.unconsumed_tail, 'exact_bounded_output_required')
        correct = actual == expected_output(size)
        for key in ('reference_ms', 'candidate_ms'):
            require(type(case[key]) in (int, float) and math.isfinite(case[key]) and 0 < case[key] < 90000,
                'finite_positive_timing_required')
        cases[str(size)] = dict(correct=correct, output_sha256=hashlib.sha256(actual).hexdigest(),
            reference_ms=case['reference_ms'], candidate_ms=case['candidate_ms'],
            reported_speedup=case['reference_ms'] / case['candidate_ms'] if correct else None)
    correct = all(case['correct'] for case in cases.values())
    return dict(status='CORRECT' if correct else 'INCORRECT', correctness_verified=correct, cases=cases,
        first_compile_seconds=result['first_compile_seconds'], timing_origin='TRUSTED_DRIVER_CUDA_EVENTS',
        timing_is_child_reported=False, kernel_source_contract='R132_BOUNDED_TRITON_AST_V1',
        speedup_claim_authorized=False, reported_runtime={key: result.get(key) for key in ('torch_version', 'triton_version')})


def stop_owned(unit, root):
    result = subprocess.run(['sudo', '-n', 'systemctl', 'show', unit + '.service',
        '--property=LoadState,RootDirectory'], capture_output=True, text=True, timeout=5)
    fields = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
    if fields.get('LoadState') == 'not-found':
        require(result.returncode in (0, 1) and not fields.get('RootDirectory'), 'unverified_unit_absence')
        return
    result.check_returncode()
    require(fields.get('RootDirectory') == str(root / 'rootfs'), 'refuse_unowned_unit_stop')
    subprocess.run(['sudo', '-n', 'systemctl', 'stop', unit + '.service'],
        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=True)


def unit_properties(raw):
    properties = {}
    device_values = []
    last_key = None
    for line in raw.splitlines():
        if '=' in line:
            last_key, value = line.split('=', 1)
            properties[last_key] = value
            if last_key == 'DeviceAllow':
                device_values.extend(value.split())
        elif last_key == 'DeviceAllow' and line.strip():
            device_values.extend(line.split())
    require(len(device_values) % 2 == 0, 'complete_device_allow_pairs_required')
    return properties, list(zip(device_values[::2], device_values[1::2]))


def observe_unit(unit):
    observed = subprocess.run(['sudo', '-n', 'systemctl', 'show', unit + '.service',
        '--property=MainPID,ControlGroup,DevicePolicy,DeviceAllow,RootDirectory'],
        capture_output=True, text=True, timeout=5, check=True)
    fields, device_allow = unit_properties(observed.stdout)
    if fields.get('MainPID') in ('0', '', None) or not fields.get('ControlGroup'):
        return None
    group = Path('/sys/fs/cgroup') / fields['ControlGroup'].lstrip('/')
    limits = {name: (group/name).read_text().strip() for name in ('cpu.max','memory.max','memory.swap.max','pids.max')}
    bpf = subprocess.run(['sudo','-n','/usr/sbin/bpftool','-j','cgroup','show',str(group),'effective'],
        capture_output=True, text=True, timeout=5, check=True)
    return dict(properties=fields, device_allow_entries=device_allow, raw_properties=observed.stdout,
        cgroup_files=limits, bpf=json.loads(bpf.stdout))


def assigned_contexts():
    import xml.etree.ElementTree as element_tree
    observed = subprocess.run(['nvidia-smi', '--id=' + GPU_UUID, '-q', '-x'],
        capture_output=True, text=True, timeout=10, check=True)
    tree = element_tree.fromstring(observed.stdout)
    devices = tree.findall('gpu')
    require(len(devices) == 1 and devices[0].findtext('uuid') == GPU_UUID, 'only_assigned_GPU_context_query')
    return [int(process.findtext('pid')) for process in devices[0].findall('./processes/process_info')]


def run_trusted_probes(probe_root, runtime_root, admission_path):
    admission_hash = validate_admission(admission_path, time.time())
    runtime = trusted_path(runtime_root)
    runtime_hash = validate_runtime(runtime)
    devices = device_identity()
    identity = policy_identity(runtime, runtime_hash, devices)
    require(not assigned_contexts(), 'assigned_GPU_must_be_idle_before_trusted_probes')
    base = trusted_path(probe_root)
    base.mkdir(mode=0o755, exist_ok=False)
    canary = base/'synthetic_canary.txt'
    canary.write_bytes(b'R132 synthetic canary only\n')
    all_checks = {}
    references = {}
    for mode in ('basic', 'output', 'timeout', 'memory', 'files', 'gpu_context'):
        if mode == 'gpu_context':
            require(all(all_checks.values()) and 'unassigned_gpu_device_policy_denied' in all_checks,
                'device_files_network_negative_tests_before_GPU_allocation')
        root = base/mode
        root.mkdir(mode=0o755)
        inputs = root/'input'
        inputs.mkdir(mode=0o755)
        (root/'empty').mkdir(mode=0o755)
        filesystem = root/'rootfs'
        filesystem.mkdir(mode=0o755)
        for name in ('usr','runtime','input','work','tmp','etc','dev','proc','sys','run'):
            (filesystem/name).mkdir(mode=0o755)
        for name in ('bin','lib','lib64'):
            (filesystem/name).symlink_to('usr/'+name)
        host_socket = str(base/'s')
        host_abstract = '\0r132-' + hashlib.sha256(str(base).encode()).hexdigest()[:24]
        payload = BOUNDARY_PROBE.replace('__OUTSIDE__',repr(str(canary))).replace('__PEER__',str(os.getpid())).replace('__HOST_SOCKET__',repr(host_socket)).replace('__HOST_ABSTRACT__',repr(host_abstract)) if mode == 'basic' else RESOURCE_PROBES[mode]
        (inputs/'harness.py').write_text(payload)
        (inputs/'task.json').write_text(json.dumps(task_spec()))
        (inputs/'left.f32').write_bytes(b'\0'*4)
        if mode == 'basic':
            subprocess.run(['sudo','-n','mknod','--mode=444',str(inputs/'denied_gpu_fixture'),'c','195','254'],
                check=True, timeout=5, stdin=subprocess.DEVNULL)
        unit = 'orch-r132-kernel-' + hashlib.sha256(str(root).encode()).hexdigest()[:32]
        invocation = command(root,runtime,unit)
        receipt = dict(schema='R132_TRUSTED_GPU_PROBE_V1', mode=mode, identity=identity,
            admission_sha256=admission_hash, command=invocation,
            payload_sha256=hashlib.sha256(payload.encode()).hexdigest(), checks={}, passed=False,
            source_kind='FIXED_BUILDER_PROBE_NOT_CHILD', started_unix=time.time())
        (root/'INTENT.json').write_text(json.dumps(receipt,sort_keys=True,indent=2))
        process = None
        listeners = []
        try:
            if mode == 'basic':
                for endpoint in (host_socket, host_abstract):
                    listener = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
                    listeners.append(listener)
                    listener.bind(endpoint)
                    listener.listen(1)
            preflight = subprocess.run(['sudo','-n','systemctl','show',unit+'.service','--property=LoadState'],
                capture_output=True,text=True,timeout=5)
            require(preflight.returncode in (0,1) and preflight.stdout.strip() == 'LoadState=not-found','new_probe_unit_required')
            process = subprocess.Popen(invocation,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
            for attempt in range(30):
                if process.poll() is not None: break
                observation = observe_unit(unit)
                if observation:
                    receipt['host_observation'] = observation
                    break
                time.sleep(0.1)
            captured = capture(process,lambda:stop_owned(unit,root),max_bytes=MAX_OUTPUT,
                timeout=2 if mode == 'timeout' else 15 if mode == 'gpu_context' else 100)
            stdout,stderr = captured.pop('stdout'),captured.pop('stderr')
            (root/'STDOUT.bin').write_bytes(stdout)
            (root/'STDERR.bin').write_bytes(stderr)
            receipt.update(capture=captured,stdout_sha256=hashlib.sha256(stdout).hexdigest(),
                stderr_sha256=hashlib.sha256(stderr).hexdigest())
            outcome = subprocess.run(['sudo','-n','systemctl','show',unit+'.service','--property=Result,ExecMainStatus'],
                capture_output=True,text=True,timeout=5)
            receipt['unit_outcome'] = dict(line.split('=',1) for line in outcome.stdout.splitlines() if '=' in line)
            observation = receipt.get('host_observation',{})
            limits_ok = observation.get('cgroup_files') == {'cpu.max':'200000 100000','memory.max':'4294967296','memory.swap.max':'0','pids.max':'64'}
            if mode == 'basic' and captured['returncode'] == 0:
                checks = read_document(stdout)['checks']
                allowed = {tuple(entry) for entry in observation.get('device_allow_entries',[])}
                expected = {('/dev/null','rw'),('/dev/zero','rw'),('/dev/random','r'),('/dev/urandom','r'),
                    ('/dev/nvidia1','rw'),('/dev/nvidiactl','rw'),('/dev/nvidia-uvm','rw')}
                checks['device_bpf_exact'] = allowed == expected and observation.get('properties',{}).get('DevicePolicy') == 'strict' and any(item.get('attach_type') == 'cgroup_device' for item in observation.get('bpf',[]))
                checks['resource_limits_verified'] = limits_ok
                receipt['checks'].update(checks)
            elif mode in ('output','timeout'):
                receipt['checks'][{'output':'output_limit_enforced','timeout':'timeout_descendants_removed'}[mode]] = captured['limit_reason'] == {'output':'OUTPUT_LIMIT','timeout':'TIMEOUT'}[mode] and captured['teardown_error'] is None
            elif mode == 'memory':
                receipt['checks']['memory_limit_enforced'] = receipt['unit_outcome'].get('Result') == 'oom-kill'
            elif mode == 'files' and captured['returncode'] == 0:
                receipt['checks']['scratch_limit_enforced'] = read_document(stdout).get('passed') is True
            elif mode == 'gpu_context':
                receipt['checks']['gpu_context_removed_after_timeout'] = b'TRUSTED_GPU_CONTEXT_READY\n' in stdout and captured['limit_reason'] == 'TIMEOUT' and captured['teardown_error'] is None and not assigned_contexts()
            require(limits_ok,'actual_limits_required_on_every_probe')
        except Exception as error:
            receipt.update(error_type=type(error).__name__,error=str(error)[:4096])
        finally:
            for listener in listeners:
                listener.close()
            if process is not None:
                try:
                    stop_owned(unit,root)
                    process.wait(timeout=5)
                    receipt['cgroup_removed'] = not (Path('/sys/fs/cgroup/system.slice')/(unit+'.service')).exists()
                except Exception as error:
                    receipt['teardown_error'] = str(error)[:4096]
                for pipe in (process.stdout,process.stderr):
                    if pipe is not None:pipe.close()
            receipt['passed'] = bool(receipt['checks']) and all(value is True for value in receipt['checks'].values()) and receipt.get('cgroup_removed') is True and not receipt.get('error') and not receipt.get('teardown_error')
            receipt['finished_unix'] = time.time()
            receipt_raw = json.dumps(receipt,sort_keys=True,indent=2).encode()
            (root/'RECEIPT.json').write_bytes(receipt_raw)
        if not receipt['passed']:
            return dict(passed=False, failed_mode=mode, receipt_path=str(root/'RECEIPT.json'),
                error=receipt.get('error'), stderr_path=str(root/'STDERR.bin'))
        all_checks.update(receipt['checks'])
        for name in receipt['checks']:
            references[name] = dict(passed=True,receipt_path=str(root/'RECEIPT.json'),receipt_sha256=hashlib.sha256(receipt_raw).hexdigest())
    require(set(all_checks) == GATE_CHECKS and all(all_checks.values()),'full_probe_matrix_required')
    gate = dict(schema='R132_GPU_CONFINEMENT_GATE_V1',identity=identity,passed=True,
        observed_unix=time.time(),expires_unix=time.time()+3600,checks=references)
    (base/'GATE.json').write_text(json.dumps(gate,sort_keys=True,indent=2))
    return dict(passed=True,gate_path=str(base/'GATE.json'),checks=len(all_checks))


def run_request(raw, *, spool, runtime_root, gate_path, admission_path, origin_verifier=None):
    parse_request(raw)
    lock_path = trusted_path(LOCK_PATH)
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW
        | os.O_NONBLOCK | os.O_CLOEXEC, 0o600)
    with os.fdopen(descriptor, 'r+') as lock:
        metadata = os.fstat(lock.fileno())
        require(stat.S_ISREG(metadata.st_mode) and metadata.st_nlink == 1
            and metadata.st_uid == os.geteuid() and metadata.st_mode & 0o077 == 0,
            'private_regular_GPU_lock_required')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        previous = lock.read(65537)
        require(len(previous) <= 65536, 'bounded_GPU_lock_receipt_required')
        if previous:
            last_job = read_document(previous.encode('utf-8'))
            admission = read_document(read_regular(trusted_path(admission_path), 65536))
            require(type(admission.get('observed_unix')) in (int, float)
                and admission['observed_unix'] > last_job['last_finished_unix'],
                'new_Main_census_after_previous_GPU_job_required')
        lock.seek(0)
        lock.truncate()
        lock.write(json.dumps(dict(last_finished_unix=time.time(),
            request_id=parse_request(raw)['request_id'], result_status='ADMISSION_IN_PROGRESS',
            requires_fresh_Main_census=True)))
        lock.flush()
        os.fsync(lock.fileno())
        result = _run_request(raw, spool=spool, runtime_root=runtime_root, gate_path=gate_path,
            admission_path=admission_path, origin_verifier=origin_verifier)
        if result['launch_attempted']:
            lock.seek(0)
            lock.truncate()
            lock.write(json.dumps(dict(last_finished_unix=time.time(), request_id=result['request_id'],
                result_status=result['status'], requires_fresh_Main_census=True)))
            lock.flush()
            os.fsync(lock.fileno())
        return result


def _run_request(raw, *, spool, runtime_root, gate_path, admission_path, origin_verifier=None):
    request = parse_request(raw)
    if request['origin']['kind'] == 'TRAIN_CHILD_RESPONSE':
        require(origin_verifier is not None, 'trusted_child_origin_verifier_required')
        verified_origin = origin_verifier(request)
        require(type(verified_origin) is dict and verified_origin.get('child_generated') is True
            and verified_origin.get('kind') == 'TRAIN_CHILD_RESPONSE'
            and verified_origin.get('record_sha256') == request['origin']['record_sha256'],
            'verified_child_origin_required')
        for name in ('request_record_sha256', 'commit_record_sha256'):
            require(type(verified_origin.get(name)) is str
                and re.fullmatch('[0-9a-f]{64}', verified_origin[name]), 'committed_TRAIN_origin_required')
    else:
        verified_origin = dict(kind='BUILDER_TEST', child_generated=False)
    admission_hash = validate_admission(admission_path, time.time())
    runtime = trusted_path(runtime_root)
    runtime_hash = validate_runtime(runtime)
    devices = device_identity()
    identity = policy_identity(runtime, runtime_hash, devices)
    gate_hash = validate_gate(gate_path, identity, time.time())
    spool = trusted_path(spool)
    spool.mkdir(mode=0o700, exist_ok=True)
    metadata = spool.stat()
    require(metadata.st_uid == os.geteuid() and metadata.st_mode & 0o077 == 0, 'private_broker_spool_required')
    root = spool / request['request_id']
    root.mkdir(mode=0o755, exist_ok=False)
    unit = 'orch-r132-kernel-' + hashlib.sha256(str(root).encode()).hexdigest()[:32]
    inputs = root / 'input'
    inputs.mkdir(mode=0o755)
    (root / 'empty').mkdir(mode=0o755)
    (inputs / 'candidate.py').write_bytes(request['source'].encode('utf-8'))
    kernel_validation = validate_kernel_source(request['source'])
    (inputs / 'kernel.py').write_text(kernel_validation['canonical_source'], encoding='utf-8')
    (inputs / 'harness.py').write_bytes(HARNESS.encode('utf-8'))
    (inputs / 'task.json').write_text(json.dumps(task_spec(), sort_keys=True), encoding='utf-8')
    for name, modulus, offset, divisor in (('left', 257, 128, 8), ('right', 251, 125, 16)):
        (inputs / (name + '.f32')).write_bytes(float_bytes(
            ((index % modulus) - offset) / divisor for index in range(max(LENGTHS))))
    filesystem = root / 'rootfs'
    filesystem.mkdir(mode=0o755)
    for name in ('usr', 'runtime', 'input', 'work', 'tmp', 'etc', 'dev', 'proc', 'sys', 'run'):
        (filesystem / name).mkdir(mode=0o755)
    for name in ('bin', 'lib', 'lib64'):
        (filesystem / name).symlink_to('usr/' + name)
    for directory in [root, inputs, filesystem, root / 'empty'] + [path for path in filesystem.iterdir() if not path.is_symlink()]:
        directory.chmod(0o755)
    for path in inputs.iterdir():
        path.chmod(0o444)
    invocation = command(root, runtime, unit)
    result = dict(schema='R132_KERNEL_RESULT_V1', request_id=request['request_id'],
        source_sha256=request['source_sha256'], requested_origin=request['origin'], origin=verified_origin,
        identity=identity, gate_sha256=gate_hash, admission_sha256=admission_hash, command=invocation,
        kernel_ast_sha256=kernel_validation['ast_sha256'],
        input_sha256={path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs.iterdir()},
        raw_request_sha256=hashlib.sha256(raw).hexdigest(), status='DISPATCH_INCOMPLETE',
        started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        output_is_untrusted=True, speedup_claim_authorized=False, launch_attempted=False)
    (root / 'REQUEST.json').write_bytes(raw)
    (root / 'INTENT.json').write_text(json.dumps(result, sort_keys=True, indent=2))
    process = None
    try:
        require(validate_admission(admission_path, time.time()) == admission_hash, 'admission_changed_before_launch')
        require(device_identity() == devices, 'device_mapping_changed_before_launch')
        preflight = subprocess.run(['sudo', '-n', 'systemctl', 'show', unit + '.service', '--property=LoadState'],
            capture_output=True, text=True, timeout=5)
        require(preflight.returncode in (0, 1) and preflight.stdout.strip() == 'LoadState=not-found',
            'no_existing_unit_reuse')
        result['launch_attempted'] = True
        process = subprocess.Popen(invocation, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, close_fds=True)
        captured = capture(process, lambda: stop_owned(unit, root), max_bytes=MAX_OUTPUT, timeout=120)
        stdout, stderr = captured.pop('stdout'), captured.pop('stderr')
        (root / 'STDOUT.bin').write_bytes(stdout)
        (root / 'STDERR.bin').write_bytes(stderr)
        result.update(capture=captured, stdout_sha256=hashlib.sha256(stdout).hexdigest(),
            stderr_sha256=hashlib.sha256(stderr).hexdigest())
        result['status'] = captured['limit_reason'] or 'PROCESS_FAILED'
        if captured['limit_reason'] is None:
            result['measurement'] = validate_measurements(stdout)
            if captured['returncode'] == 0:
                result['status'] = result['measurement']['status']
        if captured['teardown_error']:
            result['status'] = 'TEARDOWN_UNVERIFIED'
    except Exception as error:
        result.update(status='DISPATCH_FAILED_NO_RETRY', error_type=type(error).__name__, error=str(error)[:4096])
    finally:
        if result['launch_attempted']:
            try:
                stop_owned(unit, root)
                result['cgroup_removed'] = not (Path('/sys/fs/cgroup/system.slice') / (unit + '.service')).exists()
                result['gpu_context_teardown_verified'] = False
                result['requires_fresh_Main_census_before_next_job'] = True
                if not result['cgroup_removed']:
                    result['status'] = 'TEARDOWN_UNVERIFIED'
            except Exception as error:
                result.update(status='TEARDOWN_UNVERIFIED', teardown_error=str(error)[:4096])
        if process is not None:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                result['status'] = 'TEARDOWN_UNVERIFIED'
                try:
                    process.kill()
                    process.wait(timeout=5)
                except Exception as error:
                    result['client_still_running'] = True
                    result['client_cleanup_error'] = str(error)[:4096]
            finally:
                for pipe in (process.stdout, process.stderr):
                    if pipe is not None:
                        pipe.close()
        result['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        (root / 'RESULT.json').write_text(json.dumps(result, sort_keys=True, indent=2, allow_nan=False))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--describe', action='store_true')
    for name in ('request', 'spool', 'runtime-root', 'gate', 'admission'):
        parser.add_argument('--' + name, type=Path)
    options = parser.parse_args()
    if options.describe:
        print(json.dumps(environment_schema(), sort_keys=True, indent=2))
        return 0
    require(all(getattr(options, name) is not None for name in
        ('request', 'spool', 'runtime_root', 'gate', 'admission')), 'all_operator_paths_required')
    result = run_request(read_regular(options.request, 100000), spool=options.spool,
        runtime_root=options.runtime_root, gate_path=options.gate, admission_path=options.admission)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result['status'] == 'CORRECT' else 1


if __name__ == '__main__':
    sys.exit(main())
