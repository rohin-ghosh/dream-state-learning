"""Transplant only Main's four R181 native changes; retain every other source byte."""

import ast


def replace_once(source, before, after):
    if source.count(before) != 1:
        raise ValueError('R181_exact_delta_match:' + before[:70])
    return source.replace(before, after, 1)


def patch(source, canonical):
    functions = {node.name: ast.get_source_segment(canonical, node) for node in ast.parse(canonical).body
                 if isinstance(node, ast.FunctionDef)}
    before = "plan['new_presentations'] == 16 and plan['rehearsal_presentations'] == 1"
    after = "plan['new_presentations'] == 16 and type(plan['rehearsal_presentations']) is int\n            and plan['rehearsal_presentations'] in (0, 1)"
    result = replace_once(source, before, after)
    result = replace_once(result, 'def readout_name(', functions['select_rehearsal_rows'] + '\n\n\ndef readout_name(')
    sleep_lines = canonical.splitlines(keepends=True)
    sleep_start = next(index for index, line in enumerate(sleep_lines) if line == '    def sleep(self, new_rows, old_rows, anchors, record):\n')
    sleep_end = next(index for index in range(sleep_start + 1, len(sleep_lines))
                     if sleep_lines[index].startswith('        from gpu.orch_r108_guided_native import '))
    prefix = ''.join(sleep_lines[sleep_start:sleep_end])
    result = replace_once(result, '    def sleep(self, new_rows, old_rows, anchors, record):\n', prefix)
    result = replace_once(result, 'def finish_sleep(', functions['respond_to_presleep_inbox'] + '\n\n\ndef finish_sleep(')
    result = replace_once(result, '                prepare_sleep(child, stream, journal, cycle)\n',
                          '                prepare_sleep(child, stream, journal, cycle)\n                respond_to_presleep_inbox(child, stream, journal, cycle)\n')
    compile(result, 'actual_R181_successor_native', 'exec')
    return result
