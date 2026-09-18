"""Deliver a genuine bounded source excerpt without renderer metadata keys."""

import ast
import json
from pathlib import Path
import sys
import time

from r209_filter_resume import REPAIR_FILES, ROOT, read, require, sha, write
from r209_node3_audit import metadata, read_record


def source_excerpt(text):
    function = next(item for item in ast.parse(text).body
        if isinstance(item, ast.FunctionDef) and item.name == 'prose_exclusions')
    boundary = next(item for item in ast.walk(function) if isinstance(item, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == 'check' for target in item.targets))
    return '\n'.join(text.splitlines()[function.lineno - 1:boundary.lineno - 1]), function.lineno, boundary.lineno - 1


def main():
    arm = ROOT / 'peer_repo'
    source = arm / 'r210_enrichment/source'
    sys.path.insert(0, str(source))
    from gpu.orch_r127_pilot_console import publish_parent
    from organism_v6.orch_r125_plain_context import has_scaffolding
    destination = arm / 'r210_parent/OPENER_VISIBILITY_REPAIR.json'
    if not destination.exists():
        prior = read(arm / 'r210_parent/PUBLICATION_000.json')
        require(has_scaffolding(prior['text']), 'actual_original_metadata_marker_omission')
        relative = 'organism_v6/orch_r203_prose_target_filter.py'
        require(sha(source / relative) == REPAIR_FILES[relative], 'actual_pinned_source')
        excerpt, first_line, last_line = source_excerpt((source / relative).read_text())
        text = ('Astra, R210 repository object follow-up. My earlier full-function excerpt was recorded but '
            'not shown by the plain-context renderer because it contained reserved metadata names. '
            'That is a delivery limitation, not your failure to respond. Here is an exact shorter contiguous '
            'excerpt from your deployed organism_v6/orch_r203_prose_target_filter.py, lines '
            + str(first_line) + ' through ' + str(last_line) + '; it is an excerpt, not the complete function. '
            'New object: does the scanner read the external prefix or the own target? Compare an English '
            'own target with Chinese only in external context against Chinese in the own target. Point to '
            'the actual read expression and propose two cases in your own English. No executor is connected; '
            'this is source reasoning, not execution or passing tests. Keep R211 LANGUAGE CHECK child-chosen '
            'and brief, and do not restart the inherited V investigation.\n\n```python\n' + excerpt + '\n```')
        require(not has_scaffolding(text), 'new_opener_visible_under_unchanged_renderer')
        publication = publish_parent(arm / 'raw', 'Astra', text)
        write(destination, dict(observed_unix=time.time(), publication=publication, text=text,
            source_path=str(source / relative), source_file_sha256=sha(source / relative),
            first_line=first_line, last_line=last_line, exact_excerpt=excerpt,
            replaces_unrendered_publication_id=prior['publication']['id'], runtime_unchanged=True,
            raw_history_unchanged=True, status='PUBLISHED_NOT_YET_RENDERED'))
    receipt = read(destination)
    rendered_path = arm / 'r210_parent/OPENER_VISIBILITY_RENDERED.json'
    if rendered_path.exists():
        print(json.dumps(read(rendered_path)))
        return
    for path in reversed(sorted((arm / 'raw/stream/records').glob('[0-9]' * 20 + '.json'))):
        if metadata(path) != 'REQUEST':
            continue
        record = read_record(path)
        if any(receipt['text'] in item.get('content', '') for item in record['document']['messages']):
            require(record['document']['render_receipt']['all_history_tokens_masked'], 'source_excerpt_context_only')
            rendered = dict(request_index=record['index'], request_sha256=record['sha256'],
                publication_id=receipt['publication']['id'], exact_text_rendered=True,
                all_history_tokens_masked=True, observed_unix=time.time())
            write(rendered_path, rendered)
            print(json.dumps(rendered))
            return
    print(json.dumps(dict(publication_id=receipt['publication']['id'], status='PUBLISHED_WAITING_FOR_REQUEST')))


if __name__ == '__main__':
    main()
