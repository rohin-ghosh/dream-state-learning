"""Finite OFF/AUTH protocol capture using the existing native worker supervisor."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time

sys.dont_write_bytecode = True
SELF = Path(__file__).absolute()
MATERIAL = Path('/tmp/astra_birth_protocol_clarified_material_20260913.py')
MATERIAL_SHA = 'ecba56d4c25ee14c4caf26dafc8d6d38d18406e8107a19bee76b01bdefa6e76d'
FORMATION = Path('/tmp/astra_born_rulegame_formation_run_20260912.py')
FORMATION_SHA = '90919a280f78cce8f41c1ef7bf7b08e722f4ab0b3cf3d278d256bfd91653dda4'
CONTROLLER = 1500
COLLECTION = 300
STATES = ('OFF', 'AUTH')
CLAIMS = 'SOURCE_AUTHORED_PROTOCOL_PRACTICE_NOT_CLEAN; scaffolded protocol only; no training, induction, H1/H2, P1, G3/G5 or freeze'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(filename):
    return hashlib.sha256(Path(filename).read_bytes()).hexdigest()


def read(filename):
    return json.loads(Path(filename).read_text())


def write(filename, value):
    with Path(filename).open('x') as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')


def load(filename, expected, name):
    require(digest(filename) == expected, 'dependency hash mismatch: '+str(filename))
    spec = importlib.util.spec_from_file_location(name, filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def api(source):
    source = Path(source).resolve(strict=True)
    sys.path.insert(0, str(source))
    from organism_v6 import fundamental_teaching_readout as capture
    require(Path(capture.__file__).resolve().parent.parent == source, 'wrong source import')
    material = load(MATERIAL, MATERIAL_SHA, 'protocol_probe_material')
    formation = load(FORMATION, FORMATION_SHA, 'protocol_probe_formation')
    return capture, material, formation


def read_plan(root, pin):
    root = Path(root).absolute()
    require(digest(root/'plan.json') == pin, 'plan hash mismatch')
    plan = read(root/'plan.json')
    require(plan['root'] == str(root) and plan['driver_sha256'] == digest(SELF), 'root/driver changed')
    require(plan['states'] == list(STATES) and plan['claims'] == CLAIMS and plan['controller_seconds'] == CONTROLLER,
            'probe scope changed')
    require(plan['python'] == os.path.abspath(sys.executable), 'wrong interpreter')
    for filename, expected in plan['source_hashes'].items():
        require(digest(filename) == expected, 'source changed: '+filename)
    return root, plan


def prepare(args):
    upstream = Path(args.formation_root).absolute()
    require(digest(upstream/'plan.json') == args.formation_plan_sha256, 'formation plan mismatch')
    inherited = read(upstream/'plan.json')
    os.environ['V6_MODEL'] = inherited['model']
    capture, material, formation = api(inherited['source_root'])
    normalized = read(upstream/'normalized_birth.json')
    require(digest(upstream/'normalized_birth.json') == inherited['normalized_file_sha256'], 'birth normalization changed')
    formation.verify_custody(normalized, inherited['source_root'], capture.base)
    require(time.time()+CONTROLLER+COLLECTION < args.deadline < inherited['real_lease_end']-21600,
            'bounded work/collection must precede six-hour lease margin')
    candidate = material.build_candidate()
    material.check_candidate(candidate)
    requests = material.call_map(candidate)
    require(requests['OFF'] == requests['AUTH'] and len(requests['OFF']) == 16, 'fixed paired inventory required')
    child = normalized['pin']['child_identity']
    tokenizer = capture.base.native_tokenizer(inherited['model'])
    cells = {}
    for state in STATES:
        adapter = child['adapter_input'] if state == 'AUTH' else None
        native = capture.native_inputs(tokenizer, requests[state])
        require(all(len(row['prompt_token_ids'])+request['max_tokens'] <= capture.base.MAX_MODEL_LEN
                    for row, request in zip(native, requests[state], strict=True)), 'context budget exceeded')
        cells[state] = dict(model=inherited['model'], adapter=adapter,
            identity=capture.base.expected_identity(inherited, adapter), model_files=normalized['pin']['model_files'],
            adapter_files=normalized['adapter_all_files'] if adapter else {}, requests=requests[state], native_inputs=native)
    require(cells['AUTH']['identity'] == child, 'original AUTH identity required')
    root = Path(args.root).absolute()
    root.mkdir()
    source_hashes = dict(inherited['source_hashes'])
    for filename in (SELF, MATERIAL, FORMATION, formation.BIRTH, formation.birth.COMMON,
                     Path(capture.__file__), Path(material.spec.__file__), Path(material.process.__file__),
                     Path(material.rulegame.__file__)):
        source_hashes[str(filename)] = digest(filename)
    plan = dict(root=str(root), source_root=inherited['source_root'], python=os.path.abspath(sys.executable),
        driver_sha256=digest(SELF), source_hashes=source_hashes, states=list(STATES), claims=CLAIMS,
        model_origin='UNRESOLVED_LOCAL_HASHES_ONLY', model=inherited['model'], device=args.device,
        deadline=args.deadline, real_lease_end=inherited['real_lease_end'], controller_seconds=CONTROLLER,
        eos_token_id=tokenizer.eos_token_id,
        collection_seconds=COLLECTION, candidate=candidate, cells=cells, normalized=normalized,
        formation_root=str(upstream), formation_plan_sha256=args.formation_plan_sha256,
        metric_caveat='public_contract_correct is formatting-sensitive; instruction_compliant is reference serialization, not semantic truth')
    write(root/'plan.json', plan)
    return dict(status='PREPARED_NOT_LAUNCHED', plan_sha256=digest(root/'plan.json'), root=str(root))


def command(mode, root, pin, *extra):
    return [os.path.abspath(sys.executable), '-B', str(SELF), mode, '--root', str(root), '--plan-sha256', pin, *extra]


def worker(args):
    require(args.allow_gpu, 'explicit GPU opt-in required')
    root, plan = read_plan(args.root, args.plan_sha256)
    require(args.state in STATES and os.environ.get('CUDA_VISIBLE_DEVICES') == plan['device'], 'worker state/device mismatch')
    capture, _, formation = api(plan['source_root'])
    stage = root/'run'/args.state
    with formation.birth.owned_worker(stage/'worker', args.hard_end):
        data = stage/'data'
        data.mkdir()
        capture.capture(plan['cells'][args.state], data)


def controller(args):
    require(args.allow_gpu, 'explicit GPU opt-in required')
    root, plan = read_plan(args.root, args.plan_sha256)
    require(os.getpid() == os.getpgrp() == os.getsid(0) and os.environ.get('CUDA_VISIBLE_DEVICES') == plan['device'],
            'fresh owned controller session/device required')
    capture, _, formation = api(plan['source_root'])
    run = root/'run'
    run.mkdir()
    started = time.time()
    hard_end = min(started+CONTROLLER, plan['deadline'])
    write(run/'controller.json', dict(formation.birth.process_identity(os.getpid()), started_wall=started, hard_end=hard_end))
    try:
        with formation.birth.work_window(hard_end):
            for state in STATES:
                stage = run/state
                stage.mkdir()
                with formation.birth.supervisor_window(hard_end):
                    capture.base.supervise(run, dict(model=plan['model'], device=plan['device'], lease_end=hard_end),
                        stage/'worker', command('_worker', root, args.plan_sha256, '--state', state,
                            '--hard-end', str(hard_end), '--allow-gpu'), stage/'data/calls')
            write(run/'capture_barrier.json', dict(states=list(STATES), calls=32, scores_computed=False, completed_wall=time.time()))
        return dict(status='CAPTURED_NOT_SCORED', seconds=time.time()-started)
    except BaseException as error:
        write(run/'failure.json', dict(error=str(error), error_type=type(error).__name__, seconds=time.time()-started))
        raise


def launch(args):
    require(args.allow_gpu, 'explicit GPU opt-in required')
    root, plan = read_plan(args.root, args.plan_sha256)
    capture, _, formation = api(plan['source_root'])
    require(time.time()+CONTROLLER+COLLECTION < plan['deadline'], 'full phase/collection window unavailable')
    test_log = Path(args.native_cpu_log).read_text()
    require(f'Ran {args.native_test_count} tests' in test_log and test_log.rstrip().endswith('OK'), 'CPU acceptance missing')
    formation.verify_custody(plan['normalized'], plan['source_root'], capture.base)
    from gpu.astra_mini_sudoku_diagnostic import check_free
    gpu, xml = check_free(plan['device'])
    logs = root/'launch'
    logs.mkdir()
    (logs/'gpu.xml').write_text(xml)
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES=plan['device'], V6_MODEL=plan['model'],
        PYTHONPATH=plan['source_root'], ASTRA_SOURCE_ROOT=plan['source_root'], HF_HUB_OFFLINE='1',
        TRANSFORMERS_OFFLINE='1', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='1',
        VLLM_WORKER_MULTIPROC_METHOD='spawn')
    started = time.time()
    require(started+CONTROLLER+COLLECTION < plan['deadline'], 'preflight exhausted bounded launch window')
    with (logs/'stdout.log').open('xb') as stream:
        process = subprocess.Popen(command('_controller', root, args.plan_sha256, '--allow-gpu'), cwd=plan['source_root'],
            env=environment, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    write(logs/'process.json', dict(formation.birth.process_identity(process.pid), started_wall=started,
        launcher=formation.birth.process_identity(os.getpid()), gpu_uuid=gpu['gpu_uuid'],
        cpu_log_sha256=digest(args.native_cpu_log), plan_sha256=args.plan_sha256))
    print(json.dumps(dict(status='LAUNCHED_NOT_COMPLETE', controller_pid=process.pid, root=str(root))), flush=True)
    returncode = process.wait()
    write(logs/'exit.json', dict(returncode=returncode, ended_wall=time.time()))
    return dict(status='EXITED_REQUIRES_COLLECTION', returncode=returncode)


def reduce_captures(root, plan, capture, material):
    barrier = read(root/'run/capture_barrier.json')
    require(barrier['scores_computed'] is False and barrier['states'] == list(STATES) and barrier['calls'] == 32,
            'complete capture barrier required')
    require(not list((root/'run').rglob('failure.json')), 'failed capture cannot be reduced')
    tokenizer = capture.base.native_tokenizer(plan['model'])
    outputs = {}
    usage = {}
    for state in STATES:
        stage = root/'run'/state
        receipt = read(stage/'worker/supervision.json')
        require(receipt['ok'] and receipt['reservation_release_verified'] and receipt['returncode'] == 0, 'owned worker not released')
        data = stage/'data'
        manifest = read(data/'manifest.json')
        require(manifest['files'] == capture.base.tree_hashes(data, ('manifest.json',)), 'incomplete capture manifest')
        for filename, expected in manifest['files'].items():
            require(digest(data/filename) == expected, 'raw capture changed')
        cell = plan['cells'][state]
        require(read(data/'backend.cleanup.json')['closed'] is True, 'backend not closed')
        require(read(data/'identity.json') == dict(backend=cell['identity'], model_files=cell['model_files'],
            adapter_files=cell['adapter_files']), 'cell identity mismatch')
        require(len(list((data/'calls').glob('*.json'))) == 32, 'unexpected raw call count')
        outputs[state] = {}
        for request, native in zip(cell['requests'], cell['native_inputs'], strict=True):
            sent = read(data/'calls'/(request['call_id']+'.request.json'))
            got = read(data/'calls'/(request['call_id']+'.response.json'))
            require(sent['request'] == request and sent['identity'] == cell['identity'], 'raw request mismatch')
            response = got['response']
            require(sent['prompt_sha256'] == capture.base.value_hash(request['prompt'])
                and got['response_sha256'] == capture.base.value_hash(response), 'raw content hash mismatch')
            require(0 <= got['ended']-sent['started'] <= 120, 'invalid call duration')
            capture.base.validate_response(request, response)
            require(all(response[key] == native[key] for key in ('rendered_prompt', 'prompt_token_ids')), 'native prompt mismatch')
            outputs[state][request['case_id']] = response['text']
        usage[state] = capture.base.usage(data)
        require(read(data/'usage.json') == usage[state], 'recorded usage differs from raw calls')
        capture.base.audit_native_calls(tokenizer, data)
    return dict(scores=material.check_outputs(plan['candidate'], outputs), usage=usage, raw_outputs=outputs,
                claims=CLAIMS, metric_caveat=plan['metric_caveat'])


def collect(args):
    started = time.time()
    root, plan = read_plan(args.root, args.plan_sha256)
    capture, material, formation = api(plan['source_root'])
    formation.verify_custody(plan['normalized'], plan['source_root'], capture.base)
    require(read(root/'launch/exit.json')['returncode'] == 0, 'failed/unfinished controller; preserve raw partial evidence')
    process = read(root/'launch/process.json')
    require(process['plan_sha256'] == args.plan_sha256, 'launcher plan mismatch')
    workers = [read(root/'run'/state/'worker/process.json') for state in STATES]
    for identity in (process, process['launcher'], *workers):
        try:
            current = formation.birth.process_identity(identity['pid'])
        except FileNotFoundError:
            continue
        require('start_ticks' in identity and current['start_ticks'] != identity['start_ticks'], 'owned process still live')
    from gpu.astra_mini_sudoku_diagnostic import check_free
    gpu, xml = check_free(plan['device'])
    require(gpu['gpu_uuid'] == process['gpu_uuid'], 'GPU identity changed')
    write(root/'release.json', dict(verified_wall=time.time(), gpu=gpu, controller_exited=True))
    (root/'release_gpu.xml').write_text(xml)
    result = reduce_captures(root, plan, capture, material)
    require(time.time()-started <= COLLECTION, 'collection budget exhausted')
    write(root/'audit.json', result)
    archive = Path(args.archive)
    require(not archive.exists() and root not in archive.parents, 'fresh external metadata archive required')
    files = {}
    for filename in root.rglob('*'):
        require(not filename.is_symlink(), 'metadata symlink rejected')
        if filename.is_file():
            relative = str(filename.relative_to(root))
            formation.common.scan_text(filename.read_bytes(), relative)
            files[relative] = digest(filename)
    with tarfile.open(archive, 'x:gz') as output:
        for filename in sorted(files):
            output.add(root/filename, arcname=filename, recursive=False)
    validation = dict(status='COLLECTED_RELEASED', root=str(root), plan_sha256=args.plan_sha256,
        archive_sha256=digest(archive), files=files, claims=CLAIMS)
    require(time.time()-started <= COLLECTION, 'collection budget exhausted')
    write(str(archive)+'.validation.json', validation)
    return dict(status=validation['status'], archive=str(archive), archive_sha256=validation['archive_sha256'],
                validation_sha256=digest(str(archive)+'.validation.json'), members=len(files))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('prepare', 'start', '_launch', '_controller', '_worker', 'collect'))
    parser.add_argument('--root', required=True)
    parser.add_argument('--plan-sha256')
    parser.add_argument('--formation-root')
    parser.add_argument('--formation-plan-sha256')
    parser.add_argument('--device', default='0')
    parser.add_argument('--deadline', type=float)
    parser.add_argument('--state', choices=STATES)
    parser.add_argument('--hard-end', type=float)
    parser.add_argument('--native-cpu-log')
    parser.add_argument('--native-test-count', type=int)
    parser.add_argument('--archive')
    parser.add_argument('--allow-gpu', action='store_true')
    args = parser.parse_args()
    if args.mode == 'start':
        require(args.allow_gpu, 'explicit GPU opt-in required')
        root, _ = read_plan(args.root, args.plan_sha256)
        environment = dict(os.environ)
        environment.pop('CUDA_VISIBLE_DEVICES', None)
        with (root/'launcher.log').open('xb') as stream:
            process = subprocess.Popen([os.path.abspath(sys.executable), '-B', str(SELF), '_launch', *sys.argv[2:]],
                env=environment, stdin=subprocess.DEVNULL, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        result = dict(status='LAUNCHER_STARTED', launcher_pid=process.pid)
    elif args.mode == 'collect':
        formation = load(FORMATION, FORMATION_SHA, 'protocol_collection_window')
        with formation.birth.collection_window():
            result = collect(args)
    else:
        result = {'prepare': prepare, '_launch': launch, '_controller': controller, '_worker': worker, 'collect': collect}[args.mode](args)
    print(json.dumps(result, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
