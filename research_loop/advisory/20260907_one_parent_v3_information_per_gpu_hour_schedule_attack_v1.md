# One-parent v3 information-per-GPU-hour and schedule attack v1

Date: 2026-09-07

Status: fresh read-only systems/statistics advisory over proposal-only and
legacy evidence. This memo changes no bound source, estimand, task, service,
writer, benchmark, model, tokenizer, adapter, or execution state. It
authorizes no implementation, model/tokenizer/embedding call, task generation,
CompilerGym execution, adapter operation, external access, GPU use, or claim.

## Verdict

**NO-GO as an evidenced September-16 schedule today; CONDITIONAL GO as a
workload if and only if a one-root-per-A40, multi-LoRA runtime and the exact
stage/lease gates below pass by September 10.**

The frozen scientific topology is not the problem. Fixed `N=32`, 48 wake
programs, four P/U causal cells, `R0`, three childhood writes per P/U branch,
and three deployment writes per P1/U1 form a coherent, expensive but finite
experiment. The problem is that the repository currently supplies ceilings on
logical calls, output tokens, fits, and only the active-memory portion of
input tokens—not a measured all-in root runtime or a finite upper wall-time
bound. The current legacy runner also cannot execute the required stochastic
or multi-adapter service topology unchanged.

The maximum-information path is therefore not to shrink `N`, the lifetime, or
the causal surface. Those are frozen. It is to (1) kill invalid writers and
baselines before roots, (2) time-multiplex all five isolated services of one
root through one dynamic multi-LoRA 7B engine and batch only simultaneously
ready calls, (3) share one reset/stateless tensor-parallel 32B parent service
across the independently isolated childhoods, (4) run the four-root directional
pilot before confirmation, and (5) defer every post-lock link/binding/PCFL or
named-method diagnostic until the C4 headline artifacts are immutable.

## Audited source receipt

| source | SHA-256 | use |
|---|---|---|
| `research_loop/plans/one_parent_child_headline_v1.md` | `e356bcecc0cdec3199cf8ecb23c2dc9790a59a11ee6dc8f81b1bfd399c7cf4d5` | topology, calls, fits, active-text workload |
| `research_loop/plans/one_parent_child_headline_v2_addendum.md` | `3c13492bb1378e07d966597efb9eb72f3c8742631a1e7ef1cb7b8977a5039cff` | fixed `N=32`, root distribution, endpoint, failures |
| `research_loop/plans/one_parent_child_headline_v3_spending_repair.md` | `632008a3306da4e09e6cfb73563f398aab5f6abf81e31b32de249ee177a81cd3` | four-root advancement conjunction and writer receipts |
| `research_loop/plans/active_text_fixed_contract_v1.md` | `0fbb16b124f640c0adcecc46d2270a7ee11e6c63866885d56e3b0e3468ed09c7` | exact active-text implementation/certification burden |
| `research_loop/changes/chg_20260907_one_parent_child_headline_v3/scope_proposal.json` | `a74e3be6c41dedc0de788cb25862b8e13abf9f8d9a3476e807dad4a24fe6f7bf` | frozen/forbidden scope |
| `research_loop/advisory/20260907_fable_v61_terminal_three_root_report_v3.md` | `3595b428295a5678ae8ab8a4edeb21e19f7f100010badc379b7b5c16d1f1c44e` | legacy writer instability; not timing proof |
| `research_loop/advisory/20260906_iclr_headline_resource_attack_v1.md` | `419bae0d353b3c2ee7c2c7c15099d6924831fedb8dcce87ddf2f192bd4119551` | supplied legacy fit timings and resource cautions |
| `organism_v6/model_backend.py` | `1b224307db99e33423bd7029415384967bb7dee831966bdbecc0a72bb80c92c8` | current single-adapter, seed-ignoring serving limitation |
| `organism_v6/run_life_v2.py` | `08cfe6669c46b30df01a9bddc14a2bbff66e03af536fce7c2c4d068d3777096c` | current shutdown/train/reload lifecycle |
| `organism_v6/train_adapter.py` | `234d8a93b8fb9f79e2daef11b4b2b5c0eda860c3a096b5222a252be5019d2f1b` | legacy trainer boundary |

The source-bound v3 workflow itself was at zero attempts and awaited exact
human deliberation authorization when inspected. A proposal PASS would still
not authorize any implementation or scientific execution.

## Exact recomputation

The v1 resource table gives one full root:

| stage | calls | maximum output tokens | fixed fits |
|---|---:|---:|---:|
| P/U childhood, including parent | 636 | 90,624 | 6 |
| five-service deployment, active-text updates, dreams, probes | 4,655 | 881,920 | 6 |
| **one complete root** | **5,291** | **972,544** | **12** |

Child-model work is 5,279 calls and 969,472 maximum output tokens/root; the
32B parent is 12 calls and 3,072 output tokens/root. `ACTIVE_TEXT_FIXED` alone
adds up to 480 child calls and 215,040 output tokens/root, in addition to
retrieval. Thus it is only 9.1% of logical calls but as much as 22.1% of the
output-token ceiling.

Current v2 fixes 32 confirmation roots. V1 also requires two development and
four excluded spending-pilot roots. Consequently the mandatory full-root
campaign contains 38 roots, not 32:

```text
full-root calls          = 38 * 5,291   = 201,058
full-root output tokens  = 38 * 972,544 = 36,956,672
full-root fits           = 38 * 12      = 456
writer canary            = 1,032 calls + 528,384 output + 18 fits
through writer canary    = 202,090 calls + 37,485,056 output + 474 fits
active-text strength cap = +2,000 calls + 400,000 output
through both gates       = 204,090 calls + 37,885,056 output + 474 fits
```

The scientific roots also expose a maximum 311,296,000 active-memory input
tokens (`38 * 8,192,000`). This is not a whole-input ceiling: v1 caps
`REFLECT`/`CURATE` partitions, but does not give one finite campaign ceiling
for all ordinary actor, nursery, DREAM, parent, and probe prefills. Therefore
the proposal has no valid maximum GPU-hour or wall-time bound yet.

The fit arithmetic is finite but not a runtime proof. The supplied legacy
rank-16 observations were 42 seconds at sleep 32, 227 seconds at sleep 256,
and 575 seconds at sleep 736 from `COMPILED` to `DONE`. Applying those timings
mechanically to 474 fits gives 5.53, 29.89, and 75.71 A40-hours; applying the
candidate ten-minute fit threshold gives 79.0 A40-hours. Applying the
15-minute shutdown-to-remount lifecycle threshold gives 118.5 A40-hours. None
is a bound on the new rank-8 response-only writer because corpus geometry,
masking, optimizer positions, and engine lifecycle differ. The plan specifies
p95 thresholds, not a finite per-fit maximum, so a strict upper time remains
undefined.

## What the legacy evidence actually implies

Fable v6.1 is useful evidence against optimistic systems assumptions, not an
estimate of this experiment. It established that 1,024-program paths with 32
cumulative fits and repeated vLLM shutdown/reload can take days and fail via
action-dialect drift. Its three terminal on-minus-off values were `+.0371`,
`+.0589`, and `-.4348`; the third root produced one registered action. This
supports hard transactional, native-routing, and adapter-off gates. It does
not estimate `D`, writer quality, parent teachability, N=32 variance, or a new
root's wall time.

The current code makes the schedule worse if reused literally:

- `VLLMBackend` enables at most the one adapter named at engine construction;
- the offered per-call seed is ignored;
- each fit tears down vLLM, loads a Transformers base, trains, saves, and
  reloads serving; and
- batching reduces engine dispatches but not logical samples/tokens.

The paper topology needs base/R0, frozen P and U childhood adapters, and
evolving P1 and U1 adapters concurrently addressable. It also needs the
counter-key seed to be honored. The legacy backend therefore fails before
resource timing; it is not a conservative implementation of the new design.

## Planning subtotals, not claimed bounds

Let `R` be effective batched child decode output tokens/s, `P` effective
prefill tokens/s, and `f` seconds per fit. Charging the entire 8.192M
active-memory input ceiling to deployment, but still omitting ordinary actor,
parent, engine, hashing, storage, and audit input/work, yields:

| scenario | R | P | f | childhood subtotal | deployment subtotal | root subtotal |
|---|---:|---:|---:|---:|---:|---:|
| optimistic anchor | 200 | 2,000 | 42 s | 0.192 h | 2.433 h | 2.624 h |
| middle anchor | 100 | 1,000 | 227 s | 0.622 h | 5.104 h | 5.725 h |
| conservative anchor | 50 | 500 | 600 s | 1.486 h | 10.451 h | 11.937 h |

These are sensitivity calculations, not hardware claims. `R` and `P` have
not been measured for the required prompts, batch shapes, LoRA mixture, or
A40 runtime. Maximum token allowances are not minimum realized work because
early completion burns accounting capacity without generating dummy tokens.
Accordingly neither a nontrivial empirical lower bound nor a finite empirical
upper bound is available from current artifacts.

## The only efficient eight-A40 mapping I would approve

Use one isolated root per child A40, not four GPUs per root. Within a root,
time-multiplex the five services through one resident 7B base and use
per-request LoRA selection. Batch only causally ready calls across its five
services; never share state, KV, stores, ledgers, RNG streams, or adapters.
During childhood, reserve two A40s for the pinned 32B parent under exact tensor
parallelism and run up to six child roots on the remaining A40s. The reset
parent may batch independent correction requests because batching weights is
not shared learning or parent state. After all parent outputs for a stage are
sealed and deletion audits pass, release those two GPUs; deployment can run
eight roots concurrently.

Let `H_N` be measured p95 childhood wall/root on one child GPU with the shared
TP2 parent available, and `H_D` measured p95 five-service deployment wall/root
on one GPU. Without cross-stage overlap, the exact staged wave count for all
38 roots is:

```text
development:  1*H_N + 1*H_D       (2 roots)
pilot:        1*H_N + 1*H_D       (4 roots)
confirmation: 6*H_N + 4*H_D       (32 roots; 6 child slots, then 8)
all roots:    8*H_N + 6*H_D
```

At the three sensitivity subtotals above this is 16.13, 35.59, or 74.60 wall
hours before omitted work and reserve. This mapping is conditional on dynamic
multi-LoRA correctness and one-root isolation. If those fail, it does not
exist.

The older four-GPU/root plan is not an eight-GPU shortcut. Counting mandatory
stages gives one two-root development wave, two pilot waves, and sixteen
confirmation waves: 19 waves. At six hours/root that is 114 wall hours before
canaries, review, failures, or reserve—not the 96 hours obtained by counting
confirmation alone. A literal one-GPU-per-service mapping is worse because
the frozen design has five deployment services, not four. Dividing aggregate
GPU-hours by eight also remains invalid wherever childhood, writes, probes,
and cut promotion are causally serial.

## Critical versus deadline-overengineered machinery

### Critical to the estimand or evidence validity

1. One complete root packet and root-level reducer; no task-level pseudo-n.
2. Exact P/U task matching, cached paired entry probes, counter-keyed RNG with
   a backend proof that seeds are honored, and no committed-call retry.
3. Native typed action/outcome provenance, response-only target masks/EOS,
   fixed slots/rehearsal, cumulative clean-base rebuild, and exact
   writer-path receipts.
4. Transactional fit/quarantine/remount, strict action/dream canaries, and
   adapter-off behavior after every cut. V6.1 makes these empirical rather
   than ceremonial.
5. Capability-root and byte-level parent/nursery deletion before deployment.
6. A finite actor-input/prefill envelope and a terminal-size all-in runtime
   canary under the exact multi-LoRA and parent topology.
7. `ACTIVE_TEXT_FIXED` source isolation and a once-only use/headroom
   certificate if the paper says *strong*, *validated*, or *plateau*.

### Scientifically defensible but overengineered for the deadline

The 866-line active-text contract combines a bespoke `REFLECT`/`CURATE`
language, five operation/status transitions, canonical content-addressed IDs,
BM25 plus BGE plus reciprocal-rank fusion, link expansion, strict partitioned
prompt packing, and multiple 100-case certificates. This is a second method
paper embedded in the control. It consumes up to 22.1% of root output tokens
before retrieval/prefill and creates a large implementation surface unrelated
to the primary `D` algebra.

That is not permission to simplify it silently: `ACTIVE_TEXT_FIXED` is frozen
into this proposal. The information-efficient ruling is instead: implement
the exact version once, run its certificate once, and stop tuning it. If it
fails but its common deterministic lifecycle is safe, call it an active-text
reference and delete *strong*, *validated*, and plateau claims as the existing
contract already requires. Replacing it with a simpler comparator would be a
new material decision and deliberation; spending days repairing it after one
sealed certificate failure is worse information/GPU-hour than proceeding to
the four-root causal pilot with the narrower label.

The two post-lock link/binding diagnostics, PCFL carrier assay, rank sweep,
LEAFE-style comparator, second domain, second child, and alternate parent have
zero value on the pre-C4 critical path. Their execution cannot rescue failed
`D`, `W_P`, or `L_terminal`.

## Explicit GO / NO-GO sequence

### G0 — authority and capacity, no later than Sep 8

GO only after exact v3 deliberation approval, five-role consensus, exact-byte
ratification, and an enforceable eight-A40 inventory with UUIDs, end timestamp,
preemption policy, and capacity through at least Sep 16 plus reserve. Current
“lease through Sep 14” evidence is a NO-GO for a result promised on Sep 16.

### G1 — CPU closure, no later than Sep 9

GO only if model-free fixtures prove root/counter manifests, five-service
isolation, cached entries, target/probe nonreturn, native action provenance,
writer slot/rehearsal arithmetic, exact masks/EOS, transaction rollback,
parent deletion, active-text transition/retrieval packing, failure values, and
the fixed `D -> W_P -> L_terminal -> C_public -> T_R0` reducer. These are
critical. Cosmetic report formatting, optional diagnostic overlays, and a
general-purpose memory framework are not.

### G2 — serving/writer/baseline canaries, no later than Sep 10

GO only if:

- the pinned 32B parent serves under a bound TP configuration and reset proof;
- the 7B engine addresses all required base/life adapters per request, honors
  supplied seeds, preserves strict native routing, and shows no cross-service
  cache/state edge;
- the full fixed active-text system prompt fits its 4,096-token partition;
- all three writer heats, duplicate fit, mount/off, generic anchors, and
  terminal-size fit/lifecycle thresholds pass; and
- one terminal-size timing packet measures `H_N`, `H_D`, input/output tokens,
  prefill/decode, all 12 fits, engine lifecycle, stores, and durable receipts.

The scheduling gate must be arithmetic, not “rank 8 is fast”:

```text
1.20 * (8*H_N + 6*H_D + remaining_canary_and_review_wall)
    <= min(bound_time_to_result_freeze,
           bound_lease_remaining - 12 hours)

38*(occupied_child_A40_hours/root)
  + parent_TP2_A40_hours + canary_A40_hours
    <= 0.80 * bound_remaining_A40_hours.
```

For a robust September-16 path I recommend the sharper operational screen
`H_N <= 1.5 h`, `H_D <= 7 h`, and all-in root `<= 8.5 h`, followed by the
exact inequalities above. This threshold is a reviewer recommendation, not a
silent source amendment. Failure is NO-GO for N=32 by this deadline, not
permission to use N=20: v2 fixed `N=32` and superseded v1's adaptive route.

### G3 — two development roots

Both roots must complete, justify all three `.05` scales and program
headroom, freeze the 2,048-token task budget from the development saturation
curve, and expose no target/probe leakage or resource violation. Any remaining
“fixed later” input, throughput, compiler-universe, or adverse-bound field is
NO-GO.

### G4 — four excluded spending roots, no later than Sep 11

Apply v3 literally: zero validity/resource failures; `D`, `W_P`, and
`L_terminal` jointly positive in at least 3/4 roots; all three means positive;
no separately ratified adverse crossing; complete writer-path tables. A
`D`-only pass is NO-GO for confirmation. Never pool, replace, or tune on these
roots.

### G5 — fixed N=32 confirmation

Prebind all roots and run without efficacy peeking, root replacement, or
adaptive `N`. Administrative missingness that removes a primary cut blocks
release. First priority is the four causal cells and registered probes; R0 is
still required by the frozen packet, but optional post-lock diagnostics wait
until C4 is immutable. An independent reducer must reproduce every root row,
failure, figure, and resource table from one manifest by Sep 16.

## Claim ladder without changing the registered estimand

The repository's informal C1--C4 fallback language must not be confused with
four powered hypotheses. Under the frozen v2 bytes only `D` and its stopped
fixed sequence are confirmatory; canaries and unsequenced contrasts do not
become inferential because the headline fails.

| rung | minimum clean evidence | maximum honest sentence |
|---|---|---|
| **C1** | native writer plus at least one supported process correction expressed on a fresh parent-absent homologous task | this fixed child can internalize and later express one practiced process correction; canary/teachability evidence only |
| **C2** | prospective personal-write curves and adapter-on/off behavior, but no passing primary interaction | bounded per-life experiential consolidation behavior/pathology; `U1-U0` is descriptive under current bytes unless separately ratified before roots |
| **C3** | either a passing `D` followed by failure of `W_P`/`L_terminal`, or a descriptive P1-versus-R0 system advantage after primary failure | in the first case, parenting changed write effects but did not establish beneficial learning; in the second, a full-package system association only—no parenting causality or confirmatory superiority |
| **C4** | N=32 primary `D` passes, then `W_P` and `L_terminal` each pass their `.05`/CI rules, with all validity gates | this fixed target-blind parent improved this fixed child's later benefit from personal writes and the parented child improved over its finite life under `Q` |

`C_public`, `T_R0`, and the local-plateau composite are additional stopped
rungs after C4, not prerequisites for the bounded parenting-learning sentence.
A clean C4 is paper-worthy. C3 may support an honest mechanism/negative paper
if the root evidence is strong. C2 is unlikely to carry an ICLR main paper
without a separately registered causal contribution. C1 alone is a canary,
not a submission result.

## Bottom line

The current `N=32`, 48-program, five-service experiment is **plausible but not
yet schedulable**. Its exact output/fit workload fits an eight-A40 campaign in
the middle sensitivity scenario only if the new runtime achieves dynamic
multi-LoRA within-root batching, the 32B parent is amortized as a shared reset
TP2 service, ordinary actor inputs are finitely capped, and root p95 timings
pass before Sep 10. The current backend, current lease record, and current
absence of an all-in timing packet fail those conditions.

Do not buy calendar comfort by deleting the U factorial, shortening the
lifetime, using N=20, or substituting P1--R0 for `D`; each changes the
scientific object. Buy it by killing invalid machinery early, batching only
causally ready calls, separating parent/child role pools, deferring all
diagnostics, and refusing the 32-root spend unless the four excluded roots
show jointly positive `D`, `W_P`, and `L_terminal`.
