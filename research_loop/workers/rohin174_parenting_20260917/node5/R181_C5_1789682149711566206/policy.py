"""Apply only Main's R181 native recipe and presleep inbox deltas."""

import ast


SELECT = '''def select_rehearsal_rows(plan, old_rows):
    presentations = plan.get('rehearsal_presentations', 1)
    require(type(presentations) is int and presentations in (0, 1), 'explicit_rehearsal_schedule')
    return old_rows if presentations else []
'''
PRESLEEP = '''def respond_to_presleep_inbox(child, stream, journal, cycle):
    require(stream.pending is None and stream.sleep_due, 'presleep_inbox_at_completed_response')
    known_ids = {event.event_id for event in stream.history.events}
    incoming = [event for event in journal.read_inbox() if event.event_id not in known_ids]
    if not any(event.actor == 'parent' for event in incoming):
        return False
    journal.record('PRESLEEP_INBOX_RESPONSE', dict(cycle=cycle,
        event_ids=[event.event_id for event in incoming], maximum_extra_segments=1,
        all_external_text_masked=True, additional_own_row_presentations=16))
    stream.step(child.generate, child.count_tokens, journal.record, incoming=incoming)
    return True
'''
RECIPE = '''        available_old_rows = len(old_rows)
        old_rows = select_rehearsal_rows(self.plan, old_rows)
        record('SLEEP_RECIPE', dict(policy='R181_NEW_ONLY_V1' if not self.plan.get('rehearsal_presentations', 1)
            else 'LEGACY_FULL_REHEARSAL', new_presentations=16, new_rows=len(new_rows),
            available_old_rows=available_old_rows, selected_old_rows=len(old_rows), anchor_lambda=0.25))
'''


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('actual_source_anchor_count:' + old[:70])
    return text.replace(old, new, 1)


def patch_native(original):
    if 'def select_rehearsal_rows(' in original or 'def respond_to_presleep_inbox(' in original:
        raise ValueError('already_R181_no_double_patch')
    changed = replace_once(original,
        "    require(plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 1\n",
        "    require(plan['new_presentations'] == 16 and type(plan['rehearsal_presentations']) is int\n"
        "            and plan['rehearsal_presentations'] in (0, 1)\n")
    changed = replace_once(changed, 'def readout_name(plan, cycle):', SELECT + '\n\ndef readout_name(plan, cycle):')
    changed = replace_once(changed, '    def sleep(self, new_rows, old_rows, anchors, record):\n',
        '    def sleep(self, new_rows, old_rows, anchors, record):\n' + RECIPE)
    changed = replace_once(changed, 'def finish_sleep(child, stream, journal, anchors, root, cycle):',
        PRESLEEP + '\n\ndef finish_sleep(child, stream, journal, anchors, root, cycle):')
    changed = replace_once(changed, '                new_rows = stream.pending_rows()\n                pending = stream.checkpoint()',
        '                respond_to_presleep_inbox(child, stream, journal, cycle)\n'
        '                new_rows = stream.pending_rows()\n                pending = stream.checkpoint()')
    ast.parse(changed)
    return changed


def canonical_functions_match(canonical):
    module = ast.parse(canonical)
    for name, text in (('select_rehearsal_rows', SELECT), ('respond_to_presleep_inbox', PRESLEEP)):
        actual = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == name)
        if ast.dump(actual, include_attributes=False) != ast.dump(ast.parse(text).body[0], include_attributes=False):
            raise ValueError('canonical_Main_function_mismatch:' + name)
    return True
