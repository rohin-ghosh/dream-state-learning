# Contrastive-perception Level-1 screen: independent terminal reduction

**Date:** 2026-09-13 UTC  
**Role:** independent raw-artifact reducer  
**Disposition:** operationally reportable; registered exploratory screen **FAIL**  
**Scope:** one authored Level-1 fixture, one learner seed and one fit per arm;
not keyed memory, child-authored SLEEP, parenting, or self-learning evidence

## Bottom line

The training worked, but almost all of the apparent strict-score gain over the
frozen model was **formatting**. The frozen model usually returned the correct
record inside a Markdown JSON fence; both LoRAs learned to emit bare JSON. Once
that fence is permissively removed, held record accuracy is **OFF 23/24,
PLAIN 17/24, CONTRASTIVE 19/24**. Thus neither trained arm improved content over
OFF, and both made it worse on this fixture.

CONTRASTIVE was two held items better than PLAIN, but that difference was not
wrapper-general: it was +3 on `D1` and -1 on the semantically duplicated `D2`.
Moreover, a preregistered shortcut that copies the final action and prediction
but **negates the earlier observation**, without reading the final outcome,
constructs the exact target on **24/24** held renderings. Even a perfect result
could not identify selected-outcome use. The result therefore does not support
conditional/keyed memory or contrastive perception as a general mechanism.

## Custody and independent replay

Before opening any response, fit, loss, score, or adapter content, I used
read-only access to the frozen root
`/localhome/local-rohing/astra_diagnostics/contrastive_perception_20260913_attempt1`
and established:

- no `python*` process whose command named `contrastive_perception` remained;
- exactly **405** regular files;
- whole-root C-order SHA-256
  `c0419145b04415457e3a9f9311b02dabe003432d86afad4ad0ef6567f79feab8`,
  exactly matching the prior unscored custody memo.

I then copied the frozen root read-only to a temporary local directory and
recomputed the same 405-file hash there. All file hashes registered in
`capture_complete.json` matched. I independently joined each of the 144 raw
requests and responses to `material.json`, checked row IDs and input messages,
checked response prompt-token IDs against the request, and rescored from raw
text. All **144/144** responses ended with `finish_reason=stop`; none was
missing or truncated. I used the interpretation bounds frozen result-blind in
commit `d6de454a` (current rebased commit `23db416f`).

For record panels, strict credit means the entire stripped response parses
directly as one JSON object, has exactly the four required keys with exact
types, has no duplicate key, and all four values match the source-derived
target. The permissive diagnostic removes one complete outer Markdown JSON
fence and then applies the same schema and content checks. It does not extract
JSON from arbitrary prose or repair fields. `C-general` uses exact requested
text; stripping surrounding whitespace changes no result.

## Raw scores

| state | D1 strict | D2 strict | held strict | C-record strict | C-general strict |
|---|---:|---:|---:|---:|---:|
| OFF | 0/12 | 2/12 | 2/24 | 0/12 | 11/12 |
| PLAIN | 9/12 | 8/12 | 17/24 | 8/12 | 12/12 |
| CONTRASTIVE | 12/12 | 7/12 | 19/24 | 9/12 | 12/12 |

| state | D1 fence-stripped content | D2 fence-stripped content | held content | C-record content | C-general |
|---|---:|---:|---:|---:|---:|
| OFF | 12/12 | 11/12 | **23/24** | **11/12** | 11/12 |
| PLAIN | 9/12 | 8/12 | 17/24 | 8/12 | 12/12 |
| CONTRASTIVE | 12/12 | 7/12 | 19/24 | 9/12 | 12/12 |

The registered screen does not pass:

- CONTRASTIVE held: **19/24**, below the required 20;
- wrapper minima: `D1=12/12`, but `D2=7/12`, below the required 9;
- strict held advantage: +17 over OFF, but only **+2 over PLAIN**, below the
  required +4 over each control;
- OFF strict held was 2/24, below the ceiling limit of 21;
- CONTRASTIVE retained all 11 OFF-correct `C-general` items and gained the one
  OFF miss. OFF had zero strict `C-record` passes because of fences, so the
  registered strict record no-harm check is vacuous. On permissive content,
  CONTRASTIVE instead lost two OFF-correct `C-record` items.

## Schema and field decomposition

The table gives `try / observed / predicted / relation` correct among outputs
that pass the permissive exact-four-key schema. The final column is that shared
denominator.

| state | panel | correct fields | schema-valid |
|---|---|---:|---:|
| OFF | D1 | 12 / 12 / 12 / 12 | 12 |
| OFF | D2 | 12 / 12 / 11 / 11 | 12 |
| OFF | C-record | 12 / 12 / 11 / 11 | 12 |
| PLAIN | D1 | 12 / 12 / 9 / 9 | 12 |
| PLAIN | D2 | 9 / 10 / 8 / 8 | 10 |
| PLAIN | C-record | 10 / 10 / 8 / 8 | 11 |
| CONTRASTIVE | D1 | 12 / 12 / 12 / 12 | 12 |
| CONTRASTIVE | D2 | 8 / 9 / 8 / 8 | 9 |
| CONTRASTIVE | C-record | 11 / 11 / 10 / 10 | 12 |

Strict paired wins-losses (`left-only correct : right-only correct`) were:

| comparison | D1 | D2 | C-record | C-general | held total |
|---|---:|---:|---:|---:|---:|
| CONTRASTIVE vs OFF | 12:0 | 5:0 | 9:0 | 1:0 | 17:0 |
| PLAIN vs OFF | 9:0 | 6:0 | 8:0 | 1:0 | 15:0 |
| CONTRASTIVE vs PLAIN | 3:0 | 0:1 | 2:1 | 0:0 | **3:1** |

Those strict comparisons against OFF are dominated by fences. On the subset
where both outputs have a valid permissive record schema, joint-content
wins-losses become:

| comparison | D1 mutually valid | D2 mutually valid | C-record mutually valid |
|---|---:|---:|---:|
| CONTRASTIVE vs OFF | 0:0 of 12 | 1:2 of 9 | 0:2 of 12 |
| PLAIN vs OFF | 0:3 of 12 | 1:2 of 10 | 0:2 of 11 |
| CONTRASTIVE vs PLAIN | 3:0 of 12 | 0:1 of 9 | 1:1 of 11 |

The field transitions on those same mutually valid denominators locate the
small contrastive-versus-plain difference:

- On `D1`, action and observation tied 12/12; CONTRASTIVE gained three
  `predicted` fields and the corresponding three `relation` fields, with no
  losses.
- On `D2`, observations tied on all nine mutually valid rows. For prediction
  and relation, both states were correct on eight and wrong on one; neither
  gained. Actions had one gain and one loss. Jointly CONTRASTIVE lost one.
- On `C-record`, CONTRASTIVE versus PLAIN had two gains and one loss on both
  prediction and relation; action and observation had no transitions. Jointly
  it was one gain and one loss.
- Against OFF, CONTRASTIVE had no content transition on `D1`; on `D2` it had
  one prediction/relation gain and one loss plus one action loss; on
  `C-record` it lost one item on every field and another item's prediction and
  relation. There is no content-level no-harm result.

## Failure modes

- **OFF:** 34/36 record responses were semantically parseable only after
  removing a Markdown fence. The remaining two were bare JSON. After removing
  fences, 34/36 records were exactly correct; the two content errors were a
  prediction/relation pair in `D2` and another in `C-record`.
- **PLAIN:** no fences. Three malformed records repeated the `observed` key and
  omitted `try` (two `D2`, one `C-record`). Among the 33 schema-valid records,
  eight had wrong content.
- **CONTRASTIVE:** no fences. Three malformed `D2` records repeated
  `observed` and omitted `try`. Among the 33 schema-valid records, five had
  wrong content.
- **C-general:** PLAIN and CONTRASTIVE were exact 12/12. OFF was 11/12; on the
  sole miss it returned `794` instead of the target `804`. This single gain is
  not evidence of broad no-harm or arithmetic improvement.

There was no arbitrary prose, generation truncation, or missing response. The
dominant OFF failure is therefore a narrow interface habit, while the trained
states add both malformed duplicate-key objects and substantive field errors.

## Fit and dose integrity

Both fits used the same 12 row IDs, assistant target strings, target-token IDs,
epoch order, seed, and optimizer recipe. Corpus and adapter hashes matched
their native manifests and fit receipts. Each was a fresh all-layer attention
plus MLP rank-8 LoRA (alpha 16, dropout .05; 20,185,088 trainable parameters),
learning rate `1e-4`, batch 4, four epochs, **12 optimizer updates**, and **48
presentations**. Each epoch contained 372 target-plus-assistant-end tokens, so
both saw 1,488 supervised tokens. No item or token was truncated and there
were zero nonfinite batches.

| fit | context + target tokens/epoch | train tokens seen | mean loss by epoch | final loss |
|---|---:|---:|---|---:|
| PLAIN | 4,434 + 372 = 4,806 | 19,224 | 1.05623, 0.28048, 0.00171, 0.00390 | 0.002928 |
| CONTRASTIVE | 4,542 + 372 = 4,914 | 19,656 | 1.07241, 0.30286, 0.00106, 0.00753 | 0.005047 |

The treatment therefore was not exactly compute matched: CONTRASTIVE saw 108
extra masked context tokens per epoch, 432 over the fit (+2.25% total native
tokens). Both fits drove supervised loss nearly to zero, so failure cannot be
described as the writer never fitting the authored targets. The last-epoch
mean loss rebounded slightly in both arms; no nonfinite or truncation event
explains the readout.

## Negate-earlier shortcut replay

For every held row I constructed a response without inspecting the selected
final outcome:

1. copy the final event's visible `ACT: TRY` triple;
2. copy its visible `PREDICT: T/F`, or use `null` when absent;
3. set `observed` to the Boolean negation of the earlier event's outcome;
4. derive `relation` from prediction and that constructed observation.

This matched all four exact target fields on **12/12 D1 and 12/12 D2**. The
shortcut is thus a perfect 24/24 solver. It is aligned specifically with the
CONTRASTIVE training instruction to notice opposite observations. The observed
`D1=12/12` cannot tell whether the adapter selected the final outcome or merely
learned this fixture-specific polarity relation.

## Scientific disposition

This is a cleanly executed **negative curriculum screen**. The authored
training strongly learned an interface convention (bare JSON), while its
semantic execution was below the already-near-ceiling frozen model after fair
fence removal. Explicit contrastive presentation recovered two held records
relative to PLAIN overall, but that effect changed sign across wrappers and is
not evidence of wrapper-general perception. The perfect polarity shortcut
prevents attribution to selected-outcome reading in every case.

Permitted statement: at this one seed and dose, the exact authored contrastive
bundle improved strict and content execution over the exact plain authored
bundle by 2/24 overall: +3 in `D1`, offset by -1 in `D2`. Both bundles trained
away Markdown fences and both underperformed OFF on fence-stripped record
content.

Forbidden statements: that contrastive perception, keyed storage, child
learning, child-authored SLEEP, parenting, connected knowledge, or a general
attention mechanism was demonstrated or falsified.

The correct next screen must break the negate-earlier correlation, vary event
relations independently, withhold the target value so a keyed read is required,
use fresh source families and learner seeds, and preserve the same strict
format-versus-content decomposition.
