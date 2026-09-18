"""Bounded parent notes from recorded own outputs; never messages isolated P7."""

import importlib.util
import json
from pathlib import Path


OWN = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('node1_parent', OWN/'r210_parent.py')
parent = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(parent)


def main():
    observed = json.loads((OWN/'R212_OBSERVED_1789709500118719027.json').read_bytes())
    actions = json.loads((OWN/'R212_ACTION_AUDIT_1789709598875119074.json').read_bytes())
    notes = {
        2: (6362, '2宝对应的是数字2', 6369, 'and９',
            'Our current object is still the sum of the first five positive odd integers and a clear '
            'explanation to a learner. Your paired-sum prose is an attempt, but the CPU delivery for '
            'ACT6369 reports PROCESS_FAILED, not a successful Python result. Make one clean, short '
            'explanation and check the variable names in any code you actually choose to submit.'),
        3: (6404, 'raw３', None, None,
            'Our current object is the actual read-only routing function below, not import discovery. '
            'ACT6466 was LANGUAGE_RESPONSE_UNVERIFIED: no execution occurred. '
            'No supplied API establishes Astra.query_module_location; do not depend on it. '
            'Use the supplied lines to choose one concrete input and predict its route. '
            'Report source inference as source inference, not as an executed test.'),
        5: (6423, '-６', 6439, '和the formula',
            'Our current object is your sum-of-three-consecutive-integers rule and its countercheck. '
            'You actually corrected the negative example to -6 in THINK6423. ACT6430 was '
            'LANGUAGE_RESPONSE_UNVERIFIED, so no Python result was returned. Continue the already '
            'requested crossing-zero countercheck: write the direct sum and your formula calculation '
            'as ordinary prose/digits; distinguish your arithmetic from a tool execution.'),
    }
    output = OWN/'R212_LANGUAGE_NOTES'
    output.mkdir(mode=0o700, exist_ok=True)
    for physical, specification in notes.items():
        assert physical not in parent.policy()['suspended_physical']
        first_index, first_text, second_index, second_text, guidance = specification
        arm = observed['arms'][str(physical)]
        exact = []
        for index, excerpt in ((first_index, first_text), (second_index, second_text)):
            if index is None:
                continue
            source = next(row for row in arm['stages'] if row['index']==index)
            assert source['new_phase'] and excerpt in source['text']
            start = source['text'].index(excerpt)
            exact.append(dict(response=source, start=start, end=start+len(excerpt), exact_excerpt=excerpt))
        outcome = actions['arms'][str(physical)]['R184_ACT']['record']
        if physical==2:
            assert outcome['document']['outcome']['result_status']=='PROCESS_FAILED'
        else:
            assert outcome['document']['outcome']['status']=='LANGUAGE_RESPONSE_UNVERIFIED'
        text = '[R210_PARENT] R212 receipt-grounded parent note. Your own exact excerpts, unchanged: '
        text += '; '.join('RESPONSE '+str(item['response']['index'])+' '+json.dumps(item['exact_excerpt'], ensure_ascii=False)
                          for item in exact)
        text += ('. This recurring English/script or full-width-digit issue needs active language care, '
                 'not only exclusion by a filter. Choose a periodic LANGUAGE CHECK and its cadence '
                 'in your own action policy: check word boundaries, spelling, ASCII digits/punctuation '
                 'and unintended script mixing. State your choice, without claiming checks you did not do. '
                 +guidance+' Keep the R209 exclusion backstop. There is no hold, homework gate, '
                 'or new V exercise; your THINK/ACT/LEARN cycle continues. ')
        if physical==3:
            excerpt = arm['excerpt']
            text += '\nRead-only '+excerpt['path']+' SHA256 '+excerpt['sha256']+'\n'
            text += '\n'.join(str(excerpt['line']+offset)+': '+line
                              for offset, line in enumerate(excerpt['text'].splitlines()))
        source = dict(exact_own_excerpts=exact, actual_action_receipt=outcome,
                      read_only_source=arm['excerpt'], objective_quality_score=None,
                      operator_grounded_parent_note=True)
        parent.write(output/(str(physical)+'_SOURCE.json'), dict(text=text, source=source))
        publication = parent.publish(physical, text, 'R212_LANGUAGE_AND_OBJECT', source=source)
        parent.write(output/(str(physical)+'_PUBLICATION.json'), publication)
        print(json.dumps(dict(physical=physical, publication_id=publication['publication']['id'],
                              status='PUBLISHED_RENDER_PENDING')))


if __name__=='__main__':
    main()
