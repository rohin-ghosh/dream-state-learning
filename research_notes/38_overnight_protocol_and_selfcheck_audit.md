# 38 — Overnight protocol + verifier-free replication audit

Date: 2026-08-26. These are live H100 results inspected directly from the
artifacts/logs. D3 is omitted because v0 D3 is now invalid.

## 1. The substrate×read-protocol isolation is complete

All rows use the same 65-line C3e self-checked dream corpus (1,086 tokenizer
tokens) on aligned seed 0.

| Memory substrate / read protocol | D0 | D1 | D2 |
|---|---:|---:|---:|
| dump all memories in prompt, direct generation | .833 | .167 | .083 |
| entity-keyed retrieval (~28 lines), direct generation | 1.000 | .083 | .083 |
| context, model resolves atomic reads, then composes | 1.000 | .417 | .333 |
| **context + candidate-recognition reads + clean compose** | .750 | **.500** | **.500** |
| **LoRA + candidate-recognition reads + clean compose** | .750 | **.500** | **.500** |

The matched final two rows are decisive at this scale: the weights themselves
do not create the gain. The atomic query plan + finite candidate recognition +
clean composer do. Naive context and naive RAG fail because the model does not
reliably select and resolve the necessary leaves from even 65 organized lines.

The honest current statement is:

> Dreaming creates useful structural memories, and a structured recognition-
> read interface makes them usable. At 1,086 memory tokens, context and LoRA
> are accuracy-equivalent under that interface. LoRA remains a persistence and
> beyond-window scaling hypothesis, not a demonstrated small-memory advantage.

Consequences for the paper:

- Never compare prompt-direct against LoRA-recognition as a substrate result.
- Report prompt tokens, candidate queries, and read-plan construction.
- Treat recognition reads as part of the memory *system*, not as evidence that
  weights alone reason.
- The next substrate test must sweep memory horizon past the prompt budget and
  include context+recognition/RAG+recognition, not a weak direct-generation RAG.

## 2. Verifier-free aligned replication is positive but not robust

C3e uses the mechanical episodic cell layer, model proposals, epistemic
self-check, provisional connector re-check, LoRA write, recognition reads, and
clean composition. The exact verifier only labels proposals offline.

| seed | raw precision | supported precision (all kinds) | accepted equivs true/false | gauge | D1 | D2 |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | .526 | .833 | 6 / 2 | .867 | .500 | .500 |
| 1 | .507 | .911 | 9 / 2 | .632 | .417 | .500 |
| 2 | .480 | .804 | 7 / 4 | .667 | .583 | .250 |

The D2 mean is .417 versus a .167 floor, but the seed spread (.25-.50) is too
large for a headline. Overall self-check precision is misleading because it is
dominated by easy cell claims. The high-impact `ANIMAL_EQUIV` claims are much
less precise, and one false equivalence can merge otherwise separate latent
classes. False memories have unequal blast radii.

The equivalence counts above also include reversed duplicates such as
`horse↔raven` and `raven↔horse`. After canonical deduplication, structural
precision is lower still. Reverse surface form is required later for LoRA
exposure because of the reversal curse, but it is one assertion—not independent
support—at dream/claim level.

## 3. The implemented self-check is not yet Rohin's intended self-check

The current C3e initial check sends every proposal with:

```text
structure = (none yet)
```

`structure_view()` is used only for new drift claims. Therefore the main batch
does **not** check each dream against the current accepted LTM/structure, despite
the documentation describing an evidence×structure check. The connector pass
retrieves a third entity, but the prompt asserts transitivity without first
establishing both edges; this is where false structural promotions can enter.

This matters because the desired architecture was explicit: self-check should
hold the dreamed memory, lived evidence, and existing checked structure at the
same time; agreement supports, disagreement triggers rethinking/revision, and
insufficient evidence remains provisional.

## 4. Minimum repair before more scale

1. **Canonicalize at claim level.** Deduplicate symmetric equivalences before
   scoring or support accumulation. Emit both QA directions only at write time.
2. **Report per-kind metrics.** Precision/recall and false-memory count for
   cells, equivalences, operators, and parent sets separately. Overall precision
   is not an adequate safety metric.
3. **Risk-tier consolidation.** A structural edge/operator/parent claim should
   require more independent support than a local cell because its downstream
   blast radius is larger. Repetition or reverse wording is not independence.
4. **Actually use existing memory.** Check in waves: evidence-supported core ->
   provisional structural claims against core -> add only surviving claims ->
   re-dream unresolved entities. Exclude the claim under test from its own
   support view.
5. **Predictive self-check.** Ask what additional witnessed cells the claim
   predicts and compare at least two independent consequences. If none are
   observable, retain PROVISIONAL rather than forcing a binary verdict.
6. **Track contamination blast radius.** Alongside claim precision, report the
   number of entities/components touched by any false accepted structural edge.
7. **Complete the matched ladder across seeds.** The current replication runs
   self-check only. Run no-gate and perfect-gate on the same seeds/corpora;
   separate self-check-without-drift from self-check+drift.

This repair is not a new exact verifier. It is a general epistemic policy over
the model's own evidence and memories. The offline solver continues to score
only after the batch commits.

## 5. Updated immediate order

1. Finish the currently running neutral/conflicting C3e cells; preserve them as
   diagnosis, not a final matrix.
2. Merge/audit Semantic World v0.2 and run its clean-model gameability gate.
3. Repair claim canonicalization and structure-aware self-check.
4. Rerun the full four-arm ladder on aligned seeds 0-2, with per-kind and
   contamination metrics.
5. Only then run v0.2 higher-order dreaming, skins, and scale.
6. Keep Action World parked until the memory/depth mechanism survives this
   ladder.

