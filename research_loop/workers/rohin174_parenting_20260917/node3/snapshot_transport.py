"""Fresh-wrapper, in-memory R166 TRAIN reducer; no remote files are written."""

import inspect
import json
from pathlib import Path
import subprocess
import takeover


def poll(physical, cursor=None):
    helper, assignments = takeover.release()
    bundle = takeover.HERE / ('source_' + assignments[physical]['arm'])
    sources = {str(path.relative_to(bundle)): path.read_text() for path in bundle.rglob('*.py')}
    prepared = takeover.read(takeover.HERE / 'parents' / ('physical' + str(physical)) / 'PREPARATION.json')
    root = prepared['assignment']['active_child_root']
    script = '''import ast, hashlib, importlib.abc, importlib.util, json, sys, types
from pathlib import Path
'''
    script += 'sources=' + repr(sources) + '\nroot=' + repr(root) + '\ncursor=' + repr(cursor) + '\n'
    script += inspect.getsource(takeover.require) + '\n' + inspect.getsource(takeover.project_artifact_writer)
    script += '''
class MemorySource:
    def __init__(self, name=''):
        self.name = name
    def __truediv__(self, name):
        return MemorySource(name)
    def read_text(self):
        return sources[self.name]
    def __str__(self):
        return '<owned-node3/' + self.name + '>'
class SourceLoader(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    def find_spec(self, fullname, path=None, target=None):
        name = fullname.replace('.', '/') + '.py'
        if fullname in ('gpu', 'organism_v6'):
            return importlib.util.spec_from_loader(fullname, self, is_package=True)
        if name in sources:
            return importlib.util.spec_from_loader(fullname, self)
        return None
    def create_module(self, specification):
        return None
    def exec_module(self, module):
        name = module.__name__.replace('.', '/') + '.py'
        if name in sources:
            module.__file__ = '<owned-node3/' + name + '>'
            exec(compile(sources[name], module.__file__, 'exec'), module.__dict__)
sys.meta_path.insert(0, SourceLoader())
project_artifact_writer(MemorySource())
from gpu.orch_r166_parent_snapshot import poll, _digest
observed = poll(root, cursor, cursor_sha256=_digest(cursor) if cursor is not None else None, max_records=100000)
print(json.dumps(observed, sort_keys=True, allow_nan=False))
'''
    result = subprocess.run(['bash', str(takeover.REPO / 'gpu/ovx2_ssh.sh'), 'python3 -B -'],
                            input=script, capture_output=True, text=True, timeout=90)
    if result.returncode:
        final_line = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else 'no_remote_error_text'
        raise ValueError('readonly_R166_snapshot:' + final_line[:240])
    observed = json.loads(result.stdout)
    state = observed['snapshot']
    mapping = prepared['recovery_clock']
    for kind, field in (('REQUEST', 'request_count'), ('RESPONSE', 'response_count')):
        offset = mapping['terminal_counts'][kind] - mapping['saved_counts'][kind]
        state['journal_' + field] = state[field]
        state[field] += offset
    state['R179_lifetime_offsets_preserved'] = True
    for delivery in state['delivered'].values():
        delivery['journal_request_count'] = delivery['request_count']
        delivery['request_count'] += mapping['terminal_counts']['REQUEST'] - mapping['saved_counts']['REQUEST']
    return observed


if __name__ == '__main__':
    import sys
    physical = int(sys.argv[1])
    observed = poll(physical)
    folder = takeover.HERE / 'parents' / ('physical' + str(physical))
    takeover.write(folder / 'LIVE_BOOTSTRAP.json', observed)
    state = observed['snapshot']
    print(json.dumps({key: state[key] for key in ('journal_id', 'caught_up', 'response_count', 'request_count', 'sleep_count', 'head_sha256')}))
