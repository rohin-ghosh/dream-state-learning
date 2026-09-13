# PCFL v2.2: distractor frontier and opaque-ID production bindings

**Date:** 2026-09-13 UTC  
**Role:** critical-path specification extraction for Astra  
**Scope:** authoritative-record audit only; no scientific redesign, runtime or
test edit, tokenizer/model call, fixture generation, fit, or GPU execution

## Verdict

The production opaque-identifier rule is sufficiently specified once the
v2.2 PAD supersession is applied. The production distractor is **not**. The
passed documents freeze what the distractor must prove, what may be public,
and every denominator, but they never freeze its concrete isolated frontier,
its two public outcome renders, or the exact transition after a distractor
commitment. Those bytes/topology cannot be inferred from the archived partial
core: its `D` bit changes neither an edge nor a public outcome.

Therefore Astra can implement the scientific opaque namespace now. It may
also implement the D-neutral algebra and all fail-closed interfaces below, but
must not invent the missing distractor endpoints/outcome bytes and call the
construct complete. A contract lacking them remains
`execution_contract_valid=false` / `VS_ASSAY_INVALID`.

## 1. Authority and v2.2 precedence

This extraction uses the exact pinned sources named by the v2.2 closure:

- base world/science: `2026-09-13_pcfl_vertical_dev_v2_synthesis.md`,
  SHA-256 `222677395031224e5bb645a18ada975a571db28ae9c818f12fa396e09a394456`;
- retained literal bindings: `2026-09-13_pcfl_vertical_dev_v2_prospective_binding_register.md`,
  SHA-256 `5d7920ea8e515794c57d19a9bd0d4793c835848727266aa0cb41ed729e5abadd`;
- implementation/test denominators: `2026-09-13_pcfl_vertical_dev_v2_exact_build_ledger.md`,
  SHA-256 `f3fe13058b86cc0af4863abd5a54bdaa98bf3e846761a8e87230a3d5f2c53679`;
- controlling writer supersession:
  `2026-09-13_pcfl_vertical_dev_v2_2_writer_repair.md`, SHA-256
  `683fcba7762b69f408e5371cd9525e62c7ba6c8aa25494542f3041fec275dfca`;
  and
- v2.2 execution closure:
  `2026-09-13_pcfl_v22_minimum_execution_closure_contract.md`, SHA-256
  `f9b9891761c47e6d8047e7a9161a827d00fae464df91940c523b40f85af535d0`.

The v2.2 writer delta removes loss-active PAD and target-token equalization.
Consequently, retain the identifier search and substitution-class equality
rules, but delete every opaque-search dependency on `PAD_S1_*`, `PAD_S2_*`,
PAD target search, the `+64` reserve, or equal stage target tokens. Ordinary
post-EOS tensor padding is unrelated and remains legal only when masked with
`attention_mask=0` and label `-100`.

The archived partial core is evidence, not authority. In particular, its
lowercase `[0-9a-f]{24}` IDs and its nine-edge graph are fixture-only.

## 2. Exact world topology and state transitions that are frozen

Structural names below are private construction labels and never reach a
model. Every model-visible occurrence is replaced by its prepared opaque ID.

### 2.1 OLD state

For `O in {0,1}`, the eight witnessed OLD events are exactly:

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

The four witnessed OLD links are exactly:

```text
l0  e0 THEN e1 VIA A
l1  e1 THEN e2 VIA H
l2  e3 THEN e4 VIA B
l3  e3 THEN e5 VIA B
```

Changing `O` swaps only the opaque port bindings of `e0` and `e6`; IDs and
token marginals do not change. OLD route targets are:

```text
S_L -> G_L  : a_O,b,c
S_R -> G_R0 : d,f_0
```

### 2.2 Reachout and relevant continuation

After the authentic S1 write, restore the untouched pre-evaluation S1_AUTH
snapshot. The mounted child receives a sterile future task from `S_L` to
`G_R0` or `G_R1` and exactly two symmetric opaque probe affordances:

- structural relevant probe: missing frontier `H -> S_R`;
- structural distractor probe: one isolated matched frontier.

There is one `PROBE <probe_id>` commitment, no retry, and no result before the
commitment. A missing, malformed, fixed-choice, post-outcome, or distractor
choice scores zero. If the lineage-entering primary choice is not relevant,
the root stops before S2 and the relevant outcome is not revealed.

For a relevant commitment, the ordinary public result reveals which of the
two opaque `q` ports applies:

```text
e8  H --q_R--> S_R
l4  e1 THEN e8 VIA H
l5  e8 THEN e3 VIA S_R
```

The child then commits `EXPLORE H q_R`, receives a normal immutable public
executed-event receipt, and gets exactly one EVENT and two LINK opportunities.
The two R continuations restore one byte-identical sealed native pre-outcome
state, use coupled seeds, and differ only in the ordinary public R result.
No OLD receipt, row, roster, ledger, service return, or compiler state may be
in either continuation; OLD IDs in NEW LINKs must be generated from mounted
parametric state.

The two delayed routes are exactly:

```text
G=0  S_L -> G_R0 : a_O,b,q_R,d,f_0
G=1  S_L -> G_R1 : a_O,b,q_R,d,f_1
```

Deleting `e0` or `e8` destroys every successful delayed route. `D` must never
change either route, create an alternate successful route, or enter authentic
lineage. It exists to make the choice nontrivial and to certify that entropy
alone does not identify usefulness.

### 2.3 Collision cube

Every root expands before use to all eight `(O,R,D) in {0,1}^3` cells. For
each fixed `(root,O,G)`, the four R/D cells must have byte-identical visible
pre-outcome state and the exact outcome table `00,01,10,11`. Required exact
information values are:

```text
H(Y_R)=1, H(Y_D)=1, I(Y_R;Z_G)=1, I(Y_D;Z_G)=0
```

`D` duplicates labels only: at fixed `(root,G)`, eight identical native task
prompts have four correct routes, each occurring exactly twice. Prompt-only
Bayes accuracy is therefore `.25`.

The cube is a CPU certificate. `D` is never injected into authentic fitted
lineage. Only R0/R1 are the two authentic counterfactual continuations.

## 3. Exact public/private boundary

### 3.1 Public before probe commitment

The only two reachout surfaces are the literal registered `RA` and `RB`
templates. They contain:

- opaque START and GOAL IDs;
- both opaque probe IDs;
- each probe's opaque source and destination endpoints; and
- the one-line `PROBE <probe_id>` commitment instruction.

`RA` lists structural probe 0 then 1. `RB` presents the same facts in the
opposite neutral wording/order, structural probe 1 then 0. `PROBE_0` means the
relevant frontier and `PROBE_1` the distractor only inside private
construction; those words never reach the model. DEV root 0 primary is RA,
root 1 primary is RB; the diagnostic panel alternates RA/RB four times.

The public pre-outcome bytes omit `O`, `R`, `D`, every outcome, route ports,
correct route, relevance/usefulness labels, scores, candidates, and private
cut facts. At fixed `(root,O,G)`, those bytes—including IDs and order—must be
identical across all four R/D cells.

### 3.2 Public after commitment

Only the selected probe's ordinary result may become public, and only after
the one commitment. For the relevant lineage, this is the applicable opaque
`q_R` port followed by the public receipt for the executed `H --q_R--> S_R`
transition. All receipt fields are public exact bytes; private route/cut/bit
facts are not.

The compiler may verify/copy a child span but may not render or repair its
meaning. It may not translate a private bit into a model-visible label.

### 3.3 Private only

Private state contains the structural roles, `O/R/D`, probe-role map, complete
counterfactual outcome map, graph oracle, correct routes, dependency cuts,
collision memberships, and scores. `WorldCell` and `TaskRender` need closed
public/private allowlists, and any private field in a public projection is a
hard preparation failure.

All ten zero-fit projections must have exact UTF-8 bytes, placement, ordering,
separator, final-LF policy, and task join frozen in `render_registry`:

```text
EXACT_WITNESSED_GRAPH  FULL_CHILD_TEXT  EVENT_ATOMS_TEXT
ACTIVE_LINKED_TEXT     NATIVE_CONTEXT   RAW_EPISODIC
OLD_ONLY_TEXT          NEW_ONLY_TEXT    NONE_OFF  WRONG_ROOT
```

Dynamic joins are typed placeholders with one allowed substitution class; no
free string assembly is legal.

## 4. Required D/projection/shortcut audits

Before any model call, four excluded roots give 32 worlds and 64 delayed
tasks. The construct gate must prove all of the following without averaging:

1. **Entropy/collision:** all `16/16` `(root,O,G)` quartets have one identical
   pre-outcome hash, exact 00/01/10/11 outcomes, and `(1,1,1,0)` information
   values.
2. **D neutrality:** toggling only D changes the registered distractor outcome
   but not the public pre-outcome bytes, relevant outcome, graph route, OLD or
   NEW target rows, correct delayed ROUTE, or either OLD/NEW cut result.
3. **OLD-only:** `32/32` fixed `(root,O,D,G)` R-pairs are byte-identical and
   have exactly two route labels.
4. **NEW-only:** `32/32` fixed `(root,R,D,G)` O-pairs are byte-identical and
   have exactly two route labels.
5. **Native prompt:** all `8/8` `(root,G)` groups contain eight identical
   prompts and four correct routes at exactly `2/8` each.
6. **Route dependence:** FULL unique success `64/64`; OLD cut failure `64/64`;
   NEW cut failure `64/64`; two independent oracles agree everywhere.
7. **Candidate-free execution:** private oracle success, OLD-cut failure, and
   NEW-cut failure are each `64/64`, with zero intermediate returns/retries:
   192 deterministic decisions.
8. **Projection shortcuts:** for goal text, start/target IDs, event/link
   handles, row/order positions, port frequencies, outcome frequencies, route
   length, affordance order, and every pairwise combination, record key count,
   coverage, minimum support/labels, deterministic keys, decoded occurrences,
   and Bayes-best route accuracy. Every registered projection covers `64/64`,
   has support `>=2`, labels `>=2`, and has zero deterministic keys/decoded
   occurrences.

The separate reachout certificate is exactly 32 cells:
`4 roots x 2 O x 2 goals x 2 surfaces`. RA/RB make each structural position
occur `16/32`. EXACT_WITNESSED_GRAPH, FULL_CHILD_TEXT, and ACTIVE_LINKED_TEXT
must select the relevant probe `>=30/32`; NONE/OFF and WRONG_ROOT must be
`<=18/32`. Every registered ID-only, probe-order, wording, and fixed-choice
projection must also remain `<=18/32`.

The validator must snapshot all ten projection renders and fail on a one-byte
placement/order/separator mutation. It must also reject missing coverage,
singleton collision keys, a deterministic decoded subgroup, D-dependent route
labels, or any D outcome present before commitment.

## 5. Scientific opaque identifier namespace

### 5.1 Lexical grammar and typed fields

Scientific model-visible IDs are fixed-width uppercase ASCII:

```text
N_[A-Z2-7]{10}   node
P_[A-Z2-7]{10}   port
E_[A-Z2-7]{10}   event / fresh EVENT address
L_[A-Z2-7]{10}   link / fresh LINK address
Q_[A-Z2-7]{10}   probe
R_[A-Z2-7]{10}   public receipt
G_[A-Z2-7]{10}   goal namespace
```

The prefix and ten RFC-4648 base32 characters make every ID 12 ASCII bytes.
Parsers must enforce the field's namespace, not one generic ID regex:
sources, destinations, shared nodes, and ROUTE endpoints are `N_`; action and
ROUTE ports are `P_`; EVENT/LINK/PROBE/receipt fields use their matching
prefix. Lowercase hex fixture IDs must fail scientific parsing.

Every required ID is globally unique and namespace-disjoint across the sealed
root registry; no ID may be a substring of another. No ID may collide with a
prompt keyword, canary ID, parser prefix, or reserved literal. O/R/D swaps and
RA/RB ordering reuse the same inventory; hidden bits never trigger a redraw.

### 5.2 Deterministic allocation

Seeds are exactly:

```text
seed(label) = first 8 bytes, big-endian, of
SHA256(ASCII("PCFL-V2.1-PREP\0") || ASCII(label)), masked to 63 bits
```

Opaque seed domains are `opaque/{excluded/0..3,disposable/0,dev/0..1}`.
Order slots by root class/index, then namespace `N,P,E,L,Q,R,G`, then frozen
structural index. For every slot enumerate salt `0..999999`; candidate bytes
are prefix plus the first ten base32 characters of:

```text
SHA256(master_seed || NUL || namespace || NUL || decimal_index || NUL ||
       decimal_salt)
```

where `master_seed` is the unsigned eight-byte big-endian opaque seed.

For each common bare-token length `L=4..12`, retain per slot the first 4,096
salt-ordered candidates that have length L under the pinned tokenizer and pass
local uniqueness/keyword tests. Run deterministic depth-first constraint
search in structural slot order and ascending salt order, pruning uniqueness,
substring, and fully instantiated substitution-class violations. Select the
first complete solution at the smallest feasible L; within L this is the first
salt vector under the fixed traversal. Pool/length exhaustion is
`VS_ASSAY_INVALID`; there is no redraw or fallback.

### 5.3 Tokenizer qualification

Preparation pins the exact tokenizer revision/files, chat-template hash, and
every tokenization result used. Acceptance requires:

- all bare IDs have the one selected common tokenizer length in `4..12`;
- every registered grammar row, query, EVENT_TWIN replacement,
  LINK_PERMUTE replacement, collision render, and RA/RB substitution mate has
  equal token count within its prospectively named substitution class;
- every complete rendered training sequence is `<512` with zero target
  truncation; and
- tokenization receipts exist for every candidate considered and every
  accepted substitution class.

V2.2 does **not** require active-target-token equality across arms and forbids
using trainable PAD to manufacture it.

For diagnostic grammar/content NLL, any tokenizer offset overlapping an opaque
field byte span is content; boundary overlap resolves to content. Fixed
grammar, separators, and EOS are grammar. Every supervised token must be
classified exactly once.

## 6. Fail-closed test additions for Astra's first slice

The archived 20 tests remain useful route-algebra tests, but production needs
at least these exact additions:

1. reject `[0-9a-f]{24}`, lowercase base32, wrong prefix by field, wrong byte
   width/alphabet, duplicates, substrings, reserved collisions, missing slots,
   and cross-root collisions;
2. golden-test seed derivation, candidate derivation, slot order, smallest-L
   search, first-valid salt vector, and identical rerun; tokenizer/source/hash
   drift or exhausted candidate pools must fail without redraw;
3. enumerate every required substitution class and prove equal tokenizer
   counts; one altered ID or render must fail; assert no PAD/equal-token field
   exists in a v2.2 contract;
4. prove the exact eight-cell cube and all 16 entropy quartets, including that
   D toggles a real public-after-commit distractor outcome but no route/row;
5. prove all four R/D pre-outcome renders byte-collide and that adding D,
   relevance, result, route, or usefulness to public bytes fails the allowlist;
6. snapshot RA/RB, prove identical facts/opposite order, exact 16/32 position
   balance, and reject any role word (`relevant`, `distractor`, `PROBE_0`,
   `PROBE_1`) in model-visible bytes;
7. prove one PROBE commitment, no outcome before it, no retry, and no R reveal
   or authentic continuation after a distractor/malformed primary action;
8. execute all 64 full/OLD-cut/NEW-cut routes with two independent oracles and
   run the complete singleton/pairwise projection audit with the exact
   denominators in Section 4;
9. validate all ten public render snapshots and their private allowlists;
   one-byte mutation, free join, missing final-LF policy, or private field fails;
10. verify field-specific EVENT/LINK/READ/ROUTE/EXPLORE/PROBE parsing under the
    accepted scientific inventory and reject extra prose/multiple commands;
11. prove `root_skeleton_hash` includes topology, slot IDs, opaque inventory,
    render IDs, roots, bits/goal assignments, cuts, addresses, and counterpart
    maps but rejects generated bytes, scores, losses, or receipts; and
12. keep `ready_for_model_calls=false` until the concrete distractor and every
    preceding test are present in the sealed execution contract.

## 7. Remaining ambiguities — do not invent these

### Blocking: distractor topology and outcome bytes

The authority says only “isolated matched frontier.” It does not say:

- which structural nodes are its source and destination;
- whether it adds a counterfactual graph edge or only a probe-result record;
- whether D selects one of the existing `q_0/q_1` ports or needs separate
  port slots;
- the exact public result text/fields for D=0 and D=1;
- whether a distractor result has a receipt ID and, if so, its schema; or
- the exact terminal public response after a distractor commitment.

`e6: S_L -> X` and `e7: Z -> Y` suggest a possible `X -> Z` isolated gap, but
that is an inference, not a frozen requirement. Likewise `q_D` is plausible
but never stated. Neither may be silently promoted into scientific source.

This is why the archived partial core's current assertion that changing D
leaves all edges equal is insufficient: it proves route independence by making
D causally nonexistent, not by presenting an equally uncertain irrelevant
experiment to the model.

### Blocking: exact public probe-result render

RA/RB pre-outcome bytes are frozen, but no literal relevant or distractor
result template is supplied. “Only the ordinary public outcome changes” is a
visibility invariant, not an exact renderer. Both R and D result byte families
must be frozen before tokenizer inventory acceptance and before the collision
hash can become a native rather than structural certificate.

### Smaller namespace/render ambiguity

The register requires a `G_` goal namespace, while the ROUTE examples and
partial core use the opaque target **node** as `GOAL` and as the second ROUTE
field. The authoritative records do not state where a separate `G_` goal ID is
model-visible, or whether it is internal metadata only. They likewise do not
state a model-visible root-ID grammar. The contract must explicitly type these
fields; it must not substitute a `G_` token for an `N_` route endpoint by
guesswork.

## Handoff

Astra's first safe production slice is:

```text
replace fixture hex IDs with the exact typed base32 allocator
  -> bind/validate all known OLD + relevant-frontier structure
  -> encode D as an unresolved required closed object, not a no-op bit
  -> fail preparation until its topology and result render are frozen
  -> then run all D/projection/tokenizer tests before any model call
```

This memo resolves the extraction problem. It does not itself resolve the one
remaining scientific construction choice.
