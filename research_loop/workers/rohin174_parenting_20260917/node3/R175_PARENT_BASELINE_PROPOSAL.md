# Proposed baseline and seminar operations — not yet Main-bound or delivered

## Baseline for all six lives

Use only the learner's real, permitted training observations. Distinguish an
intended action, an action actually performed, and its observed result.
For each completed learning cycle, keep a small operational record:

- `observation`: what was actually observed, with the training-record or tool-result reference; not a held/sealed/readout result.
- `prior_intention`: the intention before acting.
- `action_selected`: the concrete next operation; this is not evidence that it ran.
- `action_performed`: what actually ran, with its evidence reference, or explicitly `not_performed`/`unknown`.
- `post_action_state`: the state after that action, its evidence reference and observed/pending/unavailable status. Never predict an outcome and relabel it observed.
- `next_intention`: what the learner will now do differently, or an honest unchanged/unknown value.
- `intention_change_reason`: the specific observation or post-action evidence supporting the difference from `prior_intention`.
- `open_uncertainty`: what remains unknown and which observation would resolve it.
- `provenance`: life ID, completed-sleep/cycle identity, REQUEST/parent-turn references, action-result references, and self-observation versus peer-report labels.

The target is at least one evidence-backed changed intention per completed
cycle. The target is an audit criterion, not permission to invent a change.
If no supported change occurs, preserve that fact. No proposed procedure is
described as already learned; no C2 or exact success propagation is introduced.

When the existing compaction mechanism asks for or uses a learner summary,
request that the operational record and its unresolved next action be carried
forward within the existing summary budget and visibility rules. Do not request
a reset, alter R179/sleep/context code, or claim persistence without checking the
actual post-compaction record. Repeating a field name is not proof that its value
and provenance survived.

## Proposed assignments for Main to freeze

| GPU | Life | Prospective intervention |
| --- | --- | --- |
| 2 | brain_free | baseline + A: strict dense long-message guidance, every response |
| 1 | creative_reread | baseline + B: real-transcript walkthrough, every 2 responses |
| 3 | brain_guided | baseline + C: questions-only self-derivation, every 3 responses |
| 7 | creative_select | baseline + D: exactly three light-steering questions, every 3 responses |
| 4 | creative_free | baseline + hands-off contrast, no A/B/C/D overlay |
| 0 | support_free | baseline + hands-off contrast, no A/B/C/D overlay |

All six receive the baseline. Contrast cadence and exact baseline delivery
mechanism remain for Main to bind; the table is not an exact assignment freeze.
In particular, the currently request-clock parents on GPUs 0 and 2 must not be
silently represented as already response-clock. A hands-off contrast receiving
baseline and a seminar is baseline-plus-seminar prospective, not untouched R166.

## Suggested seminar pairs and explicit post-action exchange

1. `brain_free (GPU2, proposed A)` ↔ `brain_guided (GPU3, proposed C)`: same brain programme; compare a concrete explanatory/derivation operation and the state it actually left behind.
2. `creative_reread (GPU1, proposed B)` ↔ `creative_select (GPU7, proposed D)`: same creative programme; compare a concrete reread/revision/selection operation and its actual post-action state, without reading or supplying caption ratings.
3. `creative_free (GPU4, proposed baseline hands-off)` ↔ `support_free (GPU0, proposed baseline hands-off)`: cross-programme procedural exchange only. Exchange uncertainty, performed operation, post-action state and changed next intention; do not import domain outcomes as transferable successes.

Each speaker sends the operational record only after the relevant action was
actually performed and its post-action state was observed. If either condition
is missing, send an explicit pending/unavailable status, not a simulated result.
Include sender life ID, source REQUEST/turn and action-result references, the
actual post-action state, prior and next intentions, and the reason for change.

The peer labels this `peer_report`, states which next operation it proposes to
test locally, and records its own post-action state separately after execution.
A peer report does not establish a local outcome or shared learning success.
Do not replay old inbox IDs, use sealed evaluation information, or copy an
answer/success payload as if it were the recipient's evidence.

Relay through each life’s single bound parent lead using Main's common helper;
do not spawn a second lead or construct an independent child-message channel.
Log both directions and the eventual rendered training REQUEST evidence. Pair
participation creates cross-life exposure: label prospective contrasts and do
not represent these connected lives as independent causal replications.

## Three-completed-sleep check

- Anchor at the actual first rendered REQUEST containing the bound baseline, with its parent-turn/publication identity and record hash. A config or STARTED receipt is not the anchor.
- Count the next three distinct, actually completed SLEEP_COMPLETE events/cycles after the anchor. Keep partial-cycle exposure explicitly labelled; Main must bind how a partly exposed first cycle is scored.
- For each completed cycle, check for at least one changed intention with a real prior/next difference and source/action/post-action references supporting it. Missing or unchanged is recorded honestly, not inferred from fluent text or fabricated to meet a quota.
- Where compaction actually occurred, compare the carried field values and provenance in the pre/post records. If none occurred, report `not_observed`, not passed retention. If a required artifact is unavailable, report `evidence_pending`.
- If three completed sleeps or the required evidence do not arrive before the unchanged stop, report pending/incomplete. Do not reset counters, prolong the lease, retire a live learner, or infer death from a waiter.

## CPU-tool-feedback audit scope

After staging parent changes, inspect only package metadata in the actual child
interpreter and tool executable availability. Do not install/import heavy GPU
packages, execute learner actions, read credentials, modify environments, or
claim that an installed library is exposed through a child tool. A real feedback
path still needs a bound allowed operation, actual execution receipt, resulting
state, and rendered training exposure; availability alone establishes none of
those.
