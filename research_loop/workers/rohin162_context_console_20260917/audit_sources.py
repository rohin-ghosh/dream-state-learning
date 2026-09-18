"""Read-only source/plan census; never opens child text or evaluation data."""

import ast
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import time


FILES = {
    'native': ('gpu/orch_r125_continual_native.py', ('prepare_sleep', 'finish_sleep', 'run')),
    'stream': ('organism_v6/orch_r125_continual_stream.py', ('commit_sleep', 'render', 'checkpoint')),
    'history': ('organism_v6/orch_r124_train_history.py', ('compact', 'evict_oldest', 'render', 'checkpoint')),
    'presentation': ('organism_v6/orch_r125_plain_context.py', ('event_message', 'replay_prefix')),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def inspect_source(root):
    result = {}
    for label, (relative, wanted) in FILES.items():
        path = Path(root) / relative
        raw = path.read_bytes()
        if len(raw) > 1024 * 1024:
            raise ValueError('source_limit')
        tree = ast.parse(raw)
        functions = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name in wanted:
                functions[node.name] = {
                    'line': node.lineno,
                    'ast_sha256': digest(ast.dump(node, include_attributes=False).encode()),
                }
        result[label] = {'path': str(path), 'sha256': digest(raw), 'functions': functions}
    return result


def inspect_rows(rows):
    output = []
    for row in rows:
        result = {'life_root': row['life_root'], 'node': row['node'], 'observed_unix': time.time()}
        try:
            identity = row['natives'][0]['identity']
            stat_path = Path('/proc') / str(identity['pid']) / 'stat'
            if stat_path.exists():
                fields = stat_path.read_text().rsplit(')', 1)[1].split()
                result['registered_identity_live'] = fields[19] == str(identity['start_ticks']) and fields[0] != 'Z'
            else:
                result['registered_identity_live'] = False
            source = row['current_source_root']
            plan_path = Path(row['natives'][0]['plan_ref']['path'])
            raw = plan_path.read_bytes()
            if len(raw) > 1024 * 1024:
                raise ValueError('plan_limit')
            plan = json.loads(raw)
            result['plan_ref'] = {'path': str(plan_path), 'sha256': digest(raw)}
            result['plan'] = {key: plan.get(key) for key in (
                'root', 'source_root', 'presleep_variant', 'context_limit', 'segment_tokens',
                'segments_per_sleep', 'presentation_version', 'hard_end_unix')}
            result['source'] = inspect_source(source)
        except (OSError, ValueError, KeyError, IndexError) as error:
            result['error'] = str(error)
        output.append(result)
    return output


def main():
    if '--remote' in sys.argv:
        print(json.dumps(inspect_rows(json.load(sys.stdin)), sort_keys=True))
        return
    root = Path.cwd()
    roster_path = root / 'research_loop/workers/r171_forward_roster_20260917/CURRENT_LEARNER_ROSTER.json'
    roster_raw = roster_path.read_bytes()
    roster = json.loads(roster_raw)
    rows = [row for row in roster['rows'] if row['status'] == 'LIVE']
    nodes = sorted({row['node'] for row in rows})
    remote_command = '/localhome/local-rohing/v2/venv/bin/python -B -c ' + shlex.quote(Path(__file__).read_text()) + ' --remote'

    def capture(node):
        process = subprocess.run(['bash', f'gpu/{node}_ssh.sh', remote_command],
            input=json.dumps([row for row in rows if row['node'] == node]),
            text=True, capture_output=True, timeout=90)
        if process.returncode:
            return {'node': node, 'returncode': process.returncode, 'stderr': process.stderr[-2000:]}
        return {'node': node, 'rows': json.loads(process.stdout)}

    with ThreadPoolExecutor(max_workers=4) as pool:
        captures = list(pool.map(capture, nodes))
    document = {'schema': 'ROHIN162_READONLY_SOURCE_CENSUS_V1', 'observed_unix': time.time(),
        'roster_ref': {'path': str(roster_path), 'sha256': digest(roster_raw)},
        'local_source': inspect_source(root), 'nodes': captures,
        'limitations': ['Registered identity/source census, not full process ancestry validation.',
            'No child journal, sealed readout, provider call, inbox write, signal, or GPU action.']}
    path = Path(__file__).parent / f'SOURCE_CENSUS_{time.time_ns()}.json'
    with path.open('x') as handle:
        json.dump(document, handle, indent=2, sort_keys=True)
        handle.write('\n')
    print(path)
    for capture in captures:
        entries = capture.get('rows', [])
        print(capture['node'], 'rows', len(entries), 'identity_live',
            sum(row.get('registered_identity_live', False) for row in entries),
            'errors', sum('error' in row for row in entries))


if __name__ == '__main__':
    main()
