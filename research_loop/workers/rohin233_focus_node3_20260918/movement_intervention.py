"""Parent changes bound to the three actual alerted ACT responses, not heuristics."""

import argparse
import hashlib
import json
from pathlib import Path

import classroom
from retirement import record, save, sha, stamp


SOURCES = {
    'r213_math_a': (2991, 'd25c98e8e42b51d778a8f26ace1350eda4e56a743e10a43f0fb6c4f40814b48b', 2994),
    'r213_r226_caption_perspective_fork': (1961, 'd88f0d311eafeb8b8d46a5fe5228b4a780643ccf2d3e637ca43d64215333bfaf', 1964),
    'r213_r226_caption_revision_fork': (1714, '06258968b12e50707398fa0c89ca5f458d1b5b1ae39e8017d9022a48381aa2da', 1717),
}
TEXTS = {
    'r213_math_a': (
        'Your last submitted math answer changed the range several times and switched divisors while asserting '
        'unsupported counts. It also mixed scripts. This repeats the clarity and checking problem; more prose '
        'about a pattern is not a deciding check. The current shared object is still ordered integer pairs '
        'from zero through nine, with sum divisible by four. Do not replace it with the ranges or divisors '
        'from that last answer. For your next action, write the actual residue classes of the complete domain '
        'in readable English, account for every value once, and manually check which class combinations work. '
        'Then derive your own count. Address the actual peer argument if delivered, otherwise say it is missing. '
        'No executor is connected: do not promise Python as if it ran. Choose a brief language check before '
        'submitting. If the deciding check is incomplete, say exactly what remains unverified. This parent '
        'does not supply a count or declare agreement.'),
    'r213_r226_caption_perspective_fork': (
        'Your last submitted response gave a mostly Chinese list of captions despite the English caption task. '
        'That is a repeated language fault, not evidence of improvement. The actual action receipt also says '
        'no unambiguous scene was identified; it contains no judged batch or feedback for that attempt. '
        'Do not claim those captions were scored or accepted. Change approach now: identify the released '
        'scene you are actually using from the supplied material, choose a different comic perspective '
        'grounded in one visible detail, and submit a complete readable English caption in your own words. '
        'Do not merely translate or repeat the previous list. If the scene is unavailable, ask for it rather '
        'than inventing one. During THINK choose your own brief language check before the next ACT. '
        'There is no required caption label or wire format, and no learning row is being excluded by this parent.'),
    'r213_r226_caption_revision_fork': (
        'Your last submitted response repeated the same finances and baby-name premise with small synonym '
        'changes, mixed in other-script characters, and promised future submission. That promise is not '
        'proof of successful submission. The actual action receipt says no unambiguous scene was identified '
        'and contains no judged batch or feedback for that attempt. Change the intervention now: first '
        'identify the actual released scene from the supplied material; then choose a materially different '
        'comic premise tied to a visible detail. In the next ACT write the caption itself in readable English '
        'rather than more near-duplicate fenced lists or a plan to submit later. No fixed label or caption '
        'schema is required. If no scene or feedback is visible, state that gap honestly. Choose a brief '
        'language and repetition check during THINK. This changes parenting, not learning eligibility.'),
}


def source(root, name):
    if name not in SOURCES:
        raise ValueError('only exact alerted node3 lives')
    index, expected, act_index = SOURCES[name]
    records = root / name / 'raw/stream/records'
    response = record(records / f'{index:020d}.json')
    act = record(records / f'{act_index:020d}.json')
    origin = act['document'].get('origin', {})
    if (response['kind'] != 'RESPONSE' or response['sha256'] != expected or act['kind'] != 'R184_ACT'
            or origin != dict(kind='TRAIN_CHILD_RESPONSE', record_index=index, record_sha256=expected)):
        raise ValueError('exact own ACT and RESPONSE provenance required')
    report = act['document'].get('outcome', {}).get('environment', {}).get('report', {})
    if name != 'r213_math_a' and (report.get('error') != 'scene_not_unambiguously_identified'
            or report.get('batch_reports') != [] or report.get('feedback') != []):
        raise ValueError('claimed unsuccessful scene routing must match actual receipt')
    return dict(response=dict(index=index, sha256=expected), act=dict(index=act_index, sha256=act['sha256']),
        raw_sha256=hashlib.sha256(response['document']['response']['raw'].encode()).hexdigest(),
        actual_environment_error=report.get('error'), native_execution_claimed=False,
        raw_target_changed=False, other_lives_success_not_inferred=True)


def run(root, output, config, publish=False):
    helper, bound = classroom.load_helpers(root, config)
    rows = []
    for name in SOURCES:
        evidence = source(root, name)
        directory = output / name
        if publish and not (directory / 'PUBLISHED.json').exists():
            if directory.exists():
                raise ValueError('uncertain intervention publication cannot be repeated')
            parent = classroom.publish(helper, root, name, TEXTS[name], 'R233_SOURCE_BOUND_MOVEMENT_INTERVENTION',
                directory, bound[name], helper.latest_checkpoint(root, name))
            save(directory / 'SOURCE.json', dict(observed_utc=stamp(), evidence=evidence,
                intervention_changed=True, scientific_success_claimed=False, training_exclusions=0))
        if (directory / 'PUBLISHED.json').exists():
            prepared = json.loads((directory / 'PREPARED.json').read_bytes())
            publication = json.loads((directory / 'PUBLISHED.json').read_bytes())
            if publication['prepared_sha256'] != sha(directory / 'PREPARED.json') or sha(Path(publication['path'])) != publication['sha256']:
                raise ValueError('unchanged intervention source required')
            rows.append(dict(life=name, evidence=evidence, parent_id=publication['id'], parent_sha256=publication['sha256'],
                published_utc=publication['published_utc'], delivery=helper.actual_delivery(root, name, publication, prepared['floor'])))
        else:
            rows.append(dict(life=name, evidence=evidence, published=False))
    return dict(observed_utc=stamp(), rows=rows, parent_code_sha256=sha(Path(__file__)),
        no_alert_does_not_mean_success=True, learning_policy_changes=0, native_signals=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--receipt', type=Path, required=True)
    options = parser.parse_args()
    result = run(options.root, options.output, json.loads(options.config.read_bytes()), options.publish)
    save(options.receipt, result)
    print(json.dumps(result))
