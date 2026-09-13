# Q0-FULLDOSE-v2 frozen implementation: independent static audit

**Date:** 2026-09-13 UTC
**Scope:** read-only scientific/code audit of authoritative commit `aeea04a7`
and the later pre-launch sidecar registration at `5695d65a`. I did not edit
`organism_v6/`, `gpu/`, or `tests/`; run a test, model, or tokenizer; inspect a
live root; or use a GPU.

## Verdict

The claim-bearing computation in frozen source
`gpu/astra_pairwise_q0_fulldose.py`, SHA-256
`f63c77f9c371433442a204d6bd7bb10e3769a3bb709ae1d728648d765ee8ceca`,
is faithful to the selected Q0-FULLDOSE-v2 endpoint experiment. I found no
target leakage, held/control training leakage, target-dependent scheduling,
canary efficacy veto, checkpoint selection, denominator substitution, or gate
arithmetic error that would by itself invalidate an honestly produced endpoint.
The matching test source is
`ea5ea21c8b508e8621a673b61fa324c4303b3ec25160d666a7431dfb7459ea72`.

There is one real terminal-custody weakness: the durable-finalization witness
is outside the seal and is trusted during claim promotion. This does not show
that any bytes have changed, and it does not alter endpoint arithmetic, but an
endpoint should not be treated as hash-closed solely from this module's
`SEAL.json`. An external immutable capsule/receipt that hashes the finalization
markers is required, or the closure should be repaired prospectively before a
claim is accepted.

## Protocol and isolation checks

- `ALLOCATIONS` fixes `R0/R1/R2` to identifier seeds `501/502/503` and learner
  seeds `1/2/3` (`:87-88`). The worker derives its actual seed from the bound
  allocation (`:1780-1784`); both arm processes reconstruct equal initial
  tensors, RNG and zero-step logits (`:915-932`), and the reducer compares all
  per-row pre-forward RNG receipts between arms (`:1368-1371`). Root and seed
  vary together and are correctly described as confounded, not independent
  seed replication.
- Alpha-renaming consumes only the pinned old material, renames trained and
  wrong-root identifiers separately, proves within/cross-allocation
  disjointness, and retains source-row hashes (`:190-222`). Prompts receive no
  arm, target, replica or learner-seed field. The pinned native preparations
  contain 296 rows/root with exact/held/spill/wrong-root/copy counts
  `128/64/32/64/8`, 296 unique rendered-prefix hashes, branch IDs
  `10536/21404`, and no inspected metadata-name occurrence in model-visible
  prompt text. Only the 128 exact row IDs occur in `training_order`; every one
  appears four times.
- The schedule is target-free and has 32 quartets ordered
  `(orientation0,mode0)`, `(orientation0,mode1)`,
  `(orientation1,mode0)`, `(orientation1,mode1)`; each is 2/2 balanced under
  both complementary maps (`:326-349`). AUTH and DERANGED are separate
  cold-start adapters. OFF is a bare-base fresh load; held, locality,
  wrong-root and copy rows never enter a loss.
- Every admitted fit runs all 128 quartet updates, saves only fixed snapshots
  32/64/128, and preserves/replays the original raw update-one canary without
  branching on its pass flag (`:915-998`, `:1218-1233`). `next_fit` fixes AUTH
  then DERANGED independent of canary or endpoint values (`:1209-1215`). The
  lifecycle is exactly audit, OFF, AUTH fit/read32/read64/read128, DERANGED
  fit/read32/read64/read128; integrity failure stops, while an AUTH scientific
  miss does not cancel DERANGED (`:1236-1334`). No V/unary arm, retry, dose
  extension, or best-checkpoint route remains.
- Endpoint 128 alone reaches `primary_label`. Exact/held acquisition, class
  recall, validity, multiple-action, key coverage, per-class exact gain, copy,
  per-family q/M and identity locality, exact/held complementary double-correct
  counts, and wrong-root-opposite count reproduce the declared noncompensatory
  thresholds (`:1116-1192`, `:1337-1412`). Missing/extra readouts, short fits,
  bad snapshots/RNG/raw canaries, OFF-copy failure, and counter/release/deadline
  defects cannot become endpoint failures or passes. CPU fixture reports remain
  non-scientific; native promotion occurs only after the native reducer.
- Forward arithmetic is exact: one complete root has 256 updates, 1,024
  training-row forwards, 1,632 evaluation prefix reads, 888 generations and
  3,072 natural-prefix forwards. The decoder hook requires model calls equal
  natural-prefix forwards plus actual generated-token count (`:2121-2134`).

## Receipts and actual preparations

The archived Linux native receipt records 282 tests with zero failures,
errors, or skips and binds the exact 20-file source set plus separately
hash-pinned historical test support. `native_prepare` rejects any skip or
source/environment difference (`:1619-1631`). I did not rerun those tests.

All three archived prepared roots share campaign SHA-256
`1f29967875bb7e84fd479c25a1a54aed59405675c9bccc74305be8449d7884df`.
Their archived manifest/prepared hashes exactly match the preparation receipt:

| root | manifest | prepared |
|---|---|---|
| R0 | `b21fba8b93130a24d95164b87ec45448d4f20b28c0079dcb018479d707d3b01e` | `44cb464002a7e477e876d5bbd0ea57d7602bfedd2c334e1a0facc5dcbec222f0` |
| R1 | `509fd3ba6900e4bac6bcf071e187db5b98e3e81f1ce96561be0a8fb9480df2d3` | `1abdd31d538653916abd636a2683ed9743d628a635bb7a1ea2612f8ecb0ae615` |
| R2 | `eafe1e55b61e34bc48754cf94aebd4f04b7d22631fda2ab0da0933ae86428b4d` | `64419ef1fe6629c017b6465761d78daf320edc18dbe6bbcade3911b8ef75223c` |

The node-specific public binding is hash-pinned as `a7481b25...`, retains the
official 14-file identity map, binds node/environment/resolved model and
tokenizer paths, rehashes local inventories, and explicitly denies clean
lineage (`:149-178`, `:1542-1570`). Execution rechecks prepared/source/model
bindings and requires the reserved A40 UUID, deterministic environment,
fresh root, fresh process/load per stage, exact adapter snapshot, owned-group
cleanup and GPU release.

## Finding: finalization is not bidirectionally hash-closed

`_native_execute` inventories and seals the root before writing
`FINALIZED.json` (`:2010-2017`). `native_replay` then deliberately excludes
`FINALIZED.json` and `FINALIZATION_ABORT.json` from the sealed-inventory
comparison (`:2148-2153`), and trusts their unsealed times to retain or revoke
`scientific_claim` (`:2167-2186`). `FINALIZED.json` points backward to the
sealed bytes, but no sealed byte points forward to the finalization witness.

Consequently, after closure, rewriting `FINALIZED.json` with earlier values
together with removing `FINALIZATION_ABORT.json` would not be detected by
`SEAL.json` and can turn a late terminal into an eligible one; changing a
timely witness to late values can revoke eligibility. The included late-write
tests establish
correct behavior for markers produced by the same uninterrupted process; they
do not close this post-terminal mutation channel. Treat this as a custody
qualification, not evidence of actual corruption. Before accepting a result,
preserve a separately hash-addressed capsule/receipt containing `SEAL.json`,
`FINALIZED.json`, any `FINALIZATION_ABORT.json`, `RESOURCE.json`, and
`reduction.json`, and verify that receipt independently. A future source repair
should make final claim eligibility depend on a bidirectionally closed terminal
chain.

## Map-dynamics sidecar and campaign-level limits

`Q1_MAP_DYNAMICS_SIDECAR_v1` was committed at `5695d65a` before the notebook's
05:03 UTC no-launch checkpoint; its exact memo SHA-256 is
`2cee7e3757d31903d31fea9afee45a4c716dbd360d712e6e077842fd4a91d15b`.
The frozen run collects everything its unambiguous `0/1/32/64/128` version
needs without extra model work: OFF exact margins, ordered update-one
before/after surfaces and signs, all exact prefix records at 32/64/128, fixed
quartet order, step losses, q/M, and sealed snapshots. The quartet order makes
the declared C/O/M/X Walsh signs correct; AUTH aligns with `+X`, DERANGED with
`-X`.

The sidecar is chronologically predeclared, but it is **not internally
capsule-bound**: neither its name/hash nor the selected full-dose protocol/design
hash appears in `native_source_pins`, the prepared manifests, or the launcher.
Therefore custody must record the pre-launch Git commit/memo hash externally,
and the sidecar reducer must wait for all three fixed roots and publish missing
roots as incomplete. It cannot alter, rescue, select, or suppress a root-level
Q0 endpoint. The executor itself emits only root-level labels with an explicit
one-root claim scope; it has no all-three campaign-pass reducer, so any
all-three label is a separate failure-inclusive terminal aggregation task.

Finally, the selected protocol specifies a 10,800-second root ceiling and only
says post-terminal collection/replay is separately bounded. The archived
implementation handoff selects 180 seconds, which the source and launcher
enforce. The earlier design memo proposed 1,800 seconds and a 12,600-second
admission window. Because the selected protocol incorporates that memo only
for endpoint gates, material construction and CPU acceptance, I do not classify
the 180/1,800 difference as a frozen-protocol violation. It should remain
explicit in custody; these node-2 preparations have much more lease time than
either bound.

## Claim boundary

Even a clean three-root pass establishes only supervised finite complementary
branch selection plus strict action completion under this candidate-conditioned
DEV task. It does not establish full tool-call SFT, cross-map coexistence,
parenting, sleep, clean ancestry, retention, H1/H2, P1/G5, general G3, or an
integrated developmental mechanism.
