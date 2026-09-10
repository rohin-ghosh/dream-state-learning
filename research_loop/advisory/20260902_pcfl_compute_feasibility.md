# PCFL-Compose / PCFL-Stream compute feasibility audit

**Date:** 2026-09-02  
**Scope:** read-only calendar and compute audit. No code, GPU, provider, or
experiment launch was performed.

## Executive conclusion

A bounded two-week development package is plausible on the existing fleet if
the scientific surface is kept to one frozen renderer, one frozen resolver,
D1/D4, four lifetime checkpoints, a small independent-law sentinel, and the
core text/program/LoRA controls. A powered confirmation paper is not credible
in the same two weeks: the area-chair review requires tens of independent
world-life/twin pairs, while the present small-world results are explicitly
DEV-only.

The only directly measured LoRA training anchor is **Qwen2.5-7B**: 94,000
training lines, four epochs, batch 32 and length-sorted batches took **53 min**
(the run-v2 code subsequently caps larger corpora at two or one epochs). The
only directly measured 32B inference anchor is **Qwen2.5-32B-Instruct** on an
H100 NVL: the 12-target dream/compiler stage took **29m29s**, with 53 model
calls and roughly 50k input / 73k output tokens; the 44-call thinker stage took
**3m01s**. There is no measured 32B-LoRA training result in the repository.
Therefore a strict one-backbone 32B-LoRA paper plan cannot be honestly costed
from current evidence. The practical two-model transport path is a pinned 32B
resolver/compiler plus a pinned 7B LoRA memory base; changing that split needs
fresh review and a canary.

## Existing evidence and its limits

### Runtime anchors

| Workload | Measured configuration | Measured time | Use in planning |
|---|---|---:|---|
| LoRA training | Qwen2.5-7B; LoRA rank 64 in the later semantic runs; batch 32; length-sorted; **94k lines × 4 epochs** | **53 min** | Conservative per-adapter upper anchor. Small PCFL canonical corpora should be shorter, but no PCFL timing is measured. |
| 32B compiler/dream | Qwen2.5-32B-Instruct, pinned revision `5ede1c97...`; vLLM; one H100 NVL; 53 calls, 12 targets, 4 samples, max 900 output tokens | **29m29s** | Per world-side full compiler pass. Prompts in logs commonly take 26–52s each at ~44 output tok/s. |
| 32B thinker | Same pinned model/job; 44 calls, 30 goals | **3m01s** | Short-target resolver/reader order of magnitude; target action calls must still be timed in the actual harness. |
| 7B v2 eval harness | Existing `seed*_results.json`; 200-query points, 7B vLLM harness | LoRA reads commonly **20–100s** per arm/point; multi-read **~80–214s**; RAG rises to minutes at long contexts | Supplemental inference anchor; not a PCFL result. |

The 53-minute measurement is recorded in the run-v2 history as
`53min/94k-lines/4ep measured`; the same change projects a previously
14-hour final training schedule to roughly 3.5 hours by reducing epochs for
large corpora. That projection is not a PCFL measurement. The 32B timings are
recoverable from the copied remote job progress and log artifacts:

```text
gpu_artifacts_local/research_loop/
  dream-ladder-v5-dev-20260831T161813-13cf3c10/job/progress.json
  dream-ladder-v5-dev-20260831T161813-13cf3c10/job/02_dream_v5.log
  dream-ladder-v5-dev-20260831T161813-13cf3c10/job/03_think_dreamtext.log
```

The 32B model loaded a 61.03 GiB checkpoint, used a 32,768-token maximum
sequence length, and reported 13.06 GiB KV-cache memory. Startup includes
roughly 5.2s model loading, 33.9s torch compilation, warmup, and CUDA graph
capture; keep at least a few minutes of process/setup slack per fresh worker.

### Existing scientific results

The v0.2 branch-depth result is a controller ceiling, not a parametric-memory
result: 32B achieved 23/24 final answers on two untouched seeds, but used
exhaustive 57-subset branching and 114 atomic checks per target, while storing
memories in text. It explicitly says the context-vs-LoRA comparison remains to
be run. The G-series demonstrates that rank-64 7B LoRA transport can work, but
with noisy reads, heavy mechanical/recognition assistance, and tiny worlds.
Neither is confirmation evidence for PCFL-Compose/Stream.

## Recommended model and world surface

### Models

Use the existing split only for a development/transport package:

1. **Writer/compiler and resolver:** `Qwen/Qwen2.5-32B-Instruct`, revision
   `5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`, bf16/vLLM on H100 NVL or GH200.
2. **Memory LoRA base:** `Qwen/Qwen2.5-7B-Instruct`, pinned to the revision
   used by the existing execution bundle (`a09a35458c702b33eeacc393d103063234e8bc28`)
   if that revision is revalidated. Existing adapters target q/k/v/o projections
   at rank 64 and are about **154 MB** each.

This is a two-model pipeline, not evidence for a one-backbone claim. If the
paper insists on one pinned 32B backbone for both resolver and LoRA, schedule
a single 32B-LoRA canary first and treat all cost numbers below as lower
bounds; no 32B training runtime is currently measured.

### Worlds, twins, and checkpoints

The Compose family should be the factorized noncommutative `S_6` tray world
with the two composition orientations, plus a matched independently sampled
transition-table sentinel. Each authentic life has an exact stem-binding twin;
all target-visible bytes remain equal while the valid action labels swap.

For CPU calibration, choose factor counts that land in the tokenizer-exact
visible envelope, rather than fixing episode count or repeating old factors.
The provisional checkpoint bins are **0.75C, 1.5C, 3C, and 6C**, where `C` is
the measured usable context (including system prompt, reader/workspace bytes,
operation history, and output reserve). For the current 32B vLLM envelope,
`C` cannot be assumed to be 32,768 model tokens: measure the usable boundary
after the exact PCFL prompt is frozen. If all three post-native bins cannot be
completed, report no lifetime growth/continued-acquisition/saturation claim.

At every checkpoint retain separate D1 and D4 cohorts:

- new-factor acquisition;
- old-factor retention after its support leaves the visible window;
- cross-era D4 composition;
- paired goal twin and the independent-law sentinel.

The exact factor counts, source slots, target paths, and byte sizes must come
from the CPU generator/certifier. They are not present in the current advisory
and must not be guessed from the old Alchemy episode counts.

## Two-week roster

### Development/calibration surface (credible)

Use **two independent world-life/twin pairs** for end-to-end development:
one calibration pair and one untouched sentinel pair. Run all four checkpoints
on the calibration pair; run the independent-law and binding/order diagnostics
at one pre-registered sentinel checkpoint. This is enough to expose plumbing,
reader, adapter, twin, and storage failures, but it is not a powered claim.

Core arms:

1. no persistent memory / target-only Bayes;
2. native-context then frozen-truncation context;
3. raw episodic RAG or linked external memory (one selected implementation);
4. exact public factor-law program/planner;
5. direct raw-transition-to-QA LoRA;
6. target-blind compiled schema text;
7. identical-corpus compiled schema LoRA;
8. oracle-schema text as a compiler/reader ceiling.

Run unaided generative-LoRA, candidate-only clean-base, wrong/twin adapter,
order-law cut, decisive-binding cut, and equal-size sham cut only at the
sentinel checkpoint. Do not spend the two weeks on a full rank × reader ×
depth × age Cartesian sweep, second backbone, multiple skins, on-policy
exploration, or faithful new implementations of every named baseline.

### Confirmatory surface (defer or explicitly label calibration)

The area-chair review's requirement is **at least tens of independent
world-life/twin pairs**; four pairs are explicitly inadequate. A reasonable
future confirmation roster is **16–20 independent pairs**, with a frozen
sentinel endpoint and the same core arms, followed by the four-checkpoint curve
only if the endpoint gates pass. Existing three-world G-series runs, the two
development pairs above, and any six-pair short run must remain DEV/calibration
evidence. Do not call them confirmatory or use nested target cells as sample
size.

Confirmatory cells must be frozen before model outputs: generator/twins,
checkpoint bins, D1/D4 allocation, direct-QA and compiled corpora, adapter
recipe, reader/candidate interface, cuts, missingness, and pair-blocked
analysis. Any prompt, threshold, parser, factor-count, or capacity change is
DEV and resets the confirmation clock.

## Compute and wall-time envelope

The table uses intentionally conservative arithmetic from measured anchors.
It counts GPU-hours as the sum of occupied device time; four H100s can reduce
wall time for independent jobs, but cannot make a single 32B process fit twice
on one 95 GB GPU.

### Per world side and checkpoint

| Component | Working estimate | Basis / caveat |
|---|---:|---|
| 32B compiler pass | 0.5 GPU-h | 29m29s measured full pass; include 0.1h warm/setup slack if process is reused, more if reloaded. |
| 32B short resolver pass | 0.05 GPU-h | 3m01s measured 44-call thinker; PCFL D4 action protocol must be benchmarked. |
| One 7B LoRA adapter | 0.1–0.9 GPU-h | 0.1–0.3h expected for a small canonical corpus; **0.883h** is the conservative 94k-line/4-epoch anchor. No PCFL timing yet. |
| 7B read/eval | 0.03–0.1 GPU-h | Existing per-arm/point v2 timings; recognition reads and target actions may add calls. |

For a single world side at four snapshots, budget four compiler snapshots and
four adapter snapshots. Incremental checkpoint files can reuse the same source
life and model process; do not independently regenerate the lifetime. Training
must occur in a subprocess separate from vLLM, as the existing G-series found
in-process vLLM/PEFT handoff corruption.

### Development pair budget

For two pairs (four sides), two LoRA arms, four checkpoints:

- 32B compiler: `4 sides × 4 checkpoints × 0.5h ≈ 8 GPU-h`;
- 32B resolver/reader: approximately `0.8–2 GPU-h`;
- LoRA training: `32 adapter jobs × 0.1–0.883h ≈ 3–28 GPU-h`;
- read/action evaluation and retries: approximately `2–6 GPU-h`.

**Total:** roughly **14–44 GPU-h**, with the wide range driven by the unknown
PCFL corpus size and whether each adapter approaches the 94k-line anchor.
On four H100 NVLs this is about **6–18 wall hours** of occupied work after
CPU artifacts, model pulls, and failed-canary slack. A one-day to three-day
calendar reservation is safer because gates and reruns are serial.

### Six-pair calibration envelope

Six pairs would require approximately **50–158 GPU-h** under the same upper
bound, around **13–40 wall hours** on four H100s. This can be a descriptive
calibration batch if the harness is already frozen; it cannot provide the
pair count requested for confirmation.

### Future 16–20-pair confirmation envelope

At the conservative 94k-line LoRA upper bound, 16 pairs imply about **134–418
GPU-h** for the same four-checkpoint/core-arm shape; 20 pairs imply **168–522
GPU-h**. Four H100s turn that into roughly **1.5–5.5 wall days** of pure occupied
compute, not a two-week paper calendar once CPU certification, adapter sanity
failures, artifact transfer, independent review, and reruns are included. If
the PCFL canonical corpus is small, training may be much cheaper; that is an
unmeasured upside, not a planning entitlement.

## Storage and transfer

Per H100, the pinned 32B checkpoint consumes about **61 GiB** before caches;
reserve at least 100 GiB local NVMe for weights, vLLM compile/cache files, and
logs. The 7B base is roughly 15 GiB class. Existing rank-64 adapters are about
**154 MB** each; rank 32 should be treated as approximately half only after a
canary confirms the serializer and tensor shapes.

Adapter-only snapshot storage (not optimizer state) is approximately:

- two DEV pairs: `32 adapters × 154 MB ≈ 4.9 GB`;
- six-pair calibration: `96 × 154 MB ≈ 14.8 GB`;
- 16-pair confirmation: `256 × 154 MB ≈ 39.4 GB`;
- 20-pair confirmation: `320 × 154 MB ≈ 49.3 GB`.

Add 2–4× for public source logs, prompts/generations, compiler traces, twin
manifests, and temporary copies. If optimizer state is persisted, add roughly
0.6–1.0 GB per rank-64 adapter; the current `train_lora` saves adapter weights
but not optimizer state, so record optimizer metadata and do not assume
resume-state storage is free. Keep artifacts on local NVMe during runs and
pull completed manifests/adapters incrementally; the copied v2 branch-artifact
directory is already **5.8 GB** for a much smaller prior campaign.

## Fleet fit and constraints

The currently described fleet is:

| Node | GPUs / status | Feasible use |
|---|---|---|
| `4u4g-gen-0310` | **4× H100 NVL**, current v2 wrapper | Primary 32B vLLM/compiler/resolver and parallel independent sides. H100 log reports 95,830 MiB and 61.03 GiB 32B weights. |
| `lego-cg1-qct-034` | GH200 worker, current wrapper | 32B fallback/parallel worker after the documented ARM CUDA/vLLM setup; GH200 requires `memhp_default_state=online_movable` and has higher setup risk. |
| `a4u8g-0105` | **8× A40**, lease noted through 2026-09-14 | 7B LoRA/read workers or CPU-like preprocessing; not a credible bf16 32B host. |

The bootstrap policy prefers 8×H100/H200, then 4×, production B200, and 8×A100;
it asks for at least 32 CPU cores preferred (16 minimum), 256 GB RAM, 1 TB
NVMe, standard Ubuntu x86_64, and a seven-day lease. The scout accepts
B200/GB200/GH200/H200/H100/A100 and rejects TS/SIFX bring-up samples. These
are availability/policy descriptions, not a fresh inventory result.

## Critical path and stop rules

1. CPU generator, exact `C`, target/twin byte equality, D1/D4 uniqueness,
   target-only Bayes, and independent-law sentinel.
2. 32B compiler/text/program calibration on one DEV pair; no LoRA before the
   compiled-text and exact-program ceilings are valid.
3. One 7B LoRA canary (direct-QA and compiled corpus) with post-train sanity
   read. The existing measured recipe warns that 5e-4 can destroy the adapter;
   keep 2e-4 and the 1e-4/5e-5 ladder, and train in a subprocess.
4. Reader/candidate accounting, authentic-vs-twin adapter and order/binding
   cuts at the sentinel checkpoint.
5. Fan out the frozen DEV roster across H100s; archive hashes and resource
   ledgers before any claim review.
6. Only after a fresh bound approval, run the separate confirmation roster.

Immediate stop conditions are: compiler/text ceiling failure; 32B prompt
context not reaching three post-native bins; malformed or gibberish LoRA
sanity output; PCFL corpus/training time approaching the 53-minute anchor per
adapter without an explicit rebudget; independent-law sentinel above chance;
or crossed twin/order/binding cuts failing to redirect action. These are
resource/scientific gates, not reasons to silently reduce denominators.

## Bottom line

The honest two-week deliverable is a reproducible **DEV/calibration assay**:
one pinned 32B compiler/resolver, one pinned 7B LoRA transport base, two
world-life/twin pairs, D1/D4, four tokenized checkpoints, exact program and
compiled text, two LoRA arms, and one sentinel/cut panel. It fits the active
H100 fleet in roughly a day of occupied GPU time with several days of calendar
slack. It does not support a powered lifetime or LoRA superiority claim. Keep
the ≥16–20-pair confirmation roster separate and future-dated; only promote it
after the CPU, text, reader, twin, and LoRA gates are frozen and independently
reviewed.
