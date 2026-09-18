"""Prospective continuity prompts; fixed R184 comparison prompts stay unchanged."""


SCHEMA = 'R193_CONTINUITY_V1'
PARENT_QUESTION = ('What from your last attempt remains useful? What does the result tell you '
    'to change? Does the action you are about to take actually make that change? Then fade '
    'the reminder and observe whether the child follows through on its own.')


def continuity_prompt(stage, *, think_remaining=1, environment_facts=None):
    carry = ('Your working state survives sleep and compaction; preserve useful judgments and '
        'unfinished questions without reciting a fixed field block. Update only what changed. '
        'For each claim you keep, retain its status in your own text: POSSIBILITY (an uncommitted '
        'idea), EXPERIMENT (tried locally with an expectation), or STANDING PRACTICE (a revisable '
        'default supported by experience). These are your judgments, not automatic verification. '
        'Optional labelled lines such as POSSIBILITY [name]: ... can update a claim; reuse its '
        'name when changing its status. Next intention: ... may carry unfinished work. '
        'Keep original observations intact; label a later reinterpretation separately with its '
        'source and reason. Revisit an older episode selectively when a new result contradicts '
        'it, a failure recurs, or it becomes relevant—not merely to retell it. ')
    if stage == 'THINK':
        return ('Runtime status: THINK. Before continuing, consider what you currently think '
            'about the work and your approach. Has anything changed your judgment, strengthened '
            'it, or left something unresolved? Explore what seems worth exploring. If your '
            'judgment remains the same, carry it forward briefly and continue acting. '
            'Compare the last actual result with what you expected: what will you PRESERVE, '
            'what will you CHANGE, and what is the change EXPECTED to do? Are you testing '
            'an alternative or following a practice? Nothing changed is an acceptable answer. '
            'When useful, look across recent attempts: is your pattern of thinking and acting '
            'helping, and what actual results support that judgment? '
            'Should you keep thinking, or are you better off with new data? '
            + carry + f'At most {think_remaining} Think responses remain. You choose when '
            'to act by writing Ready to act. The bounded fallback is recorded. No code '
            'written in Think is executed.')
    if stage == 'ACT':
        facts = '' if environment_facts is None else 'Bound environment facts: ' + environment_facts + ' '
        return ('Runtime status: ACT. Carry out the revised approach from your last THINK; '
            'before executing, check in one line that this action actually incorporates '
            'the change you chose. Continue what remains useful from the previous attempt '
            'rather than restarting or repeating a rejected script. For a calculation or '
            'program provide a plain Python fenced block. The CPU tool has no network or GPU. '
            + facts + 'Wait for the actual receipt; do not invent an outcome. Failure or no '
            'feedback must remain visible. ' + carry)
    if stage == 'LEARN':
        return ('Runtime status: about to LEARN (sleep), after the bounded action/feedback cycle. '
            'No optimizer update has happened yet. Review the actual observation or explicit '
            'absence of feedback. What did you try, what happened, and therefore what will '
            'you preserve or change next? What unfinished decision must survive? Nothing '
            'changed is valid. Distil what is worth keeping in this existing review; do not '
            'rewrite an observation as if it had a different outcome. ' + carry
            + 'Sleep trains new child responses with their preceding context and status labels; '
            'parent, runtime and tool text are context, not targets. No older-row rehearsal.')
    raise ValueError('known_wake_or_sleep_notice')
