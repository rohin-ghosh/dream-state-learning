# Experience Model v6 / CompilerGym lifetime v4: normative recipe-feasibility specification

## 0. Status and boundary

This specification authorizes no installation, import, execution, model call,
training, target opening, or GPU run. All `must`, `shall`, and `fail` clauses
are normative for a later authorized implementation. `HARNESS` and
`EXPERIENTIAL` are the only two on-policy systems. This is a one-life,
fixed-recipe wiring/feasibility assay, not evidence of efficacy, causal credit,
mechanism, lifetime growth, arm effect, population behavior, or baseline
superiority. Environment acceptance and instruction-count improvement are not
functional-correctness evidence.

The only candidate substrate is already-local, unchanged official CompilerGym
0.2.5 / LLVM 10 `benchmark://poj104-v1`. A failure rejects this substrate or
recipe for this change; it never permits a patch, download, substitute,
parameter sweep, retry, target-informed choice, or changed threshold.

## 1. Constants, packet, and loss authority

These manifest constants are exact:

```text
acquisition=8; targets=4; sleeps=[4,8]; decisions/task=6
input/call=4096; output/call=256; generated/task=3072; recent-tail=512
ORIENT recalls<=2; row/sequence=768; corpus<=192; view<=64; bucket<=24
old/view=32; new/view=32; presentations/row=24; gamma=0.7; rho=0.5
epsilon_instruction_count=1
LoRA: r=16, alpha=16, dropout=0, q_proj+v_proj in every transformer block
precision=bf16; AdamW(lr=1e-4, betas=(0.9,0.95), eps=1e-8,
 weight_decay=0.01, grad_clip_norm=1.0); no scheduler; accumulation=1
```

At each sleep the adapter is rebuilt from the pinned clean base using a fresh
optimizer. There are no anchor, preservation, KL, instruction, preference,
auxiliary, or non-acquisition rows/losses. Optimizer moments, gradients,
loader/cache state, packed batches, and trainer process are destroyed before
the next inference process.

Canonical JSON is UTF-8, Unicode NFC, the declared schema key order,
causal-order arrays, decimal integers, no insignificant whitespace, and a
final LF. Every artifact ID is `sha256(canonical_json)`. Unknown, duplicated,
missing, or out-of-order fields are invalid. The exact field orders and phase
grammars are owned by `context_visibility_spec.md`.

Every call reconstructs the exact `v4.packet` defined in
`context_visibility_spec.md`, with no provider history, KV/prefix cache, raw
IR, `BitcodeFile`, path, condition, adapter identity, row count, or telemetry.
That companion spec exclusively owns the ordered ORIENT and THINK_ACT JSON
grammars, finite enums, prose caps, parser charges, packet collision order,
event/notebook schemas, and directional reader/writer allowlist. This file
does not define a second abbreviated grammar.

Positive-loss tokens are only the companion spec's finite focus/recall enums,
operation tag, and finite operation arguments, including the legal pass
index. All delimiters, observations, counts, outcomes, note text, raw or
unparsed output, parse errors, rationale, strategy, questions, hypotheses,
predictions, uncertainties, expected effects, and other prose are mask zero.
Rows over 768 tokens after the fixed renderer are rejected as `ROW_OVER_CAP`;
packet overflow and truncation follow the companion spec exactly, and no cap
changes after inspection or outcomes.

## 2. Lifecycle and exact readers/writers

Both systems have the same base, bootstrap, packet, grammar, tools, task
order, logical budgets, append-only ledger, bounded notebook/retriever, and
sleep schedule. EXPERIENTIAL mounts its LoRA below packet assembly; HARNESS
mounts null. HARNESS crosses the same declared sleep boundary and receives a
sleep-accounting receipt but does not compile, train, or create sham adapter
bytes. Natural compute and wall cost are reported rather than padded.

The ledger contains the exact public decision projection, public
observations/outcomes, and note hashes. The notebook contains only accepted
public note text and is retrievable through the common two-record cap. Raw,
unparsed, and private output is discarded. Bounded parsed public prose may
persist as zero-mask provenance. For a selected decision, the compiler may
read only the exact public packet projection that conditioned that decision,
including any recalled public notebook/ledger payload and parsed public
provenance present in that packet; it cannot scan unrelated notebook text or
read private/raw prose, targets, evaluation data, adapter bytes, optimizer
state, or training receipts. Every prose token has loss mask zero.

At task end destroy focus, tail, workspace, environment, task RNG/cache, and
task retrieval cache. Ledger/notebook/immutable receipts persist only within
life as common nonparametric source evidence; only the LoRA is adaptive
parameter state across sleep. Destroy all at life end. Target forks are
read-only and write back nowhere.

| Item | A static | B2 sealer | H/E wake | compiler | trainer | target fork | auditor |
|---|---:|---:|---:|---:|---:|---:|---:|
| public catalog/source/IR/static features | R | R | current projection | - | - | target projection | hashes |
| roles/spares/target IDs | W | R/W seal | - | - | - | router only; model - | R |
| own sealed ledger/notebook | - | - | R/W | selected-decision public projection R | - | R snapshot/W- | aggregate |
| official acquisition outcome | - | - | R/W | R | - | - | aggregate |
| target outcome/descendant | - | B2 reset/baseline only | - | - | - | R/W inside fork | aggregate after quarantine |
| adapter bytes | - | hash | E mount/H null | W candidate | R/W publish | assigned RO mount | receipt/hash |
| labels/telemetry/receipts | - | R | - | receipt W only | R/W | - | R |
| raw/unparsed/provenance prose | - | - | parser transient | - | - | parser transient | - |

Each target fork reads its own system's capped, target-blind life-memory
snapshot at that checkpoint. Thus `D_HE` is explicitly a whole-system
descriptive contrast, not a parameter-only contrast. Off/shuffled forks use
the EXPERIENTIAL snapshot. Every fork cold-starts and is destroyed.

## 3. IrInstructionCountOz score and edge cases

`IrInstructionCountOz` is the sole reward-space identifier. Retain its raw
official reward only for audit. The primary scalar uses its pinned public
`IrInstructionCount` costs. Reset must provide finite integer `I0`, `IOz`, with
`d=I0-IOz>0`; set `B0=I0`. For decision slots `k=1..6`:

| Operation/result | mandatory score handling |
|---|---|
| accepted `ENV_ACT`, finite returned count `Ik` | `Bk=min(B(k-1),Ik)`; valid environment transition |
| INSPECT, NOTE_APPEND, FOCUS_REVISE, malformed output, STOP | `Bk=B(k-1)`; charged; not an environment transition; STOP closes and remaining slots carry `Bk` |
| invalid/rejected ENV_ACT proven by B2 to leave state unchanged | `Bk=B(k-1)`; charged and counted invalid |
| timeout/error/partial result or rejection with unknown/missing/nonfinite/unproved post-state | whole cell `INDETERMINATE` |
| reset/baseline failure, `d<=0`, missing cost, illegal schema | whole cell `INDETERMINATE` |

Therefore reset supplies a valid baseline; non-environment operations and all
worsening valid passes retain it. For a complete cell:

```text
S(i,k)=(I0-Bk)/d
G(i)=sum(k=1..6,S(i,k))/6
```

Neither is clamped. `epsilon_instruction_count=1` only defines a compiler
improvement; it never rounds score. Every named cell has exactly two fresh
cold score realizations `r=0,1`; it is complete only if both complete, and its
value is their arithmetic mean. These are receipts, never inferential samples.

At `c in {0,4,8}`, unweighted over four targets:

```text
D_HE,c  = mean_i(G(E,c,i)-G(H,c,i))
D_off,c = mean_i(G(E-authentic,c,i)-G(E-off,c,i))
D_shuf  = mean_i(G(E-authentic,8,i)-G(E-shuffled,8,i))
```

Any missing/indeterminate constituent makes its contrast indeterminate; never
drop, weight, regenerate, or impute it. Report parse/valid/terminal/STOP/
invalid/timeout/error rates beside, never inside, G.

## 4. Outcome-filter compiler, deduplication, packing, and updates

SLEEP runs only after acquisition tasks 4 and 8. It is model-free and reads
only EXPERIENTIAL's sealed operational acquisition ledger plus public numeric
outcomes/constants. For a task, update `Bt` only on accepted finite ENV_ACTs.
Let `j0=0<j1<...` be exact decision indices with `Bj<B(j-1)` by at least one.
For `jq`, with prior best index `p=j(q-1)`, segment `[p+1,jq]` contains only
parse-valid accepted ENV_ACTs. With `Deltaq=Bp-Bjq` and
`Zq=sum_a gamma^(jq-a)`, every member `a` gets:

```text
credit(a,jq)=Deltaq*gamma^(jq-a)/Zq.
```

Invalid/malformed/timeout/error/non-environment/non-improving actions get no
positive ACT credit. Setup actions get credit only as accepted members of a
later improving segment. A failure is parse-valid rejected/invalid/timeout/
error ENV_ACT or an accepted ENV_ACT in no improving segment. For each failure
`f`, find first later positive-credit action `a`; if present make one REVISE
candidate from finite pre-failure state, failure class, failed pass, and
intervening operational event IDs to `a`'s finite focus/action. Its credit is
`rho*credit(a,jq)`. The failed action is never a target. No negatives,
counterfactuals, or causal-necessity labels exist.

Views are: ORIENT (pre-action state -> finite focus/recall); ACT (pre-action
state+focus -> ENV_ACT(pass)); REVISE (failure construction -> finite
focus/recall+recovered ENV_ACT(pass)). `static_bucket=(view, legal-pass-family,
Autophase-sign-bin)` is formed before outcomes join. Exact dedup key is
canonical rendered `(input,target)` bytes; retain maximum credit, tie by
earliest `(task,decision,candidate_kind,candidate_id)`. Retain all discards and
reasons in manifest.

For each view independently, OLD is all dedup candidates sourced no later than
the prior sleep; NEW is candidates since it. Rank each by descending credit,
ascending `sha256(candidate_id)`, then causal tuple. Take <=32 OLD and <=32
NEW under <=24/bucket. If either has fewer, fill from the other in that same
rank/order/cap. If <64 remain, leave short: no pad, duplicate, cross-view loan,
or quota alteration. Sleep 1 has empty OLD and uses this same fallback. Append
views ORIENT, ACT, REVISE; corpus <=192.

Tokenize selected rows once, make exactly 24 copies each, append zero-loss EOR,
sort `(sha256(row_id),copy_index)`, apply manifest-seeded Fisher-Yates, then
next-fit pack in that order into <=768-token sequences without splitting rows.
One sequence is one optimizer update. No accumulation, early stopping, dynamic
batch size, final-pack drop, retry, or content-dependent resampling. Record
selected rows, copies, positive-loss tokens, pack boundaries, updates, each
gradient norm, finite status, and final tensor hash. Any mismatch/nonfinite/
skipped update fails recipe.

## 5. Binding shuffle

Final shuffled adapter uses authentic selected row inputs and identical
view/row/token/pack/update budgets. Partition by `(view,operation tag,
legal-pass family,Autophase-sign-bin)`, sort by row hash, cyclically permute
finite targets. Every stratum must contain >=2 and every permuted pass differ
from source pass. If any authentic selected row fails that rule, shuffled is
`INDETERMINATE`: no coarser stratum, deletion, reroll, or alternate shuffle.
It is only a post-selection state-operation-binding diagnostic, never a test
of outcome necessity or causal temporal credit.

## 6. Split and target headroom authority

`A_STATIC_SPLIT` reads only already-local public catalog/source/IR/metadata.
It must not import/instantiate CompilerGym or read target costs/outcomes/model
data. Canonicalize IR by removing module IDs/debug/source paths/identifier
numbering and commutative operand order while preserving types/opcodes/
constants/call+CFG edges/memory categories/loop bins. Record source/IR hashes,
normalized callgraph, CFG WL hashes 0--3, opcode/type/layout histogram, loop
signature. Duplicate components are transitive exact source/IR equality,
normalized graph isomorphism, identical normalized signature under identifier/
constant renaming, or exact public vector equality (distance <=0.00).

Relation grouping uses immutable official POJ104 family token with provenance;
otherwise lexicographic deterministic clustering of public feature vectors into
four clusters. Sort `(group_key,canonical_IR_hash,URI)`; select first two
acquisition, first target, then two spares per group, excluding all cross-role
duplicate-component links.

Only non-cognitive `B2_EXECUTABLE_SEALER` may instantiate unchanged local env
before model access. It binds reset/baseline/reward semantics and gets `I0`,
`IOz` for selected targets/spares; it performs no model call, learned action,
or target trajectory. `SCORE_SCALE_HEADROOM` means finite integer costs with
`I0-IOz>=1`: a normalization property, not transfer opportunity/effect. If a
target fails, use first sorted same-group predeclared spare passing every A/B2
rule; after two spares fail, reject. Seal 8/4 split, reports, substitution,
baseline receipts and hashes before model access. Neither A nor B2 ranks using
target action outcomes or calls headroom efficacy.

## 7. Seeds and determinism tiers

Manifest `master_seed` is exactly 64 lowercase hex chars. Each seed is first
64 bits big-endian of `SHA256(master_seed||0x00||domain||canonical_index)`.
Domains: `split(group)`, `acquisition_order(life)`,
`compiler_order(life,sleep)`, `trainer(life,sleep,adapter_kind)`,
`canary(repeat)`, `cold_replay(stage,adapter_kind,sleep)`, and
`score(stage,checkpoint,fork,target,repeat)`. Matched forks share score seed;
each is consumed once, never replaced after crash/error/malformed/timeout.

1. Exact logical: split, ledger projection, labels, rows, dedup, corpus, token
   IDs, copy order, pack plan, seed receipt, manifest are byte-identical on
   identical inputs on every platform.
2. Bound same-stack numerical: manifest pins model/tokenizer/library/driver/
   runtime/GPU count/model/precision/determinism flags/kernels. Two clean
   rebuilds same stack+seed require finite tensors, max absolute LoRA-tensor
   delta <=1e-6 and relative L2 <=1e-6. Bytes reported, not substituted.
3. Same-stack cold behavioral: fresh base+assigned adapter+packet+replay seed
   twice reproduces exact token IDs, parsed operations, event classes, score
   state. Failure is not retried/downgraded. Cross-stack results are never
   pooled or used to loosen a tier. Different score realizations intentionally
   use distinct seeds and need not match.

## 8. B3 scale and Stage-C dispositions

B3 is acquisition-only. For exactly three `canary(repeat)` seeds, cold-load
final authentic adapter and score all eight acquisitions. Let `Cr` be their
unweighted mean G; all complete, and

```text
s_canary=sqrt(sum_r(Cr-mean(C))^2/2); m=max(0.05,2*s_canary).
```

This is a pre-target descriptive scale, not effect variance/power. B3 also
requires nonzero positive-loss gradients, fixed receipts, all determinism
tiers, parser/schema health, and no target access. Failure stops recipe.

Stage C uses one common locked acquisition order (not counterbalancing). At
0/4/8 cold evaluate H and E for four targets; E also off at 0/4/8 and shuffled
at 8 only if Section 5 passes. Same six-decision/call/token/action/retrieval/
packet rules, read-only snapshots, and quarantine apply.

Exactly one integrity-only disposition applies, first applicable:

1. `INTEGRITY_OR_WIRING_FAILURE`: a sealed byte, lifecycle, visibility,
   budget, seed, determinism, split, mount, snapshot, or quarantine invariant
   fails.
2. `INDETERMINATE_PRIMARY`: any required HARNESS, EXPERIENTIAL-authentic, or
   EXPERIENTIAL-off cell is indeterminate after its single frozen execution.
3. `RECIPE_ASSAY_COMPLETE`: every required primary and adapter-off cell
   completes with valid receipts, regardless of the direction or magnitude of
   any score difference.

Binding-shuffled is a secondary construction-dependent diagnostic. If its
semantic derangement cannot be constructed exactly, record
`SHUFFLE_UNAVAILABLE` and omit only `D_shuf`; this does not alter a completed
primary assay. Report `D_HE`, `D_off`, any `D_shuf`, the pre-target scale `m`,
validity/parser/style summaries, neighbor audits, notebook/text use, and all
raw curves without turning any threshold or explanation into a success label.
No p-value, CI, slope, power, efficacy, mechanism, or target-level inference is
produced from this one realization.

## 9. Enforceable staged state machine

Controlling state is canonical JSON:
`{spec_hash,state,permitted_scope_hash,receipt_hashes,review_hash,human_ratification_hash,failure_reason}`.

```text
UNRATIFIED --human ratifies exact v4 spec + A/B1 scope--> A_STATIC
A_STATIC --A receipt + independent review--> B1_IMPLEMENT
B1_IMPLEMENT --fixtures/implementation + independent review--> B2_EXECUTABLE_SEAL
B2_EXECUTABLE_SEAL --B2 receipt + independent review--> AWAIT_GPU_MANIFEST_RATIFICATION
AWAIT_GPU_MANIFEST_RATIFICATION --fresh review + human ratifies exact run bytes--> B3_CANARY
B3_CANARY --B3 receipt + independent review--> C_TARGET_RECIPE_ASSAY
C_TARGET_RECIPE_ASSAY --sealed report--> COMPLETE
any state --missing/failed/mismatched receipt or unauthorized action--> STOPPED
```

`A_STATIC` is read-only static split work. `B1_IMPLEMENT` may create only
fixtures, inspector, harness, compiler, trainer, and tests required by this
spec; it may not execute/model-run. `B2` may execute only disposable unchanged
offline CPU semantic sealer/non-model traces. `B3`/`C` need the separately
ratified exact model/dependency/hardware/run-manifest bytes. `STOPPED` has no
outgoing transition; repair or byte change requires a new change.

Architecture/spec ratification can authorize A through B2 and scoped B1
implementation. It cannot waive the fresh independent review and human
ratification of exact generated run bytes before GPU/model work: that boundary
is required by `AGENTS.md`. This spec requires golden tests for every compiler,
score, seed, visibility, lifecycle, A/B2 authority, cold-load, scarcity,
packing, and disposition edge case above. It does not require a factorial,
powered study, or paper claim; omitted controls must be disclosed.
