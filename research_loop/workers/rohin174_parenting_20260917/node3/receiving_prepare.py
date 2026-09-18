"""Preparation-only support for the already-absent original support parent."""

import inspect
import receiving_parent as receiver


def prepare(physical, handoff_path):
    source = inspect.getsource(receiver.prepare)
    before = "stopped['status'] == 'SETTLED_ORIGINAL_PARENT_STOPPED'"
    after = "stopped['status'] in ('SETTLED_ORIGINAL_PARENT_STOPPED', 'ORIGINAL_PARENT_ALREADY_ABSENT')"
    receiver.base.require(source.count(before) == 1, 'one_documented_retirement_status_check')
    namespace = dict(receiver.__dict__)
    exec(compile(source.replace(before, after), __file__, 'exec'), namespace)
    return namespace['prepare'](physical, handoff_path)
