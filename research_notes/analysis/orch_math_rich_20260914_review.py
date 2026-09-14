"""Explicit full-text author readings, not a keyword/heading semantic classifier.

Read against the original 32 questions and all 64 non-terse responses on
2026-09-14. First-person plural accounts are accepted; no literal-I gate.
P/F/U encode the combined semantic/voice rubric, independently of token and
oracle eligibility. These judgments never repair or synthesize target bytes.
"""

import json
from pathlib import Path
import sys


READINGS = [
    ('1649', 'rich', 'P', 'Nested proportions are correctly applied to the four-leaved subset; first-person plural computation is grounded. Below150 tokens separately.', 'we first calculate'),
    ('1649', 'record', 'P', 'Own account identifies the conditional subset, computes100 then25 and checks both operations; reusable nested-proportion procedure.', 'First, I calculated the number of four-leaved clovers:'),
    ('1613', 'rich', 'P', 'Own calculation composes conversion rate, split purchase values and workdays;10 buyers,1000/day,5000/week are grounded.', 'Now, I calculate the daily sales:'),
    ('1613', 'record', 'F', 'Grounded reusable rate/split/week procedure, but entirely impersonal exposition rather than the required first-person account. This is a voice-contract exclusion, not false arithmetic.', 'Weekly sales: $1000 * 5 days = $5000.'),
    ('6898', 'rich', 'F', 'Correct capacity chain150,75,325, but impersonal exposition; also104tokens, independently below the floor.', 'Adding these together, the total capacity is 100 + 150 + 75 = 325 liters.'),
    ('6898', 'record', 'F', 'Correct reusable multiplicative changes and total, but impersonal recipe rather than first-person account; not rejected for missing a heading.', 'Sum the capacities of all three coolers to get the total capacity.'),
    ('6932', 'rich', 'P', 'Own account distinguishes extra reward72 from new reward432; operations link rate change to12hours.', 'Finally, I find the difference between the new and original total video game time:'),
    ('6932', 'record', 'F', 'Grounded before/after difference with concrete432-360 check, but impersonal exposition does not meet first-person contract.', 'Difference: 432 - 360 = 72 minutes.'),
    ('441', 'rich', 'P', 'Own account correctly constructs5+10+15 and adds20% of that30; reusable subgroup aggregation and proportional add-on.', 'First, I identify the given quantities:'),
    ('441', 'record', 'F', 'Grounded subgroup/add-on operations, but no first-person account. Final-match assertion is only a restatement, not independent external evidence.', 'Calculate the remaining invitations as 20% of the total from step 2.'),
    ('4062', 'rich', 'U', 'Arithmetic is correct conditional on a four-week month, explicitly admitted as an assumption; question does not establish that calendar/payroll convention. Conservatively unresolved, not silently fitted.', 'Assuming there are 4 weeks in a month'),
    ('4062', 'record', 'F', 'Record turns the earlier four-week assumption into an alleged given quantity. Correct benchmark answer does not establish this invented premise.', 'Weeks in a month: 4'),
    ('6550', 'rich', 'P', 'Own account uses hybrid subset360, subtracts144 deficient headlights to216; grounded complement-within-subset operation.', 'Next, I calculate the number of hybrid cars:'),
    ('6550', 'record', 'F', 'Correct complementary subset calculation and check; nevertheless impersonal recipe rather than required first-person account.', 'Subtract the number of hybrids with only one headlight from the total number of hybrids'),
    ('4442', 'rich', 'P', 'Own calculation converts36additional pounds to18ingots, applies qualifying20%discount to90; does not confuse extra and total vest weight.', 'First, I calculate the additional weight needed:'),
    ('4442', 'record', 'F', 'Useful grounded unit conversion and conditional discount recipe, but impersonal exposition, not first-person account.', 'Since 18 ingots are more than 10, apply the 20% discount'),
    ('5724', 'rich', 'P', 'Own route calculation conserves120miles and1.5hours, computes remaining distance/time and checks the full timeline.', 'Total time: 0.5 hours + 1 hour = 1.5 hours'),
    ('5724', 'record', 'F', 'Correct reusable residual-distance/time operation but impersonal exposition; separately457tokens exceeds400, no truncation or target shortening permitted.', 'Required average speed for the remainder of the drive'),
    ('1916', 'rich', 'P', 'Own account applies each distinct wage to matching hours, then sums105+108+60; reusable weighted-sum operation.', 'Next, I calculate the earnings for each family:'),
    ('1916', 'record', 'F', 'Grounded weighted-sum recipe and repeated arithmetic check; no first-person account.', 'Sum the earnings from all families to get the total earnings.'),
    ('6513', 'rich', 'F', 'Correct rate-times-time minus loss, but impersonal imperative and135tokens. Voice/token exclusion, not an arithmetic criticism.', 'First, calculate the total number of fish caught:'),
    ('6513', 'record', 'F', 'Explicitly reusable rate-plus-adjustment content is good; still an impersonal recipe rather than first-person account.', 'The operations are reusable for similar problems involving a constant rate'),
    ('7458', 'rich', 'P', 'Own calculation composes laps times quarter-mile, divides by half-hour, then halves speed; units and intermediate3miles/6mph are grounded.', 'To find Polly\'s speed, I calculate the total distance she traveled:'),
    ('7458', 'record', 'F', 'Correct reusable unit/rate chain, but impersonal recipe; detailed equations alone do not satisfy first-person contract.', 'Calculate Gerald\'s speed, which is half of Polly\'s speed.'),
    ('3145', 'rich', 'U', 'Question says sailboat60 but ski boat80/hour; literal flat-fee reading yields420, whereas gold120 assumes sailboat60/hour. Reference ambiguity, not certified learner arithmetic error.', "Ken's total cost = $60 (since he only paid for the sailboat rental)"),
    ('3145', 'correction', 'F', 'No meaningful revision or reusable correction lesson: repeats420 and speculates checker-format trouble. Gold ambiguity means rejection must not coerce a120 rationalization.', 'the exact-answer checker might have been looking for a specific format'),
    ('3322', 'rich', 'F', 'Correct arithmetic-mean equation and solution40 under dataset interpretation, but impersonal derivation rather than first-person account.', 'Multiply both sides by 5 to clear the denominator:'),
    ('3322', 'record', 'F', 'Correct equation-solving recipe with substitution yielding59; fails first-person account, not arithmetic or missing headings.', 'Verify the average speed with the calculated speed of the fifth coaster:'),
    ('2998', 'rich', 'F', 'Correct25hours times30sites, but impersonal exposition and84tokens; not repairable by padding.', '20 + (1/4 * 20) = 20 + 5 = 25 hours per website.'),
    ('2998', 'record', 'F', 'Grounded proportional time increase then repetition, but entirely impersonal exposition.', 'Calculate the time Naomi takes to develop one website.'),
    ('6712', 'rich', 'U', 'Answer8 is terminal speed after two blisters; gold11 is time-average of12 and10 across the two intervals. Question asks speed without explicitly distinguishing these. Preserve oracle failure and ambiguity.', 'after accounting for the blisters, is 12 - 4 = 8'),
    ('6712', 'correction', 'F', 'Repeats terminal-speed8 without distinguishing average from terminal speed or producing a meaningful correction/lesson; rejection-only feedback did not help.', 'initial speed) - 4 miles per hour (reduction) = 8'),
    ('3590', 'rich', 'F', 'Correct dependent day counts and conservation29, but impersonal exposition and149tokens; do not pad the one-token deficit.', '354 - 325 = 29 pages.'),
    ('3590', 'record', 'F', 'Useful conservation check recovers354 pages, but impersonal recipe rather than first-person account.', '63 (day 1) + 126 (day 2) + 136 (day 3) + 29 (day 4) = 354 pages'),
    ('3426', 'rich', 'F', 'Correct split-amount/denomination counts2,5,10, but exclusively third-person narration, not first-person account.', 'Adding these up, 2 + 5 + 10 = 17 pieces of bills.'),
    ('3426', 'record', 'F', 'Grounded denomination-conversion recipe, but impersonal exposition. The final count restatement is not an independent conservation check.', 'Confirm the total number of pieces of bills is 17.'),
    ('5895', 'rich', 'P', 'Own account composes two doublings then2/3 to16 with grounded units;143tokens separately exclude it from training.', 'Now, I calculate the height of each jump:'),
    ('5895', 'record', 'F', 'Correct reusable multiplicative chain and stated checks, but impersonal exposition.', 'Calculate James\'s jump height by taking 2/3 of Jacob\'s jump height.'),
    ('7054', 'rich', 'P', 'First-person plural account tracks carryover inventory11,7,6; 52sold after batch2 uses earlier surplus, not negative physical inventory. Grounded reusable state-update operation.', 'since we already had 11 from the first batch'),
    ('7054', 'record', 'F', 'Material false check despite correct FINAL6: sums successive inventory states to24, then invents18sold. Actual total sold138 and states must not be summed. Also impersonal exposition.', '24 - 18 (sold) = 6'),
    ('1436', 'rich', 'P', 'Own first-person plural invitation to calculate is followed by grounded per-owner counts4 and3 and aggregation7; accepts plural voice, not only literalI.', "Now, let's calculate the total number of instruments each owns:"),
    ('1436', 'record', 'F', 'Grounded proportional category counts and sum; impersonal recipe rather than first-person account.', 'Add the totals from Charlie and Carli:'),
    ('1379', 'rich', 'P', 'Own stock-flow account separates breeding stock, additions, returns and removals across two springs;65+56=121.', 'Now, I calculate the number of kittens remaining after adoptions and returns:'),
    ('1379', 'record', 'F', 'Correct reusable stock-flow operations; first-person account absent. Summary remaining55 includes returns already represented in calculations.', 'Calculate the first spring remaining kittens:'),
    ('7073', 'rich', 'P', 'Own account inverts the remaining quarter to recover80, with explicit operation and known20 evidence;99tokens separately below the floor.', 'I need to determine what 1/4 of her savings is'),
    ('7073', 'record', 'F', 'Correct inverse-proportion recipe, but impersonal exposition and several repetitive restatements of20times4.', 'Recognize that the sweater cost represents 1/4 of her total savings.'),
    ('6388', 'rich', 'P', 'Own first-person plural equation-building uses the post-removal amount as the half-increase base; invert1.5 then restore6, yielding22.', 'we can set up the equation:'),
    ('6388', 'record', 'P', 'Own account records exact state equation and performs concrete substitution22→16→24, a genuinely reusable operation with a constraint check.', 'To check the result, substitute'),
    ('2554', 'rich', 'U', 'Invents equal3+3 split under an ambiguous six-small-and-medium statement; gold45 interprets6each. No uniquely supported34.5 answer; cannot coerce gold with reference reasoning.', 'Assume 3 apples are small and 3 are medium'),
    ('2554', 'correction', 'F', 'Rejection triggers repeated defense of arbitrary equal split, not meaningful correction or actionable lesson; recognizes ambiguity but still reports unsupported unique34.5.', 'the calculation based on the simplest assumption is correct.'),
    ('5714', 'rich', 'F', 'Correct time→sandwiches→slices→peppers dimensional chain, but impersonal instructions, not first-person account.', 'First, calculate the number of sandwiches served in an 8-hour day:'),
    ('5714', 'record', 'F', 'Grounded reusable dimensional conversion chain with numeric checks, but impersonal recipe.', 'Determine the total number of jalapeno slices needed.'),
    ('3289', 'rich', 'P', 'Own account nests floor/hall/room factors separately for each wing then sums1728+2520; avoids crossing wing rates.', "First, I'll calculate the number of rooms in the first wing."),
    ('3289', 'record', 'F', 'Good reusable hierarchical aggregation with units; impersonal exposition rather than first-person account.', 'Add the total number of rooms in the first wing to the total number of rooms in the second wing'),
    ('3501', 'rich', 'P', 'Own account subtracts known plate subtotal then divides residual cost by spoon unit price; grounded inverse-purchase operation.', 'Next, I subtract the cost of the plates'),
    ('3501', 'record', 'P', 'Own reusable residual-cost/unit-price account with concrete18,6,4 checks; all quantities grounded in task.', 'To solve this, I perform the following steps:'),
    ('4789', 'rich', 'P', 'Own first-person plural account converts packages to burgers and subtracts host; reusable capacity-minus-reserved-unit operation.131tokens separately fail floor.', 'we need to subtract one'),
    ('4789', 'record', 'F', 'Correct capacity-minus-host recipe and concrete guest/host count; impersonal exposition.', 'Subtract one from the total number of burgers'),
    ('2730', 'rich', 'F', 'Correct equal-share per-person/per-day calculation, but impersonal instructions and128tokens.', '200 flowers / 5 people = 40 flowers per person'),
    ('2730', 'record', 'F', 'Grounded normalization with reverse multiplication restoring200; impersonal recipe, not first-person account.', 'Total flowers planted by all 5 people in 2 days:'),
    ('1703', 'rich', 'P', 'Own account separately totals each coach then subtracts; grounded arithmetic290-53=237.143tokens separately below floor.', 'Now, I find the difference between what Coach A and Coach B spent:'),
    ('1703', 'record', 'F', 'Correct category-cost/difference recipe, but impersonal exposition rather than first-person account.', 'Subtract the total cost for Coach B from the total cost for Coach A'),
    ('5449', 'rich', 'P', 'Own first-person plural account identifies equal distribution and irrelevant mailbox colors; explicitly states equal-share assumption rather than inventing color-specific rules.', 'we assume each house, regardless of mailbox color'),
    ('5449', 'record', 'P', 'Own first-person plural explanation links even distribution to division and checks8times6=48; reusable relevance filtering plus normalization.', 'we need to distribute the total number of pieces of junk mail evenly'),
]


def main():
    rows = json.loads(Path(sys.argv[1]).read_text())
    lookup = {row['task_id'] + ':' + row['kind']: row for row in rows if row['kind'] != 'terse'}
    decisions = {}
    for task, kind, status, reason, span in READINGS:
        key = 'gsm8k-train-' + task + ':' + kind
        row = lookup[key]
        assert span in row['target'], key
        assert key not in decisions
        decision = dict(status={'P': 'PASS', 'F': 'FAIL', 'U': 'UNRESOLVED'}[status],
            target_sha256=row['target_sha256'], reason=reason, evidence_spans=[span],
            reviewer='MATH-RICH full-text author reading, not independent verification',
            first_person=status == 'P' or (task, kind) in {
                ('4062', 'rich'), ('4062', 'record'), ('3145', 'correction'), ('2554', 'correction')},
            grounded_operations=True, checkable_expectation=True, reusable_content=True, no_padding=True)
        if status == 'U' or kind == 'correction':
            decision['grounded_operations'] = None
            decision['checkable_expectation'] = None
        if (task, kind) in {('4062', 'record'), ('7054', 'record')}:
            decision['grounded_operations'] = False
            decision['checkable_expectation'] = False
            decision['reusable_content'] = False
        if kind == 'correction':
            decision['meaningful_revision'] = False
            decision['reusable_content'] = False
            decision['no_padding'] = False
        decisions[key] = decision
    assert decisions.keys() == lookup.keys(), 'every_nonterse_row_must_have_explicit_reading'
    Path(sys.argv[2]).write_text(json.dumps(decisions, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
