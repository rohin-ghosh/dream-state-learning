"""CPU-only late identity binding; keeps the frozen CODE actor closure unchanged."""

import argparse
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys
import time

from gpu import orch_r118_code_parallel_final as final


io, require, handoff = final.io, final.require, final.handoff


def rebind(service, *, clock=time.time, cancel=final.cancel_timer):
    service = Path(service)
    runtime = io.read(service / 'RUNTIME.json')
    authorization = runtime['authorization']
    document, own, unused = handoff.authorize(authorization, runtime['root'], 'LAUNCH', clock)
    require(own['service'] == str(service.resolve()), 'exact_stage_service')
    old_root, new_root = Path(own['final_old_root']), Path(own['final_new_root'])
    require(not new_root.exists(), 'new_FINAL_custody_no_retry')
    plan = deepcopy(final.unused_allocation(old_root))
    source_manifest = handoff.ref(final.SOURCE_ROOT.parent / 'SOURCE_SHA256.json')
    require(source_manifest['sha256'] == own['source_manifest_sha256']
        and runtime['source_manifest'] == source_manifest, 'same_frozen_actor_source')
    plan.update(source_root=str(final.SOURCE_ROOT), source_manifest=source_manifest,
        cpu_receipt=runtime['cpu_tests'])
    final.functions()['source_check'](plan)
    released = handoff.checked(runtime['handoff'])
    require(released['all_original_processes_exited'] is True
        and not handoff.alive(released['native']['identity']) and not handoff.alive(released['guardian']),
        'actual_old_CODE_exit')
    launched = io.read(service / 'LAUNCH.json')
    require(handoff.alive(launched['identity']) and handoff.alive(launched['guardian']),
        'actual_Main_dispatched_guard_and_native')
    expected = io.read(old_root / 'CPU_DISPATCH.json')['identity']
    require(expected == own['old_final_identity'] and expected['pid'] != 1519259,
        'only_pinned_own_FINAL_never_Main_selector')
    new_root.mkdir(parents=True)
    io.write(new_root / 'REBIND_STARTED.json', dict(old_allocation=handoff.ref(old_root / 'PLAN.json'),
        old_timer=expected, authorization=authorization, auxiliary_stager=handoff.ref(__file__),
        cpu_receipt=runtime['cpu_tests']))
    stopped = cancel(old_root, expected, clock=clock)
    plan['inherited_allocation'] = handoff.ref(old_root / 'PLAN.json')
    io.write(new_root / 'FINAL_REBIND.json', dict(schema='R118_CODE_FINAL_CUSTODY_REBIND_V1',
        old_root=str(old_root), service=str(service), old_timer_stop=stopped,
        authorization=authorization, auxiliary_stager=handoff.ref(__file__), old_handoff=runtime['handoff'],
        new_launch=handoff.ref(service / 'LAUNCH.json'), native_identity=launched['identity'],
        guardian_identity=launched['guardian'], same_eight_calls=True, native_cap_added=0,
        old_ledger_preserved=True, canonical_selection_path=plan['main_binding_path']))
    plan['rebind_reference'] = handoff.ref(new_root / 'FINAL_REBIND.json')
    io.write(new_root / 'PLAN.json', plan)
    final.functions()['validate_plan'](new_root)
    return new_root


def wait_for_launch(service, *, clock=time.time, pause=time.sleep):
    service = Path(service)
    runtime = io.read(service / 'RUNTIME.json')
    while True:
        handoff.authorize(runtime['authorization'], runtime['root'], 'LAUNCH', clock)
        require(not (service / 'GUARD_TERMINAL.json').exists(), 'guard_terminal_no_late_custody')
        if (service / 'LAUNCH.json').exists():
            return
        pause(.2)


def serve(service):
    service = Path(service)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU_stager_only')
    (service / 'FINAL_STAGER_ONCE').mkdir()
    runtime = io.read(service / 'RUNTIME.json')
    handoff.authorize(runtime['authorization'], runtime['root'], 'LAUNCH')
    io.write(service / 'FINAL_STAGER_ARMED.json', dict(identity=handoff.identities.identity(os.getpid()),
        runtime=handoff.ref(service / 'RUNTIME.json'), source=handoff.ref(__file__),
        observed_unix=time.time(), GPU_launches=0, actual_FINAL_rebind=False))
    try:
        wait_for_launch(service)
        root = rebind(service)
        with (root / 'SCHEDULER.log').open('x') as output:
            child = subprocess.Popen([sys.executable, '-B', '-m', final.MODULE, 'schedule', '--root', str(root)],
                cwd=final.SOURCE_ROOT, env=dict(os.environ, PYTHONPATH=str(final.SOURCE_ROOT),
                    CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'),
                stdout=output, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
        io.write(root / 'SCHEDULER_SPAWN.json', dict(identity=handoff.identities.identity(child.pid),
            parent=handoff.identities.identity(os.getpid()), CPU_only=True, observed_unix=time.time()))
        end = min(time.time() + 45, handoff.checked(runtime['authorization'])['expires_unix'])
        while not (root / 'SCHEDULER_STARTED.json').exists():
            require(child.poll() is None and time.time() < end, 'actual_FINAL_scheduler_start_deadline')
            time.sleep(.1)
        supervision = final.bind_supervision(root, runtime['authorization'])
        io.write(service / 'FINAL_STAGER_COMPLETE.json', dict(final_root=str(root),
            supervision=handoff.ref(service / 'SUPERVISION.json'), observed_unix=time.time(),
            actual_FINAL_timer_identity=supervision['final_identity_bindings'][0]['identity'], GPU_launches=0))
    except BaseException as error:
        io.write(service / 'FINAL_STAGER_FAILED.json', dict(error_type=type(error).__name__,
            observed_unix=time.time(), no_retry=True, original_calls_unchanged=True))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--service', required=True, type=Path)
    serve(parser.parse_args().service)
