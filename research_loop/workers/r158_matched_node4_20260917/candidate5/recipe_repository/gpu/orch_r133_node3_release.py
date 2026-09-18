"""Read-only node3 release verification with honest optional scanner timing."""

import inspect
from pathlib import Path
from types import FunctionType

from gpu import orch_r133_retire_old_lanes as original


def scanner_summary_compatible(report):
    result = dict(report)
    result.setdefault('finished_unix', None)
    return result


def verify(evidence_root):
    evidence = Path(evidence_root)
    original.require(evidence.parent == original.BASE/'orch_r133_retirement_20260916',
                     'exact_node3_evidence_directory')
    request = original.read(evidence/'REQUEST.json')['request']
    original.require(request['node'] == 'ovx2' and request['physical'] in (3, 4, 5, 6, 7),
                     'owned_remaining_node3_only')
    def fresh(output, physical):
        return scanner_summary_compatible(original.fresh_release(output, physical))
    function = FunctionType(original.verify_release_remote.__code__,
                            dict(original.verify_release_remote.__globals__, fresh_release=fresh))
    return function(dict(evidence_root=str(evidence)))


def grid_listener_source():
    source = inspect.getsource(original.retire_remote)
    original.require(source.count('0x8 | 0x80') == 2, 'pinned_two_inotify_masks')
    return source.replace('0x8 | 0x80', '0x8 | 0x80 | 0x100')


def retire_grid(request):
    original.require(request['node'] == 'ovx2' and type(request['physical']) is int
                     and request['physical'] == 7, 'only_owned_grid7_listener')
    from gpu.orch_r133_node3_handoff import archive_paths
    def fresh(output, physical):
        return scanner_summary_compatible(original.fresh_release(output, physical))
    namespace = dict(original.retire_remote.__globals__, archive=archive_paths, fresh_release=fresh)
    exec(compile(grid_listener_source(), __file__+':grid_create_event', 'exec'), namespace)
    return namespace['retire_remote'](request)
