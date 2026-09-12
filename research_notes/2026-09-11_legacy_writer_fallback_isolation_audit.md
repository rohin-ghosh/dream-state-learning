# Legacy writer fallback/isolation audit (2026-09-11 PDT)

## Decision

The live `NOT_ISOLATED` messages do **not** show that the trained adapters saw
targets from a different corpus item.  They show that the attempted custom
4-D-mask forward was not equivalent to two solo forwards on the deployed
Qwen/Transformers/bf16 path, so the trainer rejected that path before any
backward or optimizer step and trained with one encoded item per sequence.
The current runs may safely finish without restart.

The fallback is nevertheless not merely a speed loss.  With the live defaults
(`batch_size=1`, `grad_accum=1`) it changes one packed-sequence update into one
AdamW update per item.  That changes the number of optimizer steps, Adam
moments, and the weighting of short versus long items.  These are valid
**unpacked fallback recipe scouts**, not executions of the preregistered
packed-neighbourhood recipe.

## Fresh live and source check

Read-only snapshot at 2026-09-12 00:59 UTC:

- node 1 controllers: `R2_B_seed1`, `R2_B_seed5`, `R2_B_seed6`; the first was
  fitting C, the second C_tmem, and seed6 was in its final probe and completed
  during this audit;
- node 2 controllers: `R2_B_seed2`, `R2_B_seed3`, `R2_B_seed4`,
  `RP_B_seed400`, and `R4_B_seed601`; respectively probing A or fitting C, Bs,
  Bs, and C at the snapshot.

No process was launched, stopped, signalled, or modified.  The trainer,
runbook, probe-only script, and compiler bytes relevant here match between the
laptop and both nodes (`train_adapter_v3.py` SHA-256 `02f47008...55e169`,
`write_ab.sh` `f4a0ecce...e8acfc6`, `write_ab_probe_only.sh`
`52b194e2...1259c26`, compiler `d66d5bab...9833fc`).  Both nodes use torch
2.13.0+cu130, Transformers 5.5.3, PEFT 0.20.0, Qwen2.5-7B-Instruct and bf16.

I inspected all 27 completed warned manifests in those eight live chains.
Every one records `pack=true` in the requested config but actual mode
`fallback_one_item_per_sequence (NOT_ISOLATED)`, mean segments/sequence 1,
batch size 1, gradient accumulation 1, `steps == micro_batches ==
n_sequences`, zero target-token drops, and zero non-finite batches.  The
short-forward tolerance was 0.25.  Observed packed-versus-solo maximum-logit
differences were 1.27344 for A_v3, 1.125 for B-family cells, and 3.1875 for C;
negative-control differences were 22.30--46.38.  This is a repeatable backend
compatibility rejection, not an intermittent training failure.

## What the messages mean

`isolation_check` runs under `eval()` and `no_grad()`.  It compares each of two
48-token items alone under a normal 2-D mask with their concatenated logits
under the 4-D block mask and reset positions
(`train_adapter_v3.py:434-475`).  `NOT_ISOLATED` means either item exceeded the
tolerance.  Because even the *first* causally preceding segment differs, the
receipt does not localize the cause to attention from item B into item A; it
only establishes non-equivalence of the custom-mask path.  It is not evidence
that cross-item attention actually occurred.

On failure, before enabling checkpointing and before constructing the
optimizer, `mask_mode` becomes `2d` and `pack` becomes false
(`train_adapter_v3.py:577-610`).  `pack_by_group(..., false)` returns `[[e]]`
for every encoded item (`326-347`), and training uses those packs
(`596-640`).  Thus no two items occupy the same token sequence in an actual
training forward.  A B episode-window item can intentionally contain several
target spans from the **same episode/window** (`sleep_compile_v3.py:520-595`),
so later tokens can see earlier within-item child text.  That is corpus design,
not leakage introduced by the failed packer.  Local B items and C QA items
have one target unit per item.

The shell warning is a policy check, not a nonzero training return.  Its two
failure conditions are (a) any dropped target token, or (b) packing was
requested but the realized mode is not `block4d_by_group`
(`gpu/write_ab.sh:87-98`).  Only (b) fired in these receipts.  The default is
`WRITE_AB_STRICT=0`, so `warn_or_fail` reports and continues; strict mode would
exit after the already-completed fit (`67-72`).

## Scientific admissibility

Valid diagnostics/results:

- the isolation receipts are evidence that this exact 4-D path failed its
  preflight equivalence criterion and was not used for optimization;
- completed `train_manifest.json`, `DONE`, timing, token, truncation,
  non-finite, and realized-step fields describe the actual unpacked fit;
- compile manifests describe the rendered corpus and intended exposure counts,
  subject to the separately documented provenance/rendering caveats;
- raw completed probe JSONs and replicate ledgers, paired to the same-life OFF
  cell with the same panel/generation settings, remain descriptive behavioural
  measurements of the **fallback recipe**.  They may support a scout/stop
  decision about that realized recipe.

Inadmissible claims:

- that block-diagonal packed attention was validated, or that these runs tested
  the intended packed-neighbourhood implementation/effect;
- that `NOT_ISOLATED` proves cross-example target leakage in the actual fit;
- that fallback changed only throughput while preserving optimizer geometry,
  item weighting, or the preregistered W1/B estimand;
- causal attribution of an A/B/C score difference to packing, locality,
  masking, or another single ingredient of these bundled recipes;
- use of an in-progress cell without its completed manifest/DONE receipt.

One independent reporting limitation remains: both nodes have legacy
`write_ab_report.py` SHA-256 `a36bd604...c24853`, while the repaired local file
is `c1d07efb...80f36c`.  Therefore node-generated table/summary **raw means and
mean deltas** can be traced back to their probe JSONs, but legacy-A token-pass
fields and collapsed-replicate flags are non-authoritative until recomputed
from the raw receipts with the repaired reporter.  This does not affect the
fallback safety conclusion.

## Operational disposition

Let the current chains finish.  Restarting with unchanged bytes/backend would
repeat the same conservative fallback and would not recover packed evidence.
If a future claim requires packed-neighbourhood training, run a separately
ratified fresh comparison only after the actual backend passes positive and
negative isolation controls; preserve these outputs as explicitly labelled
unpacked-fallback scouts.  No current adapter needs to be discarded on grounds
of cross-item attention leakage.
