"""Existing caption parent API rebound to the exact recovered native incarnation."""

import inspect
import json
from pathlib import Path
import sys

from observe import observation
from recover import locations, read, require, sha


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import caption_remote as previous


def scoped_inspector(source, floor):
    changes = {
        "headers = [focus.metadata(path) for path in paths[-256:]]":
            f"headers = [entry for entry in [focus.metadata(path) for path in paths[-256:]] if entry['index'] >= {floor}]",
        "loaded_headers = [focus.metadata(path) for path in paths[:8]]":
            f"loaded_headers = [focus.metadata(directory / '{floor:020d}.json')]",
    }
    for original, replacement in changes.items():
        require(source.count(original) == 1, 'exact_existing_caption_readout_seam')
        source = source.replace(original, replacement)
    return source


def run(request):
    root, _, control, _ = locations('CAPTION')
    observed = observation('CAPTION')
    require(observed['status'] == 'LOADED', 'actual_caption_recovered_native_required')
    owner = observed['native']
    previous.PID, previous.START = owner['pid'], owner['start_ticks']
    previous.EPOCH = HERE / 'CAPTION_RENEWED_EPOCH.private.json'
    previous.focus.STORE = HERE

    def identity():
        actual = previous.focus.process(owner['pid'])
        require(actual and actual['start_ticks'] == owner['start_ticks'] and actual['uid'] == 2524
            and actual['state'] not in ('T', 'Z', 'X') and str(control / 'GUARD.json') in actual['argv'],
            'exact_recovered_caption_identity')
        plan = read(control / 'PLAN.json')
        return dict(pid=owner['pid'], start_ticks=owner['start_ticks'], state=actual['state'],
            cmdline_sha256=actual['cmdline_sha256'], root=str(root), physical_gpu=2,
            plan_sha256=sha(control / 'PLAN.json'), guard_sha256=sha(control / 'GUARD.json'),
            hard_end_unix=plan['hard_end_unix'])

    previous.identity = identity
    namespace = dict(previous.inspect.__globals__)
    source = scoped_inspector(inspect.getsource(previous.inspect), observed['loaded']['index'])
    exec(compile(source, __file__ + ':current_incarnation', 'exec'), namespace)
    previous.inspect = namespace['inspect']
    source = inspect.getsource(previous.main)
    require(source.count("ROOT/'control/PLAN.json'") == 1, 'exact_parent_source_lookup')
    source = source.replace("ROOT/'control/PLAN.json'", "ROOT/'control_r233_recovery/PLAN.json'")
    namespace = dict(previous.main.__globals__)
    exec(compile(source, __file__ + ':new_finite_parent_epoch', 'exec'), namespace)
    return namespace['main'](request)


if __name__ == '__main__':
    print(json.dumps(run(json.load(sys.stdin)), sort_keys=True))
