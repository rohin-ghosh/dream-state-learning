"""Apply only Main's four R181 deltas to the actual Node3 native sources."""

import ast
from pathlib import Path

from takeover import HERE, REPO, require, read, write, reference


def function_text(source, name):
    node = next(item for item in ast.parse(source).body
                if isinstance(item, ast.FunctionDef) and item.name == name)
    return '\n'.join(source.splitlines()[node.lineno - 1:node.end_lineno])


def patch_native(original, canonical):
    require('R181_NEW_ONLY_V1' not in original, 'not_already_patched')
    previous = "require(plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 1"
    replacement = "require(plan['new_presentations'] == 16 and type(plan['rehearsal_presentations']) is int\n            and plan['rehearsal_presentations'] in (0, 1)"
    require(original.count(previous) == 1, 'one_original_schedule_validation')
    result = original.replace(previous, replacement)
    for name, anchor in (('select_rehearsal_rows', 'def readout_name('),
                         ('respond_to_presleep_inbox', 'def finish_sleep(')):
        require(result.count(anchor) == 1, 'one_helper_anchor:' + anchor)
        result = result.replace(anchor, function_text(canonical, name) + '\n\n\n' + anchor)
    anchor = '    def sleep(self, new_rows, old_rows, anchors, record):\n'
    start = canonical.index(anchor) + len(anchor)
    end = canonical.index('        from gpu.orch_r108_guided_native import validate_anchor_inventory', start)
    require(result.count(anchor) == 1, 'one_native_sleep')
    result = result.replace(anchor, anchor + canonical[start:end])
    anchor = '                new_rows = stream.pending_rows()\n'
    require(result.count(anchor) == 1, 'one_post_presleep_pre_request_boundary')
    result = result.replace(anchor, '                respond_to_presleep_inbox(child, stream, journal, cycle)\n' + anchor)
    compile(result, '<node3-r181-native>', 'exec')
    return result


def build():
    canonical = (REPO / 'gpu/orch_r125_continual_native.py').read_text()
    for physical in (0, 1, 2, 3, 4, 7):
        folder = HERE / 'r181' / ('physical' + str(physical))
        original = (folder / 'original_native.py').read_text()
        write(folder / 'new_native.py', patch_native(original, canonical))
    write(HERE / 'r181/DELTA_SOURCE.json', dict(canonical=reference(REPO / 'gpu/orch_r125_continual_native.py'),
        patch=reference(__file__), status='FOUR_DELTAS_PREPARED_NOT_APPLIED_TO_RUNNING_CHILDREN',
        originals_preserved=True, new_presentations=16, rehearsal_presentations=0))


if __name__ == '__main__':
    build()
