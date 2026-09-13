# Independent terminal audit: Q0 root 1 attempt 2

**Date:** 2026-09-13 UTC  
**Root:**
`/localhome/local-rohing/astra_diagnostics/astra_pairwise_Q0_root1_20260913_attempt2`  
**Role:** fresh raw-artifact auditor. I did not build or run the experiment.  
**Mutation scope:** none. I changed no builder source, root artifact, model,
adapter, job, process, GPU state, threshold, label, or downstream experiment.

## Verdict

I reproduce the registered scientific terminal
**`EARLY_XOR_QUARTET_STOP_AUTH`** from the sealed raw tensors. The first
P_AUTH update failed the noncompensatory eight-predicate canary; therefore no
128-update AUTH fit, P-map qualification, confirmation root, or action-relay
release is permitted. The mandatory one-step complementary diagnostic and the
prospectively released unary-tool diagnostic also failed their canaries, so the
registered qualifiers are:

- `BOTH_MAP_FIRST_STEP_MISS`;
- `EARLY_UNARY_TOOL_STOP`; and
- `OPAQUE_TOOL_WRITE_FAILURE_THIS_RECIPE`.

This is a narrow negative for **this supplied synthetic direct-action writer
recipe at root 1**. It is not a universal LoRA-capacity result, an endogenous
experience result, clean-lineage evidence, H1/H2, retention, robustness, or a
whole-organism result.

I found one real but label-invariant replay defect: the frozen reducer's exact
equality check over a full-vocabulary CPU `logsumexp` is sensitive to CPU thread
count, which the terminal manifest does not bind. The documented bare replay
command under the node's default multi-thread setting aborts because one audit
row's derived `log_normalizer` and `M` move by
`7.105427357601002e-15`. With `OMP_NUM_THREADS=1` and
`MKL_NUM_THREADS=1`—the setting used by the bound numerical tests—the same
frozen source performs an exact immutable replay and returns report SHA-256
`250e67b36c16325f5b8042e7731dd71c615cd0387c1f1f6d092b68e8188c87e5`.
The discrepancy does not approach or change any canary predicate or label, but
future executors must bind/set the reducer thread count or compare this derived
quantity under an explicit FP64 error bound.

## Custody, identity, sealing, and release

- Manifest SHA-256:
  `bd263500a4d1176dfec5e3489db0c20e479f9703eb745b9902dde017d82754d1`.
- Prepared-material SHA-256:
  `aa96210c73048d9980011930cb57e3407beacbe7ed094ae13b46dda187de4852`.
- Seal SHA-256:
  `abac7fe73e1b5952cb3d92be21bb604d304c57470ee734a4ce3889694e5ef937`.
  I independently hashed all `16,098` sealed files; the path/hash map is exact
  (`15,439` tensor files, `611` stage files, `17` source files, and the bound
  logs/jobs/receipts/root metadata).
- Provisional reduction SHA-256:
  `8b269dd0a57acd98bd45cf42c3a01ddcf456271453cfb4569eb83fee2348f332`.
  It correctly remains `CANDIDATE_ONLY_NOT_A_TERMINAL_CLAIM` before durable
  finalization. The post-finalization read-only replay supplies the scientific
  terminal above.
- Durable-finalization file SHA-256:
  `cd6fb48d488fe05efdc45928eba1bbb03f38aafea1b2c9d35335591160c750e1`;
  it binds the seal and records completion at `1378.081` seconds, before the
  fixed `2700`-second deadline. Resource completion was `1373.553` seconds.
- Controller PID/PGID/session `306207`; worker PIDs
  `306490/307094/307542/308239/308779`. All are absent. The five workers have
  unique process-start and load identities, one attempt each, serial
  start-after-prior-finish timing, exact job/load/ticket/receipt hashes, and
  complete cleanup receipts. A live GPU process query was empty.

The five registered stages—and no others—are:

```text
00_audit
01_eval_OFF_0
02_fit_P_AUTH
03_fit_P_DERANGED
04_fit_P_UNARY_TOOL
```

Every event file exists exactly once, its content hash matches its DONE
inventory, and there are no unlisted event files. Source pins are `17/17`
exact. The public model-only binding remains
`Qwen/Qwen2.5-7B-Instruct@a09a35458c702b33eeacc393d103063234e8bc28`,
inventory SHA-256
`1b248450cd087dad8956a8b77ccc4829040d614133f3c0aba834729af8075422`;
it explicitly does not certify clean ancestry.

## Material and initialization

The reconstructed material has the registered root-1 orientation
`[0,1,1,0,1,0,0,1]`, native branch IDs `[10536,21404]` for
`-mem2reg/-gvn`, `296` unique decision prefixes, and exact panel counts:

```text
exact 128; held 64; missing-mode 8; unsupported-mode 8;
neighbour-ID 16; wrong-root 64; copy 8
```

There are `32` pair-balanced XOR quartets, repeated four times for the frozen
`128`-update schedule. Token/material reconstruction passed under the frozen
tokenizer during exact replay.

The audit and all three fit workers have byte-equal initialization records:

- `392` ordered FP32 LoRA tensors, trainables digest
  `10f27437b37405a09062608efd04b4528a3221d645988d897c412deea83e1917`;
- full initialization-record digest
  `fb93d14e2d9e69b29c3cba5e74aeedfaf538d843d910cb1903787f1af39a25df`;
- step-zero logits digest
  `7055119b165cd8d8b48e87a828ec7b6dbbad18a63e585d11d63aefb2e75dcb70`;
- CPU RNG `acb02626...` and CUDA RNG `aeb93e36...`; and
- one exact AdamW parameter group with initially empty state.

The manifest binds rank `8`, alpha `16`, dropout `.05`, all seven projection
families, seed `1`, BF16 base/forward, FP32 trainables/gradients/optimizer,
AdamW `3e-5`, betas `(.9,.999)`, eps `1e-8`, weight decay `.01`, and no
scheduler, clipping, TF32, or checkpointing.

## Exact work accounting

| stage | natural-prefix forwards | native model forwards | generations | emitted token IDs |
|---|---:|---:|---:|---:|
| zero-update audit | 128 | 128 | 0 | 0 |
| contemporary OFF | 288 | 2,353 | 296 | 2,065 |
| P_AUTH first-update attempt | 148 | 148 | 0 | 0 |
| P_DERANGED diagnostic attempt | 148 | 148 | 0 | 0 |
| P_UNARY_TOOL attempt | 148 | 148 | 0 | 0 |
| **total** | **860** | **2,925** | **296** | **2,065** |

OFF reconciles as `288 + 2,065 = 2,353`. Each stopped fit reconciles as
`128` step-zero prefixes + `8` repeated dropout-off before surfaces + `4`
train-mode quartet forwards + `8` repeated dropout-off after surfaces =
`148`. Each performed one optimizer update and four training row forwards;
the total is three updates and twelve training forwards. The zero-update audit
contains all `128` row records, all `32` P/V gradient records, no optimizer
step, and a nondegenerate objective contrast with no zero-tangent branch.

## Independent first-update arithmetic

I loaded the sealed binary operands directly, independently verified every
FP32 `theta_after - theta_before = delta` tensor bit-for-bit, reconstructed the
signed target maps from the prepared rows, recomputed the FP64 directional
dots and error bounds, and reconstructed each before/after output-head margin.
The independent dots differ from the recorded values by at most
`6.3e-15`—many orders below their registered bounds.

| arm | registered signs | projection predicates | observed-change predicates | all 8 |
|---|---|---:|---:|---:|
| P_AUTH | `[+,-,-,+]` | 2/4 | 3/4 | **fail** |
| P_DERANGED | `[-,+,+,-]` | 2/4 | 1/4 | **fail** |
| P_UNARY_TOOL | `[+,+,-,-]` | 2/4 | 2/4 | **fail** |

The canary is a conjunction, not a majority vote. For P_AUTH, two projected
dots are strongly negative (`-4.42299`, `-4.55901`) against positive numerical
bounds of about `4.2e-8`, and its fourth observed signed margin change is
`-0.0184103` against a positive bound of about `6.5e-10`. DERANGED and unary
likewise contain large negative predicates. Thus the misses are directional,
not rounding-edge cases. All three recorded Gram matrices satisfy the analytic
PSD check (minimum eigenvalue about `409.005`, allowed floor
`-0.000443087`).

The numerical policy is safety multiplier `4`, gradient floor `1e-12`, and
even median = arithmetic mean of the middle two. Because every fit stopped at
update 1, no update-128 exact/held acquisition cell or median gate was reached;
no median may be used to rescue or reinterpret the result.

## Stop logic and implication

The frozen lifecycle requires AUTH first. Its canary miss fixes the primary
label immediately. It then permits exactly one DERANGED step as a mandatory
complement diagnostic; because both maps missed, it permits exactly one unary
tool attempt. The unary canary also missed. No snapshot or later readout was
created for any fit, and no retry or optional objective substitution occurred.

Accordingly, attempt 2 is a valid failure-inclusive rejection of this direct
pairwise action-writer recipe. Preserve the root and label. Do not launch Q0
confirmations or the Q0-dependent endogenous action relay, and do not tune
rank/rate/dose/quartet/objective on this direct-action family using this
result. A separately preregistered, differently factored endogenous memory
representation may be tested, but it cannot be called a repair or pass of Q0.
