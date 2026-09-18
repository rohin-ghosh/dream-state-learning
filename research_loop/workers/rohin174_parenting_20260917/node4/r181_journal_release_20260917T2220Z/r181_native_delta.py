"""Copy only Main's R181 deltas onto an actual, already-R179 native source."""

import ast


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def function(source, name):
    matches = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == name]
    require(len(matches) == 1, 'unique_Main_function:' + name)
    node = matches[0]
    return ''.join(source.splitlines(keepends=True)[node.lineno - 1:node.end_lineno])


def once(source, old, new):
    require(source.count(old) == 1, 'actual_source_seam_drift:' + old[:70])
    return source.replace(old, new, 1)


def patch_native(actual, canonical):
    require('from gpu.orch_r179_context_survival import retain_or_compact' in actual, 'preserve_actual_R179_native')
    require('select_rehearsal_rows' not in actual and 'respond_to_presleep_inbox' not in actual, 'fresh_R181_successor_only')
    selector = function(canonical, 'select_rehearsal_rows')
    responder = function(canonical, 'respond_to_presleep_inbox')
    old_schedule = "plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 1"
    new_schedule = "plan['new_presentations'] == 16 and type(plan['rehearsal_presentations']) is int\n            and plan['rehearsal_presentations'] in (0, 1)"
    require(new_schedule in canonical, 'exact_Main_plan_zero_or_one')
    sleep_start = '    def sleep(self, new_rows, old_rows, anchors, record):\n'
    main_start = canonical.index(sleep_start) + len(sleep_start)
    main_end = canonical.index('        from gpu.orch_r108_guided_native import validate_anchor_inventory', main_start)
    prefix = canonical[main_start:main_end]
    require('SLEEP_RECIPE' in prefix and 'old_rows = select_rehearsal_rows(self.plan, old_rows)' in prefix,
        'Main_selection_before_eligibility_and_encoding')
    patched = once(actual, old_schedule, new_schedule)
    patched = once(patched, sleep_start, sleep_start + prefix)
    seam = '                new_rows = stream.pending_rows()\n'
    patched = once(patched, seam, '                respond_to_presleep_inbox(child, stream, journal, cycle)\n' + seam)
    insertion = '\n\ndef readout_name(plan, cycle):'
    patched = once(patched, insertion, '\n\n' + selector.rstrip() + '\n\n' + responder.rstrip() + insertion)
    restored = patched.replace(new_schedule, old_schedule, 1).replace(sleep_start + prefix, sleep_start, 1)
    restored = restored.replace('                respond_to_presleep_inbox(child, stream, journal, cycle)\n' + seam, seam, 1)
    restored = restored.replace('\n\n' + selector.rstrip() + '\n\n' + responder.rstrip() + insertion, insertion, 1)
    require(restored == actual, 'all_other_actual_native_bytes_unchanged')
    ast.parse(patched)
    return patched
