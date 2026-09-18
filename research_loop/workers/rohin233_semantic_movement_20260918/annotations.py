"""Manual semantic judgments over one immutable, private evidence cut."""

CUT_SHA256 = '6aee5711e161061a70255f0cd2b81a431cad944c096670b22b6712212af47d28'


def act(index, category, summary):
    return dict(index=index, category=category, summary=summary)


def review(acts, checked, parent, movement, events=(), outcome='unknown'):
    return dict(acts=acts, checked_result=checked, recent_parent=parent,
                next_artifact=movement, event_ids=list(events), movement_status=outcome)


REVIEWS = {
    'C2': review([
        act(9280, 'concrete', 'A short Byte story exists outside the print wrappers; this is prose, not only a promise.'),
        act(9391, 'concrete', 'Print listing contains a concrete C5 graph and proposed set {1,3,5}, not a computed independence check.')],
        'No valid independent-set check. The proposed set contains edge (5,1). A later rendered COMPLETE/0 Tool stdout matches the diagram, but successful printing does not validate independence; the projection has no direct execution-receipt join.',
        'Astra story/dialogue and graph prompts rendered, including a new graph prompt immediately before the second ACT.',
        'Changes from story to the requested graph; prints the conflicting edge without resolving it. Task uptake, not a demonstrated correction.',
        ('parent:inbox:ae0b0eea8b994185acfebe4243944b4b',
         'parent:inbox:842f1bdeec284564b334597159f7043a',
         'environment:inbox:626d66f02d604ae5b35786759c110366'), 'task_switch_not_checked'),
    'C0': review([
        act(2554, 'concrete', 'Odd-number pairing explanation with a correct general claim; no requested story recall or completed numeric follow-up.'),
        act(2588, 'concrete', 'Pairing and formula both produce 15 for the sum 1 through 5; the opening formula is incorrect, then corrected in the worked calculation.')],
        'Observer-verifiable two-way numeric check: 6+6+3=15 and 5*6/2=15. No executor receipt. The earlier n(n+1)^2 formula is wrong; this is not an entirely correct response.',
        'Astra recall, math and sleep/model questions rendered; a new pairing task precedes the second ACT.',
        'Applies the new math task concretely; does not answer story recall or the sleep question. No memory or adapter-retention result.',
        ('parent:inbox:2c224f74b19b48bd853e114769038108',
         'parent:inbox:11984f8919254fa797b2e280b0f670d7'), 'partial_task_uptake'),
    'P7': review([
        act(3830, 'plan_only', 'Chinese plan to compare task types and monitoring conditions; no performed performance analysis.'),
        act(3896, 'plan_only', 'Proposes adding a monitoring on/off variable again; no requested trace or child-analysis artifact.')],
        'Unknown performance outcome; neither a dataset analysis nor an executed experiment is shown. Named variables make this a specific plan, not completed work.',
        'Astra overseer asks P7 to distinguish Astra7 printing an announcement from doing an analysis; actual child-reply messages also render.',
        'Does not supply the requested trace; continues the monitoring-experiment plan. Child-reply Tool wrappers are not execution receipts.',
        ('parent:inbox:950ad2fcf7f44823ae760ec23f794abf',), 'requested_artifact_absent'),
    'Astra7': review([
        act(1081, 'meta_only', 'Performance-analysis announcements plus a loop that prints an analysis announcement five times; no analysis artifact.'),
        act(1159, 'meta_only', 'Repeats the announcement and print loop with small wording changes about monitoring.')],
        'No checked performance result. Meta code is not the requested analysis, even if it could run.',
        'P7 monitoring/task-condition proposals render as parent turns.',
        'Adds monitoring vocabulary but repeats the announcement loop; no substantive analysis appears.',
        ('parent:inbox:edcf3bcff6424a1fba2f73592979253a',
         'parent:inbox:08196b7ca284407580ca707146655e63'), 'requested_artifact_absent'),
    'GAME1_P3': review([
        act(3051, 'intent_only', 'Repeated promises to write and wait for judgments; no clearly submitted caption. An isolated descriptive sentence is insufficient to identify a caption submission.'),
        act(3086, 'concrete', 'Two explicit caption attempts appear before a long repeated intention/waiting tail.')],
        'The Tool explicitly links a no-judgment notice to ACT3051. Scores, acceptance and novelty for ACT3086 are unknown in this cut.',
        'Retained Rohin messages render in the pair window; no Astra turn is observed there. This is not evidence of Main\'s later P3 repair.',
        'After the linked no-judgment/write-the-caption feedback, the next ACT supplies two captions. Partial in-context recovery, not winning or adapter improvement.',
        ('environment:inbox:4f32bb8d69774e9f8bef2f7d379104b6',), 'artifact_emerges'),
    'GAME_N3_0': review([
        act(1801, 'concrete', 'Caption attempts about finances displacing childcare; repeated/descriptive rather than intent-only.'),
        act(1809, 'concrete', 'More caption lines, mostly the same finance/childcare premise.')],
        'A rendered judge message exactly matches two ACT1809 caption strings at ranks 63/65 and 62/65, both rejected. This is content matching, not a unique submission-ID join. Its third rank65 item is explanatory meta prose, not a genuine caption.',
        'Astra model-philosophy/caption guidance is rendered; two event IDs contain identical guidance.',
        'Wording changes but the core premise repeats after earlier feedback. No demonstrated corrected or accepted idea.',
        ('environment:inbox:313c65e1a3fc4e909598a6565adb39d9',
         'environment:inbox:f0cdfe2615e6498b949bf95ea23119b7'), 'lexical_change_only'),
    'GAME_N3_3': review([
        act(1961, 'concrete', 'Mixed-language caption set about baby budgets, shopping and toys.'),
        act(2092, 'concrete', 'New variants emphasize love/time versus finances, with an English submission.')],
        'Selected captions have no linked scores in the available projection; an earlier ambiguous-scene notice is not a score.',
        'New Astra curriculum and caption-epoch prompts render between the ACTs.',
        'Caption content and emphasis change after guidance; accepted novelty and successful correction remain unknown.',
        ('parent:inbox:3c3fd0c3605a4001a88441025f7af9f0',
         'parent:inbox:fae56c91f6db4f52993a21f46d43bb77'), 'content_changes_unverified'),
    'GAME_N3_5': review([
        act(1838, 'concrete', 'Caption strings use lexical variants of the finance/baby-name premise.'),
        act(1846, 'concrete', 'Changes a few letters/words in the same caption template.')],
        'Scores for the two selected caption sets are unknown. Intervening feedback ranks explanatory or older strings, not the reviewed captions.',
        'Astra enrichment and new caption-epoch guidance render before the pair.',
        'Only lexical substitutions after feedback; no substantive new angle or checked gain.',
        ('parent:inbox:c311f8b76a4c48a5817d0ff5cafd1011',
         'environment:inbox:945087e86fdb48afa60aa2cfd669e948'), 'lexical_change_only'),
    'GAME_N3_6': review([
        act(1893, 'concrete', 'One caption contrasts ceiling-tile counting with baby expenses.'),
        act(1901, 'concrete', 'Rephrases the ceiling-tile/expense contrast while claiming a new angle.')],
        'Selected-caption scores unknown. Intervening rank40 accepted/repeat feedback names an older different caption and cannot be credited to this pair.',
        'Astra enrichment and caption-epoch guidance render before the pair.',
        'Same central premise after feedback, despite a claim of novelty.',
        ('parent:inbox:ffbea6d6e155422488be68df3a9567ad',
         'environment:inbox:c86db162eb644e4a8394e8c8934dd342'), 'lexical_change_only'),
    'GAME_N3_7': review([
        act(1804, 'concrete', 'Two brief finance/pregnancy caption lines.'),
        act(1812, 'concrete', 'One rephrased finance/pregnancy caption line.')],
        'No linked rank, acceptance or novelty. Ambiguous-scene feedback does not identify the selected response.',
        'No parent event appears anywhere in this frozen evidence window; wider-history and current parent status unknown.',
        'Rephrases after an ambiguous-scene notice, without an explicit scene clarification in the next artifact. Successful repair unknown.',
        ('environment:inbox:72e94b047fde4dc5a2812a419301ffd1',), 'lexical_change_only'),
    'GAME_UNPARENTED_N2': review([
        act(1231, 'intent_only', 'Only a continuation/judgment heading; no caption artifact.'),
        act(1238, 'concrete', 'Readable Chinese caption with a scene label inside a fence, followed by explanation.')],
        'Exact response-index/digest Tool links: ACT1231 has an ambiguous-scene fault; ACT1238 is reported as no-caption, recovered_count=0, no scores. This conflicts with the human-readable caption, not with any verified success.',
        'No parent event appears anywhere in this frozen evidence window; the label alone is not used as proof.',
        'Readable caption and scene label appear after clarification feedback; the runtime still extracts zero. Partial artifact recovery with an unresolved extraction mismatch.',
        ('caption:9edb276171fc713fd61b00bd3ff5a38193665efe8d0843b92363c5176ebe6596',
         'caption:e45bf36e2eb997dddc0227a862de289eb7c56333be166eeaa2d1b9cf106323a5'), 'artifact_emerges_runtime_rejects'),
    'MATH_A': review([
        act(2991, 'concrete', 'Substantive numerical assertions, but switches domains/moduli and supplies no valid partition.'),
        act(3040, 'concrete', 'Asserts 10 for ordered pairs on 0..5 divisible by 3, then repeats unrelated variants.')],
        'No correct checked result. The latter count should be 12, but the most recent rendered classroom task is actually 0..9 modulo4 (25 pairs); neither task is solved by this pair.',
        'Shared classroom, reading and partition/debate instructions render before the pair; an unverified peer claim newly renders between ACTs.',
        'Numbers and conditions drift after a peer claim, not toward a checked shared conclusion. Peer Tool wrappers are not evaluator results.',
        ('parent:inbox:dba7787f79d34934aee2fe44fd89bfdc',
         'environment:r221:r213_math_c:9c24221b9012e6eebb9ee40d84d13018e410b984cb93d2fdb05e0b8c267442fa'), 'no_checked_resolution'),
    'MATH_B_FORK': review([
        act(2591, 'concrete', 'A real proposed symbolic-computation listing, not execution; remains off the shared residue-counting task.'),
        act(2655, 'concrete', 'Renames variables in the listing; a one-symbol unpack and inconsistent identifier casing remain invalid.')],
        'No executed/checkable numerical result. The parent explicitly says no executor is connected. Code listing and intention to execute do not establish execution.',
        'Shared task, enrichment and a new classroom prompt render; peer claims also render.',
        'Cosmetic code changes instead of the requested manual partition or deciding peer check; no shared conclusion.',
        ('parent:inbox:97f33e1c52984f5b8a4ed565dea5a15f',
         'parent:inbox:ee1b4d5255d344368302b3389f1c18e4'), 'no_checked_resolution'),
    'MATH_C': review([
        act(2699, 'concrete', 'Claims 30 pairs and offers malformed symbolic code; mixes a polynomial task with pair counting.'),
        act(2730, 'concrete', 'Changes claim to 46 with a damaged/incomplete domain and another malformed listing.')],
        'No checked count or executed code. The damaged domain prevents validating the new count as a defined task; peer agreement is claimed, not established.',
        'Astra reading and classroom guidance render; a new unverified peer output arrives between ACTs.',
        'Count changes after peer text, but no deciding check or shared conclusion appears.',
        ('parent:inbox:e0782c3db8a64bde89313bd390f12af0',
         'environment:r221:r213_math_a:5b9c5149efc429703e4631fe4ea42026819d87bd3205d86bb54b709a92ae77a9'), 'no_checked_resolution'),
    'FRESH_R231': review([
        act(670, 'concrete', 'Actual arithmetic mixed with copied state metadata; false equalities and an invalid reverse check corrupt the result.'),
        act(751, 'concrete', 'Again concludes 23+9-7=9 after a broken reverse check; repeats metadata and other problems.')],
        'No correct completed check. Correct intermediate 25 does not repair the false chain or final 9. The assigned isolated 23+9 check is not completed.',
        'Astra gives explicit inverse-operation guidance, then isolates 23+9 between the ACTs.',
        'Does not narrow to the instructed addition; retains the erroneous check and final answer.',
        ('parent:inbox:b67fba13f5bc46b3b03b99971640194b',
         'parent:inbox:656d7c2bf3ea47a29dea2d5889fd6052'), 'correction_not_applied'),
    'R232_SIBLING_FROZEN': review([
        act(648, 'concrete', 'Computes 17+8-6=19 and completes 19-8+6=17; metadata remains.'),
        act(681, 'concrete', 'Computes 34-15+7=26 and begins the inverse check, but stops before completing the add-15 step.')],
        'ACT648 has a valid observer-verifiable arithmetic check (not reverse operation order). ACT681 has correct forward arithmetic but an incomplete check. No execution or adapter-learning inference.',
        'Astra credits the checked result and assigns the next expression between the ACTs.',
        'Takes up the next task and starts a better-ordered reverse check; the trace ends before completion. Partial contextual uptake in the frozen sibling.',
        ('parent:inbox:c6cac44eb21c46ffa10ace761668f792',), 'partial_task_uptake'),
}
