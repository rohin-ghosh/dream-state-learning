"""Pure startup-only adaptation of the pinned cursorless A100 parent source."""

import ast
from copy import deepcopy
import hashlib
from pathlib import Path
import re


SOURCE_SHA256 = 'c3577a21c1e908dbc4a009e6c97d20a7353b3fcaeea66aa2c3f9f915a0c1cfca'
CONFIG_LINE = '    config = validate(json.loads(config_path.read_text()))\n'
CURSOR_LINE = '    last_count = 0\n'
SCHEMA = 'R167_A100_PARENT_CURSOR_HANDOFF_V1'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def validate_binding(binding):
    require(type(binding) is dict and set(binding) == {
        'schema', 'root', 'branch', 'programme', 'old_output',
        'started_sha256', 'reserved_response_count'}, 'exact_resume_binding')
    require(binding['schema'] == SCHEMA, 'resume_schema')
    require(type(binding['reserved_response_count']) is int
            and binding['reserved_response_count'] >= 0, 'nonnegative_reserved_cursor')
    require(re.fullmatch(r'[0-9a-f]{64}', binding['started_sha256']) is not None,
            'started_hash')
    for name in ('root', 'old_output'):
        path = Path(binding[name])
        require(path.is_absolute() and '..' not in path.parts, 'absolute_bound_path')
    require(binding['branch'].startswith('a100_')
            and re.fullmatch(r'[A-Za-z0-9_-]{1,64}', binding['branch']) is not None,
            'A100_parent_only')
    require(type(binding['programme']) is str and bool(binding['programme']), 'programme')
    return binding


def startup_checks(binding):
    validate_binding(binding)
    return (
        '    require(config.get("r167_parent_resume") == ' + repr(binding)
        + ', "bound_parent_resume")\n'
        '    require(config["root"] == ' + repr(binding['root'])
        + ' and config["branch"] == ' + repr(binding['branch'])
        + ' and config["programme"] == ' + repr(binding['programme'])
        + ', "same_parented_life")\n'
        '    require(output.resolve() != Path(' + repr(binding['old_output'])
        + ').resolve(), "new_parent_output_only")\n'
        '    require(sha(Path(' + repr(binding['old_output'])
        + ')/"STARTED.json") == ' + repr(binding['started_sha256'])
        + ', "preserved_predecessor_started")\n'
    )


def patch_source(source, binding):
    validate_binding(binding)
    require(type(source) is str and hashlib.sha256(source.encode()).hexdigest() == SOURCE_SHA256,
            'exact_original_A100_source')
    tree = ast.parse(source)
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == 'serve']
    require(len(functions) == 1, 'one_original_serve')
    original = ast.get_source_segment(source, functions[0])
    require(source.count(CONFIG_LINE) == source.count(CURSOR_LINE) == 1
            and CONFIG_LINE.strip() in original and CURSOR_LINE.strip() in original,
            'exact_startup_only_sites')
    checks = startup_checks(binding)
    cursor = '    last_count = ' + str(binding['reserved_response_count']) + '\n'
    patched = source.replace(CONFIG_LINE, CONFIG_LINE + checks).replace(CURSOR_LINE, cursor)
    recovered = patched.replace(CONFIG_LINE + checks, CONFIG_LINE, 1)
    require(recovered.replace(cursor, CURSOR_LINE, 1) == source, 'all_other_source_bytes_preserved')
    compile(patched, '<R167-A100-parent-only>', 'exec')
    return patched


def resume_config(candidate, binding):
    validate_binding(binding)
    require(all(candidate[key] == binding[key] for key in ('root', 'branch', 'programme'))
            and candidate['node'] == 'a100', 'same_candidate_parent')
    require('r167_parent_resume' not in candidate, 'new_successor_only')
    successor = deepcopy(candidate)
    successor['r167_parent_resume'] = deepcopy(binding)
    return successor
