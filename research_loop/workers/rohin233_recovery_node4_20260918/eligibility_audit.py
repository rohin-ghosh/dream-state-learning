"""Read actual completed-sleep exclusions and doses without exporting row text."""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time

from deadline_resume import TARGETS, digest, read, require


def receipt_projection(row):
    document = row['document']
    result = dict(index=row['index'], sha256=row['sha256'], kind=row['kind'])
    for key in ('cycle', 'new_rows', 'optimizer_step', 'optimizer_steps', 'total_optimizer_steps',
            'finished_unix', 'loaded_unix', 'learn_row_policy', 'active_semantic_filters',
            'semantic_row_exclusion'):
        if key in document:
            result[key] = document[key]
    if row['kind'] == 'TARGET_ELIGIBILITY':
        review = document.get('learn_review_filter', {})
        result.update(retained_new_rows=len(document['new_row_sha256']),
            merged_exclusion_entries=len(document.get('excluded', [])),
            content_checks_executed=len(review.get('content_target_filter', {}).get('checks', [])),
            prose_checks_executed=len(review.get('prose_target_filter', {}).get('checks', [])))
    return result


def projection(complete, eligibility, recipe):
    require(recipe['index'] < eligibility['index'] < complete['index'], 'ordered_sleep_evidence')
    document = eligibility['document']
    candidates = Counter(complete['document']['new_row_sha256'])
    retained = Counter(document['new_row_sha256'])
    rejected = Counter(entry['source_sha256'] for entry in document.get('excluded', [])
        if entry.get('cohort') == 'NEW')
    require(candidates == retained + rejected, 'completed_candidates_match_retained_plus_excluded')
    review = document.get('learn_review_filter', {})
    prose = review.get('prose_target_filter', {})
    content = review.get('content_target_filter', {})
    checks = prose.get('checks', [])
    result = dict(cycle=complete['document']['cycle'], complete_index=complete['index'],
        complete_sha256=complete['sha256'], eligibility_index=eligibility['index'],
        eligibility_sha256=eligibility['sha256'], recipe_index=recipe['index'], recipe_sha256=recipe['sha256'],
        new_rows=recipe['document']['new_rows'],
        final_new_rows=len(document['new_row_sha256']),
        completed_optimizer_steps=complete['document']['optimizer_steps'],
        total_optimizer_steps=complete['document']['total_optimizer_steps'],
        actual_excluded_rows=len(complete['document']['excluded_rows']),
        merged_exclusion_entries=len(document.get('excluded', [])),
        exclusion_receipts=[{key: entry[key] for key in (
            'reason', 'policy', 'cohort', 'row_index', 'source_sha256', 'raw_target_sha256') if key in entry}
            for entry in document.get('excluded', [])],
        actual_code_excluded=len(document.get('code_target_filter', {}).get('excluded', [])),
        actual_review_excluded=len(review.get('excluded', [])),
        actual_content_excluded=len(content.get('excluded', [])),
        actual_prose_excluded=len(prose.get('excluded', [])),
        content_checks_executed=len(content.get('checks', [])),
        prose_checks_executed=len(checks),
        own_CJK_rows_checked=sum(entry['evidence'].get('cjk_characters', 0) > 0 for entry in checks),
        CJK_exclusion_disabled_rows=sum(entry['evidence'].get('CJK_exclusion_enabled') is False for entry in checks),
        ordinary_Chinese_punctuation_admitted=sum(entry['evidence'].get('admitted_fullwidth_prose_punctuation', 0) for entry in checks),
        active_semantic_filters_receipt=recipe['document'].get('active_semantic_filters'),
        semantic_row_exclusion_receipt=recipe['document'].get('semantic_row_exclusion'),
        exclusion_component_counts_overlap=True,
        all_off_inferred_from_zero_exclusions=False, raw_row_text_exported=False)
    return result


def audit(name, maximum=5):
    guard = read(TARGETS[name]['guard'])
    plan = read(guard['plan_path'])
    root = Path(plan['root']) / 'stream/records'
    results = []
    latest = {}
    complete = eligibility = None
    for path in reversed(sorted(root.glob('[0-9]' * 20 + '.json'))):
        with path.open('rb') as stream:
            stream.seek(max(0, path.stat().st_size - 512))
            ending = stream.read()
        kinds = re.findall(rb'"kind"\s*:\s*"([A-Z0-9_]+)"', ending)
        if not kinds:
            continue
        kind = kinds[-1].decode()
        if kind not in ('SLEEP_COMPLETE', 'TARGET_ELIGIBILITY', 'SLEEP_RECIPE', 'UPDATE', 'LOADED'):
            continue
        if kind in ('UPDATE', 'LOADED') and kind in latest:
            continue
        row = read(path)
        require(row['journal_id'] == TARGETS[name]['journal']
            and row['sha256'] == digest({key:value for key,value in row.items() if key != 'sha256'}),
            'canonical_completed_sleep_evidence')
        latest.setdefault(row['kind'], receipt_projection(row))
        if row['kind'] == 'SLEEP_COMPLETE':
            complete, eligibility = row, None
        elif row['kind'] == 'TARGET_ELIGIBILITY' and complete is not None:
            eligibility = row
        elif row['kind'] == 'SLEEP_RECIPE' and complete is not None and eligibility is not None:
            results.append(projection(complete, eligibility, row))
            complete = eligibility = None
            if len(results) == maximum:
                break
    return dict(life=name, observed_utc=datetime.fromtimestamp(time.time(),timezone.utc).isoformat(),
        reviewed_completed_sleeps=len(results), latest_first=results, latest_observed=latest,
        scope='BOUNDED_COMPLETED_SLEEP_RECEIPTS_NOT_LIFETIME_OR_POLICY_DISABLED_CLAIM')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('life', choices=TARGETS)
    print(json.dumps(audit(parser.parse_args().life), indent=2), flush=True)
