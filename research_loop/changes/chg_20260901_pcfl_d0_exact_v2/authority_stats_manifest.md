# PCFL D0 exact authority, estimator, resource, and claim manifest

**Change:** `chg_20260901_pcfl_d0_exact_v2`  
**Stage:** D0 only  
**State:** proposed, inert until exact-byte human ratification

This part of the successor bundle disposes G01, G06, G07, and G08 from the
PCFL execution-bundle v1 consensus. It is a design-and-authority contract, not
an implementation, model run, scientific cell, promotion, or claim. Agreement
with any golden below means only that the future local CPU reference checker
implements the ratified convention.

## Artifact map

| Artifact | Normative responsibility |
|---|---|
| `authority_manifest.json` | Exact D0 repository writes, read-only authority inputs, argv, output paths, transitive capabilities, environment, CPU ceiling, exhaustion behavior, post-ratification scope, and the mandatory future-backend reauthorization. |
| `estimator_manifest.json` | Exact pair estimand, failure-as-zero, studentizer, exhaustive sign flips, max-T/Romano--Wolf, grid bounds, Holm families, bootstrap stream, and six-pair power/no-claim screen. |
| `golden/estimator_cases.json` | Independently checkable rational arrays for aggregation, missing cells, degeneracy, ties, stepdown, bounds, bootstrap indices, and power decisions. |
| `resource_ledger.schema.json` | Strict per-pair/world/checkpoint/arm/adapter-seed accounting, including unequal substrate resources and energy method. |
| `claim_policy.json` | Exact D0 and dormant future templates, baseline-reversal dispositions, PCFL-13 scale firewall, operational-support qualifier, and adversarial paraphrase fixtures. |

The files name one another but do not embed their own hashes. Their bytes are
bound by the successor change/context map and the exact human-ratification
artifact. The ratification artifact is in turn bound by the authority receipt.
This directed chain avoids a self-hash cycle. A missing path, digest mismatch,
or missing affirmative D0-only human decision fails before implementation or
execution.

## G01 — exact D0 authority

After ratification, repository writes are confined to these modules:

```text
pcfl_d0/__init__.py
pcfl_d0/canonical.py
pcfl_d0/schema_validation.py
pcfl_d0/world.py
pcfl_d0/generator.py
pcfl_d0/controllers.py
pcfl_d0/reader.py
pcfl_d0/claims.py
pcfl_d0/compiler.py
pcfl_d0/interventions.py
pcfl_d0/estimators.py
pcfl_d0/resources.py
pcfl_d0/claim_policy.py
pcfl_d0/preflight.py
pcfl_d0/run_cpu_gate.py
```

The only tests are `pcfl_d0/tests/__init__.py`, `test_package.py`, one named
test for each module, and `test_contract.py`, exactly as enumerated in the JSON
manifest. There is no `src/**`, `tests/**`, plugin, generated-file, or sibling
package wildcard.

The only entry points are the exact argument vectors for:

```text
.venv/bin/python -B -m pcfl_d0.preflight ...
.venv/bin/python -B -m pcfl_d0.run_cpu_gate ... --suite full
```

The sole variable is `derived_run_id`, mechanically equal to `d0-` plus the
first sixteen lowercase hex characters of the raw human-ratification SHA-256.
Outputs are confined to `.research_loop/pcfl_d0/{derived_run_id}/`; final files
and their one-to-one SHA-named staging paths are fixed in the manifest.

The recursive capability closure is standard-library, deterministic CPU only.
It permits ratified local reads, run-scoped writes, local resource observation,
and the exact `unittest` modules. It forbids, including through lazy/error-path
imports:

- network, DNS, sockets, IPC, remote sync, telemetry, and providers;
- credential, keychain, cloud-metadata, secret, or environment enumeration;
- model weights, inference, embeddings, tokenizers, or tokenizer libraries;
- CUDA, ROCm, Metal/MPS, MLX, OpenCL, GPU enumeration, or accelerator kernels;
- training, autograd, optimizers, adapters, checkpoints, PEFT, and LoRA;
- shell, child processes, threads, dynamic native loading, plugins, pickle, and
  execution of data;
- DEV, calibration, confirmation, reserves, scientific outcomes, or future
  backend artifacts.

The reference execution ceiling is one local process, one thread, one
concurrent CPU core, 16 GiB peak resident memory, 64 file descriptors, and
2 GiB of run output. Preflight is limited to 900 wall/CPU seconds. The
1,000-step simulator is independently limited to 300 wall/CPU seconds. The
full gate is limited to 43,200 wall/CPU seconds; combined preflight plus gate is
limited to 44,100 seconds.

Energy is not left as a future choice. The ratified host must certify a maximum
CPU-package envelope of 65 W. The decision quantity is the exact monotonic
duration times 65 W, compared rationally against 2,866,500 J; any direct meter
is supplemental. Unavailable/ambiguous wall, CPU, RSS, descriptor,
process/thread, host-power, or energy measurement fails. Crossing any ceiling
produces `RESOURCE_EXHAUSTED_FAIL`; no instance, pair, seed, machine, or run is
replaced and no ceiling is relaxed after controller output is seen.

Ratification authorizes only construction and local execution of these D0
bytes. It never promotes itself. After submission for D1 review, byte changes
invalidate the run; material changes require a new deliberation and human
ratification.

## G07 — estimator choices are bytes, not implementation discretion

The independent unit is one counterfactual twin pair. For each arm, the fixed
order is eight targets within seed and ladder, two paired adapter seeds within
world and ladder, equal A2/A3 weight within world, then equal H/H-dagger weight.
Failures and missing post-dispatch cells occupy their fixed slot with value
zero. There is no complete-case deletion or favorable replacement.

For a centered 16-pair vector, sample variance uses denominator 15. The
studentized statistic is ordered exactly through its sign and squared rational:

```text
T^2 = (sum x)^2 * 15 / (16 * sum(x^2) - (sum x)^2)
```

Zero variance maps positive mean to positive infinity, zero mean to exact zero,
and negative mean to negative infinity. Thus an all-zero vector has `T=0` and
one-sided `p=1`, never NaN.

All 65,536 sign masks occur in unsigned integer order. Bit `i=0` is plus, bit
`i=1` is minus, mask zero is the observed vector, and the same signs are used
across hypotheses. Exceedance ties are included and exhaustive enumeration has
no add-one correction.

The three registered co-primaries retain their v1 meanings:

```text
D1 = E-LoRA - D-LoRA       null 0, mean >= .10, simultaneous LB > 0
D2 = E-LoRA - A-native     null 0, mean >= .10, simultaneous LB > 0
D3 = E-LoRA - E-text       null -.10, simultaneous LB > -.10
```

Romano--Wolf orders decreasing observed T, with UTF-8 hypothesis ID resolving
an exact tie, uses the maximum remaining permuted T at each step, and applies a
cumulative-maximum adjusted p. Equality at `.05` rejects. The lower bounds use
the fixed integer grid `-10000..10000`, divided by 10,000, and an explicit
single-step max-T candidate test. The bound is the greatest member of the
contiguous rejected prefix; the first hole stops inversion. Bound equality to
a claim threshold fails.

Locked usefulness versus N is an additional necessary intersection-union gate:
positive mean, exact one-sided p at most `.05`, and a one-sided grid lower
bound above zero. Because the bounded positive conclusion requires this gate
and all co-primaries, it cannot rescue or create a co-primary rejection.

Holm secondary families sort exact p-values ascending, break ties by UTF-8
contrast ID, stop on the first failure, and reject equality to the step
threshold. Mechanism contrasts and A2/A3-specific superiority remain separate
families. The 100,000 pair-cluster bootstrap has a complete SHA-256 counter
derivation, draws the same pair indices for every arm, and is report-only.

The six locked calibration pairs enter a deterministic planning screen for
four necessary gates. It uses denominator-five calibration variance, projected
`n=16` standard error `s/4`, and exact constant
`2.241402727604947`. The square-root-free comparison is:

```text
mean - b > 0
and
16 * (mean - b)^2 > z^2 * s^2
```

If any projected bound or D1/D2 mean condition fails, the disposition is
`INADEQUATE_POWER_AT_16_NO_POSITIVE_CLAIM`. No confirmation outcome, reserve,
larger `n`, or new contrast may repair it without a new ratification. The first
twelve confirmation pairs, if operationally run, stay masked and cannot enter
the screen or change the study.

## Resource vector, not false equivalence

Every ledger line has a complete pair/world/checkpoint/arm/adapter-seed key and
counts source events/actions/bytes/tokens; writer and compiler activity; every
claim status; records/atoms/edges/roots/views; active, retained, index, adapter,
optimizer, cache, and temporary bytes; candidate enumeration; retrieval,
reader, resolver, and training operations/tokens/FLOPs/time/energy; retries,
indeterminate/missing/zero failures; action costs; and total CPU/RAM/process/
thread/energy measurement.

Native linked memory, common-channel memory, text, context, retrieval, and LoRA
remain unequal substrates. The schema requires `fixed_memory_claim=false`,
`fixed_compute_claim=false`, `efficiency_claim=false`, and Pareto/resource-vector
reporting. Equal source or visible return bytes equalize only those bytes.

## G06 — baseline reversal and the PCFL-13 claim firewall

A future positive result requires locked usefulness versus N. Failure or
reversal versus N withdraws every useful-memory, retention, action-improvement,
and complete-pipeline claim. D-LoRA or A-native margin failure defeats the
bounded positive template. E-text non-inferiority failure becomes, at most, an
explicit-memory/compiler result or negative parametric-transport result.

Reversal against Bayes-N, CTX-C, CTX-H, R-rec, X-text, or A-common must be
disclosed by exact arm ID and forbids superiority to that comparator or any
“best memory” interpretation. A-native matching or winning removes the LoRA
moat. None of these outcomes may be hidden by calibration, averaging, unequal
resources, or the three original co-primaries.

The only eligible positive PCFL-13 template is exact and includes all of:

- `fixed-deck`;
- `post-working-window retention`, referring only to the imposed 8,192-token
  resolver budget;
- `operationally supported PCFL relations under registered interventions`;
- named comparator and registered-margin qualification;
- interpretation with the complete per-arm resource ledger.

PCFL-13 contains thirteen reusable mappings—about 16.7 bits before excluded
exceptions—and all can be operationally supported by 2C. It cannot support a
scale curve, increasing unique causal coverage, development, crossover,
saturation, continued lifetime improvement, or post-native-context language.
Operational support is a finite-generator prediction/contrast status. It is not
independent causal truth, autonomous discovery, or evidence outside PCFL.

`claim_policy.json` makes public claim fields exact-template-only and includes
adversarial paraphrases such as “keeps accumulating useful structure,”
“survives growing histories,” “developmental retention,” “DREAM autonomously
finds useful connections,” and “future provider calls cannot leak targets.” A
lexical linter is expressly insufficient: untemplated scientific prose is
rejected for fresh human semantic review.

## G08 — D0 evidence stops at the checker boundary

Every D0 expected/falsifies interpretation is narrowed to reference-contract
conformance. Scripted traces can show that a checker rejects the registered bad
fixture; they cannot show that a model composes memory, that a LoRA transports
action value, that A-native has no timing/cache side channel, or that a provider
resume is safe.

Before any future result or mechanism credit, a new predecessor-bound authority
must name the exact text, common/native A-MEM, recognizer, generative, LoRA,
renderer/tokenizer, provider, cache, index, and process implementations. Those
actual backends must repeat complete visible-input collisions, timing/error
tests, isolation/resume, all-cut masking, twin substitution from exact sealed
pre-decision model states, and S-life/S-bind/T-swap on actual built corpora and
adapters. D0 receipts are not inherited as scientific evidence.

## Ratification checklist

An exact D0 ratification should be rejected unless all answers are yes:

1. Does the ratification hash-bind every companion and deliberation artifact
   without relying on a self-hash?
2. Are only the exact `pcfl_d0` files, tests, argv, and derived outputs in scope?
3. Does recursive capability closure fail before network, credential, model,
   tokenizer, GPU, remote, training, adapter, LoRA, or scientific side effects?
4. Are cores, RAM, processes, threads, wall/CPU time, file descriptors, energy,
   measurement failure, and exhaustion all pass/fail rather than descriptive?
5. Do exact rational goldens cover zero variance, all-zero, tie, endpoint,
   missing, bootstrap, Holm, and power-screen behavior?
6. Does locked usefulness versus N fail the future positive claim, and does
   every strong-baseline reversal constrain the conclusion?
7. Is the only PCFL-13 positive language fixed-deck, post-working-window,
   operational-support-, comparator-, and resource-qualified?
8. Does every D0 statement stop at checker/reference conformance and require a
   newly authorized rerun on every exact future backend?

Passing this checklist makes the exact D0 bytes eligible for human
consideration. It does not itself ratify them.
