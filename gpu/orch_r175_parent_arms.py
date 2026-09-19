"""Build immutable parent-only arm bundles; never signal or modify a living child."""

import argparse
import ast
import copy
import hashlib
import json
from pathlib import Path


SCHEMA = 'ROHIN175_PARENT_ARMS_V1'
ARMS = {
    'A': dict(cadence=1, words=240, style='strict-dense'),
    'B': dict(cadence=2, words=160, style='transcript-grounded walkthrough'),
    'C': dict(cadence=3, words=120, style='questions-only self-derivation'),
    'D': dict(cadence=3, words=90, style='light steer'),
    'H': dict(cadence=1, words=160, style='baseline once then hands-off'),
}
BASELINE = (
    'ROHIN175_OBSERVATION_TO_ACTION_BASELINE_V1. This prospective policy supersedes conflicting '
    'earlier parenting advice, not evidence, safety, masking, frozen controls, or the sleep recipe. '
    'Use the child\'s actual current object. Connect a real attempt and its actual observation to one '
    'specific next action that the child chooses, carries forward, and performs without another '
    'reminder. No result obtained is a valid finding. A prediction or code listing is not execution. '
    'Carry concise task state: finding, uncertainty, next intention, and the source of any observation. '
    'These are task-relevant outputs, not a request for private reasoning or a memorized stage header. '
    'Perceive, judge, predict, act and reflect are selectable operations, not a mandatory recital. '
    'Reflection should lightly change the next action, not replace acting. Ask what deserves more '
    'attention and what observation would discriminate. Keep the object moving rather than resetting '
    'it or repeating wrappers. Use only actual visible TRAIN evidence; never invent a worked result, '
    'tool availability, execution receipt, or claim of learning in weights. Preserve CREDIT attribution '
    'and the existing three-turn unresolved-mismatch budget, without expiring the project. '
    'Own prose stays English. Parent, peer and environment text stays masked; only the child\'s own '
    'restatement can be eligible under the unchanged runtime. Peer statements are attributed claims, '
    'not observations: the recipient predicts and tests before accepting them. Do not request a peer '
    'exchange unless the assigned real channel exists. No sealed scores, evaluator answers or FINAL data. '
    'At compaction ask which decision and unfinished work must survive, but do not claim this prompt '
    'changes the compactor. Preserve the existing private rationale schema and response JSON exactly. '
)
ARM_TEXT = {
    'A': ('At every available response boundary, give explicit, object-grounded guidance. Ask for '
          'finding, uncertainty and a concrete next intention in the child\'s own concise wording, '
          'then ask it to enact the intention. No obligatory headings or repeated template. On a '
          'subsequent attempt check whether the chosen action occurred and use actual feedback.'),
    'B': ('Every two responses, show one brief worked example from the child\'s own visible transcript: '
          'actual attempt, observed evidence or no result, tentative judgment, and changed next action. '
          'Mark proposed actions as unexecuted. Then have the child choose and enact its next step.'),
    'C': ('Every three responses, use questions only in child-facing prose: what would useful perception '
          'or reflection reveal for this object, what evidence is available, what will you do next, '
          'and how will you check it? Do not prescribe an answer or fabricate an example.'),
    'D': ('Every three responses, use the relevant light-steer question: What specifically will you '
          'do differently on your next attempt? Did you do it, and what happened? What decision and '
          'unfinished work must survive for you to continue? Do not demand all three every time.'),
    'H': ('Give exactly one object-grounded baseline invitation to connect an actual observation or '
          'no result to a specific next action and carry finding, uncertainty, next intention. '
          'The operator stops this parent after one verified publication; do not send follow-ups.'),
}
PARENT_PATH = 'gpu/orch_r133_programme_parent.py'
POLICY_PATH = 'gpu/orch_r166_parent_policy.py'
PROVIDER_PATH = 'gpu/orch_route_parent_campaign_providers.py'
PATCH_PATHS = (PARENT_PATH, POLICY_PATH, PROVIDER_PATH)


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def specification(arm):
    require(arm in ARMS, 'known_arm')
    return dict(ARMS[arm])


def instruction(arm):
    selected = specification(arm)
    return ('\n\n' + BASELINE + ARM_TEXT[arm] +
            f' Combined child-facing publication including any one-time grammar lesson: '
            f'at most {selected["words"]} words and 4096 UTF-8 bytes. '
            'Silence must remain possible and is measured as an uncovered parenting boundary.\n')


def configure(original, arm):
    selected = specification(arm)
    require(isinstance(original, dict), 'config_object')
    result = copy.deepcopy(original)
    result.update(r175_schema=SCHEMA, r175_arm=arm, schedule_on='response',
                  cadence_responses=selected['cadence'], parent_style=selected['style'],
                  cadence_label='PERSISTENT' if arm == 'A' else 'SPARSE',
                  r175_word_limit=selected['words'])
    if arm == 'A':
        result['minimum_duration_seconds'] = max(3600, original.get('minimum_duration_seconds', 0))
    if arm == 'H':
        result['r175_max_publications'] = 1
    return result


def replace_once(source, before, after):
    require(source.count(before) == 1, 'source_drift:' + before[:80])
    return source.replace(before, after, 1)


def replace_assignment(source, name, value):
    matches = [node for node in ast.parse(source).body if isinstance(node, ast.Assign)
               and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
    require(len(matches) == 1, 'unique_assignment:' + name)
    node = matches[0]
    lines = source.splitlines(keepends=True)
    return ''.join(lines[:node.lineno - 1]) + name + ' = ' + repr(value) + '\n' + ''.join(lines[node.end_lineno:])


def patch_sources(sources, arm):
    selected = specification(arm)
    require(all(path in sources for path in PATCH_PATHS), 'complete_parent_sources')
    require(all(SCHEMA not in sources[path] for path in PATCH_PATHS), 'no_double_patch')
    patched = dict(sources)
    words, cadence = selected['words'], selected['cadence']
    patched[PARENT_PATH] = replace_once(patched[PARENT_PATH], 'message(string, at most90 words)',
                                        f'message(string, at most {words} words)')
    patched[PROVIDER_PATH] = replace_once(patched[PROVIDER_PATH],
        "len(response['message'].split()) <= 90",
        f"len(response['message'].split()) <= {words} and len(response['message'].encode('utf-8')) <= 4096")
    policy = patched[POLICY_PATH]
    policy = replace_assignment(policy, 'PROMPT_POLICY_MARKER', SCHEMA + '_' + arm)
    policy = replace_assignment(policy, 'PROMPT_POLICY', instruction(arm))
    policy = replace_once(policy, "config.update(cadence_responses=1, cadence_label='SPARSE', schedule_on='response')",
                          f"config.update(cadence_responses={cadence}, cadence_label='SPARSE', schedule_on='response')")
    policy = replace_once(policy, "config['cadence_responses'] == 1", f"config['cadence_responses'] == {cadence}")
    policy = replace_once(policy, 'word_budget = 90 - len(GRAMMAR.split()) if lesson else 90',
                          f'word_budget = {words} - len(GRAMMAR.split()) if lesson else {words}')
    policy = replace_once(policy, 'The combined publication is capped at 90 words:',
                          f'The combined publication is capped at {words} words:')
    policy = replace_once(policy, 'len(message.split()) <= 90', f'len(message.split()) <= {words}')
    policy = replace_once(policy,
        "clock = 'request_count' if config['community_learner'] or config.get('schedule_on') == 'request' else 'response_count'",
        "clock = 'request_count' if config.get('schedule_on') == 'request' else 'response_count'")
    policy = replace_once(policy, '    validate(config)\n    if not state[\'caught_up\']:',
        f"    validate(config)\n    require(config.get('r175_schema') == {SCHEMA!r} and config.get('r175_arm') == {arm!r}\n"
        f"        and config.get('schedule_on') == 'response' and config['cadence_responses'] == {cadence}\n"
        f"        and config.get('r175_word_limit') == {words}, 'bound_r175_arm')\n    if not state['caught_up']:")
    if arm == 'H':
        policy = replace_once(policy, '    if memory_state[\'awaiting_render\']:',
            "    if any(attempt['result']['status'] == 'PUBLISHED' for attempt in local_attempts(output)):\n"
            "        return dict(status, status='HANDS_OFF_BASELINE_PUBLISHED')\n    if memory_state['awaiting_render']:")
    patched[POLICY_PATH] = policy
    for path in PATCH_PATHS:
        compile(patched[path], path, 'exec')
    return patched


def build_bundle(source_root, output, arm):
    from gpu.orch_r166_parent_policy import SOURCE_FILES

    source_root, output = Path(source_root), Path(output)
    paths = sorted(set(SOURCE_FILES) | set(PATCH_PATHS))
    original = {}
    for name in paths:
        path = source_root / name
        require(not path.is_symlink() and path.is_file() and path.stat().st_size <= 16 * 1024 * 1024,
                'bounded_regular_source:' + name)
        original[name] = path.read_text()
    successor = patch_sources(original, arm)
    manifest = dict(schema=SCHEMA, arm=arm, specification=specification(arm),
                    change_scope='PARENT_ONLY_NO_CHILD_OR_TRAINING_MUTATION',
                    builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), files={})
    output.mkdir(parents=True, exist_ok=False)
    for name in paths:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = successor[name].encode()
        with target.open('xb') as stream:
            stream.write(raw)
        target.chmod(0o444)
        manifest['files'][name] = dict(before_sha256=hashlib.sha256(original[name].encode()).hexdigest(),
                                     sha256=hashlib.sha256(raw).hexdigest(), changed=original[name] != successor[name])
    manifest_path = output / 'ARM_BUNDLE.json'
    with manifest_path.open('x') as stream:
        json.dump(manifest, stream, indent=2, sort_keys=True)
    manifest_path.chmod(0o444)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--arm', choices=tuple(ARMS), required=True)
    arguments = parser.parse_args()
    manifest = build_bundle(arguments.source, arguments.output, arguments.arm)
    print(json.dumps(dict(output=str(arguments.output), arm=manifest['arm'], status='BUILT_NOT_ACTIVATED')))


if __name__ == '__main__':
    main()
