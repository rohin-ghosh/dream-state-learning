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
        canonical_functions_match(original)
        for required in (RECIPE, "and plan['rehearsal_presentations'] in (0, 1)",
                         '                respond_to_presleep_inbox(child, stream, journal, cycle)\n'):
            if original.count(required) != 1:
                raise ValueError('incomplete_existing_R181_patch')
        return original
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


def journal_methods(source):
    journal = next(node for node in ast.parse(source).body if isinstance(node, ast.ClassDef) and node.name == 'StreamJournal')
    return {node.name: node for node in journal.body if isinstance(node, ast.FunctionDef)}


def patch_journal(original, canonical):
    methods = journal_methods(original)
    upstream = journal_methods(canonical)
    additions = ('_file_identity', '_record_snapshot', '_reload_state', '_validated_state', 'audit')
    if any(name in methods for name in additions):
        for name in additions:
            if name not in methods or ast.dump(methods[name], include_attributes=False) != ast.dump(upstream[name], include_attributes=False):
                raise ValueError('partial_or_different_journal_cache')
        for name in ('__init__', 'record', 'latest_checkpoint', 'read_inbox'):
            if 'self._scan()' in ast.unparse(methods[name]):
                raise ValueError('partial_journal_cache_callsite')
        return original
    lines = canonical.splitlines(keepends=True)
    first = upstream[additions[0]]
    start = min(node.lineno for node in [first, *first.decorator_list]) - 1
    block = ''.join(lines[start:upstream[additions[-1]].end_lineno]) + '\n\n'
    changed = replace_once(original, '    @staticmethod\n    def _validate_entry',
                           block + '    @staticmethod\n    def _validate_entry')
    replacements = (
        ('__init__', '            self._scan()\n', '            self._state = self._reload_state()\n'),
        ('record', '                state = self._scan()\n', '                state = self._validated_state()\n'),
        ('record', "                self._publish(self._records_fd, f'{index:020d}.json', record)\n",
         "                self._publish(self._records_fd, f'{index:020d}.json', record)\n"
         "                for name in (f'{index:020d}.intent.json', f'{index:020d}.json'):\n"
         "                    self._record_signatures[name] = self._file_identity(\n"
         "                        os.stat(name, dir_fd=self._records_fd, follow_symlinks=False))\n"
         "                state['index'], state['previous'] = index + 1, record['sha256']\n"),
        ('latest_checkpoint', "return deepcopy(self._scan()['latest'])", "return deepcopy(self._validated_state()['latest'])"),
        ('read_inbox', '            state = self._scan()\n', '            state = self._validated_state()\n'))
    for name, before, after in replacements:
        method = journal_methods(changed)[name]
        lines = changed.splitlines(keepends=True)
        body = ''.join(lines[method.lineno - 1:method.end_lineno])
        changed = ''.join(lines[:method.lineno - 1]) + replace_once(body, before, after) + ''.join(lines[method.end_lineno:])
    actual = journal_methods(changed)
    mutable = {'__init__', 'record', 'latest_checkpoint', 'read_inbox'}
    for name, method in methods.items():
        if name not in mutable and ast.dump(method, include_attributes=False) != ast.dump(actual[name], include_attributes=False):
            raise ValueError('noncache_journal_method_changed:' + name)
    return changed
