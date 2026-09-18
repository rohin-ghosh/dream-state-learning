"""Prospective local eligibility and immutable source packaging, without native calls."""

import collections
import datetime
import hashlib
import io
import json
from pathlib import Path
import tarfile
import warnings

from organism_v6 import orch_code_channel as policy


ROOT = Path('research_notes/analysis/orch_code_channel_20260915_attempt1')
OLD = Path('research_notes/analysis/orch_code_bounded_20260914_attempt1')
BASE = Path('research_notes/analysis/orch_base_contract_20260914_attempt1')


def write(path, document):
    with Path(path).open('x') as stream:
        stream.write(json.dumps(document, indent=2, ensure_ascii=False) + '\n')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    prior = json.loads((OLD / 'TASKS.json').read_text())['tasks']
    prior += [entry['task'] for entry in json.loads((BASE / 'FREEZE.json').read_text())['entries']
              if entry['domain'] == 'CODE']
    excluded_ids = sorted({task['id'] for task in prior})
    excluded_hashes = sorted({policy.sha(task['text']) for task in prior})
    records = [json.loads(line) for line in (OLD / 'mbpp.jsonl').read_text().splitlines()]
    eligible, excluded, seen = [], [], set()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', SyntaxWarning)
        for record in records:
            question_hash = policy.sha(record['text'])
            try:
                task = policy.code.extract_task(record)
                if task['id'] in excluded_ids or question_hash in excluded_hashes:
                    raise ValueError('prior_code_diagnostic_id_or_question')
                if question_hash in seen:
                    raise ValueError('duplicate_question')
                seen.add(question_hash)
                eligible.append(task)
            except Exception as error:
                excluded.append(dict(id=record['task_id'], question_sha256=question_hash, reason=str(error)))
    eligibility = dict(total=len(records), eligible=len(eligible), eligible_ids=[task['id'] for task in eligible],
                       source_sha256=digest(OLD / 'mbpp.jsonl'), excluded_ids=excluded_ids,
                       excluded_question_sha256=excluded_hashes, exclusions=excluded,
                       exclusion_sources={str(path): digest(path) for path in (OLD / 'TASKS.json', BASE / 'FREEZE.json')})
    write(ROOT / 'ELIGIBILITY.json', eligibility)
    print(json.dumps(dict(total=len(records), exact_available=len(eligible), native_calls=0)))
    if len(eligible) < 64:
        raise SystemExit('INSUFFICIENT_ELIGIBLE_POOL_NO_NATIVE_CALLS')
    families = {family: sorted([task for task in eligible if task['family'] == family], key=lambda task: task['id'])
                for family in sorted({task['family'] for task in eligible})}
    tasks = []
    while len(tasks) < 64:
        for family in families:
            if families[family] and len(tasks) < 64:
                tasks.append(families[family].pop(0))
    owned = sorted([*Path('gpu').glob('orch_code_channel*'),
                    *Path('organism_v6').glob('orch_code_channel*'),
                    *Path('tests').glob('orch_code_channel*')])
    freeze = dict(created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        denominator=64, max_calls=384, lifetime_seconds=5400, source_ceiling=1536,
        record_ceiling=512, context_ceiling=4096, target_range=[150, 400],
        selection='family_round_robin_sorted_ids_without_replacement',
        family_counts=dict(collections.Counter(task['family'] for task in tasks)), tasks=tasks,
        eligibility_sha256=digest(ROOT / 'ELIGIBILITY.json'), source_sha256=eligibility['source_sha256'],
        action_grammar=policy.code.SPEC, separation_template=policy.SEPARATION,
        manifest_sha256=policy.MANIFEST, mounted_sha256=policy.MOUNTED, base_sha256=policy.BASE,
        devices=policy.DEVICES, files={str(path): digest(path) for path in owned},
        prior_snapshot_sha256=digest(OLD / 'source_final.tar'),
        scanner_sha256='6ed5c48c144dcf26dcb856798ab31d69e39bc66b6780211f2b10553972f8519b',
        service_exceptions_sha256='4a96b33797ab47ed7a1685de0ffe6c7ec4d210c143b720b85519b0ca05265391',
        initial_templates={arm: [policy.prompt(task, arm)[0] for task in tasks] for arm in policy.ARMS},
        neutral_prefixes=[policy.neutral_prefix(task) for task in tasks],
        generation=dict(do_sample=False, num_beams=1, repetition_penalty=1.0, min_new_tokens=0),
        gate_axes=policy.AXES, source_or_new_qualifies_distinct_task=True,
        primary=dict(minimum_gain=8, maximum_initial_deficit=4),
        review='author_full_text_first_eight_paired_then_remaining; unread_UNREVIEWED_no_autoadmit')
    assert freeze['prior_snapshot_sha256'] == '15d87269f6c0699931b4e4ee9a2ba6048d45aaa9743fb3652ce8aac8f11f0e19'
    write(ROOT / 'FREEZE.json', freeze)
    with tarfile.open(ROOT / 'source.tar', 'x') as output:
        with tarfile.open(OLD / 'source_final.tar', 'r') as source:
            for member in source:
                if member.isfile():
                    output.addfile(member, source.extractfile(member))
                elif member.isdir():
                    output.addfile(member)
                else:
                    raise ValueError('unsupported_previous_snapshot_member')
        for path in owned + [ROOT / 'FREEZE.json', ROOT / 'ELIGIBILITY.json']:
            value = path.read_bytes()
            member = tarfile.TarInfo(str(path))
            member.size = len(value)
            member.mode = 0o644
            output.addfile(member, io.BytesIO(value))
    write(ROOT / 'PACKAGE.json', dict(source_archive_sha256=digest(ROOT / 'source.tar'),
                                    freeze_sha256=digest(ROOT / 'FREEZE.json'),
                                    local_root=str(ROOT.resolve()), native_calls=0))


if __name__ == '__main__':
    main()
