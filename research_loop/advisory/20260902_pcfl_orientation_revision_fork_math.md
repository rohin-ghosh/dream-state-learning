# PCFL-Compose public-prefix-identical orientation-fork mathematics

**Date:** 2026-09-02  
**Status:** read-only mathematical advisory. This memo does not modify or
ratify the proposed experiment, authorize implementation or a CPU/model/GPU
run, change a prompt/schema/model, or license a scientific claim.

## Dispositive result

**Yes.** The sparse `S_6` double-star admits two presealed, valid hidden
continuations with:

- the same 13 raw public tree events byte-for-byte;
- one shared Dream-1 execution, hence identical Dream-1 inputs, invocation
  seed, trace, candidate packages, A predictions, commitment bytes, and
  commitment hash;
- identical announced A action requests and A before-trays; but
- different raw A after-trays which make exactly one of the two registered
  composition orientations consistent with the common tree.

Disjoint B operators can be forced to differ. More strongly, the D4 target
can have byte-identical start, goal, ordered menus, handles, and budgets in the
two continuations while the uniquely correct action label flips at every
stage. The correct public tray trajectory can remain identical: only the
emitted `USE` action bytes need differ.

This is not yet a property of the current proposed protocol bytes. The current
`experiment_spec.md` samples one orientation per root and constructs only the
`2^4` stem-row orbit at fixed orientation. Its ordinary primary/antipode lives
have different source events and independently generated Dream-1 traces. They
test life binding, not the effect of raw A while holding the entire pre-A
public history and Dream-1 object fixed. Therefore the mathematics validates
the required repair in the semantic-representation adjudication, but the
proposal still needs a material, ratified construct/certifier addition before
using the phrase **causal self-revision**. Without it, the exact description is
only “a second post-A Dream pass.”

## 1. General construction

Use the repository convention: a tuple `g=[g(0),...,g(5)]` maps the object in
slot `s` to slot `g(s)`, and `gh` means that `h` acts first. Let the common
double-star tree expose

```text
M   = t[u0,j0]
R_i = t[i,j0]
C_j = t[u0,j].
```

Write the gauge-normalized relatives

```text
r_i = M^-1 R_i,        c_j = M^-1 C_j,
```

so `R_i=M r_i` and `C_j=M c_j`. Define two hidden worlds from these same
public tree operators.

```text
V_BA: a_u0=e,  a_i=r_i,    b_j0=M,  b_j=M c_j,
      t[i,j]=b_j a_i.

V_AB: a_u0=M,  a_i=M r_i,  b_j0=e,  b_j=c_j,
      t[i,j]=a_i b_j.
```

On every one of the 13 tree edges both worlds return exactly

```text
t[u0,j0]=M,   t[i,j0]=M r_i,   t[u0,j]=M c_j.
```

On an omitted edge they instead complete the tree as

```text
P_BA(i,j)=C_j M^-1 R_i=M c_j r_i,
P_AB(i,j)=R_i M^-1 C_j=M r_i c_j.
```

Thus an omitted chord distinguishes the continuations exactly when

```text
c_j r_i != r_i c_j.
```

For A=`{(u1,j2),(v1,j2)}`, require this inequality for both `r_u1`
and `r_v1`. For the disjoint B=`{(u2,j3),(v2,j3)}`, require it for both
`r_u2` and `r_v2`. If all four inequalities hold, both A outputs and both B
outputs differ across the continuation fork. One discriminating A chord would
be mathematically sufficient; requiring both preserves the symmetric two-edge
schedule and removes an avoidable null item.

### Gauge and noncommutation conditions

The equality of the tree prefixes is not a gauge artifact. Gauge changes
alter hidden factors but leave every completed `t[i,j]` invariant. Once a
chord has `M c_j r_i != M r_i c_j`, no legal gauge can make the two chord
operators equal.

Conversely, the fork is behaviorally invalid if all relevant normalized row
and column relatives commute. The math audit's full degeneracy condition is
that the two completed tables are identical iff every row-relative commutes
with every column-relative. In that case an “orientation” bit is only hidden
parameterization, no raw A can select it, and no B/action difference can be
attributed to it. The generator must reject such roots before any public byte
or model output exists.

## 2. Strong target-label reversal

For D4 stage `l`, a sufficient condition for an exact swap of the two target
action bindings is

```text
r_vl = c_jl r_ul c_jl^-1
and
[c_jl^2,r_ul]=e.
```

Choosing `c_jl` to be an involution makes the second condition automatic. It
then follows that

```text
P_BA(u_l,j_l) = M c_jl r_ul = M r_vl c_jl = P_AB(v_l,j_l),
P_BA(v_l,j_l) = M c_jl r_vl = M r_ul c_jl = P_AB(u_l,j_l).
```

If `[c_jl,r_ul] != e`, the two menu actions are distinct. Consequently a goal
defined by the BA `u_1,u_2,u_3,u_4` trajectory is reached in the AB
continuation by `v_1,v_2,v_3,v_4`. The target start, goal, menu order, public
labels, object handles, budget, and renderer can all be byte-identical. At
each correct stage the physical operator and resulting tray are also
identical, while the action string changes from
`USE(u_l::j_l)` to `USE(v_l::j_l)`.

This condition is sufficient, not necessary. A generic accepted double-star
could instead be rejection-searched for two different four-action sequences
whose total BA and AB operators agree. The conjugacy construction is better
for a certifier fixture because it proves stagewise equality and exact action
redirection rather than only endpoint collision.

## 3. Explicit nondegenerate `S_6` witness

The following is one exact fixture. Compact string `g0g1g2g3g4g5` denotes the
serialized tuple `[g(0),g(1),g(2),g(3),g(4),g(5)]`. Let

```text
M = 012354

l    c_jl    r_ul    r_vl=c_jl r_ul c_jl
1    210345  045132  542130
2    312054  430125  103542
3    012543  301254  501432
4    534120  015234  241305
```

Every `c_jl` is an involution. The shared 13 tree operators are:

```text
edge       operator       edge       operator
(u0,j0)    012354
(u1,j0)    054132         (v1,j0)    452130
(u2,j0)    530124         (v2,j0)    103452
(u3,j0)    301245         (v3,j0)    401532
(u4,j0)    014235         (v4,j0)    251304
(u0,j1)    210354
(u0,j2)    312045
(u0,j3)    012453
(u0,j4)    435120
```

The registered A operators are all branch-discriminating:

```text
edge       V_BA       V_AB
(u1,j2)    345102     154023
(v1,j2)    542103     152403
```

The disjoint B operators are also all branch-discriminating:

```text
edge       V_BA       V_AB
(u2,j3)    540123     530421
(v2,j3)    104352     103254
```

The four target menus swap exactly:

```text
l    V_BA(u)   V_BA(v)   V_AB(u)   V_AB(v)
1    254130    450132    450132    254130
2    403125    130542    130542    403125
3    401235    301542    301542    401235
4    430512    523140    523140    430512
```

Applying stages 1 through 4 in order, the BA `0000` (`u,u,u,u`) goal operator
is `023145`; AB `1111` (`v,v,v,v`) applies the same operator stage by stage.
For completeness, the 16 BA full-sequence operators are

```text
0000 023145    0001 302451    0010 203541    0011 032154
0100 135024    0101 421305    0110 531204    0111 124035
1000 325140    1001 201453    1010 301542    1011 234150
1100 534021    1101 125304    1110 134205    1111 425031
```

They are pairwise distinct. The complete set of shorter prefix operators is

```text
L1: 254130 450132
L2: 352014 024351 254013 421350
L3: 251403 521304 413250 314520 153402 124305 310254 410523
```

It excludes `023145`. Pairwise uniqueness of the length-four list means no
wrong prefix has a legal recovery to that goal; exclusion from the shorter
list means no early `LOCK` succeeds. Fresh distinct tray handles turn every
operator inequality above into an after-tray byte inequality.

This fixture proves existence. It is not a substitute for total generator
certification over every registered root and orbit member.

## 4. Exact byte boundary and chronology

The clean implementation is a **single common trace followed by a presealed
counterfactual fork**, not two attempts to rerun Dream-1. Same model input and
seed do not by themselves guarantee bit-identical inference on every runtime.

At T0, seal both complete continuations and their certificates without using
any later model output. At T1--T2, render the tree once, invoke Dream-1 once,
hash its terminal artifact, and clone that immutable artifact into both
branches. Then expose the two different A outcomes.

The following bytes can and should be literally identical across the two
factorized branches:

- public root/life identifier, nonce label map, public schedule, event IDs,
  time/order fields, renderer version, and all nonprivate metadata;
- every byte of all 13 tree event objects: action string, before-tray handles,
  after-tray handles, separators, encoding, and line endings;
- the full rendered Dream-1 prompt and every recurrent Dream-1 input/state;
- Dream-1 invocation seed, model/revision/runtime fields, operation trace,
  reads, workspace, candidate order and bytes, A prediction bytes, terminal
  commitment, and its hash;
- A request IDs, ordered action strings, before-tray handles, request shape,
  schedule, and deadline; and
- B request IDs/actions/before-trays, Dream-2 template/static instruction,
  eligible-handle shape, budgets, model/revision, and the presealed paired
  seed-by-role.

At T3, only the A `after` tray arrays need differ at the semantic public-event
level. Any enclosing checksum, content hash, byte count, or downstream prompt
hash derived from those arrays must consequently differ and must not be
falsely included in the equality claim. A full rendered Dream-2 input cannot
be byte-identical because raw A is its causal treatment; it should differ only
in the A outcome subtree and mechanically derived hashes. The static prompt
template, field layout, budgets, B request, and seed remain fixed.

The exact public event renderer obeys

```text
after[g(s)] = before[s].
```

Therefore copying the same fresh, distinct before handles and the same tree
operator makes each tree event byte-identical. Different A operators
necessarily give different after arrays. No `MATCH`, `MISMATCH`, orientation
name, candidate rank, repaired prediction, truth bit, or scorer artifact may
enter either Dream-2 branch.

Correct branch following is stronger than output inequality. Require the
Dream-2 B predictions to equal the branch's different B after-trays, and
require target actions to equal the branch's complementary registered
sequence. Two arbitrary different B strings or action traces do not establish
revision. If the scientific question is selection rather than repair, also
require the one common `K=2` Dream-1 commitment to contain both exact A
signatures; otherwise report candidate-pool absence separately from Dream-2's
ability to author a revision.

## 5. Compatibility with the `2^4` target orbit

The orientation fork composes cleanly with the existing stage-row orbit. Let
`h=0` denote BA, `h=1` denote AB, and let `z_l=1` swap the complete hidden row
assignments of `u_l,v_l` across every suffix, as the existing orbit requires.
For the construction above, the correct target label bit is

```text
S_l(h,z) = z_l XOR h.
```

Equivalently,

```text
S(h,z) = z XOR (h * 1111).
```

Thus:

- for every fixed `z`, the two orientation continuations have identical tree
  bytes and complementary correct target action sequences;
- for every fixed `h`, the 16 `z` members retain the required bijection onto
  all 16 action sequences;
- tree/A/B evidence is row-swapped equivariantly across `z`, while the two
  `h` continuations at a fixed `z` share the tree exactly; and
- all fixed-goal target-visible packets can be byte-identical across the full
  `(h,z)` family.

There are 32 private `(h,z)` descriptions but only 16 correct action
sequences, each with two preimages. The target-only theorem therefore remains

```text
D1 action          1/2
D4 first action    1/2
D4 full sequence   1/16,
```

not `1/32`. Orientation flip is target-action-equivalent to the all-bit
antipode, but is scientifically a different intervention: it holds the tree
and Dream-1 fixed and changes raw A, whereas the ordinary antipode row-swaps
the source evidence and normally changes Dream-1. Neither substitutes for the
other.

If both the raw-A orientation fork and the usual whole-memory antipode panel
are model-materialized, the natural minimum is four nested sides for a sampled
root: `(h,z)`, `(1-h,z)`, `(h,z XOR 1111)`, and
`(1-h,z XOR 1111)`. This is a resource and protocol expansion, not a new
independent sample and not authorized by this memo.

## 6. Matched independent-table null

The null can match the prefix-fork interface, but it must not be described as
having or selecting an orientation.

For each null orbit root, generate one common 13-edge tree artifact. Preseal a
private continuation bit `q` and two A blocks, two disjoint B blocks, and two
target-table/orbit blocks. Conditional on the common tree:

1. sample the A operators independently and uniformly, rejecting only within
   the A pair until both branch outcomes differ;
2. sample B independently of tree, A, and targets, rejecting only within the
   B pair if exact branch disagreement is required;
3. generate the target orbit independently of tree/A/B, with one uniform
   four-bit base ambiguity; and
4. if matching complementary action bytes across `q` is desired, couple the
   two target blocks by a complete label complement chosen independently of
   A, not by a factor equation or A value.

The acceptance predicate must factor into an A-only predicate, a B-only
predicate, and a target-only orbit predicate. Then even if raw A identifies
which counterfactual branch was exposed, the independent uniform target bit
remains. For every visible target packet `X` and eligible public history `E`,

```text
Pr(S=s | X,E,q) = 1/16  for every s in {u,v}^4.
```

Similarly B remains conditionally unpredictable from tree+A. The two null B
truths and target actions may be different counterfactually; there is no
publicly supported map from A to those differences. Systematic exact
branch-sensitive B predictions or above-`1/16` target success in this family
is leakage, a coupled-null error, or evaluation noise.

It would invalidate the null to generate B or target operators from the BA/AB
completion selected by A, to expose the counterfactual A pair, or to reject a
root using a joint A--target condition. Pair-level marginal matching is not
enough: the certifier must prove the registered conditional target ambiguity
after every eligible tree/A history and visible target packet.

## 7. Unit of analysis and exact endpoint

The independent unit remains the **orbit root**. Orientation continuations,
`z` members, antipodes, A/B chords, target stages, D1/D4 targets, goal twins,
model calls, and repeated seeds are nested objects or interventions. A root
with both continuation sides is not `n=2`; exhaustive CPU construction of 32
private `(h,z)` states is not `n=32`.

For an opaque-note primary, no semantic parser is needed. A stringent exact
per-root revision-fork endpoint is the conjunction that, from one Dream-1
artifact:

```text
1. Dream-2's B1/B2 predicted trays are exact in V_BA;
2. Dream-2's B1/B2 predicted trays are exact in V_AB;
3. the executed target sequence is the registered BA sequence in V_BA;
4. it is the complementary registered AB sequence in V_AB; and
5. both branches use the same pre-A bytes and differ only through raw A and
   its mechanical descendants.
```

Report branchwise accuracy as well as this conjunction. Mere sensitivity
(`output_BA != output_AB`) is insufficient, and semantic claims that an opaque
note “stored orientation” remain unsupported. At the present three-root DEV,
all such values are descriptive. Any later interval or test resamples roots
as blocks and keeps every continuation/orbit/target object inside its root.

## 8. Minimal Stage-0 certifier recipe

Before any model byte, the proposal author would need a CPU certificate with
at least these checks:

1. **Common tree:** hash the canonical public rendering of all 13 tree events
   in both `h` branches for every certified `z`; require exact equality at
   fixed `z`, including labels, event order, reset handles, trays, metadata,
   UTF-8, and LF bytes.
2. **Two valid laws:** reconstruct explicit BA and AB factor assignments from
   the shared `M,R,C`; replay every tree event; require both to fit exactly and
   record the gauge convention without exposing it publicly.
3. **A selector:** for both registered A chords and every `z`, require true-law
   equality, wrong-law inequality, distinct raw after-trays, and exactly one
   orientation consistent with tree+A. Record no public match bit.
4. **Disjoint B:** prove A, B, and all target edge sets are pairwise disjoint;
   require both B operators/after-trays to differ across `h` and commit B
   requests before A is exposed.
5. **Target reversal:** hash-equal every fixed-goal target packet across
   `(h,z)`; require `S(h,z)=z XOR h*1111`, stagewise paired operators distinct,
   and the correct physical tray path equal across the `h` pair when the
   complementary labels are used.
6. **Orbit/no probes:** enumerate every one of the 16 menu sequences and every
   prefix for all `(h,z)` states; require one successful sequence, no early
   lock, no wrong-prefix recovery, no stabilizer, no future-bit probe, and the
   exact `1/16`/`1/2` target-only values. Certify each goal twin separately.
7. **Common-trace receipt:** fixture the fork after one immutable Dream-1
   artifact; require identical Dream-1 prompt/seed/trace/commitment and A
   request hashes. Mutation of either private branch must not affect any of
   those bytes.
8. **Dream-2 treatment diff:** require identical template/static fields,
   handle catalog shape, budgets, B request, model revision, and paired seed;
   byte-diff the two rendered inputs and allow differences only under the raw
   A outcome subtree and declared mechanical descendants.
9. **Firewall/reset:** prove neither orientation/fork ID, private seed,
   counterfactual A, factor/gauge, expected B/target, certificate, filename,
   RNG continuation, cache, timing, error, or retry state reaches cognition.
   Branch sessions, KV caches, readers, workspaces, and filesystem namespaces
   are fresh after the shared Dream-1 object.
10. **Independent null:** match the public envelope and tree joint law; prove
    factorized A/B/target acceptance predicates, conditional B/target
    independence, the uniform 16-way target posterior, and exact-program
    abstention/prior behavior after both null A continuations.
11. **Totality:** accept/reject the complete continuation/orbit root before
    Dream-1, retain every rejected seed/reason, forbid favorable branch
    selection after seeing Dream-1 or A, and assign every presealed branch a
    terminal outcome.
12. **Nesting manifest:** identify the root as the only independent unit and
    list every `h`, `z`, antipode, target, goal twin, branch, and model call as
    nested. No report may inflate the denominator.

The exact public program should then pass both factorized continuations,
produce their different B predictions and complementary target actions from
tree+A, and return the registered prior/abstention in both null continuations.
Only after those CPU fixtures pass would neural branch following be
interpretable.

## Final disposition

The requested public-prefix-identical causal fork exists, is compatible with
the sparse double-star and the corrected `2^4` target theorem, and has an
explicit nondegenerate `S_6` witness. Its decisive mechanism is simple: a tree
supports both gauge-fixed orientations, noncommuting A chords select between
their gauge-invariant completions, disjoint B tests prospective following,
and conjugate target row pairs turn the orientation flip into exact action-
label reversal under an unchanged goal.

The current proposal has the ingredients but not the fork dimension, shared
Dream-1 execution, `(h,z)` certificates, null analogue, or associated resource
accounting. Adding them is a material protocol change requiring the repository
deliberation and exact human-ratification path. This advisory changes only
itself. No proposal/code/model/GPU/network/authority state was changed, and no
scientific run was performed.

The digest below is SHA-256 of the `LC_ALL=C` path-sorted `shasum -a 256`
manifest for `AGENTS.md`; the sparse-factor math, paper adjudication,
model-owned revision, orbit, sparse-construct, semantic countercritique, and
semantic-representation adjudication advisories; and the current change's
`change.json`, `experiment_spec.md`, `visibility_contract.md`,
`semantic_contract.md`, and `scope_proposal.json`. It excludes this advisory.

**Orientation-fork source-manifest SHA-256:** `d02eb41a12cbea54fb5a7fd5ca6d8a312a73093cc2ee7760757af710d3602bcf`
