"""Post-hoc single-case audit of delivered guidance, not a population estimate."""

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(campaign):
    phase = campaign / 'GUIDED_SLEEP/cycle6/experience'
    episode = read(phase / 'EPISODE_00.json')
    plan = read(phase / 'PARENT_PLAN.json')
    task = episode['task']['id']
    call = episode['reflection_call']
    call_path = campaign / call['relative_path']
    assert sha(call_path) == episode['reflection_call_sha256']
    system = call['messages'][0]['content']
    assert call['messages'][0]['role'] == 'system'
    retained = []
    for row in read(phase / 'ROWS.json'):
        if row['episode_id'] != task:
            continue
        source = campaign / row['source_call_path']
        assert sha(source) == row['source_call_sha256']
        assert read(source)['response']['raw'] == row['target']
        retained.append(dict(kind=row['kind'], outcome=row['outcome'],
            presentations=row['actual_presentations'], source_sha256=sha(source),
            teacher_in_prefix=row['teacher_in_prefix']))
    return dict(measured_utc=datetime.now(timezone.utc).isoformat(), native_calls=0,
        raw_text_included=False, parent_may_read=False,
        selection='POST_HOC_SINGLE_INCORRECT_CASE_NOT_PREVALENCE_OR_CAUSAL_ESTIMATE',
        task_id=task, outcome=episode['outcome'],
        parent_plan_sha256=sha(phase / 'PARENT_PLAN.json'),
        episode_sha256=sha(phase / 'EPISODE_00.json'), reflection_call_sha256=sha(call_path),
        full_episode_guidance_delivered=plan['episode_guidance'][task] in system,
        product_recompute_instruction_delivered='31 × 21' in system,
        disagreement_stopping_rule_delivered='Let any disagreement stop' in system,
        input_truncated=call['response']['input_truncated'], retained_rows=retained,
        author_observation='Reflection acknowledges incorrect verifier outcome but repeats candidate684 and attributes failure to presentation rather than repairing the false arithmetic.',
        independently_computed_arithmetic=dict(product_31_by_21=31 * 21,
            candidate_from_correct_product=31 * 21 + 27,
            wrong_candidate_mod31=684 % 31, wrong_candidate_mod37=684 % 37),
        intervention=False, source_sha256=sha(Path(__file__)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--campaign', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    with options.output.open('x') as destination:
        json.dump(audit(options.campaign), destination, indent=2, sort_keys=True)
        destination.write('\n')
