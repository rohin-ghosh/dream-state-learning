# PCFL A4 generic-procedure terminal audit and post-reader branch

**Date:** 2026-09-13 PT  
**Role:** independent result audit and full-objective disposition  
**Scope:** documentation only; no builder/runtime source, model, tokenizer,
adapter, benchmark, process, GPU, or remote mutation

## 0. Verdict

The terminal node-2 `A4_GENERIC_PROCEDURE_SMOKE` is a valid failure of its
prospectively bound condition:

```text
native calls:                         21 / 56 maximum
accepted THINK turns:                 13
accepted first THINK:                  5 / 8
THINK + strict terminal histories:     5 / 8
strict terminal routes:                5 / 8
legal routes:                          1 / 8
graph successes:                       1 / 8
joint THINK + strict + graph:           1 / 8
required joint gate:                  >=7 / 8
fits / updates:                         0 / 0
```

Three tasks ended at the 256-token cap on their first generated THINK, so
those partial strings are retained but not accepted or scored. Of the five
tasks reaching a terminal ROUTE, one produced the exact five-edge solution.
The other four remained graph-invalid through an omitted bridge, a synthetic
node-shaped port, a dead-branch splice, or a multi-edge skip.

Therefore the zero-shot clean Qwen2.5-7B PCFL supplied-memory reader ladder is
closed. Do not run the 64-task A4 panel, alter the prompt/grammar/token cap,
salvage the three partial thoughts, or spend another zero-shot 7B retry. This
failure does not contradict the separate narrow EVENT acquisition result; it
means connected writer/use cannot be interpreted through this reader.

## 1. Artifact binding and custody

Authoritative native root:

```text
/localhome/local-rohing/astra_diagnostics/
  pcfl_interface_a4_generic_procedure_smoke_20260913_attempt1/
    A4_GENERIC_PROCEDURE_SMOKE/
```

Bound execution:

```text
model: Qwen/Qwen2.5-7B-Instruct
revision: a09a35458c702b33eeacc393d103063234e8bc28
mount: C0 (no adapter)
GPU: GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0
material: RESEARCHER_AUTHORED_EXCLUDED_ROOT_CEILING_NOT_CHILD
fits / updates: 0 / 0
```

Important hashes:

```text
manifest file:       dcaa30baba08642170d2055d202eb46f62d7b38227320c67e363ed0b6786bf8c
manifest payload:    b70bf3e287e6a13257a3cdb2b203d9f73fb39701058e670752fac64094d589a5
roster file:         448cc570070259a6a056eb23a24873f76411543c6faf5e3dcd4b5b71a2c165f7
roster payload:      813d35459727c5e884ece1b85b888fc861b8e02860805eecd068faa87a38f8e5
report file:         3c1e7d05ae7de78014c0c36de84631235ad5c90203401c2b2d6a699913ceae84
report payload:      59549ac17d2f1c818775e85863ca5d7f8ff8d92f352ce6706b889fb5305d6845
completed file:      d505821d4db40612a85ebb2615795f269ff5a8053f82a49594b9f5e0c16c9fa4
completed payload:   4f34fa05b3950fdec075f7682920d5bd8992fe63b5d5dd1cb21f5363ed6fffc1
outer collection:    e3fdb1d2fec725647778569a830148ec61770ecd7333910c83076b37db5bb041
```

I independently rehashed all `138` files named by `completed.json`: zero are
missing and zero differ. The stage contains exactly 21 attempts, 21 request
sidecars, and 21 complete native request/render/raw/response quartets. The
outer collection names 18 files; their byte lengths and hashes also match
without exception. It reports no errors and zero generation retries.

Native `custody.json` verifies the actor identity, 21 calls, 16,493 prompt
tokens and 2,033 output tokens. `replay.json` reports
`local_replay_valid=true` and deliberately leaves
`native_custody_verified=false` and `full_assay_qualified=false`; those are
not promoted here.

The stage-local completion correctly leaves `gpu_released=false` and
`outer_release_required=true`. The outer evidence closes that obligation:
worker return code `0`, owned process group released, selected GPU UUID empty,
direct queue matched, and CVD clear with the already disclosed non-worker
systemd/PAM service exceptions. Exact controller PID `212829` and worker PID
`212840` are absent. This is terminal custody for an exposed-root diagnostic,
not full-assay or clean-lineage qualification.

## 2. Protocol fidelity and the freeze-timing correction

### 2.1 What was held fixed from A3C

Direct reconstruction of the A3C and A4 rosters verifies all eight case IDs,
root/cell objects, goals, projections, source rows, user bytes, seeds, roots,
CONTINUE bytes and limits are identical. The model, mount, temperature,
parser, route scorer and first-LF transport are also unchanged.

The static grammar is byte-identical to A3C, hash
`855bc2010d90460ba3ad658a47efd031eae97bfef1e92416081789e37bff80f9`:

```regex
(?:THINK [^\r\n]*[^\s\r\n][^\r\n]*|ROUTE N_[A-Z2-7]{10} N_[A-Z2-7]{10} : P_[A-Z2-7]{10}(?:,P_[A-Z2-7]{10})*)\n?
```

It enumerates no concrete ID or answer. Every slot offers the same union;
`external_first_think=false`. The only system-message delta from A3C is one
generic procedure block.

### 2.2 Which generic procedure actually ran

The native roster binds procedure SHA-256
`ff1862745226f4fd1bbf10739eb06895979a3005616adc7fa963ce9db253e48d`:

```text
GENERIC ROUTE PROCEDURE
Treat every EDGE or EVENT as one directed transition: source --port--> destination.
In THINK turns, maintain a candidate path that begins exactly at START and a table of transitions you have actually seen.
Search for a continuous path whose final destination is GOAL. A next transition is usable only when its source equals the current end of that candidate path.
When a branch cannot reach GOAL, backtrack to an earlier branch. Do not include ports from abandoned branches.
Before committing, verify from the visible rows that every adjacent transition joins exactly and that the ordered ports take START to GOAL.
Then emit the exact ROUTE and no explanation.
```

This is byte-identical to the procedure prospectively specified in
`2026-09-13_pcfl_recurrent_reader_successor.md` section 4. It contains no
concrete node, port or event ID, no route length, no worked example, no
candidate, and no answer. It was present in repository history before A4 was
implemented or launched. The actual run therefore has a legitimate
prospective binding.

It is **not** byte-identical to the more explicit block in the later
independent A3C audit, which named `CURRENT NODE`, `PATH`, and `BRANCH STACK`
and separately forbade putting a node field in a port. That later block hashes
to `a2172372fd73c5bbedb6284c7aaf47ef7191793a731f5327c2a704b00c7451ff`.
Repository timestamps settle the chronology:

```text
09:31 PT  earlier generic procedure committed
09:56 PT  A4 source committed
09:57 PT  A4 launched
10:00 PT  later A3C audit / explicit branch-stack wording authored
```

The later bytes cannot retrospectively invalidate the prior prospective run,
and the builder did not drift from its bound bytes. They also cannot justify
another run after seeing A4. Under the no-more-7B-retries rule, treat the
later branch-stack block as an **unexecuted retired alternative**, not as a
missing replication or repair entitlement.

The native grammar backend emitted one preserved warning that a negative
character class was clamped at byte 127. The bound literal sampling policy,
raw token IDs, decoded strings and exact one-line joins all remain present.
The warning does not rescue or erase the failed scores and should remain in
the diagnostic record.

## 3. Physical behavior

Native stop inventory:

```text
first-LF stops:     9
EOS stops:          9
length stops:       3
returned lines:    21 / 21 contain no CR or LF
```

The five non-length tasks emitted 13 accepted THINK turns followed by five
strict ROUTEs. Three tasks exhausted 256 tokens during their very first THINK;
the reducer correctly records `reason=LENGTH`, `score=null`, and zero accepted
THINKs for them. Their raw bytes begin with `THINK`, but a length-limited
prefix is not a complete committed turn.

The extra generic procedure therefore lowered the physical endpoint from
A3C's `8/8` accepted first THINK and strict terminal histories to `5/8`. It
made the model narrate the graph in much greater detail, consuming the whole
turn on three tasks. Increasing the cap now would be post-outcome tuning and
is prohibited.

One length-limited root-3 trace even reaches its goal in prose and begins a
literal `ROUTE` substring inside the still-open THINK line. The static THINK
arm permits arbitrary non-newline content after `THINK`; the system asks not
to combine action and thought, but the grammar does not give an embedded word
operational action status. This is retained evidence of an unfinished
thought, not a hidden successful route.

## 4. Exact task audit

Every scored target requires five consecutive ports. Results by root/goal:

| root/goal | accepted THINKs | terminal | exact disposition |
|---|---:|---|---|
| 0/0 | 0 | none | `LENGTH` on first THINK after tracing the correct trunk through the penultimate node; no final action exists |
| 0/1 | 3 | `P_7MGNA5ALJT,P_4RWKAJVRXP,P_US3ABWJMJ3,P_Z24XENARRH,P_FOPIRGXLPW` | **strict, legal, graph success** |
| 1/0 | 0 | none | `LENGTH` on first THINK while narrating the trunk; no committed route |
| 1/1 | 1 | `P_CU72HSSTHQ,P_PG3IQT75KG,P_Q5KBAFY6SQ,P_CLTAYE7KH3` | strict but omits `P_O66CHZFQQF` between the third and final edges |
| 2/0 | 3 | `P_UKIGM5XADX,P_NXINQGYHG4,P_JKGQFEUMDQ` | strict but replaces two required bridge edges with a nonexistent port made from a node suffix |
| 2/1 | 5 | `P_UKIGM5XADX,P_NXINQGYHG4,P_SL7MPZHV2J,P_BZOTFNJ5FE` | strict but follows a dead branch and then splices the final edge from a different node |
| 3/0 | 0 | none | `LENGTH` after tracing a successful branch and beginning ROUTE text inside the incomplete THINK |
| 3/1 | 1 | `P_Y4YTR3GSDB,P_ELHF2YQISI` | strict but skips the three middle edges |

The one success is real at the task level: its three THINK turns explicitly
inspect both start branches, backtrack from two dead ends, follow five
continuous registered transitions, distinguish the two terminal goals and
emit exactly the correct five ports. It demonstrates that the supplied
procedure can be executed on one exposed task. It is not an experimental
unit, a reliable ceiling, or a near-pass.

The four strict failures reproduce the exact A3C residuals despite more
explicit reasoning: missing bridge state, converting a node to a port,
splicing after a dead branch, and jumping from the first to last edge. The
three truncated traces suggest that verbosity and the per-turn cap mattered,
but that is post-hoc qualitative evidence. The registered gate measures
usable committed behavior, not how plausible an unfinished sentence looks.

Relative to A3C:

```text
                         physical THINK+ROUTE    legal/graph
A3C static typing                 8/8                0/8
A4 supplied procedure            5/8                1/8
```

This does not establish a positive procedure effect. The deterministic
eight-case smoke was a kill gate, not a powered prompt comparison; its joint
success is `1/8`, far below `7/8`, while physical reliability worsened.

## 5. What is now terminal

The following claim branch is closed:

> An untrained clean Qwen2.5-7B actor, given the full exact PCFL graph, can
> reliably construct the required goal route under either typed recurrent
> thought alone or one supplied generic traversal procedure.

Do not:

- run A4 over 64 tasks;
- lengthen the turn, add an example, enumerate IDs, try another grammar, edit
  the procedure, or rescore partial thoughts;
- combine A4 with READ and call a retrieval failure;
- run dynamic LINK/S1/S2 through this actor and treat downstream zero as a
  writer result; or
- fit this route procedure after observing A4 and describe the result as the
  same zero-shot reader condition.

The result bounds this exact 7B configuration, not transformers, larger
models, all possible teaching, or the Dream--LoRA--Think thesis. Atomic
own-EVENT cold acquisition remains separately supported for one source
life/root/fit. Connected carriage, retention and learned use remain open.

## 6. Three honest next branches

These branches answer different questions and must not be substituted for
one another.

### 6.1 Stronger clean resolver

A larger frozen model can be evaluated under the frozen exact-graph protocol
to establish whether PCFL is a usable neural reasoning surface at higher
capability. If it passes, it localizes A4's failure to the tested 7B actor
rather than the graph/scorer. Used identically across memory arms, it could
also serve as a clean semantic resolver for connected-carrier experiments.

But this changes the child model if promoted into the organism, or creates a
two-model architecture if called as an external resolver. Either way it does
not prove the fixed 7B child learned to traverse its experience. Under the
current invariant, a stronger resolver is a **ceiling/diagnostic**, not the
headline organism. Changing the base is material and needs its own decision.

### 6.2 Generic mechanized route-state

A target-blind deterministic controller can consume only arm-visible EDGE or
EVENT rows, maintain current node/path/branch stack, backtrack, verify joins
and emit a route. It must receive no hidden graph, expected path or private
validator state, and it must be byte-identical across AUTH, atom-only,
LINK-cut, wrong-life, no-write and strong active-text arms.

This is the cleanest immediate way to test whether authentic child EVENT/LINK
records were connected, carried, selectively retrievable and retained across
S1/S2 without confounding those writer properties with A4's failed path
bookkeeping. It can support **mechanized connected-carriage** and conditional
semantic-compression evidence.

It cannot support agentic traversal, learned search, recurrent thought, or
later-action intelligence. The route algorithm rather than the child performs
the composition. It is a component assay and causal bridge, not a substitute
for the full objective.

### 6.3 Inherited procedure training

The fixed 7B child can instead be given route-state thinking as a lab-given
birth skill before any PCFL life. A clean version would train only on
topologically varied, target-disjoint generic environments and first-person
thought/action/outcome traces; it would never include these exposed roots,
their identifiers, their exact topology, A2--A4 outputs, target answers, or a
future deployment gym. The resulting child would be frozen before the PCFL
formation roots become visible.

Every memory comparison must inherit the exact same procedure capability.
Then no-write, LoRA sleep and strong text-memory arms differ in experience
storage/access, not in whether one was taught to route. Keeping the inherited
policy and experiential memory separately identifiable or independently
ablatable is preferable; otherwise a cumulative child lineage must preserve
exact corpus and adapter provenance. Fresh disjoint graph families must show
that the inherited routine transfers rather than memorizes one five-edge
surface.

This is post-training/inheritance, not spontaneous discovery and not evidence
that sleep learned the procedure from PCFL. It is also not another A4 prompt
retry: it is a separately named trained-child architecture condition with
new controls. It directly matches the project's parenting/bootstrap premise
that models arrive with lab-given tool and thinking skills, then use lived
experience to grow.

## 7. Recommended full-objective path

Use **two explicitly separated tracks**, with inherited procedure training as
the primary full-objective branch:

1. Preserve A4 as terminal and make no further zero-shot 7B reader call.
2. Use generic mechanized route-state only as a component instrument to finish
   the authentic dynamic-LINK, connected carriage, causal-cut and S2 retention
   questions. This determines whether sleep builds the requisite knowledge
   before asking a neural actor to use it.
3. In parallel, prospectively design one clean inherited-procedure child from
   disjoint data. First prove its route policy on untouched graph families
   without any PCFL experiential write. This is a new learned-skill gate, not
   a rescue of A4.
4. If both tracks pass, combine them: the inherited child forms its own PCFL
   experiences; Dream/Sleep writes them; the same child traverses and acts.
   Use the identical inherited child in no-write and active-text baselines.
5. Only then spend on powered increasing-lifetime and novelty-growth panels.
   A mechanized-only success cannot justify that spend or the whole-agent
   claim.
6. Use a stronger clean resolver only as an upper-bound/localization cell or,
   after an explicit architecture decision, as a separately labeled model
   family. Do not silently substitute it for the child.

Why this order: mechanized route-state cheaply deconfounds the missing writer
and retention evidence, while inherited procedure training is the only one of
the three branches that preserves the fixed 7B developmental thesis and can
ultimately satisfy “the agent traverses its learned knowledge.” A stronger
resolver changes the organism; a mechanized resolver narrows the claim.

The immediate claim boundary remains:

> One clean 7B LoRA acquired and cold-served eight child EVENT records in one
> scoped life, while the same zero-shot 7B actor did not reliably traverse a
> fully supplied graph even under a generic procedure. The writer and reader
> components are therefore separately localized; connected learned use is not
> yet demonstrated.

