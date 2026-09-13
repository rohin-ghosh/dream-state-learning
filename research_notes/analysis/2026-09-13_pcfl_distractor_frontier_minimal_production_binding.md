# PCFL v2.2: minimal exact distractor-frontier production binding

**Date:** 2026-09-13 UTC  
**Status:** proposal only; no implementation, tokenizer/model call, fixture
materialization, fit, GPU use, or scientific execution  
**Purpose:** close the production ambiguities isolated in
`2026-09-13_pcfl_distractor_and_opaque_id_production_bindings.md` without
changing the PCFL v2.2 scientific object

## Decision

Use the two already-present OLD dead-end fragments to construct the isolated
distractor frontier:

```text
relevant frontier:    H --q_R--> S_R
distractor frontier:  X --q_D--> Z
```

The relevant frontier connects the OLD left route to the OLD right route. The
distractor frontier connects the otherwise dead path fragments
`S_L --a_(1-O)--> X` and `Z --u--> Y`. It is therefore a real, equally
uncertain missing relation, but even if executed it can only make

```text
S_L --a_(1-O)--> X --q_D--> Z --u--> Y
```

and can never reach `G_R0` or `G_R1`.

`R` and `D` independently select the same two existing opaque port slots:

```text
q_R = q0 if R=0 else q1
q_D = q0 if D=0 else q1
```

This is the smallest binding: it adds **zero** nodes, ports, EVENT addresses,
LINK addresses, PROBE addresses, receipt addresses, or goal addresses. It also
gives the no-op `D` bit a real public-after-commit consequence.

This proposal becomes production authority only if copied unchanged into the
sealed v2.2 `execution_contract.json` and covered by the already-required
pre-model tests. Until then, preparation remains fail-closed.

## 1. Source precedence and preserved science

This proposal is a literal completion of, not a replacement for:

- `2026-09-13_pcfl_vertical_dev_v2_synthesis.md`, SHA-256
  `222677395031224e5bb645a18ada975a571db28ae9c818f12fa396e09a394456`;
- `2026-09-13_pcfl_vertical_dev_v2_prospective_binding_register.md`, SHA-256
  `5d7920ea8e515794c57d19a9bd0d4793c835848727266aa0cb41ed729e5abadd`;
- `2026-09-13_pcfl_vertical_dev_v2_exact_build_ledger.md`, SHA-256
  `f3fe13058b86cc0af4863abd5a54bdaa98bf3e846761a8e87230a3d5f2c53679`;
- `2026-09-13_pcfl_v22_minimum_execution_closure_contract.md`, SHA-256
  `f9b9891761c47e6d8047e7a9161a827d00fae464df91940c523b40f85af535d0`;
  and
- the ambiguity audit being closed here, SHA-256
  `bcdae11f3eb5c0653b842f16bbf5ba1e34cc5ffdbdc62689aca1ce2ca0f6eecf`.

All passed v2.2 writer, fit, projection, formation, reachout, custody, and
claim rules remain unchanged. In particular, `D` never enters authentic
lineage, a valid relevant primary choice still earns only one registered bit,
and both delayed goals still require the same relevant frontier. This binding
does not upgrade the claim to goal-varying experiment choice.

## 2. Closed structural topology

### 2.1 OLD executed edges, unchanged

For `O in {0,1}`:

```text
e0  S_L --a_O------> A
e1  A   --b--------> H
e2  H   --c--------> G_L
e3  S_R --d--------> B
e4  B   --f_0------> G_R0
e5  B   --f_1------> G_R1
e6  S_L --a_(1-O)--> X
e7  Z   --u--------> Y
```

The four OLD LINKs remain `l0..l3` exactly as already registered.

### 2.2 Frontier truth, before execution

`WorldCell.frontiers` is a private closed two-entry map:

```text
Q_relevant   -> (source=H, destination=S_R, applicable_port=q_R)
Q_distractor -> (source=X, destination=Z,   applicable_port=q_D)
```

These are `FrontierTruth` records, not executed events. They have no EVENT ID,
receipt ID, or LINK ID. They exist so a committed PROBE returns a real world
fact. Neither frontier is placed in the pre-outcome public graph.

For the route-neutrality certificate only, a second oracle evaluates the
maximal counterfactual topology `OLD edges + both frontier relations`. It must
still find exactly the registered delayed route and no alternative route to
either delayed goal. This stronger check prevents `D` from being declared
irrelevant merely because the runtime ignored it.

### 2.3 Relevant promotion, unchanged

After a valid relevant commitment, the child receives the relevant result,
then the already-registered singleton `EXPLORE H q_R` opportunity. Only a
valid execution promotes that frontier into:

```text
e8  H --q_R--> S_R       receipt r8
l4  e1 THEN e8 VIA H
l5  e8 THEN e3 VIA S_R
```

`e8` is the only NEW executed edge. The child still authors exactly one NEW
EVENT and two NEW LINKs.

### 2.4 Distractor never promotes

After a valid distractor commitment, the child receives the distractor result
and the reachout session terminates. It gets no `EXPLORE X q_D`, no event
receipt, and no EVENT/LINK opportunity. Consequently there is no `e9`, `r9`,
`l6`, or `l7`, and no distractor row can enter any authentic corpus.

This is intentional. The probe measures selection of a useful experiment,
not the ability to execute and memorize the experiment after selecting the
wrong one. The counterfactual maximal-graph audit above separately proves that
the real distractor relation is route-neutral.

## 3. Exact opaque inventory slots

Every root uses the existing inventory and structural order:

| namespace | exact slots | count |
|---|---|---:|
| `N_` | `S_L,A,H,G_L,S_R,B,G_R0,G_R1,X,Z,Y` | 11 |
| `P_` | `a0,a1,b,c,d,f0,f1,u,q0,q1` | 10 |
| `E_` | `e0..e8` | 9 |
| `L_` | `l0..l5` | 6 |
| `Q_` | `relevant,distractor` | 2 |
| `R_` | `r0..r8` | 9 |
| `G_` | `old_left,old_right,delayed0,delayed1` | 4 |

There is no model-visible root-ID namespace. The closed audit-only root key is
one of:

```text
excluded/0  excluded/1  excluded/2  excluded/3
disposable/0
dev/0       dev/1
```

The opaque allocator, tokenizer qualification, global uniqueness, substring,
reserved-word, first-valid search, and cross-root constraints remain exactly
those already registered. `O/R/D`, RA/RB order, and selected probe never cause
an ID redraw.

### Why reusing `q0/q1` is safe

Actions are keyed by `(source,port)`, not by `port` alone. Therefore a cell in
which `q_R == q_D` still has two different frontier relations:
`(H,q,S_R)` and `(X,q,Z)`. No ambiguity or alternate route is created. Reuse
also makes the relevant and distractor outcomes exactly matched in ID count,
byte width, and candidate pool without adding two arbitrary port tokens.

## 4. Exact `G_` and goal visibility ruling

`G_` IDs are audit-only goal-instance handles. They occur in the sealed root
registry, task/counterpart assignments, and private scorer records, but never
in a model message, training target, memory request/return, public receipt, or
public probe result.

The mapping is:

```text
G_old_left  -> public START N_S_L, public GOAL N_G_L
G_old_right -> public START N_S_R, public GOAL N_G_R0
G_delayed0  -> public START N_S_L, public GOAL N_G_R0
G_delayed1  -> public START N_S_L, public GOAL N_G_R1
```

Thus `{GOAL_ID}` in every already-frozen route or reachout template is the
target **node** `N_G_*`, and the second field of `ROUTE` is also an `N_` node.
The strict ROUTE parser must reject `G_` in either endpoint field. This keeps
the public task spatially meaningful, avoids a redundant goal token and a new
shortcut, and resolves the apparent conflict between the separate goal
namespace and the registered ROUTE examples.

The root key is likewise custody metadata only. It is never substituted into
a model-visible receipt. Hence no additional root-ID grammar or token-equality
class is required.

## 5. Exact probe-result record and model-visible bytes

### 5.1 Closed public result value

A valid selected probe creates exactly this four-field public value:

```json
{"destination":"{DESTINATION_ID}","port":"{PORT_ID}","probe":"{PROBE_ID}","source":"{SOURCE_ID}"}
```

This is ASCII/JCS canonical JSON: keys appear in the literal order above,
separators are `,` and `:`, `ensure_ascii=true`, and there is no terminal LF.
The typed substitutions are `N_`, `P_`, `Q_`, `N_` respectively. Unknown or
extra fields fail closed.

The model receives only the following exact text projection of that same
value:

```text
PROBE RESULT
PROBE {PROBE_ID}
SOURCE {SOURCE_ID}
PORT {PORT_ID}
DESTINATION {DESTINATION_ID}
```

There is one ASCII LF between physical lines and no terminal LF. The JSON and
text are both hashed, and the validator must prove field-for-field equality
between them before either is usable. The JSON is the exact public wire/audit
value; the text is its sole model-visible rendering. Neither contains a
root, goal handle, `R`, `D`, relevance label, usefulness label, route, score,
event address, receipt address, or hash.

### 5.2 Exact R/D substitution table

The four private cells instantiate the above payloads as:

| `(R,D)` | selected relevant result | selected distractor result |
|---|---|---|
| `00` | `(Q_relevant,H,q0,S_R)` | `(Q_distractor,X,q0,Z)` |
| `01` | `(Q_relevant,H,q0,S_R)` | `(Q_distractor,X,q1,Z)` |
| `10` | `(Q_relevant,H,q1,S_R)` | `(Q_distractor,X,q0,Z)` |
| `11` | `(Q_relevant,H,q1,S_R)` | `(Q_distractor,X,q1,Z)` |

The mnemonic names and bits in this table are private. Instantiated model
text contains only prepared opaque IDs.

### 5.3 Probe results are not receipts

A probe result has no `R_` identifier and is not admissible evidence for an
EVENT or LINK. It reports an unexecuted frontier fact. The private custody
envelope records root key, cell hash, selected structural probe role, committed
action hash, JSON hash, text hash, and whether the session became terminal;
none of those custody fields is model-visible.

Only a subsequent valid EXPLORE creates an executed-event receipt. This
prevents a probe from silently becoming the child-authored NEW EVENT.

## 6. Executed-event receipt visibility

The ledger's full receipt record retains its required audit fields
`root/branch/stage/turn`, receipt ID, source/port/destination, predecessor,
exact text hash, and whole-record hash. Those custody fields do not all enter
the child prompt. The sole model-visible receipt payload is:

```json
{"destination":"{DESTINATION_ID}","port":"{PORT_ID}","receipt":"{RECEIPT_ID}","source":"{SOURCE_ID}"}
```

and its sole model-visible text rendering is:

```text
EXECUTION RECEIPT
RECEIPT {RECEIPT_ID}
SOURCE {SOURCE_ID}
PORT {PORT_ID}
DESTINATION {DESTINATION_ID}
```

Both have no terminal LF and obey the same JSON/text equality-and-hash rule as
probe results. The child needs exactly these four values to author an EVENT;
showing private root/branch/stage/hash metadata would add tokens and possible
root shortcuts without adding task information.

OLD `r0..r7` form one private stage-local predecessor chain. Each R
continuation begins a fresh sterile NEW chain with `r8`, `turn=0`, and null
predecessor. `r8` is reused across the mutually exclusive R0/R1
counterfactual branches, while the receipt record and text hashes differ
because the port differs. No receipt crosses from one branch to another.

The EVENT admission checker uses the full custody record but permits the child
to cite only the public `R_` receipt ID. Any attempt to cite a `Q_` result, a
private hash, a receipt from the other branch/root/stage, or a nonexecuted
distractor frontier fails without repair.

## 7. One-shot state machine and terminal bytes

The PROBE action parser accepts exactly the ASCII byte string

```text
PROBE Q_[A-Z2-7]{10}
```

with one ASCII space, a listed probe ID, and no terminal LF. Extra whitespace,
extra prose, Markdown, two lines, two commands, an unknown/wrong-namespace ID,
or any second commitment is malformed. Generation ending without a valid
line is missing. Every attempted or missing commitment consumes the sole
opportunity.

The exact terminal response is the eight ASCII bytes:

```text
TERMINAL
```

with no terminal LF, explanation, correctness signal, or retry invitation.
The state transitions are:

1. **Valid relevant:** return the relevant `PROBE RESULT` text, do not return
   `TERMINAL`, and issue the registered singleton EXPLORE task.
2. **Valid distractor:** return the distractor `PROBE RESULT` text followed in
   the transcript by the separate exact `TERMINAL` response; request no more
   model output and reveal no relevant result.
3. **Malformed, missing, unknown, or already consumed:** create no probe-result
   JSON/text, return only `TERMINAL`, request no more model output, and reveal
   neither R nor D.

The distractor transcript is audit-only and tainted `DISTRACTOR`; it cannot be
an authentic lineage ancestor or training source. A fixed-position/fixed-ID
diagnostic policy is not detectable from one syntactically valid action and is
therefore scored at the predeclared panel level, never repaired by a hidden
per-action policy detector. If such a policy chooses the distractor in the
lineage primary, it follows transition 2 and the root stops before S2.

## 8. Token and byte substitution classes

The preparation search adds these closed classes to the already-registered
inventory constraints:

1. `PROBE_RESULT/root`: the four text instances
   `(relevant,q0)`, `(relevant,q1)`, `(distractor,q0)`,
   `(distractor,q1)` have equal tokenizer count; the four canonical JSON
   instances have equal ASCII byte length.
2. `RELEVANT_RESULT/root`: R0 and R1 text/JSON counts are equal.
3. `DISTRACTOR_RESULT/root`: D0 and D1 text/JSON counts are equal.
4. `NEW_EXPLORE/root`: singleton `EXPLORE H q0` and `EXPLORE H q1` prompts
   have equal tokenizer count.
5. `NEW_RECEIPT/root`: r8 receipts for q0 and q1 have equal tokenizer count
   and byte length.
6. `FRONTIER_SURFACE/root`: the existing RA/RB full render/order mates retain
   their registered equal-token requirement.

Context-bound tokenization, not the sum of bare-ID token lengths, decides each
class. Failure at every allowed common bare-ID length is
`VS_ASSAY_INVALID`; there is no redraw, result-dependent choice, or trainable
PAD. The `TERMINAL` constant is not part of an outcome substitution class,
because it is the post-choice control transition rather than an outcome field.

The complete model-visible pre-outcome bytes remain byte-identical—not merely
token-equal—across the four `(R,D)` cells for fixed
`(root,O,G,render_id)`. The IDs, affordance order, RA/RB selection, decoder
seed, task, and active context are all reused, not regenerated.

## 9. Exact symmetry, entropy, and route implications

### Local matchedness

Both probes name one missing directed frontier between already witnessed OLD
endpoints:

- relevant: destination of `e1` to source of `e3`;
- distractor: destination of `e6` to source of `e7`.

Both return one of the same two port IDs through the same result schema. Both
have one commitment, no pre-commit outcome, and no retry. Their only intended
asymmetry is global task usefulness, which the child must infer from OLD
structure after the future goal is shown.

### Exact information values

For each fixed `(root,O,G)`, uniform enumeration of `00,01,10,11` gives:

```text
count(q0 under relevant)=2/4   count(q1 under relevant)=2/4
count(q0 under distractor)=2/4 count(q1 under distractor)=2/4
count((qR,qD) each joint pair)=1/4
```

The correct route depends on R through `q_R` and never on D. Hence the exact
conditional values are:

```text
H(Y_R | T_pre)=1
H(Y_D | T_pre)=1
I(Y_R; Z_G | T_pre,G)=1
I(Y_D; Z_G | T_pre,G)=0
```

No floating estimate or cross-root balancing is accepted.

### Route uniqueness and cuts

For every `(O,R,D,G)`:

```text
correct route = a_O,b,q_R,d,f_G
```

Changing D changes only the `X -> Z` frontier result. It changes none of
`e0..e8`, `l0..l5`, the correct route, route length, OLD/NEW projection,
S1/S2 target row, cut result, address roster, or relevant outcome. Deleting
`e0` or `e8` destroys the unique delayed route even when the hypothetical
distractor relation is present. The distractor side path terminates at Y and
cannot rejoin any target component.

### Eight-cell label balance

At fixed `(root,G)`, O and R produce exactly four route labels:

```text
(a0,q0), (a0,q1), (a1,q0), (a1,q1)
```

with the fixed `b,d,f_G` fields around them. D duplicates each full label
exactly twice. All eight native prompts are byte-identical; prompt-only
Bayes-best route accuracy is exactly `2/8=.25`.

### Projection independence

`OLD_ONLY` omits both frontier results/NEW and therefore collides across R.
`NEW_ONLY` contains only executed relevant NEW material and therefore collides
across O. Neither projection contains a distractor result or D-derived row, so
both are exactly D-invariant. The separate reachout audit may render the
selected D result only after a valid distractor commitment; it must never mix
that result into a delayed-route projection.

RA/RB still contain the same two endpoint facts in opposite neutral order.
Across the registered 32-cell reachout certificate, each structural probe
occupies each visible position exactly `16/32`. No result, port, role, terminal
status, goal handle, root key, or bit is present before commitment.

## 10. Additional fail-closed acceptance cases

In addition to every test already required by the ambiguity audit, production
must reject any binding that fails one of these exact cases:

1. the distractor frontier is anything other than `X -> Z` or uses anything
   other than `q_D`;
2. any namespace has a slot count different from Section 3, including an
   invented e9/r9/l6/l7 or dedicated distractor port;
3. either frontier exists in the model-visible pre-outcome graph;
4. D changes an executed edge, row, route, cut, roster, identifier, render,
   seed, or authentic-lineage byte;
5. the maximal graph containing both frontier truths gains a route to either
   delayed goal or loses uniqueness;
6. probe-result JSON/text differ semantically, contain extra fields, have a
   terminal LF, or miss their substitution-class equality;
7. a probe result has/cites an `R_` ID or is accepted as EVENT/LINK evidence;
8. a distractor or malformed commitment receives an EXPLORE/receipt/retry, or
   any relevant result is disclosed after it;
9. an invalid commitment receives any outcome before the exact `TERMINAL`;
10. `G_`, root key, R, D, relevance/usefulness, route, score, or custody hash
    occurs in any pre-outcome model bytes;
11. `{GOAL_ID}` or a ROUTE endpoint is not `N_`, or any `G_` ID is found in a
    model-visible transcript/corpus;
12. a model-visible executed receipt includes audit-only root/branch/stage/
    turn/hash fields, or r8 crosses between R branches; and
13. any terminal/distractor trace can enter authentic ancestry or a fitted
    corpus.

## 11. Production handoff

The exact implementation delta implied by this proposal is deliberately
small:

```text
add private FrontierTruth(X,q_D,Z)
  -> bind one shared PROBE RESULT renderer for both probes
  -> keep probe results non-receipts
  -> promote only the relevant frontier through existing e8/r8
  -> terminate distractor/malformed paths with exact TERMINAL bytes
  -> type public GOAL/ROUTE endpoints as N_ and keep G_/root audit-only
  -> add the result/receipt substitution classes and maximal-graph audit
```

This closes every ambiguity named by the production-binding audit while
preserving the intended PCFL question: can the child use learned OLD structure
to choose the useful uncertain experiment, then combine its own OLD and NEW
experience after reset? It does not add a controller, answer candidate, hidden
label, extra training signal, or easier route.
