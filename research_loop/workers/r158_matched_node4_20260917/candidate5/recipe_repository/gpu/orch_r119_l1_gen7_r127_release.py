"""R127 retargeting of the proven whole-task releaser; acceptance unchanged."""

import argparse
import inspect
import os
from pathlib import Path

try:
    import orch_r119_l1_gen7_release as original
except ImportError:
    from gpu import orch_r119_l1_gen7_release as original


ROOT = Path('/localhome/local-rohing/orch_r119_l1_gen7_continuation_20260915_attempt1')
EVALUATOR = Path('/localhome/local-rohing/orch_r127_route_transfer_20260915')
PINS = {'PLAN.json':'12710e14684045bd5e5b31187bac6094ac4e00e65e318a2b6a11d724d0139846',
        'READY.json':'e99f4ce44ce8ae5c9534ae4de45b1935f12f797439fafec382a3caeceaa3b5df'}
ORIGINAL_SHA = '62320700cedc00c99481f41dccaa2b1a59f5d1aa3c2dd8ded3c0b3a8ebb1a127'
HANDOVER_SHA = '0e74cde9a418160c903bc9b5bb2b6d91733300b20b993348dcc1ee580a15a2b7'


def retarget(source):
    old = "    assert read(HANDOVER / 'EXECUTOR_CANCELLED.json')['status'] == 'CANCELLED_PRE_RETIREMENT_SUPERVISOR_AND_NATIVE_CONTINUED'"
    assert source.count(old) == 1
    source = source.replace(old,"    assert not (DEST / 'PRE_SIGNAL.json').exists(), 'new_one_shot_release_only'")
    assert source.count("ROOT / 'gpu7' /") == 3
    return source.replace("ROOT / 'gpu7' /",'ROOT /')


def owned_descriptor(expected, root, role, uuid):
    assert original.identity(expected['pid']) == expected and expected['uid'] == os.getuid()
    process = Path('/proc') / str(expected['pid'])
    arguments = (process / 'cmdline').read_bytes().split(b'\0')
    worker = root / 'orch_r119_l1_gen7_continue.py'
    assert str(worker).encode() in arguments and str(root).encode() in arguments and role.encode() in arguments
    assert arguments[arguments.index(b'--root')+1] == str(root).encode()
    assert original.sha(worker) == original.read(root/'CURSOR_RESUME.json')['source_sha256']
    if role == 'generate':
        assert ('CUDA_VISIBLE_DEVICES='+uuid).encode() in (process/'environ').read_bytes().split(b'\0')
    descriptor = os.pidfd_open(expected['pid'])
    try:
        assert original.identity(expected['pid']) == expected
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def execute(handover):
    assert original.sha(original.__file__) == ORIGINAL_SHA
    assert original.sha(handover/'source/orch_r119_l1_gen7_handover.py') == HANDOVER_SHA
    ready = original.read(handover/'PRE_GPU.json')
    assert ready['cpu_passed'] and ready['builder_line'].startswith('[Builder]')
    assert ready['source_sha256'] == original.sha(__file__)
    context = dict(original.__dict__,ROOT=ROOT,HANDOVER=handover,DEST=handover/'release_attempt1',
                   EVALUATOR=EVALUATOR,PINS=PINS,owned_descriptor=owned_descriptor,__file__=__file__)
    exec(compile(retarget(inspect.getsource(original.execute)),__file__,'exec'),context)
    context['execute']()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--handover',type=Path,required=True)
    execute(parser.parse_args().handover)
