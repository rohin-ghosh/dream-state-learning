"""Post-hoc literal output-shape audit; no semantic reasoning classification."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import statistics


CONDITIONS = ('SEED', 'GUIDED_C2', 'GUIDED_C4', 'GUIDED_C6',
              'UNPARENTED_C2', 'UNPARENTED_C4', 'UNPARENTED_C6')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked(reference, expected_path):
    path = Path(reference['path'])
    require(path == expected_path and path.resolve() == path, 'exact_artifact_path')
    content = path.read_bytes()
    require(hashlib.sha256(content).hexdigest() == reference['sha256'], 'artifact_hash')
    return json.loads(content)


def protocol_only(raw):
    require(isinstance(raw, str), 'raw_text_required')
    return re.fullmatch(r'(?:READ EVENT|ROUTE) [A-Za-z0-9_]+', raw.strip()) is not None


def summarize(responses):
    require(bool(responses), 'nonempty_responses')
    require(all(isinstance(row['token_ids'], list) and row['token_ids']
                and all(type(token) is int for token in row['token_ids']) for row in responses),
            'observed_token_ids_required')
    counts = [len(row['token_ids']) for row in responses]
    command_count = sum(protocol_only(row['raw']) for row in responses)
    return dict(calls=len(responses), literal_protocol_only=command_count,
                other_text_not_necessarily_reasoning=len(responses) - command_count,
                generated_tokens_including_eos=sum(counts),
                median_tokens_per_call_including_eos=statistics.median(counts),
                min_tokens_per_call_including_eos=min(counts),
                max_tokens_per_call_including_eos=max(counts), reasoning_quality='NOT_MEASURED')


def audit(verified_path):
    verified_path = Path(verified_path).resolve()
    content = verified_path.read_bytes()
    verified = json.loads(content)
    require(verified['schema'] == 'R127_VERIFIED_RESULTS_V1'
            and verified['status'] == 'COMPLETE' and not verified['errors'], 'complete_verification_required')
    root = Path(verified['inputs']['root'])
    require(root.is_absolute() and root.resolve() == root, 'exact_root')
    groups = {}
    for condition in CONDITIONS:
        evidence = verified['stages'][condition]
        require(evidence['status'] == 'VERIFIED', 'verified_condition_required')
        complete = checked(evidence['complete'], root / condition / 'COMPLETE.json')
        require(complete['condition'] == condition and complete['status'] == 'COMPLETE'
                and len(complete['calls']) == evidence['calls'], 'complete_condition_binding')
        responses = []
        for reference in complete['calls']:
            filename = Path(reference['path']).name
            require(re.fullmatch(r'CALL_[0-9]{5}\.json', filename), 'call_filename')
            call = checked(reference, root / condition / 'calls' / filename)
            require(call['status'] == 'COMPLETE' and call['condition'] == condition, 'complete_call_required')
            responses.append(call['response'])
        groups[condition] = summarize(responses)
    return dict(schema='R127_POSTHOC_PROTOCOL_SHAPE_V1', posthoc=True,
                verified=dict(path=str(verified_path), sha256=hashlib.sha256(content).hexdigest()),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                conditions=groups, definition='Entire stripped raw response is one literal READ EVENT or ROUTE command.',
                interpretation='Other text is not automatically reasoning; protocol-only text exposes no written rationale.',
                model_calls=0, optimizer_steps=0, raw_text_exported=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verified', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    result = audit(arguments.verified)
    with arguments.output.open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write('\n')
