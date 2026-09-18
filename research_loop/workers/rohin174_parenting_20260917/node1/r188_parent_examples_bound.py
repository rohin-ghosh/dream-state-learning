"""Parent-only worked examples from Rohin's R188 instruction."""


MARKER = 'R188_REPORTED_WORKED_EXAMPLES_V1'
PROVENANCE = 'Rohin message188, relayed by Fable, September17,2026'
EXAMPLES = (
    ('C2 separating case',
     'Rohin reports C2 compared competing formulas using a separating k=3 case: '
     'state what each predicts, make the actual calculation, compare the observation, '
     'revise the judgment, and carry the correction into the next choice. '
     'This is a reported example, not a new result or a numerical answer for this child.'),
    ('Pilot receipt discipline',
     'The pilot example is: "no execution receipt is visible". Distinguish a proposed '
     'action, an attempted action, a returned receipt, and evidence that the intended '
     'claim passed. A successful process exit alone does not verify its answer.'),
    ('Raw Next-Steps handshake',
     'Rohin cites the raw child\'s Next-Steps handshake: carry an unfinished next step '
     'forward and check what actually happened before reporting progress. Do not '
     'invent its transcript or an execution outcome; this is the reported pattern.'),
)


def parent_policy_suffix():
    examples = '\n'.join(name + ': ' + text for name, text in EXAMPLES)
    return ('\n\n' + MARKER + '\nSource: ' + PROVENANCE + '.\n' + examples
        + '\nUse one short worked example at a time, attributed to its source child, '
        'then ask the recipient to apply the method to its OWN current object. '
        'Do not copy another child\'s object, assert that the recipient did the example, '
        'supply its task answer, or make a recurring checklist. Preserve English, '
        'the existing message cap, parent attribution and masked training status. '
        'Do not repeat a queued baseline or inject into a fixed comparison during '
        'its declared parent-withdrawal window. Ask both ways: should you keep '
        'thinking, or are you better off with new data? If data is becoming '
        'redundant, perhaps think more. Sometimes staying with the problem is right. '
        'Show how the observation changes the next action, not merely the vocabulary.\n')


def append_parent_examples(principles):
    if type(principles) is not bytes:
        raise ValueError('principles_must_be_utf8_bytes')
    principles.decode('utf-8')
    if MARKER.encode() in principles:
        raise ValueError('worked_examples_already_present')
    return principles + parent_policy_suffix().encode('utf-8')
