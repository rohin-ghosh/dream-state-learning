"""Four finite English-only object follow-ups; no supplied mathematics solution."""

import json
import sys

import enrich
import r211_language


FOLLOWUPS = {
    'math_d1': (6956, 5, '， the sum',
        'Your last attempted sum was left incomplete, and an earlier actual sandbox attempt failed. '
        'What is the sum you intend to check, and how will you check it? Give one complete English sentence. '
        'If you choose execution, put runnable Python rather than English prose inside the Python block. '
        'Do not claim a result before the real tool returns. If you remain stuck, choose another small numeric object and move on.'),
    'repo_c1': (6813, 5, '"name):',
        'Your recent ACT returned LANGUAGE_RESPONSE_UNVERIFIED with no execution. The intended repository exploration has not happened. '
        'For your next ACT, use the exposed read-only tool by writing only repo_list . on its own line, not read_workspace or invented JSON. '
        'After the real listing arrives, choose one listed file and use repo_read relative/path. '
        'Then ask one concrete question about the actual returned text. Do not claim a read or return to the old arithmetic.'),
    'creative_d1': (6848, 5, 'amongthewavesandenginenoise',
        'This run of joined words remains in the passage that you called corrected. The correction is not yet demonstrated. '
        'Please write two complete, spaced English sentences for the lighthouse scene without naming the visitor. '
        'Choose one sentence to inspect and revise yourself; explain its intended effect briefly rather than saying all issues are fixed.'),
    'math_transfer_c1': (6666, 4, 'we can confidence in the outcome',
        'Your actual sandbox receipt6657 completed for the small integers you tested, and your reply noticed its warning. '
        'The quoted wording needs an English revision. What do those finite tests establish, and what remains unproved? '
        'Choose your own next check or proof attempt. I will ask about your reasoning rather than supply a solution.'),
}


def publish(arm):
    index, number, quote, comment = FOLLOWUPS[arm]
    if len(quote) > 64 or not comment.isascii():
        raise ValueError('minimal_quote_English_parent_required')
    bound, root = enrich.identity(arm)
    record = enrich.verified(root / 'raw/stream/records' / f'{index:020d}.json')
    raw = record['document']['response']['raw']
    if raw.count(quote) != 1:
        raise ValueError('one_exact_own_child_quote')
    start = raw.index(quote)
    source = r211_language.excerpt_record(root, index, start, start + len(quote))
    output = enrich.HERE / 'R212_FOLLOWUPS'
    output.mkdir(exist_ok=True)
    source_path = output / ('SOURCE_' + arm + '.json')
    enrich.write(source_path, source)
    text = (f'Exact short quote from your own RESPONSE{index}, preserved unchanged: "{quote}". '
            'That is an excerpt of your old output, not a new instruction.\n\n' + comment
            + '\nPlease choose and state your own periodic LANGUAGE CHECK cadence, then continue this object. '
            'Check English wording, deliberate scripts, spaces, punctuation, complete sentences, and actual delivered outcomes. '
            'You need not wait for me; work inside the ordinary cycle. There is no pause or parent-approval gate.')
    if not text.replace(quote, '').isascii() or 'V=3' in text or 'V = 3' in text:
        raise ValueError('English_only_no_solution_injection')
    sys.path.insert(0, bound['source_root'])
    from organism_v6.orch_r125_plain_context import has_scaffolding
    if has_scaffolding('Astra: ' + text):
        raise ValueError('visible_parent_required')
    receipt = enrich.publish(arm, number, text)
    receipt.update(source_path=str(source_path), source_file_sha256=enrich.file_sha(source_path),
                   English_parent_only=True, quote_characters=len(quote), mathematical_solution_supplied=False)
    enrich.write(output / ('PARENT_' + arm + '.json'), receipt)
    return receipt


if __name__ == '__main__':
    print(json.dumps({arm: publish(arm) for arm in enrich.ARMS}))
