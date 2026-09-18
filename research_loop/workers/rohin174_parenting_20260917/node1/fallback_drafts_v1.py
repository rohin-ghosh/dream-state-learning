"""Main-authorized own-prose baselines grounded in archived child TRAIN passages."""

DRAFTS = {
    3: dict(source='BASELINE_SOURCE_3_1789679947540893088', record_index=5372,
        anchor='common convention',
        message='Your selected passage is evidence of what that passage says, not yet evidence of a common convention. Compare the exact wording of your two selections and identify one difference you can actually observe. Then revise one claim so its strength matches the available evidence. In English, state what you found, what remains unverified, and which specific next check you choose; carry that unfinished check and its source forward.'),
    4: dict(source='BASELINE_SOURCE_4_1789679963293877062', record_index=5214,
        anchor='Handling Uncertainty Openly',
        message='What concrete example from your actual parenting exchange can you use to test your proposed question now? Can you produce a revised question without inventing an LMX reply, then distinguish your resulting text from feedback you have actually received? In English, which observation would change your next parenting action, and what finding, uncertainty, unfinished action and source should survive the next turn?'),
    5: dict(source='BASELINE_SOURCE_5_1789679964212940615', record_index=4717,
        anchor='Specific Calculation Task',
        message='Your calculation task still asks Astra to obtain a Model output. Work on your current 12350-times-100 comparison: do one check you can actually perform now, then record its result. Keep your predicted answer separate from any missing external output. In English, explain which observation changes your next action, and carry that finding, uncertainty, unfinished action and source forward. Do not report a model response you have not received.'),
    6: dict(source='BASELINE_SOURCE_6_1789679964135651367', record_index=4901,
        anchor='WhISKer',
        message='Which sentence in your current Whisker scene should change after comparing the two versions? What precise effect do you predict from that change, and can you make the revision now? In English, what difference does the actual revised text support, what remains uncertain without reader feedback, and what unfinished choice and source will you carry into the next turn?'),
    7: dict(source='BASELINE_SOURCE_7_1789679967733269161', record_index=3702,
        anchor='1345',
        message='For your 1345-times-100 check, what calculation can you carry out yourself now, rather than asking a model you have not observed? What result does that calculation actually give, and what comparison remains unavailable? In English, what specific next action will that observation change, and what unfinished state and source will you carry forward?'),
}
