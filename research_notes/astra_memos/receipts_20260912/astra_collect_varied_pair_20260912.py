"""Pinned varied root0 metadata collector. Main executes. No scoring or tokenizer.

Author also authored this pair's runner/material: not independent science review.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import signal
import sys
import tarfile
import time
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
HOME = Path('/localhome/local-rohing')
ROOT = HOME / 'astra_diagnostics/astra_varied_memory_replay_20260912_attempt1/fits_root0_attempt1'
SOURCE = HOME / 'astra_sources/dc2e9a3c11ccd9a3f10ea28513723bbfb8420247'
RUNNER = Path('/tmp/astra_varied_memory_pair_20260912.py')
PYTHON = HOME / 'v2/venv/bin/python'
ARCHIVE = Path('/tmp/astra_varied_pair_root0_terminal_20260912.tgz')
PLAN_SHA = '2120bb93d0458b789bb3db408e57dd077f528cfadec35691b0e5fb27889756ca'
RUNNER_SHA = 'b58f65cd482bbd2d762edc030c7967a1ecd004829cf8271c74c15d3ca54bc8c7'
HELPER_SHA = 'd2152c179ca9a6b9801933a480ed62cd203018868a52034e13676963787579eb'
CHECK_SHA = 'a586b03bdb9c52f1061aa1e477ae983cc9d45ec0a2cd440642851fd8df8b609f'
LAUNCHER_SHA = 'd3053e0f7e9811e4bf6d34b5cb0d9e81119c8e9dd15b7abfe0a3b954e107ae38'
STARTED = '2026-09-12T20:59:48.092375+00:00'
UUID = 'GPU-71e5a3e2-e9c8-5caf-70d8-73794ac34821'
PID, DEVICE, ARMS = 224587, '1', ('SINGLE_VIEW', 'FOUR_VIEW')
CLAIM = 'AUTHORED_VARIED_PHRASING_REPLAY_NOT_CHILD_EXPERIENCE_NOT_BRAIN_PROOF'
COLLECTION_SECONDS = 300


def load(path, checksum, name):
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError('aliased dependency: '+str(path))
    payload = common.read_bytes(path) if 'common' in globals() else path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != checksum:
        raise ValueError('dependency changed: '+str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(payload, str(path), 'exec'), module.__dict__)
    return module


common = load(Path('/tmp/astra_collect_memory_only_20260912.py'), HELPER_SHA, 'varied_collection_common')
require, read, digest = common.require, common.read, common.digest


def present(path):
    return common.unaliased(path).exists()


def alive():
    return Path(f'/proc/{PID}').exists()


def finite(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def timing(observed):
    started = dt.datetime.fromisoformat(STARTED).timestamp()
    require(finite(observed) and observed >= started, 'invalid observation time')
    return dict(full_reservation_seconds=observed-started, declared_pair_seconds=1500,
        external_collection_margin_seconds=300, declared_full_deadline_unix=started+1800,
        late_observation=observed > started+1800, overrun_seconds=max(0., observed-started-1800), budget_extended=False)


def check_uuid(gpu, xml):
    require(gpu['gpu_uuid'] == UUID and [node.text for node in ET.fromstring(xml).findall('gpu/uuid')] == [UUID], 'launch/release GPU UUID differs')


def records():
    require(digest(ROOT/'plan.json') == read(ROOT/'plan.sha256.json')['sha256'] == PLAN_SHA, 'plan changed')
    plan, launch = read(ROOT/'plan.json'), read(ROOT/'launch/launch.json')
    require(plan['root'] == str(ROOT) and plan['source_root'] == str(SOURCE) and plan['seed'] == 0 and plan['device'] == DEVICE and
        plan['source_hashes']['varied_pair_sidecar'] == RUNNER_SHA and plan['arm_order'] == list(ARMS) and
        plan['pair_seconds'] == 1500 and plan['cleanup_seconds'] == 140, 'wrong pinned root0 plan')
    require(launch['pid'] == PID and launch['node'] == 3 and launch['device'] == DEVICE and launch['seed'] == 0 and
        launch['root'] == str(ROOT) and launch['source'] == str(SOURCE) and launch['started_utc'] == STARTED and
        launch['plan_sha256'] == PLAN_SHA and launch['script_sha256'] == RUNNER_SHA and launch['launcher_sha256'] == LAUNCHER_SHA and
        launch['controller_bound_seconds'] == 1500 and launch['external_collection_margin_seconds'] == 300 and
        launch['aggregate_campaign_ceiling_seconds'] == 5400 and launch['continuous_reservation'] is True and
        launch['generation_calls'] == 128 and launch['no_automatic_progression'] is True and launch['arm_order'] == list(ARMS), 'launch custody changed')
    require(launch['command'] == [str(PYTHON),'-B',str(RUNNER),'run','--source-root',str(SOURCE),'--runroot',str(ROOT),'--allow-gpu'], 'launch command changed')
    check_uuid(launch['gpu'], common.read_bytes(ROOT/'launch/gpu.xml'))
    return plan, launch


def status():
    records()
    markers = ('fit-worker/process.json','fit-worker/supervision.json','adapter/DONE','fit-result.json','capture-result.json','arm-result.json',
        'dev/run/data/manifest.json','dev/run/worker/supervision.json','dev/reduction.json',
        'exact/run/data/manifest.json','exact/run/worker/supervision.json','exact/reduction.json')
    return dict(controller_pid=PID, controller_present=alive(), terminal_available=present(ROOT/'run/terminal.json'),
        arms={arm:{name:present(ROOT/'run'/arm/name) for name in markers} for arm in ARMS},
        scope='markers only; terminal/fit/reduction contents not read', observation=timing(time.time()))


def file_stats(roots, model_root=None):
    result = {}
    for root in roots:
        root = common.unaliased(root)
        paths = [root, *root.rglob('*')] if root.is_dir() else [root]
        for path in paths:
            if path.is_symlink():
                require(root == model_root and path.is_file() and not path.is_dir(), 'only original model leaf links allowed')
                result[str(path)] = (common.identity(path.lstat()),str(path.resolve(strict=True)),common.identity(path.stat()))
                continue
            common.unaliased(path)
            require(path.is_file() or path.is_dir(), 'special input path')
            result[str(path)] = common.identity(path.stat())
    return result


def current_inputs(plan, driver):
    require(driver.sources() == plan['source_hashes'] and all(plan[key] == value for key,value in driver.inspect_material(plan['materialroot']).items()), 'source/material/native receipt changed')
    require(driver.base.model_hashes(plan['model']) == plan['model_files'], 'current base changed')
    parent = plan['parent']
    parent_files = driver.trainer._warm_inventory(parent['parent'])
    parent_state = driver.old.state_inventory(parent['parent'])
    require(parent_files == parent['parent_files'] and parent_state == plan['parent_state'] and
        parent['parent'] == str(Path(plan['parentroot'])/'fit_teach/adapter') and
        all(digest(path) == checksum for path,checksum in parent['provenance'].items()) and
        driver.base.tree_hashes(Path(plan['parentroot'])/'readouts/teach') == parent['readout_files'], 'current original parent/provenance changed')
    children = {}
    for arm in ARMS:
        stage = ROOT/'run'/arm
        if present(stage/'fit-result.json'):
            fit = read(stage/'fit-result.json')
            adapter = stage/'adapter'
            require(fit['adapter'] == str(adapter) and fit['parent'] == parent['parent'] and fit['parent_files'] == parent_files and
                present(adapter/'DONE'), 'child identity/DONE changed')
            saved_files = driver.trainer._warm_inventory(adapter)
            saved_state = driver.old.state_inventory(adapter)
            driver.validate_manifest(plan, arm, read(adapter/'train_manifest.json'), parent_state, saved_state)
            require(saved_files == fit['adapter_files'] and fit['manifest_sha256'] == digest(adapter/'train_manifest.json') and
                fit['accounting'] == driver.COUNTS[arm], 'saved child inventory/manifest changed')
            children[arm] = fit
    return children


def worker(stage, command, successful=False):
    process_path, receipt_path = stage/'process.json', stage/'supervision.json'
    require(present(process_path) == present(receipt_path), 'unaccounted worker; manual reconciliation required')
    if not present(process_path):
        require(not successful, 'missing required worker')
        return None
    process, receipt = read(process_path), read(receipt_path)
    require(process['argv'] == command and process['device'] == DEVICE and type(process['pid']) is int and process['pid'] > 1 and
        process['pgid'] == process['pid'] and finite(process['started']) and finite(process['timeout']) and 0 < process['timeout'] <= 600,
        'worker command/ownership/window differs')
    require(receipt['device'] == DEVICE and finite(receipt['reserved_seconds']) and
        all(receipt[key] is True for key in ('owned_group_empty','gpu_processes_absent','reservation_release_verified')), 'worker release/cost differs')
    if successful:
        require(receipt['ok'] is True and receipt['returncode'] == 0 and receipt['error'] is None, 'successful worker receipt invalid')
    return process, receipt


def panel(root, template, fit, driver, required):
    data = root/'run/data'
    reduced_path = root/'reduction.json'
    if not present(data/'manifest.json'):
        require(not required and not present(reduced_path), 'missing capture/reduction cannot be zero')
        return dict(status='PARTIAL_OR_NOT_STARTED_NOT_SCORED')
    require(fit is not None, 'readout capture without verified fit')
    plan = read(root/'plan.json')
    require(digest(root/'plan.json') == read(root/'plan.sha256.json')['sha256'], 'readout seal changed')
    expected = dict(template, adapter=fit['adapter'], adapter_files=fit['adapter_files'], device=DEVICE,
        lease_end=read(ROOT/'run/reservation.json')['effective_deadline'])
    expected['identity'] = driver.base.expected_identity(expected, fit['adapter'])
    require(plan == expected and read(data/'identity.json') == dict(backend=plan['identity'], model_files=plan['model_files'], adapter_files=fit['adapter_files']), 'readout identity/inputs changed')
    process, receipt = worker(root/'run/worker', [str(PYTHON),'-B','-m',
        driver.dev.__name__ if root.name == 'dev' else driver.exact.__name__, '_worker','--root',str(root),'--allow-gpu'], True)
    require(read(data/'manifest.json')['files'] == driver.base.tree_hashes(data, ('manifest.json',)) and
        not present(data/'failure.json') and read(data/'backend.cleanup.json')['closed'] is True, 'capture manifest/cleanup differs')
    expected_names = {request['call_id']+suffix for request in plan['requests'] for suffix in ('.request.json','.response.json')}
    require({path.name for path in (data/'calls').iterdir()} == expected_names, 'incomplete/extra raw calls')
    ready = read(data/'backend.ready.json')
    require(ready['pid'] == process['pid'] and finite(ready['ready']) and process['started'] <= ready['ready'] <= process['started']+receipt['reserved_seconds'], 'backend ownership differs')
    previous = ready['ready']
    for request, native in zip(plan['requests'], plan['native_inputs'], strict=True):
        sent = read(data/'calls'/(request['call_id']+'.request.json'))
        received = read(data/'calls'/(request['call_id']+'.response.json'))
        response = received['response']
        require(sent['request'] == request and sent['identity'] == plan['identity'] and
            sent['prompt_sha256'] == driver.base.value_hash(request['prompt']) and received['response_sha256'] == driver.base.value_hash(response), 'raw request/response binding differs')
        require(finite(sent['started']) and finite(received['ended']) and previous <= sent['started'] <= received['ended'] <= process['started']+receipt['reserved_seconds'], 'raw call clock differs')
        previous = received['ended']
        driver.base.validate_response(request, response)
        require(all(response[key] == native[key] for key in ('rendered_prompt','prompt_token_ids')), 'actual native prefix differs')
    usage = driver.base.usage(data)
    require(usage == read(data/'usage.json'), 'native usage receipt differs')
    summary = dict(status='CAPTURE_HASHES_VERIFIED_NOT_SCORED', raw_pairs=len(plan['requests']),
        plan_sha256=digest(root/'plan.json'), capture_sha256=digest(data/'manifest.json'))
    if present(reduced_path):
        reduction = read(reduced_path)
        count = 48 if root.name == 'dev' else 16
        require(reduction['complete'] is True and reduction['counts']['total'] == count and len(reduction['rows']) == count and
            [row['case_id'] for row in reduction['rows']] == [case['id'] for case in plan['cases']] and
            reduction['plan_sha256'] == summary['plan_sha256'] and reduction['capture_sha256'] == summary['capture_sha256'] and
            reduction['identity'] == plan['identity'] and reduction['source_hashes'] == plan['source_hashes'] and
            reduction['model_files'] == plan['model_files'] and reduction['adapter_files'] == fit['adapter_files'] and
            reduction['cost'] == usage and reduction['reserved_seconds'] == receipt['reserved_seconds'] and
            reduction['native_token_text_audit'] is True, 'existing reduction binding/completeness differs')
        if root.name == 'exact':
            require(reduction['process_sha256'] == digest(root/'run/worker/process.json') and
                reduction['supervision_sha256'] == digest(root/'run/worker/supervision.json'), 'exact custody changed')
        summary['reduction_sha256'] = digest(reduced_path)
    else:
        require(not required, 'COMPLETE pair missing reduction')
    return summary


def audit(plan, terminal, children, driver):
    stage = ROOT/'run'
    require(terminal['status'] in ('COMPLETE','FAILED_PARTIAL_NO_RETRY') and terminal['controller_pid'] == PID and
        terminal['device'] == DEVICE and terminal['seed'] == 0 and terminal['plan_sha256'] == PLAN_SHA and
        all(terminal[key] == value for key,value in read(stage/'reservation.json').items()), 'terminal custody differs')
    require(all(finite(terminal[key]) for key in ('started','ended','effective_deadline','reserved_seconds','worker_reserved_seconds')) and
        terminal['effective_deadline'] == terminal['started']+1500 and terminal['ended'] >= terminal['started'] and
        terminal['real_lease_end'] == plan['real_lease_end'] and terminal['effective_deadline'] <= min(plan['deadline'],plan['real_lease_end']-10) and
        terminal['deadline_met'] is (terminal['ended'] <= terminal['effective_deadline']), 'terminal bounds/accounting invalid')
    require(terminal['worker_accounting_complete'] is True and terminal['release_verified'] is True and
        terminal['gate_evaluated'] is False and terminal['automatic_progression'] is False and terminal['outcome_selective_skips'] is False and
        terminal['claim'] == CLAIM and terminal['origin'] == 'UNRESOLVED_LOCAL_HASHES_ONLY', 'terminal release/progression differs')
    complete = terminal['status'] == 'COMPLETE'
    require(set(terminal['arms']) <= set(ARMS) and set(terminal['captured']) in (set(),{'SINGLE_VIEW'},set(ARMS)), 'unexpected terminal arms')
    reports, ordered, expected_workers = {}, [], set()
    for arm in ARMS:
        fit = children.get(arm)
        target = stage/arm
        captured = read(target/'capture-result.json') if present(target/'capture-result.json') else None
        result = read(target/'arm-result.json') if present(target/'arm-result.json') else None
        require(terminal['captured'].get(arm) == captured and (arm not in terminal['arms'] or terminal['arms'][arm] == result), 'terminal arm/capture results changed')
        if captured is not None:
            require(captured['fit'] == fit, 'captured fit differs')
        for name, command in [('fit-worker',driver.fit_command(plan,arm,target/'adapter'))] + [
            (name+'/run/worker',[str(PYTHON),'-B','-m',module.__name__,'_worker','--root',str(target/name),'--allow-gpu'])
            for name,module in (('dev',driver.dev),('exact',driver.exact))]:
            path = target/name
            record = worker(path,command,complete or (name == 'fit-worker' and fit is not None))
            if record is not None:
                expected_workers.add(path)
                ordered.append(record)
                if name == 'fit-worker' and fit is not None:
                    require(fit['supervision'] == record[1], 'fit supervision changed')
        panels = {}
        for name in ('dev','exact'):
            panels[name] = panel(target/name,plan['templates'][name],fit,driver,complete)
            if captured is not None:
                bound = captured['captures'][name]
                require(bound == dict(plan_sha256=panels[name]['plan_sha256'],capture_sha256=panels[name]['capture_sha256'],
                    pairs=panels[name]['raw_pairs'],status='CAPTURED_NOT_REDUCED'), 'capture result changed')
            if result is not None:
                bound = result['readouts'][name]
                require(bound['sha256'] == panels[name]['reduction_sha256'] and bound['reduction'] == read(target/name/'reduction.json'), 'arm reduction changed')
        if result is not None:
            require(captured is not None and result['fit'] == fit and result['captures'] == captured['captures'], 'arm result differs')
        require(not complete or (fit is not None and captured is not None and result is not None), 'COMPLETE arm missing artifacts')
        reports[arm] = dict(verified_fit=fit is not None, panels=panels)
    require({path.parent for path in stage.rglob('process.json')} == expected_workers ==
        {path.parent for path in stage.rglob('supervision.json')}, 'unexpected/missing process receipts')
    require(len({process['pid'] for process,_ in ordered}) == len(ordered), 'worker PID reuse/identity ambiguity')
    for previous,current in zip(ordered,ordered[1:]):
        require(previous[0]['started']+previous[1]['reserved_seconds'] <= current[0]['started'], 'workers overlapped/out of order')
    require(math.isclose(sum(receipt['reserved_seconds'] for _,receipt in ordered),terminal['worker_reserved_seconds'],abs_tol=1e-6) and
        terminal['worker_reserved_seconds'] <= terminal['reserved_seconds']+.001, 'worker cost sum differs')
    if complete:
        require(set(terminal['arms']) == set(terminal['captured']) == set(ARMS) and len(ordered) == 6 and
            terminal['error'] is None and terminal['deadline_met'] is True and terminal['reserved_seconds'] <= 1500, 'invalid COMPLETE pair')
    return reports


def finish_body(collection_started):
    observed = status()
    require(not observed['controller_present'] and observed['terminal_available'], 'wait for PID absence AND terminal')
    plan, launch = records()
    terminal = read(ROOT/'run/terminal.json')
    validation_path = Path(str(ARCHIVE)+'.validation.json')
    release_json, release_xml = ROOT/'run/main_release.json', ROOT/'run/main_release.xml'
    existing = [present(path) for path in (ARCHIVE,validation_path,release_json,release_xml)]
    require(not any(existing) or all(existing), 'orphan/partial collection preserved; no overwrite/retry')
    before = common.metadata(ROOT,HOME)
    protected = [SOURCE,RUNNER,Path('/tmp/astra_memory_only_20260912.py'),Path('/tmp/astra_fading_sentinel_20260912.py'),
        Path(plan['model']),Path(plan['parentroot']),Path(plan['materialroot']),Path(plan['native_prepare_path'])]
    protected += [ROOT/'run'/arm/'adapter' for arm in ARMS if present(ROOT/'run'/arm/'adapter')]
    stats = file_stats(protected,Path(plan['model']))
    driver = load(RUNNER,RUNNER_SHA,'varied_collection_driver')
    driver.bind(SOURCE,'/tmp/astra_memory_only_20260912.py','/tmp/astra_fading_sentinel_20260912.py')
    children = current_inputs(plan,driver)
    reports = audit(plan,terminal,children,driver)
    require(not alive() and file_stats(protected,Path(plan['model'])) == stats and common.metadata(ROOT,HOME) == before, 'evidence changed during audit')
    prefix = ROOT.relative_to(HOME).as_posix()+'/'
    collector_sha = digest(Path(__file__))
    if all(existing):
        validation,release = read(validation_path),read(release_json)
        require(validation['archive'] == str(ARCHIVE) and validation['sha256'] == digest(ARCHIVE) and validation['files'] == before and
            validation['plan_sha256'] == PLAN_SHA and validation['audits'] == reports and
            validation['collector_sha256'] == release['collector_sha256'] == collector_sha and
            release['terminal_sha256'] == digest(ROOT/'run/terminal.json') and release['launch_sha256'] == digest(ROOT/'launch/launch.json') and
            release['xml_sha256'] == digest(release_xml) and release['plan_sha256'] == PLAN_SHA and release['controller_pid'] == PID and
            release['controller_absent'] is True and release['full_release'] is True and release['device'] == DEVICE and release['terminal_status'] == terminal['status'], 'existing collection changed')
        check_uuid(release['gpu'],common.read_bytes(release_xml))
        require(release['timing'] == timing(dt.datetime.fromisoformat(release['release_utc']).timestamp()), 'release accounting differs')
        common.validate_archive(io.BytesIO(common.read_bytes(ARCHIVE)),before,prefix)
        require(not alive() and file_stats(protected,Path(plan['model'])) == stats and common.metadata(ROOT,HOME) == before, 'current evidence changed')
        return dict(status='ALREADY_COLLECTED_VERIFIED_NO_WRITES',archive=str(ARCHIVE),sha256=validation['sha256'],observation=timing(time.time()))
    checker = load(SOURCE/'gpu/astra_mini_sudoku_diagnostic.py',CHECK_SHA,'varied_collection_full_vacancy')
    gpu,xml = checker.check_free(DEVICE)
    check_uuid(gpu,xml)
    released = dt.datetime.now(dt.timezone.utc)
    require(not alive() and file_stats(protected,Path(plan['model'])) == stats and common.metadata(ROOT,HOME) == before, 'inputs/controller changed before release')
    common.write_new(release_xml,xml.encode())
    common.write_json(release_json,dict(full_release=True,controller_absent=True,controller_pid=PID,device=DEVICE,gpu=gpu,
        release_utc=released.isoformat(),timing=timing(released.timestamp()),collection_started_utc=dt.datetime.fromtimestamp(collection_started,dt.timezone.utc).isoformat(),
        collection_seconds_to_release=time.time()-collection_started,collection_alarm_seconds=300,
        terminal_status=terminal['status'],plan_sha256=PLAN_SHA,terminal_sha256=digest(ROOT/'run/terminal.json'),
        launch_sha256=digest(ROOT/'launch/launch.json'),xml_sha256=digest(release_xml),collector_sha256=collector_sha,
        worker_reserved_seconds=terminal['worker_reserved_seconds'],controller_reserved_seconds=terminal['reserved_seconds'],
        accounting='worker/controller windows overlap full launch-to-vacancy interval; never add them',monetary_cost=None))
    manifest = common.metadata(ROOT,HOME)
    require(all(manifest.get(name) == checksum for name,checksum in before.items()), 'old metadata changed')
    with ARCHIVE.open('xb') as stream, tarfile.open(fileobj=stream,mode='w:gz',format=tarfile.USTAR_FORMAT) as archive:
        for name,checksum in manifest.items():
            payload = common.read_bytes(HOME/name)
            require(hashlib.sha256(payload).hexdigest() == checksum, 'metadata changed during packing')
            member = tarfile.TarInfo(name)
            member.size,member.mode = len(payload),0o600
            archive.addfile(member,io.BytesIO(payload))
    common.validate_archive(io.BytesIO(common.read_bytes(ARCHIVE)),manifest,prefix)
    require(not alive() and file_stats(protected,Path(plan['model'])) == stats and common.metadata(ROOT,HOME) == manifest, 'evidence changed after packaging')
    validation = dict(archive=str(ARCHIVE),sha256=digest(ARCHIVE),files=manifest,plan_sha256=PLAN_SHA,collector_sha256=collector_sha,
        terminal_status=terminal['status'],audits=reports,excluded_suffixes=sorted(common.EXCLUDED),excluded_directories=['__pycache__'],
        collection_seconds=time.time()-collection_started,collection_alarm_seconds=300,completion_observation=timing(time.time()),
        scope='raw receipts/IDs and existing reduction bindings verified; no scoring, tokenizer, or reducer execution',
        token_decode_audit='prior reducer native_token_text_audit receipt bound, NOT rerun',
        weights='preserved native; current base/parent/successful saved children checked once per invocation',
        authorship='collector author also authored runner/material; not independent scientific review')
    common.write_json(validation_path,validation)
    return dict(status='COLLECTED',terminal_status=terminal['status'],archive=str(ARCHIVE),sha256=validation['sha256'],
        files=len(manifest),observation=validation['completion_observation'])


def finish():
    started = time.time()
    require(signal.getitimer(signal.ITIMER_REAL) == (0.,0.), 'refuse nested collector timer')
    def expired(number, frame):
        raise TimeoutError('300s external collector alarm; preserve any partial artifacts; no budget extension')
    previous = signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,COLLECTION_SECONDS)
    try:
        return finish_body(started)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=('status','finish'))
    args = parser.parse_args()
    print(json.dumps(status() if args.stage == 'status' else finish(),indent=2,sort_keys=True,allow_nan=False),flush=True)
