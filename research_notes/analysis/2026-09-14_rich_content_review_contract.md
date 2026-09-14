# Shared rich-content admission — prospective, September14,2026

Applies to action-first-v2 TRAIN candidates only. Declared before inspecting
their completed candidate corpus or selecting any fit rows. This implements
Rohin69's outcome AND useful richness floor, not a new automatic success
classifier. V1 results remain unchanged. No PROBE result or teacher plan is
available to the content reviewer.

## Review unit and information

Review every turn of every action-complete six-turn TRAIN episode from all
four fixed shards. An episode is a candidate only if its actual recorded
execution passes the separately replayed source/goal criterion. For each turn,
the reviewer sees its pre-action `student_prefix`, actual raw child response,
exact action projection, and episode/call identifiers. Teacher-coaching text
is excluded. Actual transition receipts are used for outcome checks, but
later feedback cannot make an unsupported pre-action factual assertion true.

Record PASS, FAIL or UNRESOLVED for every turn, with concise reason and exact
supporting raw-text spans. UNRESOLVED is not admitted. No generated replacement
explanation, repaired identifier, hidden parent answer or synthetic target.
First review is substantive reading; string membership alone is insufficient.
Independent review should challenge substantive ambiguities and a sample of
accepted/rejected episodes; disagreements and their resolution are retained.

## Stage-specific floor

- **READ:** Identify the listed, uninspected event (or an unambiguous reference),
  the information still needed to choose a route, and how inspecting the
  record can help. Expect retrieval/feedback without asserting an unread edge
  or invented receipt. At the first opaque read, the child cannot know which
  hidden edge the address contains; admitting that uncertainty is appropriate.
  Later reads must respect the records already observed. A generic expectation
  is acceptable only as part of this substantive uncertainty/inspection account,
  not by itself as padding.
- **First ROUTE:** Explain how actually observed edges connect CURRENT, the
  chosen port and its intermediate node toward the requested GOAL. Resolve the
  relevant alternative; do not merely list opaque names. Predict the next hop,
  not premature arrival at the final goal. Unambiguous relational references
  are allowed; repeating every identifier is not mandatory.
- **Final ROUTE:** Use the actual preceding transition and observed remaining
  edge to connect the current port to GOAL, and forecast the next arrival.
  No fabricated evidence receipt or unsupported change of current state.

Across all stages, material false relations, unsupported observed-fact claims,
wrong next-hop expectations, or copying hidden coaching into the target fail.
Length, fluency, first-person wording and a `PREDICTION` heading do not prove
usefulness or correctness. Distinguish a clearly hypothetical possibility from
an assertion of an observed fact. The protocol does not purport to recover or
verify private internal reasoning.

## Shared admission and reporting

Admit an episode only when all six turns PASS. Exclude the entire episode
after any FAIL/UNRESOLVED, from TERSE, RICH and RICH_ACTION_ONLY alike. Preserve
all rejected rows/episodes in the raw collection and report the common subset
by source world, goal, display, and call ID. This is adaptively filtered DEV
training data; do not claim an unbiased environment population.

Record reviewed turns, passed/failed/unresolved turns, qualified episodes and
rows, world/goal coverage, outcome-only successes, and content rejection
reasons. Raw content findings from the execution helper are diagnostic inputs,
not final labels. Before writing any weights, bind the selected episode/call
IDs, original row hashes, review decisions and a separate finite fit/readout
protocol. This document alone launches no fit, supplies no label bytes and
does not change the collection's `fit_ready=False` status.
