# Adaptive-parenting DEV: Gate 0/1 binding successor v1

**Date:** 2026-09-13 PT
**Status:** documentation-only binding candidate

This successor incorporates the independent audit of
`2026-09-13_smallest_adaptive_parenting_dev_after_seq158_seq160.md`.
If ratified, it freezes preparation and no-fit execution for Gate 0 and Gate 1
only. It does **not** authorize source authoring, materialization, model or
parent calls, GPU use, LoRA fitting, Gate 2/3, claims, or release.

Gate 2 and Gate 3 remain closed until a separately qualified writer acquires
its target without destructive interface change and a later execution packet
is accepted. Nothing in Gate 0/1 may be changed after seeing Gate 0 output.

## 1. Exact task family and deterministic certificate

Each `Diagnostic Panels` task contains exactly eight opaque candidate devices
and seven opaque binary probes. The complete candidate-by-probe response table
is public; one uniformly selected candidate is privately active.

Before any child output, a deterministic generator must accept a table only if:

1. every probe has four `0` and four `1` entries;
2. no candidate is identified by zero, one, or two probes;
3. an oracle adaptive policy identifies every candidate in exactly three
   probes;
4. no fixed, nonadaptive set or sequence of three probes identifies all eight
   candidates;
5. after the first outcome, at least two different second-probe choices are
   required across the two posterior branches;
6. candidate, probe, hidden-answer, row-order, column-order, optimal-first-
   probe, and first-outcome positions are exactly balanced in prospective
   blocks; and
7. all opaque IDs are namespace-disjoint, equal-format, and token-length
   balanced under the pinned child tokenizer.

Source and apply tasks are independently generated under that same difficulty
contract. They may not be the same table under renaming, share a hidden row,
share a response code, or share an ID/permutation seed. “Matched” means equal
declared difficulty, not isomorphism.

Two independent deterministic implementations must agree on every table,
oracle tree, answer, and score. The frozen shortcut certificate enumerates
fixed first/last probe, repeated probe, every fixed three-probe sequence,
fixed row/column rank, majority-outcome, choose-without-evidence, every public
ID/order singleton, and relevant pairwise projections. No such policy may
score above `1/2` on any released bank.

Before Gate 0, materialize and hash all banks: 12 calibration tasks, 16 source
tasks, 16 independently generated apply tasks, interface canaries, the
prospective localizer-selection rule, and the sealed 32-task withdrawal exam.
Calibration, source, apply, canary, localizer, and exam namespaces, IDs,
tables, hidden answers, orders, and seeds are pairwise disjoint. No redraw,
stratum substitution, regeneration-until-pass, or task replacement is allowed.

## 2. One-line child controller

The pinned child is one exact revision of `Qwen/Qwen2.5-7B-Instruct`; every
arm is a tensor-identical disposable copy. Bind its tokenizer, chat template,
decode policy, and seed schedule before materialization.

Every child response must fullmatch exactly one raw one-line family:

```text
THINK <one nonempty physical line>
PROBE Q_[A-Z2-7]{10}
CHOOSE H_[A-Z2-7]{10}
```

There is no CR/LF, mixed response, last-line extraction, trimming, fence
removal, ID repair, or semantic rescue. Each task permits at most four THINKs,
three PROBEs, one CHOOSE, eight physical generations, 256 output tokens per
generation, and 2,048 child-generated tokens cumulatively.

A valid PROBE returns only its public `0` or `1` outcome. A repeated valid
probe consumes a probe. CHOOSE is terminal. Unknown IDs, malformed or mixed
turns, cap exhaustion, a fourth probe, or failure to CHOOSE terminate as
failure without retry. THINK content is preserved but not required for world
success and is reported separately.

## 3. One exact adaptive parent

Before Gate 0, bind one strongest feasible parent inside a declared privacy,
latency, and cost envelope: exact model/revision or service-version receipt,
system prompt, tools/files, decode policy, input cap, 384-output-token cap,
retry rule, and endpoint. Parent weights never change. Changing any bound field
creates a new version.

The parent maintains at most 8 KiB of model-visible state:

- four active teaching hypotheses, each containing a process error,
  intervention, predicted effect, observed aggregate outcome, status, and
  evidence references; and
- four recent lesson summaries.

It updates that state only through one prospectively schema-bound patch after
each two-lesson round. A patch may add, revise, retire, or retain one hypothesis
and replace one recent-summary slot. The host validates schema, size, evidence
references, and forbidden fields, then applies it deterministically and
atomically. There is no free-form full-notebook replacement and no host-written
substitute. Invalid patches are not regenerated or promoted and fail Gate 1.

Notebook-visible content may not contain task/probe/device IDs, tables, exact
hidden answers, raw bit sequences, answer positions, future tasks, or generator
surface rules. Current-round exact data may enter the one update call, but only
the validated abstract patch persists.

For each source task, the parent sees only that completed public trajectory,
its hidden source answer, and the pre-round notebook. It never sees any apply
task, apply answer, future task choice, sealed exam material, or the other
source trajectory. The two correction calls in a round are isolated calls from
the byte-identical pre-round notebook. Parent A cannot see correction/source B
and vice versa.

A child-facing correction may discuss process only. It may not name or quote
any ID, table entry, exact bit sequence, hidden answer, row/column position,
concrete next action, or solved path. Exact literal checks and one frozen
independent semantic review occur without rewriting. Failure stops Gate 1 and
prohibits fitting; the message is never regenerated. The reviewer output is
not child-visible.

After both applications in a round, the patch call sees aligned applications
only, as the original design specifies. Therefore Gate 1 tests the whole
adaptive-parent package; it does not isolate whether notebook updating itself
improved teaching.

## 4. Sixteen lessons and three exact apply arms

Run eight presealed two-lesson rounds. In every round:

1. Two fresh-context base children independently attempt source A and source B
   with world feedback only.
2. From the same pre-round notebook, isolated parent calls produce exact
   corrections `cA` and `cB` before either apply task begins.
3. On apply A, `OWN_DIAGNOSIS` receives `cA`, `CROSS_YOKED` receives the exact
   bytes of `cB`, and `NO_PARENT` receives no correction. On apply B, OWN gets
   `cB`, CROSS gets `cA`, and NO_PARENT again gets none.
4. All three tensor-identical copies see the same apply task, paired decode
   schedule, action/thought budgets, and generic invitation to state a plan in
   a THINK turn. The parent never intervenes again.
5. The deterministic world scores the exact final choice and records probe
   validity, repetition, and consistency with public outcomes.
6. Only after both tasks finish may the parent propose its one notebook patch.

Correction bytes are mounted exactly once in each role. No correction is
edited, paraphrased, regenerated, rejected for being generic, or replaced to
increase contrast. OWN and CROSS therefore receive the same correction
multiset and parent-contact budget within every round. NO_PARENT is the
absolute no-teaching anchor and never enters a later fit.

## 5. Prebound future corpus boundary; no fit authority

Gate 0/1 preparation must freeze the deterministic future corpus extractor
even though no fit is authorized.

- `P` contains all 16 OWN application conversations.
- `N` contains all 16 CROSS application conversations.
- Both contain the exact same 16 source struggles as common replay anchors.
- Parent corrections, task text, notebook text, world outcomes, and other user
  messages are chronological inputs with zero loss.
- Only exact accepted child THINK, PROBE, and CHOOSE continuations receive
  loss. Invalid or uncommitted drafts are not repaired into targets. Failed
  but valid behavior is retained without success filtering.
- Tokenizer, chat rendering, EOS, segmentation, truncation, mask, maximum
  sequence length, and target-count receipt are exact and hashed. Worst-case
  legal Gate 1 trajectories must fit without post-outcome truncation.

Loss-masked parent text still conditions the supervised child response; it is
not causally absent. A future result can therefore ask whether behavior learned
under that conditioning survives parent withdrawal.

No fit may occur unless a separately qualified writer recipe is adopted
without consulting P/N outcomes. If it uses ordinary token-mean loss, the
total P:N supervised-target-token ratio must be within `[0.95, 1.05]` or the
version ends `DOSE_MISMATCH`; it may not drop verbose thoughts, resample rows,
or alter masks to pass. Such fits are episode/update-matched, not claimed
exactly token-matched. A per-turn-normalized alternative requires its own
independent writer qualification and a new Gate 2 authorization.

Any future Gate 2 must use preselected source-prefix candidate log-odds for
acquisition. It may not gate on exact regeneration under the seed that created
the original base-child target. Any future Gate 3 is a fresh parent-withdrawal
exam immediately after complete context/state deletion; the no-write filler is
deleted and no delayed-retention claim is permitted.

## 6. Frozen Gate 0 and Gate 1 reducers

### Gate 0: task/interface headroom

On the 12 calibration tasks, require all of:

- at least `11/12` valid complete histories;
- exact success from `3/12` through `8/12`, inclusive; and
- every predeclared shallow/surface policy at most `6/12`.

Above `8/12` is `TASK_SATURATED`. Below `3/12`, below `11/12` valid, or a
shortcut above `6/12` is `TASK_OR_INTERFACE_INVALID`. Either stops the version
before any parent call. No task or prompt is changed.

### Gate 1: immediate adaptive teaching

On the same 16 apply tasks per arm, require all of:

- OWN, CROSS, and NO_PARENT each produce at least `15/16` valid complete
  applications;
- `success(OWN) - success(CROSS) >= 4/16`;
- `success(OWN) - success(NO_PARENT) >= 4/16`;
- both differences are nonnegative in each of two prebound eight-task halves,
  and OWN-CROSS is strictly positive in each half;
- OWN has no more repeated probes, invalid actions, or outcome-inconsistent
  final choices than either comparator;
- all 16 corrections pass literal and semantic hygiene; and
- all eight notebook transitions pass exact patch/cap/forbidden-field checks.

Any miss is `IMMEDIATE_ADAPTIVE_TEACHING_NOT_SHOWN`. Preserve every task and
message, stop before fitting, and do not tune task, parent, notebook, prompt,
sampling, thresholds, or reducer inside this version. CROSS harm cannot rescue
a failed OWN-versus-NO_PARENT contrast.

## 7. Call, resource, custody, and quarantine bounds

Under the frozen eight-generation child cap:

| no-fit stage | maximum child calls | primary parent calls |
|---|---:|---:|
| Gate 0: 12 tasks | 96 | 0 |
| 16 source struggles | 128 | 16 corrections |
| 16 apply tasks x 3 arms | 384 | 0 |
| eight notebook transitions | 0 | 8 patches |
| **Gate 0/1 total** | **608** | **24** |

Permit at most 24 additional independent semantic-review calls, for an overall
external parent/reviewer ceiling of 48 calls. CPU literal/schema checks do not
consume that allowance. Exact realized prompt/output tokens and wall time are
reported separately. Gate 0/1 receives a conservative hard ceiling of four
aggregate A40-hours for child inference; the final execution packet must also
bind the parent's API or local-serving monetary/GPU cap. Unused capacity does
not authorize fits or more tasks.

Every context is disposable. Preserve raw model messages, token IDs, task
bytes, public outcomes, parent inputs/outputs, notebook proposals/promotions,
checks, seeds, and reductions under immutable attempt roots. No Gate 0/1 child
state, KV, notebook, or adapter may enter PCFL, another clean childhood, or a
deployment gym. Stored P/N corpus material remains quarantined to this DEV and
may be used only by a separately authorized Gate 2 descendant. Destroy the
model-visible parent notebook after terminal reduction; reuse would be a
declared parent bootstrap and new lineage.

The child root—not tasks, turns, halves, or decode calls—is the replication
unit. This version has one exploratory child/parent lineage.

## 8. Narrow release boundary

Passing Gate 0 supports only that the frozen Diagnostic Panels bank has usable
headroom and interface validity for this child.

Passing Gate 1 supports only:

> In one predeclared exploratory Diagnostic Panels lineage, process corrections
> from the exact answer-aware adaptive parent improved immediate fresh-task
> success relative to both crossed corrections and no parent while present.

It does not establish parameter learning, SLEEP, persistence, delayed
retention, improved notebook adaptation, general parenting, metacognition,
PCFL traversal, continual improvement, or the whole organism. Gate 0/1 success
licenses preparation of a later Gate 2 proposal only; it does not license a
fit.

## Ruling

After ratification and separate execution authorization, this successor is
**GO only for exact preparation and no-fit Gate 0/1 execution**. It remains
**NO-GO for Gate 2, Gate 3, any LoRA/adapter work, and every durable-parenting
claim** until the independent writer prerequisite and a new bound packet are
accepted.
