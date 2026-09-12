# Conditional W1 cumulative-replay readiness audit

Date: 2026-09-12 UTC
Scope: fresh read-only audit of decisive-path section 3, the current V10R1
writer, SLEEP/compiler paths, memory-dose artifacts, and the terminal W0
contract. No builder-owned source or remote job was changed.

## Verdict

**REWORK; W1 is not execution-eligible.** The only W0 attempt is the sealed
`NONREPORTABLE_ABORT` at optimizer step 0. It produced no adapter, raw
evaluation record, scientific label, or `MULTIKEY_BINDING_PASS`. Installing
the missing node dependency removes an operational cause; it does not turn
that terminal root into a pass. W1 must remain unlaunched unless a fresh W0
root finishes, seals, replays, and returns exactly `MULTIKEY_BINDING_PASS`.

No W1 implementation exists. The smallest valid follow-on is nevertheless
clear and can consume a future successful W0 **without changing or rerunning
its scientific recipe**: reuse its four immutable OLD adapters and OLD/OFF
records, add four equal-dose NEW-only fits, then—only after the single-bank
and orthogonality gates pass—add four clean-base, deterministically
interleaved OLD+NEW fits. That is eight new fits, not twelve; W0 supplies the
four OLD single-bank references.

A pass licenses only **replay-supported two-bank coexistence/reconstruction
without the detected action-habit spill**. It is not sequential-parameter or
unrehearsed retention because OLD rows are replayed and every cumulative
adapter starts from the clean base.

## Exact W0 activation contract

The current W0 implementation is still the executed frozen science bytes:

- module `6d23b4470ae8cb3a5e7b6a0fc00678b9c5e0aa071f5e4b825b3ad54ed13c75b0`;
- tests `9dbb4cf6ee1472e19b2fe64a181ede865aa0d90857c6a690ad77ccf6df5287b0`;
- launcher `3994bf389e63ac790b3eb500c74a974ed57b88fd8fd02d494ae6fecc0ab33665`.

It binds two roots, complementary W+/W- maps, four clean-base rank-8 fits,
128 rows and 256 steps per fit, exact target masking and candidate scoring,
and the oracle/optimization/binding/interface/spill conjunction described by
V9+V10+V10R1. A W1 manifest must name the successful W0 seal, replayed report,
model/tokenizer/environment identity, all four adapter-tree hashes, material
hash, request hash, seeds, and source hashes. It must mount/read W0 artifacts
without writing into or copying over the W0 run root.

The 07:36 W0 root cannot be that parent: it has `scientific_label=null`, zero
completed fits and `no_retry=true`. A new W0 attempt must also bind the repaired
native-build/Triton prerequisite. W1 activation is the conjunction:

1. complete untampered W0 real-execution seal and successful read-only replay;
2. exact scientific label `MULTIKEY_BINDING_PASS` across both roots/maps; and
3. four readable immutable OLD adapter trees plus complete OLD/OFF raw records.

Anything else—including a partial-root pass, CPU fixture, preparation seal,
infrastructure repair, or `OPTIMIZATION_INCONCLUSIVE`—is W1 **not run**.

For completeness, a fresh laptop run of the current 51-test suite yielded 39
passes, 2 failures and 10 errors because the executor rejects the symlinked
macOS temporary-directory ancestor before fixture creation. The exact bytes
passed 51/51 on Linux during the sealed W0 preparation. This is a portability
caveat for laptop preparation, not scientific W0 evidence and not permission
to bypass same-node CPU preparation.

## Smallest executable W1

For each root `r in {0,1}` and map `m in {W+,W-}` use three states:

| state | source | rows / steps | initialization |
|---|---|---:|---|
| `OLD_SINGLE[r,m]` | successful W0 artifact | 128 / 256 | clean base (already done) |
| `NEW_SINGLE[r,m]` | new identity-disjoint bank | 128 / 256 | clean base |
| `CUM[r,m]` | OLD+NEW replay union | 256 / 512 | clean base |

All states retain the W0 rank, alpha, dropout, target modules, `3e-5` AdamW
recipe, batch size 1, target mask, exact `ACT: a0\n`/`ACT: a1\n`+EOS bytes,
two logical epochs, tokenizer rules, decoding/scoring rules and parser. Each
bank therefore receives exactly the same 128 rows twice in its single and
cumulative condition. The larger cumulative update count is the necessary
cost of holding per-bank exposure fixed.

Within a root, OLD, NEW and CUM and both maps use the same W0 optimizer seed;
the other root uses its different predeclared seed. All new fits run on the
same node/model/tokenizer/software identity as the successful W0. Record
`training_run_replication=false`, `root_seed_confounded=true`; the four maps
are not independent units. There is one attempt and no rescue/refit-to-pass.

### NEW bank and order

Keep the exact W0 train/held template literals, coordinate multiplicities and
coordinate orders. Change only the selected identifiers and orientations, so
surface/dose differences cannot explain OLD versus NEW. A fully prospective
domain-separated candidate, selected before any W0 outcome existed, is:

- identifier `slot` value = `"u" + digest(["mwg-w1-new-identifier-v1",
  20260912, root, slot])[:12]`;
- root-0 identifiers: `u5047d7871847`, `ufae601274fcd`, `ub1afb48d326f`,
  `uae827ecb612e`, `u16ae8aec1304`, `u2149f4ad5050`, `ub0ff5d6672ca`,
  `ud80e0ec51ed4`;
- root-1 identifiers: `ud1cd6be5d468`, `ufb8c51aa6de0`, `ue8506f32b767`,
  `ub598ca58155c`, `ucb18bd09461d`, `ubcd5da0049aa`, `ue5c639f23e05`,
  `u682af07d7ce3`;
- NEW orientations root 0 = `[0,1,0,1,0,0,1,1]`, root 1 =
  `[0,1,0,1,1,0,0,1]`.

The orientations are the first SHA-256 nibble-parity vectors under
`["mwg-w1-new-orientation-v1",20260912,root,counter]` with exactly two ones
per four-slot stratum and excluding every OLD orientation or complement
(accepted counters 5 and 1; digests begin `41cd065b...` and `a74f5e63...`).
CPU recomputation confirms all 16 selected NEW IDs and their 16 one-character
neighbours are unique and disjoint from all OLD selected IDs/neighbours.
These values are a prospective audit candidate, not an executed input or a
substitute for builder binding/review; changing them after reading behavior
would invalidate the prospective comparison.

Regenerate W+/W- targets from the NEW orientation using the W0 XOR law. The
CPU geometry gate must be exact on each bank and the pooled union. In addition
to every V10R1 shortcut check, pooled best BA must be exactly 1/2 for `bank`,
`bank x mode`, `bank x stratum`, `bank x stratum x mode`, `bank x template`,
and `bank x template x mode`. Tool-only remains chance because each tool
reverses across mode. The intended full tool-by-mode key is not a shortcut
control.

For CUM logical epoch 0 use `OLD[0], NEW[0], ..., OLD[127], NEW[127]`; for
logical epoch 1 reverse within every pair: `NEW[0], OLD[0], ..., NEW[127],
OLD[127]`. This is deterministic, gives each bank both positions, and prevents
the current SLEEP path's old-then-new block order. Bind all 512 ordered
occurrences and their encodings.

## Stages and exact gates

1. **NEW preflight:** seal NEW material, geometry, real-tokenizer encodings,
   immutable NEW OFF records and explicit-map OFF oracle records. Oracle BA
   must be at least .90 for both maps/roots or `ASSAY_INVALID`; do not fit.
2. **Four NEW_SINGLE fits and reads:** NEW must pass the full absolute W0
   optimization, binding, interface and spill gates. Evaluate every
   OLD_SINGLE on NEW and both banks of the other root; evaluate every
   NEW_SINGLE on OLD and both banks of the other root. A failed single-bank
   gate gets its exact NEW optimization/interface/spill/binding subtype. Any
   otherwise eligible non-owner-bank change is `BANK_ORTHOGONALITY_FAIL`.
   Stop before CUM.
3. **Four CUM fits and reads:** only after stage 2 passes. Evaluate each CUM
   adapter on OLD and NEW in its root, both banks of the other root, and both
   banks' applicable missing/unsupported/neighbour plus unrelated-interface
   panels.

For bank `B`, root-map adapter `a`, key `k`, and its four held templates, let
`g_X(B,a,k)` be the median of `log q_target(X) - log q_target(OFF_B)`, where
`X` is its single-bank or CUM adapter. Define
`KMG_X(B,a) = mean_k g_X(B,a,k)`. Use the same immutable OFF record in both
terms and decide at full precision by cross multiplication. For **each** OLD
and NEW root-map cell, CUM must satisfy:

- all 16 `g_CUM >= .50` and the complete absolute V10R1 bank gate;
- `5*KMG_CUM >= 4*KMG_SINGLE`;
- `5*g_CUM(k) >= 4*g_SINGLE(k)` for at least 12/16 keys and 6/8 in each
  stratum; and
- `5*(BA_CUM-BA_OFF) >= 4*(BA_SINGLE-BA_OFF)` plus the absolute BA,
  stratum, directional-margin, own-minus-opposite and validity gates.

For every bank on which an adapter is supposed to be neutral, require per key

`mean_template |q0(adapter)-q0(OFF)| <= .05`

and

`|legal_ACT_rate(adapter)-legal_ACT_rate(OFF)| <= .05`.

Do not replace either with a pooled bank mean. Apply the section-3 **absolute**
legal-ACT difference even though the inherited W0 spill test is one-sided in
the current implementation. Retain the fixed missing-mode, unsupported-mode,
neighbour and unrelated-native panels and exact interface outputs. Thus a
global `a0`/`a1` habit cannot earn carriage merely by improving target-bank
means: it fails opposite-map behavior, per-key non-owner-bank TV/legal-ACT,
or explicit spill/interface gates.

After integrity and oracle precedence, use the decisive-path cause labels:
NEW exact failure subtype; `BANK_ORTHOGONALITY_FAIL`;
`CUMULATIVE_OPTIMIZATION_INCONCLUSIVE`; `CUMULATIVE_WRITER_UNUSABLE` for
cumulative interface/spill/wrong-root damage; then
`OLD_AND_NEW_CARRIAGE_FAIL`, `OLD_CARRIAGE_FAIL`, or `NEW_CARRIAGE_FAIL`
according to the absolute/relative bank conjunctions; otherwise
`TWO_BANK_CUMULATIVE_REPLAY_PASS`. Emit every primitive boolean and never tune,
retry, select a map/root, or alter a threshold from the observed result.

## What exists and what can safely be prepared now

- `multikey_writer_gateway_simple.py` contains reusable W0 material,
  tokenizer, worker, receipt and reducer primitives, but it hard-codes four
  128-row/256-step fits, four adapter identities and 1,504 W0 requests. It has
  no NEW/CUM material, interleaver, KMG-relative reducer, orthogonality matrix
  or W1 labels. A dedicated W1 executor can read W0; the W0 module/run must not
  be edited in place.
- `sleep_compile.py` performs `dedup(prior_corpus + new_texts)` and the trainer
  consumes that list in order. Despite its comment, this is concatenated
  replay, not the required interleave. The life path also uses a different
  corpus/recipe and cannot serve as W1 evidence.
- `memory_dose.py` has deterministic banks, hashes and an optional
  content-ordering mechanism, but its car-colour candidates, large padded
  corpora, dose/interference metrics and historical outcomes are not the W1
  assay. Preserved bank-0 artifacts show broad frame spill and cannot be
  relabelled as OLD/NEW or used to choose W1 identities/orientations.

Safe CPU work now is limited to a separate W1 material generator, the exact
prospective bank above, paired interleave projection, pooled-shortcut proofs,
request matrix, arithmetic-only reducer, label/precedence goldens, tamper
tests, and a non-scientific CPU fixture. It may freeze hashes and declare
`W0_PARENT_PENDING`; it must not claim execution readiness. The final real
tokenizer/manifest preparation must occur after W0 passes so it can bind the
actual successful W0 seal and same-node identity. Do not model-load, profile,
fit, inspect W0 subcell outcomes to redesign NEW, reuse memory-dose subjects,
or launch any W1 stage now.

## Claim boundary

The exact evidence above distinguishes target-specific, replay-supported
OLD+NEW coexistence from a broad action habit only over the enumerated banks,
opposite maps, wrong roots and spill/interface panels. It still cannot show
that parameters retained OLD while learning NEW without rehearsal. That
stronger claim requires a separate sequential adapter-update experiment with
OLD rows withheld during NEW learning and a prospectively matched update-heat
control; it must not be inferred from W1.
