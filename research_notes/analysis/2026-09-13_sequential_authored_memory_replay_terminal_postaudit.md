# SEQ-118 terminal post-audit: sequential authored-memory replay

**Audit date:** 2026-09-13 UTC

**Role:** independent read-only recount from the archived raw requests and
responses; no experiment code or stored reducer was imported or executed.
**Prospective interpretation:**
`2026-09-12_sequential_old_new_fixed_budget_prospective_outcome_matrix.md`,
frozen at commit `06501264` before outcomes were inspected.

## Verdict

The archived evidence reproduces the reported result. At the terminal state,
the replay allocation retained `64/64` old-bank readout decisions and acquired
the newest bank at `32/32`; the no-replay allocation retained `25/64` old-bank
decisions while also acquiring the newest bank at `32/32`. Both remained
`32/32` on the arithmetic action panel. Under the prospectively frozen matrix,
replay is state **I** (safe integration) and no-replay is state **F** (new
acquisition with old forgetting).

This is useful evidence for **one fixed-total-budget replay allocation at one
small authored seed**. It is not a pure causal effect of replay: replay gave
each current-new fact 20 presentations while no-replay gave it 40 and the
within-batch mixtures differed. It is also not child-authored SLEEP,
learning-to-learn, parenting, connected knowledge, or lifetime improvement.

## Immutable evidence and custody

- Capsule:
  `research_notes/astra_memos/receipts_20260912/astra_sequential_memory_seed0_pair_attempt2_terminal_20260913T0000Z.tgz`
- Recomputed capsule SHA-256:
  `c63437c47918603d5b784544bcae85e7febc93ec7516677eaa9a3608b78b2fb0`
- The recomputed hash equals the separate validation record.
- The archive contains exactly the 1,421 regular files named by that record:
  zero missing files, zero extra files, zero member-hash mismatches, zero
  links/special entries, and zero unsafe paths.
- Bound experiment plan SHA-256:
  `9e53c716373c2458586ff7b6a72d0fe5822d41d5a0129057e2a4e805acab8b49`.
- Bound source commit: `5a1f300fed4b7f1ef54524869c2bf11509e965ca`.
- The capsule records terminal `COMPLETE`, 640 expected calls, no native
  model/tokenizer rerun, no reducer rerun, and released resources.
- Adapter weights remain on the native machine and are not in the capsule.
  This audit therefore verifies the archived tensor/file digests and their
  lineage, not the bytes of the native safetensors independently.

## Raw-call recount

The panel has 128 unique cases: 96 memory queries (`3` banks x `16` facts x
`2` surfaces) and 32 arithmetic actions. For all five states, an independent
reader checked every raw request/response pair against the case material.

- Exactly 128 request and 128 response files exist per state (`640` calls).
- Every call ID, case ID, prompt, role, arm, seed (`20260912`), temperature
  (`0.0`), and maximum output (`64`) matches the frozen case definition.
- Every response ended with `finish_reason=stop`; maximum observed output was
  14 tokens.
- Each state used one internally consistent model/adapter identity across all
  128 calls.
- All 480 memory responses were exactly one bare permitted colour after
  whitespace normalization; there were no invalid or parser-dependent forms.
- All 160 arithmetic responses contained exactly one prediction before
  exactly one action. Every action was correct.
- Independently recomputed counts equal every stored reduction.

Counts below are `exact/dev`, each out of 16 facts. The two surfaces repeat the
same facts and are not independent trials.

| State | M0 | B1 | B2 | arithmetic |
|---|---:|---:|---:|---:|
| S0 | 16/16 | 5/5 | 6/7 | 32/32 |
| R1 | 16/16 | 16/16 | 6/5 | 32/32 |
| NEW_ONLY1 | 8/10 | 16/16 | 4/5 | 32/32 |
| R2 | 16/16 | 16/16 | 16/16 | 32/32 |
| NEW_ONLY2 | 8/9 | 4/4 | 16/16 | 32/32 |

The wrong memory outputs were still valid colours rather than malformed text.
Thus the no-replay decline is not a formatting or scoring artifact. B1 passed
both surfaces at NEW_ONLY1 and fell to `4/16` on both at NEW_ONLY2, qualifying
within-trajectory forgetting under the frozen rule rather than failed initial
acquisition.

## Material and schedule audit

The three banks use disjoint device identifiers. Each contains 16 facts with
exactly four red, four blue, four green, and four yellow targets. Each readout
fact matches its training fact and has one exact and one development wording.
The 16 arithmetic sources used during fitting are disjoint from the 32
arithmetic evaluation sources.

Every fit contains 128 rows in 32 groups of four, with context masked and only
the response span trainable. Per epoch:

| Fit | memory rows | arithmetic rows |
|---|---|---:|
| R1 | 32 B1 + 32 M0 | 64 |
| NEW_ONLY1 | 64 B1 | 64 |
| R2 | 32 B2 + 16 B1 + 16 M0 | 64 |
| NEW_ONLY2 | 64 B2 | 64 |

All fits ran 10 epochs and 320 finite optimizer steps. This yields the declared
20 current-new presentations per fact for replay versus 40 for no-replay;
R2 additionally gives 10 presentations per fact to each old bank. Each paired
fit has 6,616 input tokens and 1,000 target tokens per epoch, but its semantic
allocation differs. Final training losses were extremely small, as expected
for this deliberately high-dose storage diagnostic; that dose is not an
operational SLEEP recommendation.

## Weight-lineage audit

Both cycle-1 fits start from the same archived S0 state. R2 starts from R1;
NEW_ONLY2 starts from NEW_ONLY1. For all four writes:

- parent path, parent file digests, and all 392 parent tensor digests agree
  between the child's input, the parent's saved result, and the warm-start
  record;
- the initialized trainable state equals the recorded parent state before an
  update;
- one adapter is active and the base is recorded frozen;
- the optimizer is fresh with zero restored state entries;
- the parent is recorded unchanged;
- the final tensor digests equal the saved result;
- the 320-step worker completed with zero nonfinite batches and successful
  supervised cleanup.

Cumulative adapter steps are therefore the declared `400 -> 720 -> 1040` on
each separate trajectory, with no cross-trajectory parent substitution visible
in the archived evidence.

## Prospective disposition and next action

S0 met the parent precondition: M0 and arithmetic were perfect, while B1/B2
had ample headroom. Both arms established B1 at cycle 1. R2 then satisfies the
matrix's noncompensatory integration rule; NEW_ONLY2 satisfies forgetting with
new acquisition. R exceeds the comparator on both old banks and does not pay a
new-bank or arithmetic penalty despite receiving half as many current-new
presentations.

The colour-storage question is answered well enough for architecture
development: use varied-view, distinct-source interleaving and replay as
provisional writer ingredients. Do not spend the next GPU-hour repeating this
same unequal-dose colour comparison. The next bottleneck is selective,
input-conditional writing: the adapter must learn opposite actions in the
right conditions without exporting either action to unrelated contexts. That
Q0 gate belongs inside Level-1 birth, followed by a small birth-disjoint
  Level-2 sample to test whether the born child actually learns faster—not only
  whether it reproduces installed routines.
