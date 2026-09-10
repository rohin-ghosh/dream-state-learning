# Randomized diagnostic-action causal-cascade contract

Status: proposal only; no execution authority.

The filename is retained for continuity, but the descriptive B3 object below is
a randomized chain-complete causal-cascade contrast, not a formal natural
indirect effect or general causal-mediation estimand.

## 1. Causal graph

The paper's distinctive estimand is a randomized pulse through the complete
action--experience--memory loop:

```text
common pre-fork public state S_k and authentic prior memory M_k^-
                              |
       three-clone intervention; opaque label/order randomized
              /              |               \
         AUTHENTIC          TWIN             NULL
              \              |               /
                  one diagnostic action A_z
                              |
                  ordinary public outcome O_z
                              |
       assigned memory unmounted; branch process/cache reset
                              |
   common precommitted Dream-1 bytes + M_k^- + branch event (A_z,O_z)
                              |
             model-owned Dream-2 revision and sleep
                              |
                 branch-specific compiled delta D_z
                              |
       common evaluation memory M_k^- plus D_z; no assigned Z memory
                              |
                  later sterile fresh action Y_z
```

The treatment may affect the later outcome only by changing the diagnostic
action and its public consequence. The original assigned twin/null object may
not survive into Dream-2, the delta compiler, the later reader, the candidate
catalog, the resolver cache, or the evaluation process.

## 2. Fork construction

At each of `1.5`, `3`, and `6 L_native`, every one of the eight B3 roots contains one
presealed causal-cascade fork on **each of its two counterfactual twin sides**. For
each `(root, side, checkpoint)` fork, the byte-identical state is cloned into
exactly three isolated branch processes. The three treatments are installed
exactly once:

```text
AUTH  = that side's authentic checkpoint memory M_k^-
TWIN  = the paired twin side's checkpoint memory under the same interface
NULL  = the constant-shape registered empty-memory interface
```

All three clones therefore run; treatment inclusion is not randomized between
roots. Enumerate the six lexicographic permutations of `(AUTH,TWIN,NULL)` as
`PERM6[0..5]`. For each preassigned `(root,side,checkpoint)`, derive separate
indices from the first eight bytes of SHA256 namespaces `MED_OPAQUE_LABEL` and
`MED_EXECUTION_ORDER`, interpreted as unsigned big-endian integers and reduced
modulo six. The treatment-to-opaque `B0/B1/B2` map and execution order use those
distinct indices. This exact within-root fork randomization is not a population-
balance or inference device. The root manifest and exact `MED_ROOT_SUMMARY_V1`
record every assignment, order, clone receipt, failure, and terminal component;
label mapping is independent of order. Both are concealed
from the diagnostic actor, environment, delta compiler, target constructor,
and scorer until terminal analysis. The assigner alone holds the treatment
map. Failed or missing clones remain assigned zero-valued observations.

The root protocol hash derives disjoint counter-based RNG namespaces for
world/twin construction, opportunity allocation, target allocation, opaque
label mapping, execution order, model sampling, evaluation, and statistics.
The one diagnostic-actor draw uses common random numbers across the three
treatments from
`SHA256(protocol_hash || root_id || side || checkpoint || "ACTOR_CRN" || actor_call_index)`;
execution order cannot change it. Environment dynamics are deterministic conditional on
the selected action and side. Same-event evaluation/delta lanes use common
evaluation seeds keyed analogously with `EVAL_CRN`. No post-fork cognition seed
may contain or be derived from treatment identity, opaque `B0/B1/B2` label,
assignment-map position, execution order, assigned object/capability handle, or
any hash or metadata descended from assignment.

Every claim-bearing P1 stochastic compiler comparison instead uses the exact
pre-fork common-random-number function

```text
P1_COMPILER_SEED(w,s,k,g,i) =
  SHA256(protocol_hash || "P1_COMPILER_CRN_V1" ||
         root_id || side || checkpoint || pair_group || sample_index)
```

with length-prefixed canonical UTF-8 fields, unsigned 64-bit big-endian
`sample_index`, and a Stage-A2-pinned digest-to-provider-seed conversion.
Here `side` is the fixed recipient/evaluation twin side for the paired
contrast, never the side from which an intervened outcome packet was sourced.
`pair_group` is presealed before treatment assignment and is exactly one of
`MAIN_FORK` or `COMMON_HISTORY`; it is not a lane, method, branch, treatment,
or opaque-label identifier. All AUTH/TWIN/NULL Dream-2 compilers in a
`(w,s,k)` main fork share `MAIN_FORK` draws index by index. At `3L`, intact
`SELF-DELTA` is compiled once with those same `MAIN_FORK` draws and is reused;
`SELF-TWIN-OUTCOME` uses those identical draws while only the complete public
outcome packet changes. `SELF-SEM-CUT` and `SELF-SEM-SHAM` are deterministic
post-compilation transforms of that one intact delta and make no compiler
draw. Any stochastic common-history compiler condition entering `r_6,w` uses
the same `COMMON_HISTORY` draw at a given sample index; deterministic
conditions consume no draw. Thus P1 paired lanes differ only in their intended
input/representation intervention, never in compiler randomness.

Optional independent draws use
`SHA256(protocol_hash || "DESCRIPTIVE_COMPILER_V1" || root_id || side ||
checkpoint || presealed_descriptive_condition || sample_index)`, may not use
assignment metadata, are labeled descriptive, and cannot enter P1 or choose a
P1 retry/output. Every call starts from clean process/cache state, and the
manifest records each canonical key, seed, pair group, call index, input hash,
and output hash. The common pre-fork seed is fixed infrastructure, not a
treatment descendant; after unmount, the branch public action/outcome is the
only branch-varying input permitted to reach the delta compiler.

The diagnostic opportunity offers exactly four legal probe actions. The
offline certifier establishes before any model call that:

1. exactly one probe resolves the registered missing dependency needed by a
   later analogous target;
2. every probe is surface-plausible and has the same public request shape and
   declared cost;
3. the authentic and twin memories imply different uniquely informative
   probes, and the same registered probe has a presealed twin-side outcome
   intervention when used in the `3L` reconsolidation sentinel;
4. null-memory target-only Bayes probe value is at most `0.25`;
5. the probe outcome is ordinary public evidence, not a correctness label;
6. the later target has fresh handles and an unseen composition that requires
   the branch outcome plus at least two other provenance-distinct public events;
7. without the acquired decisive outcome, the typed later-action controller
   remains at or below its registered headroom ceiling.

One action is executed. Malformed, illegal, deferred, timed-out, or absent
actions remain zero-valued assigned outcomes; no replacement or retry occurs.

## 3. Prospective/revision chronology

Before assignment, the model-owned compiler has committed a fixed-shape
Dream-1 prospective object over all four public probe handles. It may predict
one local public consequence per probe and cite only `M_k^-` plus public
pre-fork roots. The four-prediction envelope is fixed and charged for every
branch; it is not chosen around the later action or target.

After the action outcome is sealed:

1. the exploration memory object and its process are destroyed logically;
2. all branch actor conversations, workspace, reader state, candidate order,
   KV/prefix cache, timing state, and error state are reset;
3. Dream-2 receives the exact common Dream-1 bytes, the common authentic
   `M_k^-` read interface, and only that branch's raw public action/outcome;
4. Dream-2 chooses `RETAIN`, `REVISE`, `ABSTAIN`, or a bounded local addition;
5. the truth-blind sleeper performs syntax, taint, provenance, literal
   canonicalization, lineage-local lifecycle updates, semantic-equivalence
   indexing without instance merging, supersession, and fixed view realization
   only under the Stage-A2 `SELF_AGGREGATION_V1` reducer; every proposal,
   revision, addition, and status-only slot has a unique `record_instance_id`,
   disagreeing or duplicate valid samples remain separately admitted,
   malformed/abstained/failed source slots remain fixed-shape, and no
   correctness/majority/result selection is permitted; and
6. the resulting delta `D_z` is sealed before the sterile target is rendered.

The P1 fork uses the same Stage-A2 sample reducer/admission and
checkpoint-lifecycle/constant-shape reader policies as ordinary SELF. Exact
target/truth/scorer/comparator/DEV-result mutations must leave the reducer,
admission, slot shape, and reader-visible bytes unchanged when the allowed
public event is held fixed. The ordinary cadence artifact does not add a
branch-specific call: this presealed sentinel chronology is separately
enumerated in the same cognition manifest before B0.

Direct witnessed atoms from the deterministic extractor may enter `D_z` as
public support, but no witnessed atom is keyed to or sufficient for the later
integrative target. Higher-order claims remain model-owned and must follow the
prospective/revision contract. The mechanical compiler deterministically
constructs its own `D_z` from the same public event and remains a labeled
alternative/control unless a genuine upper-bound property is separately
proved.

At the predeclared `3 L_native` sentinel on every B3 root and twin
side, one sealed branch event is copied into the following target-blind delta
lanes against the identical authentic prior:

| Lane | Delta input and permitted durable content |
|---|---|
| `RAW-AO` | canonical raw public `(before,A,after,O)` event only; no witness extractor or SELF semantics |
| `ACTION-ONLY` | identical action/provenance envelope with outcome and after-state replaced by constant-shape `OUTCOME_WITHHELD`; this is the registered outcome-drop lane |
| `WITNESS/MECH` | deterministic witnessed atoms and frozen separating-panel relations only; no model-owned semantic record |
| `SELF-DELTA` | the same witnessed atoms plus model-owned Dream-2 semantic records and statuses |

The selected probe identity, common prior, target set, reader schema,
query/operation/action caps, and evaluation seeds are identical across lanes.
The `RAW-AO` reader may return one canonical public event envelope per call
under the same query-count and returned-byte limits; it is not forced through a
one-relation parser or denied legitimate handle-based retrieval. The
`WITNESS/MECH` and `SELF-DELTA` readers return their declared one-local-relation
records. Interface differences and actual work are reported rather than
hidden under a false equal-interface claim.
All actual preprocessing, compiler, storage, index, reader, and resolver work
is charged; no equality-of-compute claim is inferred.

Two further interventions identify outcome and model-owned-content necessity:

1. `SELF-TWIN-OUTCOME` executes the **same probe identity** on the paired twin
   side in an isolated ordinary environment clone. It replaces the complete
   public outcome packet—after-state, observation, cost, and terminal flags—in
   the same SELF chronology while holding the before-state, probe identity,
   authentic prior, Dream-1 bytes, all other Dream-2 input bytes and their
   order, budgets, and seeds common. It never substitutes hidden truth or a
   scorer label.
2. `SELF-SEM-CUT` uses the executable target-blind rule in
   `compiler_memory_contract.md`: remove every branch-Dream-2 `SELF_SEMANTIC`
   record whose validated provenance contains the branch event and at least
   one earlier distinct public event. The rule, canonical serializer, DSL cap,
   tombstone, failure behavior, and sham matching/tie rule are hash-frozen at
   Stage A2 before SELF output. The sham removes the same record count from
   records that do not cite the branch event and matches serialized lengths;
   an unavailable cut or sham is a zero-valued assigned failure. Witness atoms
   and their actual returns, reader/index/candidate shapes, call slots and
   maxima, byte envelope, operation caps, seeds, and charged resource slots
   remain fixed. Removed SELF semantic bytes and resulting adaptive query bytes
   do not remain fixed: a cut-slot lookup returns `SEMANTIC_WITHHELD`. No target
   allocation, target result, scorer output, or hidden correctness selects a
   record. Neutral padding is taint-free and cannot become a key or
   lifetime-growth evidence.

The incremental reconsolidation contrast is failure-inclusive value on the
integrative targets. SELF must directionally exceed `RAW-AO`, `ACTION-ONLY`,
and `WITNESS/MECH`; intact SELF must exceed its decisive semantic cut more than
the sham; and authentic-outcome SELF must exceed same-probe twin-outcome SELF
in the certified direction. Otherwise the result is action-conditioned public
event memory or keyed replay, not evidence for model-owned reconsolidation.

The separate `3L` common-history representation sentinel feeds byte-identical
public histories to native raw RAG, `WITNESS-KV-NA`, `WITNESS-KV-REC`, MECH,
linked memory, rolling summary, generic family-blind SELF, and a labeled
class-informed SELF ceiling. Every condition receives the same one ordinary
and one integrative target per twin side, common evaluation seeds, and matched
online caps: six reader calls, 4,096 aggregate UTF-8 query bytes, 16,384
aggregate UTF-8 returned bytes, twelve resolver operations, and the presealed
target action cap. They share the frozen query grammar but keep their
backend-native records, catalogs, indexes, serializers, and return interfaces;
all are frozen and fully reported. Byte-identical catalog/return bytes are
required only for registered matched interventions and the WITNESS-KV-NA/REC
pair, not across representations. The nonadaptive policy commits all queries and
its read count/stopping rule before the first return; it may use the returned
fixed batch for its terminal action but cannot query again. The recurrent
policy uses the identical known-good atoms but may condition later queries on
earlier returns. This sentinel isolates representation/compiler use; separate
on-policy histories are never used to claim a compiler effect.

## 4. Later evaluation

The evaluation installer constructs exactly:

```text
EVAL_MEMORY(z) = immutable authentic prior M_k^- + branch delta D_z
```

It rejects any byte, adapter, index entry, candidate, cache, optimizer state,
filename, receipt, or timing dependency descended from assigned exploration
memory other than the public `(A_z,O_z)` event and its valid compiled
descendants. The later target runs in a fresh process, receives the same public
goal/state and budgets across branches, and cannot write to any life store.

Each treatment clone receives exactly two presealed `INTEGRATIVE_MED_D4`
targets after its delta freezes. Every same-event delta/cut/outcome lane at
`3L` receives the identical two targets for that twin side. Target correctness
is purely world/action-defined; no SELF record or read receipt is part of
success. For each assigned `(w,s,k,z,t)` chain define binary links and their
cumulative products:

```text
h1 = 1 iff the executed probe is the presealed unique side-valid informative probe
h2 = 1 iff exact engine information gain >= the presealed positive IG_MIN[w,s,k]
h3 = 1 iff its public outcome newly supports the presealed decisive mapping
h4 = 1 iff a target-blind branch-event descendant is admitted and returned
h5 = 1 iff the executed certified working path uses that returned descendant
h6 = 1 iff the legal target trajectory executes and earns terminal success
C_l[w,s,k,z,t] = product(h_r, r=1..l), for l=1..6
```

`IG_MIN` and the exact path-use predicate are computed from the sealed world
before any memory/compiler output. `h4` is representation-neutral: the
descendant may be raw, witness, mechanical, linked, rolling, or SELF typed. A
missing, malformed, failed, unreadable, or unexecuted link is zero. Thus any
earlier-link failure zeroes every later cumulative score even if a later action
is lucky. Raw terminal `h6` is still reported separately. These cumulative
products are the only outcomes used for the randomized causal-cascade link
contrasts; they are not formal mediation functionals.

## 5. Interventions and shams

At the `3 L_native` sentinel, also run:

- authentic versus twin exploration assignment;
- authentic versus null exploration assignment;
- a binding-only trio `BIND-AUTH`, `BIND-TWIN`, and `BIND-SHAM` installed into
  isolated copies of the same authentic pre-fork state; and
- decisive acquired-event removal from `D_z`; and
- an equal-byte nondecisive delta removal.

The binding-only installer starts from one canonical authentic checkpoint
memory projection. `BIND-TWIN` applies the presealed twin involution only to
the opaque values of the certified decisive binding records; `BIND-AUTH`
leaves those values intact; `BIND-SHAM` applies the identical number and byte
shape of substitutions to presealed nondecisive bindings. Record IDs, public
provenance/support flags, relation types, counts, serialized lengths, order,
index/candidate entries, interface, query/operation/action caps, and seeds are
otherwise byte-identical. All three diagnostic actors see opaque condition
labels. Each executes one probe; no branch is dropped or retried. The
certifier requires `BIND-AUTH` and `BIND-TWIN` to redirect toward their
corresponding unique informative probes while `BIND-SHAM` preserves the
authentic direction. This is the binding-only attribution sentinel. The
AUTH/TWIN/NULL main fork remains a whole-memory treatment and is never
misreported as binding-only.

These whole-event removals are distinct from the SELF-semantic decisive/sham
cuts above: the former tests dependence on acquired evidence; the latter holds
public witness content fixed and tests incremental model-owned semantics.

The authentic/twin contrast must redirect the probe toward the corresponding
world-valid dependency. The binding-only trio must have the registered probe
directions, the matched-action public outcome packet must change the compiled
delta/later action in the certified direction, and decisive removal must
reduce later value more than the sham. Arbitrary behavior change is
insufficient.

## 6. Exact root-level chain-complete causal-cascade summary

For each cumulative link `l`, first average `C_l[w,s,k,z,t]` over the two
assigned integrative targets, then define:

```text
d_l,w = mean over s in {0,1}, k in {1.5,3,6} of
          C_l[w,s,k,AUTH] - 0.5*(C_l[w,s,k,TWIN]
                                 + C_l[w,s,k,NULL])
for l=1..6
```

At `3L`, each same-event lane value uses the same common upstream `h1*h2*h3`
and its own representation-neutral `h4*h5*h6`, then averages the two targets
and twin sides. Let that full cumulative value be `C6_lane`. Common-history
`H_b` is failure-inclusive world/action value on the integrative target for
condition `b` under the exact common online budget; those histories do not
contain a randomized diagnostic chain. Define six reconsolidation/compiler
contrasts:

```text
r_1,w = C6_SELF - C6_RAW_AO
r_2,w = C6_SELF - C6_ACTION_ONLY
r_3,w = C6_SELF - C6_WITNESS_MECH
r_4,w = (C6_SELF - C6_SELF_SEM_CUT)
        - (C6_SELF - C6_SELF_SEM_SHAM)
r_5,w = C6_SELF_AUTH_OUTCOME - C6_SELF_TWIN_OUTCOME_SAME_PROBE
r_6,w = H_GENERIC_SELF - max_b(H_b)

b ranges over {RAW_RAG, WITNESS_KV_NA, WITNESS_KV_REC,
               MECH, LINKED, ROLLING}
```

For the binding-only trio, let `p_auth` and `p_twin` be the presealed
side-specific informative probes. The target-only four-probe Bayes value is
`.25`. Define three root scores:

```text
b_AUTH,w = mean_s(1[A_BIND_AUTH=p_auth]) - .25
b_TWIN,w = mean_s(1[A_BIND_TWIN=p_twin]) - .25
b_SHAM,w = mean_s(1[A_BIND_SHAM=p_auth]) - .25

P1_w = min(d_1,w,...,d_6,w,
           r_1,w,...,r_6,w,
           b_AUTH,w,b_TWIN,w,b_SHAM,w)
```

`P1_w` is the single root-level P1 observation. Sides,
checkpoints, treatments, lanes, cuts, targets, links, calls, and seeds remain
nested. There are no external positive-direction gates inside this descriptive
root summary: every future-claim causal link, binding intervention,
outcome/semantic intervention, and strongest common-history comparison is
inside the root minimum. Component/link means,
raw terminal success, nonadaptive-versus-recurrent behavior, and generic-
versus-class-informed SELF are always reported descriptively. If the Stage-A
nonadaptive atomic controller solves, the construct stops. If recurrent KV,
linked/rolling, raw, or MECH matches or beats generic SELF, `r_6,w` cannot be
positive, so the descriptive P1 cannot motivate a future model-owned
offline-compilation/reconsolidation claim. No B3 P1 value is population evidence.

Any future separately ratified associative-LoRA proposal must define a true
substrate cut; citation or reader masking is insufficient. Whole-life
authentic/twin and decisive-binding/sham transport comparisons may appear only
as component controls, not as the associative successor's headline.
