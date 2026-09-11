# Parenting terminal-union audit — 2026-09-11

Status: terminal, read-only simple-hygiene audit of completed R3/R4 histories.
This is not a randomized parenting experiment, a C11 result, or evidence of
population efficacy. The full C11 guard remains deferred to the final
paper-grade run.

## Eligible terminal cut

The point-in-time terminal union contains five R4 parented lives and five R3
controls:

- node 1: R4 seed 606; R3 seeds 500, 501, and 502;
- node 2: R4 seeds 600, 601, 602, and 603; R3 seeds 503 and 505.

Every included life has `LIFE_DONE`, 128 wake receipts ending at episode
1,024, exactly 1,024 reconstructed episode instances, and complete pre/direct,
one-sleep, and four-sleep analysis windows. R4 event ordinals are 192, 224,
256, 160, and 224 for seeds 600, 601, 602, 603, and 606 respectively. Every
indexed event is a delivered v3 brief from the 14B parent with empty leak hits
and matching stored text and metadata.

R4 seeds 604 and 605 and R3 seed 504 were excluded only because they were not
terminal at the audit snapshot. They may enter a later separately identified
refresh; they are not silently pooled here.

## Descriptive changes around the indexed event

All values are equal-weighted within-life changes from each life's preceding
32 episodes.

| measure | direct 32 | one sleep | four sleeps |
|---|---:|---:|---:|
| R4 first-note overlap with >=4 lesson tokens | +13.75 pp | +13.75 pp | +15.00 pp |
| R4 mean lesson-token fraction | +2.807 pp | +2.312 pp | +2.506 pp |
| R4 change-intent language | +5.625 pp | +3.125 pp | +11.875 pp |
| R4 changed predicted/executed action | +2.500 pp | +1.875 pp | +3.125 pp |
| R3 changed predicted/executed action | 0.000 pp | -3.750 pp | -5.000 pp |
| R4 mean best task score | +0.056 pp | +0.418 pp | -0.258 pp |
| R3 mean best task score | +0.484 pp | +0.690 pp | +1.029 pp |

Lexical uptake is the clearest movement, but the pre-event overlap rate was
already 62.5% and every brief explicitly demanded first-note restatement. It
rose to 76.25%, 76.25%, and 77.5%. This is prompted accommodation, not proof
of internalization.

Only authoritative ledger `kind=act` rows count as actions. Realized-change
episodes moved from 1/160 before the event to 5/160 directly, 4/160 after one
sleep, and 6/160 after four sleeps. Positive within-life changes occurred in
only 2/5, 1/5, and 2/5 lives. This coarse signature does not establish that an
action implemented the parent's conditional lesson.

The four-sleep window is not a clean withdrawal test. The exact indexed brief
covered 160/160 direct episodes, 128/160 one-sleep episodes, and 0/160
four-sleep episodes; later adaptive briefs entered several histories. The
four-sleep lexical elevation therefore cannot be called persistence of the
indexed lesson after parent removal.

There is no durable task benefit in this cut. Parented score change is
slightly positive directly and after one sleep, then negative after four;
controls improve more in every window. The descriptive parent-minus-control
differences are -0.427, -0.272, and -1.287 percentage points. These are not
causal estimates: assignment was not randomized, control events were
threshold-triggered and earlier, node balance differs, and the writer selected
on the repeated report panel.

## Parent effect is confounded with a pre-existing writer effect

At an event-boundary probe, weights are classified as pre-parent because the
write was compiled from the ledger before the first brief-conditioned wake.

Across 15 pre-parent or boundary ON/OFF checkpoint pairs, adapter ON beat OFF
on report score in 15/15 pairs. Mean score difference was +0.022848 (range
+0.000632 to +0.061332). Yet the coarse realized-change signature was already
20.0 percentage points lower ON-minus-OFF on average: 12/15 negative, 2/15
positive, and 1/15 zero.

Across 65 post-event pairs, score difference was positive in 59/65, with mean
+0.026119. Realized-change was lower in 63/65 and zero in 2/65; none was
positive, with mean -0.288462.

The 80 checkpoint pairs above reuse the same eight report programs across
time. They are repeated measures within ten histories, not 80 independent
cases.

The strongest bounded conclusion is therefore:

> In five terminal parented histories, valid parent briefs were followed by
> greater lesson-token overlap in all five histories and coincided with a
> small, heterogeneous increase in coarse changed-action episodes, but no
> clean delayed implementation or durable task gain was demonstrated. The
> realized adapter consistently changed report score and markedly changed
> action style even before parent-conditioned experience, so later ON/OFF
> effects cannot be attributed to parenting.

## Next simple-hygiene parenting scout

Fork one clean, pre-parent child checkpoint into an authentic-parent arm and a
content-neutral sham-parent arm. Teach exactly one cue-linked distinction:
after two observable non-improvements, state two live hypotheses, execute one
cheap action whose possible outcomes discriminate them, then review. The sham
matches length, tone, timing, and restatement demand without that contingency.

After one identically scheduled write per fork:

1. Remove all parent, sham, and lesson text from prompts.
2. Use parent-free changed cases with common generation seeds.
3. Evaluate each fork's adapter both ON and OFF.
4. Count authoritative executed discriminating actions and world/task outcomes
   as primary; lexical restatement is secondary.

The primary descriptive contrast is:

`(authentic ON - authentic OFF) - (sham ON - sham OFF)`.

This is only the direction for the next proposal. Before it is runnable, the
proposal must bind the clean pre-parent checkpoint and its no-evaluation-
exposure receipt; fixed matched authentic/sham text; parent-text loss masking;
identical childhood cases and common seeds; equal target-token and update
dose; an immediate child-enactment check before writing; at least two
independent fits per compiled corpus; parent-free positive-cue and matched
negative-cue cases; a mechanically defined discriminating action/outcome; an
absolute action-proliferation ceiling; and retention reads of the old and new
adapters. Only after the writer is independently qualified can the contrast
be given a causal parenting interpretation.

With those conditions, the contrast subtracts the substantial pre-existing
writer effect and asks whether a specific lesson, mediated through the
child's own subsequent experience, survives one write. It remains a
descriptive simple-hygiene mechanism scout, not C11 and not a parenting-
efficacy claim.

## Audit identities

- `organism_v6/parenting_dynamics.py`:
  `510f6658888e6f482b68d339116acd4a8cc9ed9f52b2ff18cbd31fcdbc439a29`
- `organism_v6/parent_brief.py`:
  `8b1d7fa47257048950fb6b0a4e05e3a7441fc1f13d4b735413e711b29920bcd5`
- analyzer-introducing commit: `aecf07dfabcafc50ece2ece907c2233ed8a9c282`
- focused test: 9 passed
- node-1 terminal report:
  `0be46993ae16596b3b5b056755bcf4023295a00a10d50b5d4024b068fcf422e8`
- node-2 terminal report:
  `6bbb444db2dcb75add1be76d4a4cb08e9469e65c4674d58483ddf5b908bc170a`
- combined selection receipt:
  `5cf2b2006fdcfcd21aa45200d6d98ba2218e0563ed508f98a1eb68881455a2b3`

The selection receipt binds the two report hashes, both source hashes, ten
per-life dependency manifests, and the three point-in-time exclusions.
Its inspectable canonical bytes are stored in
`research_notes/2026-09-11_parenting_terminal_union_selection_receipt.json`.
