"""Build a forward-only R188 parent wrapper from the immutable R184 wrapper."""

import ast
import hashlib
import importlib.util
import json
from pathlib import Path


HOME = Path(__file__).resolve().parent
ORIGINAL_SHA = '977242056aec3ddebcbb368e4a356568e5565ad4584b6730e1630fc1f3f9c288'
EXAMPLES_SHA = '19e813b21d2b43d3ea274eb1783d7f2a2ce0f5b703f6fda94051d5cda21c978f'


def replace_node(source, name, replacement):
    matches = [node for node in ast.parse(source).body if
        isinstance(node, ast.FunctionDef) and node.name == name or
        isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    if len(matches) != 1:
        raise ValueError('one_exact_wrapper_node:' + name)
    node = matches[0]
    lines = source.splitlines(keepends=True)
    return ''.join(lines[:node.lineno - 1]) + replacement.rstrip() + '\n' + ''.join(lines[node.end_lineno:])


QUESTION_SHAPE = '''def question_shape(message):
    lines = [line.strip() for line in message.splitlines() if line.strip()]
    prefixes = ('Reported example (Rohin; C2): ', 'Reported example (Rohin; Pilot): ', 'Reported example (Rohin; Raw): ')
    base.require(len(lines) == 4 and lines[0].startswith(prefixes), 'R188_one_attributed_example_then_three_questions')
    base.require(all(re.fullmatch(str(index) + r'\\. [^?\\n]+\\?', line)
        for index, line in enumerate(lines[1:], 1)), 'R184_three_question_lines_no_answer_prose')
    base.require(not message.endswith(raw.BASELINE_END), 'never_duplicate_baseline')


def validation_recovery(output, state):
    attempt = output / f"parent_{state['request_count']:012d}"
    source = base.read(attempt / 'SOURCE.json')
    result = base.read(attempt / 'RESULT.json')
    base.require(result['status'] == 'VALIDATION_FAILED' and 'publication' not in result
        and not (attempt / 'PUBLISH_INTENT.json').exists(), 'only_known_prepublication_validation_failure')
    base.require(result['source_sha256'] == base.sha(attempt / 'SOURCE.json')
        and source['head_sha256'] == state['head_sha256']
        and source['response_count'] == state['response_count'], 'exact_failed_source_not_replayed')
    return dict(status='AWAIT_FRESH_RESPONSE_AFTER_VALIDATION_FAILURE',
        error=result.get('error'), result_sha256=base.sha(attempt / 'RESULT.json'),
        failed_source_head=source['head_sha256'], failed_response_count=source['response_count'],
        same_source_retry=False, publication_attempted=False, observed_unix=time.time())
'''


STAGE = '''def stage(lane, physical):
    base.require(physical in ARMS, 'R188_only_parents_0_3_4_raw1_untouched')
    previous = PREVIOUS[physical]
    base.checked_bundle(previous)
    base.require(not lane.exists() and lane.parent.parent == HOME
        and lane.parent.name.startswith('activation_r188_') and lane.name == f'physical{physical}', 'new_owned_lane')
    lane.mkdir(parents=True)
    shutil.copytree(previous / 'source', lane / 'source')
    for name in ('CONFIG.json', 'PARENT_METADATA_ERRATA_V1.md', 'orch_r175_parent_response.py'):
        shutil.copyfile(previous / name, lane / name)
    base.write(lane / 'PLAN.json', dict(physical=physical, arm=ARMS[physical][0], root=base.ROOTS[physical],
        one_corrective_call=False))
    predecessor = base.read(previous / 'parent/STARTED.json')['actor']
    older = Path(base.read(previous / 'BINDING.json')['previous_lane'])
    base.require(older.parent.parent == HOME and older.name == f'physical{physical}', 'same_life_previous_exposure')
    anchors = [path / 'parent/FIRST_RENDERED_EXPOSURE.json' for path in (previous, older)]
    anchor = next((path for path in anchors if path.exists()), None)
    proof = dict(physical=physical, wrapper_sha256=base.sha(__file__), previous_lane=str(previous),
        predecessor=predecessor, config_sha256=base.sha(lane / 'CONFIG.json'),
        source_files={str(path.relative_to(lane / 'source')): base.sha(path)
            for path in (lane / 'source').rglob('*') if path.is_file()},
        raw_release_sha256=None, exposure_anchor_path=str(anchor) if anchor else None,
        exposure_anchor_sha256=base.sha(anchor) if anchor else None,
        policy_sha256=hashlib.sha256(POLICY.encode()).hexdigest(), Main_examples_sha256=EXAMPLES_SHA,
        scope='R188_next_fresh_response_only_keep_caps_English_object_rules_no_child_changes')
    base.write(lane / 'BINDING.json', proof)
    return dict(status='STAGED_NOT_PUBLISHED', physical=physical, lane=str(lane))
'''


ACTIVATE = '''def activate(lane):
    config, proof = checked(lane)
    physical = proof['physical']
    previous = PREVIOUS[physical]
    actor = proof['predecessor']
    base.require(not Path('/proc', str(actor['pid'])).exists(), 'confirmed_stopped_owned_predecessor_only')
    donor_lane = HOME / 'activation_r184_20260917T2248Z/physical1'
    donor = base.read(donor_lane / 'parent/STARTED.json')['actor']
    base.same_parent(donor, base.identity(donor['pid']))
    environment = dict(part.decode().split('=', 1) for part in
        Path('/proc', str(donor['pid']), 'environ').read_bytes().split(b'\\0') if b'=' in part)
    base.same_parent(donor, base.identity(donor['pid']))
    environment.update(CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(lane / 'source'))
    with (HOME / f'R175_PARENT_{physical}.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        latest = base.read(sorted((previous / 'parent').glob('POLL_*.json'))[-1])
        reference = latest['reference']
        for sequence in range(8):
            observed = base.snapshot(reader(proof), reference)
            reference = observed['reference']
            if observed['snapshot']['caught_up']:
                break
        base.require(observed['snapshot']['caught_up'], 'bounded_verified_current_snapshot')
        policy, parent = load(lane)
        seed = errata.preserved_seed(previous, policy, observed['snapshot'])
        base.require(not any(attempt['result']['status'] == 'PUBLICATION_UNKNOWN' for attempt in seed['attempts']),
            'unknown_publication_requires_reconciliation_no_replay')
        base.write(lane / 'SEED.json', seed)
        base.write(lane / 'TAKEOVER_SNAPSHOT.json', observed)
        base.write(lane / 'PREVIOUS_VALIDATION_FAILURES.json', dict(
            attempts=[attempt for attempt in seed['attempts'] if attempt['result']['status'] == 'VALIDATION_FAILED'],
            future_source_only=True, observed_unix=time.time()))
        command = [sys.executable, '-B', str(Path(__file__).resolve()), 'serve', '--lane', str(lane)]
        execution = subprocess.run(command + ['--preflight'], cwd=lane / 'source', env=environment,
            capture_output=True, text=True, timeout=45)
        base.require(execution.returncode == 0, 'actual_bound_CPU:' + execution.stderr[-1500:])
        base.write(lane / 'CPU.json', json.loads(execution.stdout))
        base.require(errata.preserved_seed(previous, policy, observed['snapshot']) == seed,
            'settled_attempt_ledger_unchanged')
        base.write(lane / 'ACTIVATION_INTENT.json', dict(predecessor=actor, predecessor_absent=True,
            provider_environment_donor_pid=donor['pid'], donor_unmodified=True,
            observed_unix=time.time(), native_signals=0, raw1_mutations=0))
    with (lane / 'PARENT.log').open('x') as log:
        process = subprocess.Popen(command, cwd=lane / 'source', env=environment, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    result = dict(status='R188_PARENT_STARTED_NOT_A_PUBLICATION', physical=physical,
        pid=process.pid, command=command, observed_unix=time.time(), child_signals=0, raw1_mutations=0)
    base.write(lane / 'DISPATCHED.json', result)
    return result
'''


def patch(original, append_examples):
    if hashlib.sha256(original.encode()).hexdigest() != ORIGINAL_SHA:
        raise ValueError('exact_preserved_R184_wrapper')
    policy_node = next(node for node in ast.parse(original).body if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == 'POLICY' for target in node.targets))
    policy = ast.literal_eval(policy_node.value)
    before = 'At the next legitimate parent turn, return exactly three numbered question lines, numbered 1., 2., 3., each ending in one question mark. No introductory baseline, answer, explanation, worked solution, or closing directive.'
    after = ('At the next legitimate parent turn, give one short attributed worked-method example from the supplied R188 examples, '
        'followed by exactly three numbered question lines, numbered 1., 2., 3., each ending in one question mark. '
        'The example must be a single paragraph beginning exactly with one of: Reported example (Rohin; C2): '
        'or Reported example (Rohin; Pilot): or Reported example (Rohin; Raw):. '
        'Do not supply the recipient task answer or repeat an introductory baseline. Keep the entire message within the existing arm cap; '
        'for the 90-word D arm keep the example very short. The example is reported, not recipient evidence.')
    if policy.count(before) != 1:
        raise ValueError('exact_prior_message_shape_instruction')
    policy = policy.replace(before, after) + ('\nValidator clarification, not a rule change: if disposition is set_aside, '
        'include an explicit English release such as "set aside", state "unresolved", and include the exact private next_task in the message. '
        'That next_task must retain the exact continuity.chosen_object.quote; the message must include keep/continue/stay with/within. '
        'With no actual rendered Tool receipt, say "not yet verified". If disposition is continue, private next_task and continuity stay null. '
        'Never invent an object alias to escape the existing object-turn budget, and never fabricate evidence. '
        'These constraints can be expressed inside the three questions; do not silently normalize a rejected response.')
    policy = append_examples(policy.encode()).decode()
    source = replace_node(original, 'PREVIOUS', "PREVIOUS = {physical: HOME / 'activation_r184_20260917T2248Z' / f'physical{physical}' for physical in (0, 3, 4)}")
    source = replace_node(source, 'ARMS', "ARMS = {0: ('B', 2), 3: ('D', 3), 4: ('A', 1)}")
    source = replace_node(source, 'POLICY', 'EXAMPLES_SHA = ' + repr(EXAMPLES_SHA) + '\nPOLICY = ' + repr(policy))
    source = replace_node(source, 'question_shape', QUESTION_SHAPE)
    source = replace_node(source, 'stage', STAGE)
    source = replace_node(source, 'activate', ACTIVATE)
    changes = (
        ("lane.parent.name.startswith('activation_r184_')", "lane.parent.name.startswith('activation_r188_')"),
        ("        previous_anchor = PREVIOUS[proof['physical']] / 'parent/FIRST_RENDERED_EXPOSURE.json'\n        anchor = base.read(previous_anchor) if previous_anchor.exists() else None",
         "        previous_anchor = proof['exposure_anchor_path']\n"
         "        base.require(previous_anchor is None or base.sha(previous_anchor) == proof['exposure_anchor_sha256'], 'preserved_first_exposure_clock')\n"
         "        anchor = base.read(previous_anchor) if previous_anchor else None"),
        ("            if status['status'] in ('PUBLICATION_UNKNOWN', 'VALIDATION_FAILED', 'PROVIDER_FAILED'):",
         "            if status['status'] == 'VALIDATION_FAILED':\n"
         "                base.write(output / f'VALIDATION_RECOVERY_{sequence:06d}.json', validation_recovery(output, state))\n"
         "            if status['status'] in ('PUBLICATION_UNKNOWN', 'PROVIDER_FAILED'):"),
    )
    for before, after in changes:
        if source.count(before) != 1:
            raise ValueError('one_exact_forward_parent_seam')
        source = source.replace(before, after)
    source = source.replace('R184_PUBLISHED_', 'R188_PUBLISHED_').replace('R184_RENDERED_', 'R188_RENDERED_')
    ast.parse(source)
    return source


def build():
    examples_path = HOME.parents[3] / 'gpu/orch_r188_parent_examples.py'
    if hashlib.sha256(examples_path.read_bytes()).hexdigest() != EXAMPLES_SHA:
        raise ValueError('exact_Main_examples')
    spec = importlib.util.spec_from_file_location('bound_R188_examples', examples_path)
    examples = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(examples)
    source = patch((HOME / 'r184_parent_forward.py').read_text(), examples.append_parent_examples)
    output = HOME / 'r188_parent_forward.py'
    with output.open('x') as stream:
        stream.write(source)
    return dict(path=str(output), sha256=hashlib.sha256(source.encode()).hexdigest(), examples_sha256=EXAMPLES_SHA,
        caps_provider_English_object_rules_unchanged=True, raw1_mutations=0, child_signals=0)


if __name__ == '__main__':
    print(json.dumps(build(), sort_keys=True))
