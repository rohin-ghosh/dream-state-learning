# Parenting terminal-union audit — 2026-09-11

Status: terminal, read-only simple-hygiene audit of completed R3/R4 histories.
This is not a randomized parenting experiment, a C11 result, or evidence of
population efficacy. The full C11 guard remains deferred to the final
paper-grade run.

## Eligible terminal cut

The refreshed point-in-time terminal union contains six R4 parented lives and
six R3 controls:

- node 1: R4 seeds 604 and 606; R3 seeds 500, 501, and 502;
- node 2: R4 seeds 600, 601, 602, and 603; R3 seeds 503, 504, and 505.

Every included life has `LIFE_DONE`, 128 wake receipts ending at episode
1,024, exactly 1,024 reconstructed episode instances, and complete pre/direct,
one-sleep, and four-sleep analysis windows. R4 event ordinals are 192, 224,
256, 160, 160, and 224 for seeds 600, 601, 602, 603, 604, and 606
respectively. Every indexed event is a delivered v3 brief with empty leak hits
and matching stored text and metadata. Five lives used the 14B parent; seed
604 used the 32B parent, so parent-model identity remains a disclosed
historical confound.

R4 seed 605 was the only otherwise relevant life excluded at the refresh
snapshot: it lacked `LIFE_DONE` and had reached wake 864. It may enter a later,
separately identified refresh; it is not silently pooled here.

## Descriptive changes around the indexed event

All values are equal-weighted within-life changes from each life's preceding
32 episodes.

| measure | direct 32 | one sleep | four sleeps |
|---|---:|---:|---:|
| R4 first-note overlap with >=4 lesson tokens | +13.021 pp | +12.500 pp | +13.542 pp |
| R4 mean lesson-token fraction | +2.737 pp | +2.547 pp | +2.656 pp |
| R4 change-intent language | +7.812 pp | +4.167 pp | +6.771 pp |
| R4 changed predicted/executed action | +2.604 pp | +3.646 pp | +0.521 pp |
| R3 changed predicted/executed action | -1.042 pp | -4.688 pp | -5.729 pp |
| R4 mean best task score | +0.046 pp | +0.384 pp | -0.371 pp |
| R3 mean best task score | +0.311 pp | +0.497 pp | +0.834 pp |

Lexical uptake is the clearest movement, but the pre-event overlap rate was
already 67.188% and every brief explicitly demanded first-note restatement. It
rose to 80.208%, 79.688%, and 80.729%. This is prompted accommodation, not
proof of internalization.

Only authoritative ledger `kind=act` rows count as actions. Realized-change
episodes moved from 5/192 before the event to 10/192 directly, 12/192 after
one sleep, and 6/192 after four sleeps. Positive within-life changes occurred
in only 3/6, 2/6, and 2/6 lives. The corresponding R3 counts were 11/192
before, then 9/192, 2/192, and 0/192. This coarse signature does not establish
that an action implemented the parent's conditional lesson.

The four-sleep window is not a clean withdrawal test. The exact indexed brief
covered 192/192 direct episodes, 160/192 one-sleep episodes, and 32/192
four-sleep episodes; later valid briefs entered one one-sleep window and three
four-sleep windows. The four-sleep lexical elevation therefore cannot be
called persistence of the indexed lesson after parent removal.

There is no durable task benefit in this cut. Parented score change is
slightly positive directly and after one sleep, then negative after four;
controls improve more in every window. The descriptive parent-minus-control
differences are -0.265, -0.113, and -1.205 percentage points. These are not
causal estimates: assignment was not randomized, control events were
threshold-triggered and earlier, parent models differed for one life, and the
writer selected on the repeated report panel.

## Parent effect is confounded with a pre-existing writer effect

At an event-boundary probe, weights are classified as pre-parent because the
write was compiled from the ledger before the first brief-conditioned wake.

Across 17 pre-parent or boundary ON/OFF checkpoint pairs, adapter ON beat OFF
on report score in 17/17 pairs. Mean score difference was +0.020675 (range
+0.000632 to +0.061332). Yet the coarse realized-change signature was already
17.647 percentage points lower ON-minus-OFF on average: 13/17 negative, 3/17
positive, and 1/17 zero.

Across 79 post-event pairs, score difference was positive in 70/79, with mean
+0.021609 (range -0.061759 to +0.069020). Realized-change was lower in 77/79
and zero in 2/79; none was positive, with mean -0.302215. Parent text was
absent from all 96 stored probe prompts.

The 96 checkpoint pairs above reuse the same eight report programs across
time. They are repeated measures within six histories, not 96 independent
cases.

The strongest bounded conclusion is therefore:

> In six terminal parented histories, valid parent briefs were followed by
> greater lesson-token overlap and coincided with a small, heterogeneous
> increase in coarse changed-action episodes, but no
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
  `a984c668fa2b61b801371334ec2780c170f231c4d7da4aee66360a4577ce07a8`
- node-2 terminal report:
  `7f616ab4700067d7e7929c11208cbaf222f671685514ac1082e8d233ec79e3d2`
- combined selection receipt:
  `d6bbc6361490331a648ff41d3ce6bd3220d6c11df5e7cbfaa91ccbfd3bea1bd2`

The selection receipt binds the two report hashes, both source hashes, twelve
per-life dependency manifests, and the one point-in-time exclusion.
Its inspectable canonical bytes are stored in
`research_notes/2026-09-11_parenting_terminal_union_selection_receipt.json`.
