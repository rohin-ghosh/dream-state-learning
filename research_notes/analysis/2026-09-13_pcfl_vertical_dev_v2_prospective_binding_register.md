# PCFL vertical DEV v2.1: prospective preparation binding register

**Date:** 2026-09-13 UTC  
**Status:** preparation specification only; no source/fixture authoring, model or
tokenizer call, benchmark generation, training, adapter, GPU, or scientific
execution occurred  
**Controls:** the passed v2.1 synthesis and exact build ledger control if this
memo conflicts with either; the exact inference inventory supplies the
denominator interpretation used here

## Ruling

The ten open implementation inputs are closed by two kinds of binding:

- **FIXED NOW:** literal templates, deterministic algorithms, seeds, schedules,
  caps, and failure rules below. They cannot change after a model output.
- **PREPARE-BIND:** exact tokenizer-dependent bytes and measured runtime bounds.
  The preparer must apply the fixed search/acceptance rule below, write the first
  admissible result, and seal its hash before any scientific generation. It may
  not choose among results using a route, goal, hidden bit, outcome, or model
  behavior.

There is no remaining discretionary scientific choice. Failure to find a valid
opaque inventory/PAD realization is `VS_ASSAY_INVALID`. The inference allowance
is an **actual charged-device-time cap**, not a requirement that every
independent per-call token safety ceiling be jointly consumed inside ten hours;
Section 9 binds that distinction. Exhausting the actual allowance is
`VS_RESOURCE_CAP`; neither failure is permission to tune.

## Compact register

| # | input | disposition | binding time |
|---:|---|---|---|
| 1 | eight writer wrappers | `W0`--`W7` below, in numeric order | FIXED NOW |
| 2 | task/READ/commit/ROUTE prompts | exact ASCII templates below; only public placeholders may be substituted | FIXED NOW; instantiated bytes PREPARE-BIND |
| 3 | `LINK_PERMUTE` | tail-pair derangement `(l0 l2)(l1 l3)` below | FIXED NOW |
| 4 | PAD | 64 loss-active target tokens above longest semantic arm; deterministic exact-token PAD search | rule FIXED NOW; exact bytes PREPARE-BIND |
| 5 | canary | forty deterministic two-edge route tasks; seeds `canary/00`--`39` | FIXED NOW |
| 6 | reachout renders | `RA`/`RB`; root 0 primary `RA`, root 1 primary `RB`; panels alternate 4/4 | FIXED NOW |
| 7 | opaque IDs | SHA-256/base32 first-valid joint inventory search under the pinned tokenizer | rule FIXED NOW; inventory PREPARE-BIND |
| 8 | roots/RNG/GPU schedule | domain-separated seeds and node-2 UUID table below | FIXED NOW, with fresh UUID health check |
| 9 | request inventory | finite inventory below; fixed calibration, actual charged time `<=10 A40h` | inventory FIXED NOW; timings PREPARE-BIND |
| 10 | resource unit | node 2 A40 device-seconds/3600 only; A100 use forbidden in this DEV | FIXED NOW |

All literal text is UTF-8/ASCII, uses LF (`0x0a`) only, has no trailing spaces,
and has no terminal LF unless the template explicitly shows `\n` after its
last line. Placeholder braces are metasyntax and never reach a model.

## 1. Writer wrappers and READ prompt

The system message for every parametric memory-worker call is:

```text
You are the child's local personal-memory reader. You receive one opaque address request and no task. Return only the exact stored memory block associated with that address. Do not explain, infer, repair, or invent. If nothing usable is remembered, return exactly MISS.
```

The eight loss-masked user-message wrappers, in fixed `view_id` order, are:

```text
W0  Retrieve the exact stored memory for this request.\n{REQUEST}\nReply with only the stored memory block.
W1  Personal memory query:\n{REQUEST}\nReturn only the exact stored block.
W2  {REQUEST}\nRead personal memory and output only its exact stored block.
W3  Use personal memory for the request below. Output the stored block only.\n{REQUEST}
W4  Lookup request: {REQUEST}\nRespond only with the exact memory block.
W5  Return the exact personal-memory block matching:\n{REQUEST}\nNo explanation.
W6  Read this local memory address and emit only the stored block.\nAddress request: {REQUEST}
W7  For this personal memory lookup, give only the exact stored block.\n{REQUEST}
```

`{REQUEST}` is exactly one already-registered `READ ...` or `PAD_...` line.
It is never a candidate list. Training order is slot-major then `W0..W7`
before the coupled sealed epoch permutation. Read panels use `W0..W7` once for
an eight-item panel and twice with the two registered panel seeds for a
sixteen-item panel. Thus no held-wrapper choice remains after outputs.

Direct-read request assignment is also fixed. The S1 sixteen-item EVENT panel
uses `READ EVENT e[j mod 8]` at item `j`, with wrapper
`W[(j+floor(j/8)) mod 8]`. The S1 eight-item LINK panel uses the structural
request roster `[READ LINKS_FROM e0, READ LINKS_FROM e1, READ LINKS_FROM e3]`
at `j mod 3`, with wrapper `W[j]`; ATOMS receives these same calls as held-out
addresses. Each six-item S2 NEW panel uses
`[READ EVENT e8, READ LINKS_FROM e1, READ LINKS_FROM e8]` twice in that order
under `W0..W5`; OLD_REPLAY receives the same six calls as held-out addresses.
Unseen and wrong-root panels each use their eight presealed addresses once under
`W0..W7`. Opaque spelling never determines roster position.

## 2. Global prompt templates

### Route actors

Modular actor system message:

```text
You operate a deterministic directed route system. Identifiers are opaque and case-sensitive. Use only public information in this conversation and exact local-memory reads. Never invent, rename, or repair an identifier. On each turn output exactly one line: a permitted READ request or one final ROUTE. At most 12 READs are allowed. The environment gives no route feedback before the complete ROUTE is committed, and there is no retry.
```

Native mounted actor system message:

```text
You operate a deterministic directed route system. Identifiers are opaque and case-sensitive. Use only public information in this conversation and your own learned memory. You have no external memory tool. Never invent, rename, or repair an identifier. Commit exactly one ROUTE line. The environment gives no route feedback before the complete ROUTE is committed, and there is no retry.
```

Both receive this user message, with only public IDs substituted:

```text
ROUTE TASK
START {START_ID}
GOAL {GOAL_ID}
Required final grammar:
ROUTE <start> <goal> : <comma-separated ports>
```

It contains no route length, port subset, candidates, dependency handles,
hidden bits, expected answer, or score. `ROUTE` output is one physical line
with no prefix, suffix, fence, or terminal LF.

### OLD experience and child commitments

The formation system message is:

```text
You are exploring a deterministic public route system and recording what you personally observe. Identifiers are opaque and case-sensitive. Never invent, rename, infer, or repair an identifier. An EXPLORE action can use only a listed public source and port. A memory commitment may use public receipts and accepted commitments visible in this wake context. After a reset, it may also use exact identifiers recalled from your own learned memory; no external memory text or hidden information is provided.
```

The eight OLD exploration opportunities use the fixed structural source order
`S_L,A,H,S_R,B,Z,S_L,B`. Each user message lists all and only the still-untried
public ports at that source, in the seed-bound visible order:

```text
EXPLORE TASK
SOURCE {SOURCE_ID}
AVAILABLE PORTS {COMMA_SEPARATED_PUBLIC_PORT_IDS}
Choose one still-untried port and output exactly:
EXPLORE <source> <port>
```

After each public receipt, the child receives:

```text
COMMIT EVENT
Using only the public receipt just observed, output exactly one physical line in this grammar:
EVENT <event_id> AT <source> DID <port> GOT <destination> EVIDENCE <receipt_id>
AVAILABLE EVENT ADDRESS {FRESH_EVENT_ID}
Use that fresh address as event_id. Copy every other identifier exactly. Output no other text.
```

After all eight receipts, exactly four successive LINK requests are issued:

```text
COMMIT LINK
Using only public EVENT commitments visible in this wake context and exact identifiers you recall from your own learned memory, output one not-yet-recorded directly chained pair in exactly this grammar:
LINK <link_id> FROM <event_id_1> THEN <event_id_2> VIA <shared_node> EVIDENCE <receipt_id_1>,<receipt_id_2>
AVAILABLE LINK ADDRESS {FRESH_LINK_ID}
Use that fresh address as link_id. Output no other text.
```

The request never names which pair to choose. Duplicate, malformed, unsupported,
or missing output consumes its one opportunity and remains in the denominator;
there is no correction or retry.

The one fresh address is a chronologically presealed empty storage handle, not
a semantic field, candidate memory, or roster. It is identical across the
appropriate collision mates and selected by stage/slot before outputs. This
does not authorize the compiler to fill or repair it after generation.

After reachout, the ordinary public result in each sealed R continuation reveals
the applicable public port `q_R`. The child then receives exactly one use of the
same EXPLORE template with public source `H` and the singleton revealed port,
commits `EXPLORE H q_R`, and receives the normal public executed-event receipt.
It then receives exactly one EVENT request and two LINK requests using the same
literal templates. Its context contains only the permitted sterile post-S1
material in the passed protocol. In particular, no OLD row, receipt, roster,
service return, or compiler state is substituted into any template. Permitting
weight-recalled identifiers in the global LINK instruction is necessary here:
the two NEW LINKs are otherwise syntactically impossible after the required
textual OLD-memory deletion. The instruction supplies no identifier or answer.

### Reachout

The reachout system message is:

```text
Choose one public experiment that is useful for the stated route goal. Identifiers are opaque and case-sensitive. Use only the public task and your own learned memory. The result is not shown until after commitment. Output exactly one line: PROBE <probe_id>. There is no retry.
```

The public task bytes are defined in Section 6 below. Every scientific actor,
memory-worker, formation, and canary generation uses
`temperature=0.7`, `top_p=1.0`, `top_k=-1`, `n=1`, and its registered common
random seed. Per-task actor output is cumulatively capped at 2,048 tokens;
memory returns at 4,096 tokens; no call can silently start a second sample.

## 3. `LINK_PERMUTE`

Number authentic old links in structural order `l0,l1,l2,l3`. Preserve each
row's `link_id`, first event, and first evidence receipt. Replace its tail
triple `(second_event, shared_node, second_receipt)` with the donor selected by:

```text
pi(0)=2, pi(2)=0, pi(1)=3, pi(3)=1
```

Thus every tail is changed and every resulting LINK is endpoint-incompatible.
The response address is still derived from the preserved first event, leaving
the same three `READ LINKS_FROM` query shapes. The four synthetic lines are
rendered mechanically from this mapping, tainted `CONTROL`, and never enter an
authentic lineage. The mapping uses structural slot numbers only—not opaque
lexicographic order, a future route, goal, hidden bit, or model output.

## 4. PAD and exact target-token equalization

For each stage, let `Lmax` be the largest semantic-only loss-active target-token
total among its arms after the real chat template and assistant EOS are counted.
The fixed target is:

```text
Lstage = Lmax + 64
```

The reserve `64` is fixed now and is not searched. Every semantic block occurs
under all eight wrappers, so all deficits are divisible by eight. Divide each
arm's per-view deficit over its PAD slots in slot order as evenly as possible
(earlier slots receive the remainder).

Requests are the literal `PAD_S1_00` through `PAD_S1_05` or `PAD_S2_00`
through `PAD_S2_02`, using only the prefix/count needed by that arm. For a PAD
slot needing `t` loss-active tokens including EOS, enumerate tuples
`(a,b,c)` in increasing `a+b+c`, then lexicographically, with each coordinate
in `0..255`, and candidate bytes:

```text
padvoid{(" x" repeated a)}{(" y" repeated b)}{(" z" repeated c)}\n
```

The PREPARE-bound target is the first candidate whose full assistant rendering
has exactly `t` active tokens, sequence length `<512`, and zero match under the
EVENT, LINK, READ, ROUTE, EXPLORE, and PROBE parsers. It must contain no
registered world identifier and none of the uppercase tokens `EVENT`, `LINK`,
`READ`, `ROUTE`, `EXPLORE`, `PROBE`, or `MISS`. Search failure for any slot is
`VS_ASSAY_INVALID`; reserve, semantic rows, and dose remain unchanged.

## 5. Forty-item generic canary

For `i=00..39`, construct a namespace-disjoint public micrograph with IDs
`CNiS,CNiM,CNiG,CNiX` and ports `CPiA,CPiB,CPiX`. It has exactly these edges:

```text
CNiS --CPiA--> CNiM
CNiM --CPiB--> CNiG
CNiS --CPiX--> CNiX
```

Even `i` renders edges in order `0,2,1`; odd `i` renders `2,1,0`. The prompt is:

```text
CANARY ROUTE TASK
PUBLIC EDGES
{THREE_EDGES_IN_REGISTERED_ORDER}
START CNiS
GOAL CNiG
Return exactly one line in this grammar:
ROUTE <start> <goal> : <comma-separated ports>
```

The registered exact action is `ROUTE CNiS CNiG : CPiA,CPiB`. Canary IDs never
occur in a world, corpus, wrapper, PAD target, or scientific task. The forty
generation seeds are `seed("canary/00")` through `seed("canary/39")`; C0 and
every authentic candidate use the same prompt/seed pair. Before any fit, C0
must itself produce legal form on at least 38/40 or the canary is invalid.
Candidate acceptance remains legal form `>=38/40` and exact-route correctness
no more than `2/40` below the paired C0 exact-route score. Missing/truncated
action or Markdown/private dialect is illegal. A syntactically legal but wrong
route remains legal and scores zero only in the separate exact-route column;
raw-hash diversity is reported alongside both columns to expose collapse.

## 6. Reachout renders

`RA` and `RB` contain identical facts and differ only in neutral surface/order:

```text
RA:
PROBE TASK
START {START_ID}
GOAL {GOAL_ID}
AVAILABLE PROBES
1. {PROBE_0} TESTS {SOURCE_0} TO {DESTINATION_0}
2. {PROBE_1} TESTS {SOURCE_1} TO {DESTINATION_1}
Commit exactly: PROBE <probe_id>

RB:
PROBE TASK
START {START_ID}
GOAL {GOAL_ID}
PROBE OPTIONS
1. TEST {SOURCE_1} TO {DESTINATION_1} USING {PROBE_1}
2. TEST {SOURCE_0} TO {DESTINATION_0} USING {PROBE_0}
Commit exactly: PROBE <probe_id>
```

`PROBE_0` is the structural frontier probe and `PROBE_1` the isolated matched
probe before opaque IDs are allocated; neither word reaches a model. Every
pre-outcome render omits R, D, outcomes, route ports, and usefulness labels.
The 32 excluded-root certificate uses both renders once for every
`root x O x goal`, giving each structural probe position exactly 16/32.

The eight-view DEV panel uses `RA,RB,RA,RB,RA,RB,RA,RB` with seeds
`seed("reachout-panel/00")` through `/07`. The one lineage primary is `RA` for
DEV root 0 with `seed("reachout-primary/0")`, and `RB` for DEV root 1 with
`seed("reachout-primary/1")`. This balance is by root index, never observed
performance.

## 7. Opaque inventory search

Define:

```text
seed(label) = big-endian integer from the first 8 bytes of
SHA256(ASCII("PCFL-V2.1-PREP\0") || ASCII(label)), masked to 63 bits.
```

Namespaces use the fixed prefixes `N_` (node), `P_` (port), `E_` (event),
`L_` (link), `Q_` (probe), `R_` (receipt), and `G_` (goal). PAD requests are the
literal Section 4 strings and are not part of this opaque inventory. Required
identifier slots are ordered by root class/index, namespace in the order above,
then frozen structural index. For each slot enumerate `salt=0,1,...,999999`. A
candidate ID is the namespace letter, underscore, and the first ten RFC-4648 base32 characters
of `SHA256(master_seed || NUL || namespace || NUL || decimal_index || NUL ||
decimal_salt)`. Candidate bytes are fixed-width uppercase ASCII.
`master_seed` is the unsigned eight-byte big-endian encoding of the applicable
`seed("opaque/...")` value.

For each candidate bare-token length `L=4,...,12`, retain for every slot the
first 4,096 salt-ordered candidates having bare length `L` and satisfying the
local uniqueness/keyword tests. Run deterministic depth-first constraint
search in the slot order above, candidate salt order ascending, immediately
pruning uniqueness, substring, and every fully instantiated substitution-class
constraint. The PREPARE-bound inventory is the first complete solution at the
smallest `L`; within `L` it is the lexicographically first salt vector found by
that fixed traversal. This replaces an intractable enumeration over all joint
salt vectors while preserving first-valid, output-blind selection. It must
satisfy all of:

1. all required IDs from the already-frozen structural topology exist, are
   namespace-disjoint and globally unique, and none is a substring of another;
2. all bare IDs have one common tokenizer length selected as the smallest
   feasible length in `4..12` tokens;
3. every registered grammar row, query, twin replacement, derangement
   replacement, collision render, and reachout order mate has equal token count
   within its prospectively defined substitution class;
4. the Section 4 PAD algorithm exactly equalizes every arm with no sequence
   reaching 512 tokens; and
5. no ID collides with a prompt keyword, canary ID, PAD bytes, or parser prefix.

The acceptance test enumerates the complete structural cube, not a realized
hidden outcome, and reads no oracle route, future answer, model output, or DEV
score. Tokenization receipts for every candidate and every accepted
substitution class are sealed. Exhausting every fixed candidate pool/length stops
`VS_ASSAY_INVALID`; there is no redraw after scientific output.

## 8. Seeds and GPU schedule

All seeds use the function above. Exact domains are:

```text
opaque/{excluded/0..3,disposable/0,dev/0..1}
root/{excluded/0..3,disposable/0,dev/0..1}
fit/dev/{0..1}/{S1,S2}
dropout/dev/{0..1}/{S1,S2}
shuffle/dev/{0..1}/{S1,S2}/epoch/{0..4}
generation/{stage}/{root}/{comparison_block}/{item}/{view}/{turn}
canary/{00..39}
reachout-panel/{00..07}
reachout-primary/{0..1}
```

Arms within one root/stage share initialization, dropout, slot/view order, and
epoch permutation; the arm name is deliberately absent from those seed labels.
Every registered matched causal panel also shares the generation seed: all
conditions in one `comparison_block` omit arm/condition/outcome from the seed,
and service-loop actor turn `t` and memory-read turn `t` use the same respective
turn seed across conditions. The R0/R1 NEW continuations likewise share seeds
after their byte-identical pre-outcome state; only the ordinary public outcome
differs. Unmatched tasks receive distinct comparison-block/item identities.
Canary C0 is generated exactly once globally and its forty sealed bytes are
reused for every paired candidate comparison because checkpoint, prompt,
decoding configuration, and seed are identical; it is never regenerated or
selected. DEV root 0 realizes `O=0`, root 1 `O=1`; their canonical later-life branches
are respectively `R=0` and `R=1`. These assignments are balanced by index and
cannot be redrawn.

The authoritative node is `ipp2-ovx-p2-08`, with the exact UUID schedule from
the resource audit:

```text
GPU0 GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0  S1 root0 AUTH         / S2 root0 FULL_R0
GPU1 GPU-e7a322fc-fe84-919f-7534-cdfefb6ce1e4  S1 root0 ATOMS        / S2 root0 FULL_R1
GPU2 GPU-d2db2a6a-a308-1782-bf41-e41411d8dc05  S1 root0 EVENT_TWIN   / S2 root0 OLD_REPLAY
GPU3 GPU-c9450d3d-0455-f034-b9bf-7f8956e44733  S1 root0 LINK_PERMUTE
GPU4 GPU-d304a15c-516a-16a0-a926-a560304077cc  S1 root1 AUTH         / S2 root1 FULL_R0
GPU5 GPU-0cc84073-37a0-4f7a-e555-11671425bd03  S1 root1 ATOMS        / S2 root1 FULL_R1
GPU6 GPU-a064bca2-bddc-73ad-faf1-a4fbcb49fecf  S1 root1 EVENT_TWIN   / S2 root1 OLD_REPLAY
GPU7 GPU-7c213554-a6c0-5c5a-1117-0422c8eee4ed  S1 root1 LINK_PERMUTE
```

A fresh successful product/UUID/process/free-memory check is mandatory
immediately before launch.

## 9. Finite request and resource inventory

The following is the maximum full-pass inventory. An early failed root deletes
unlaunched descendants but never enlarges a count.

| stage | single-call actor tasks | service-loop actor tasks | direct memory-worker calls | formation calls | canary calls |
|---|---:|---:|---:|---:|---:|
| zero-fit delayed/reachout | 704 | 96 | 0 | 0 | 40 C0 |
| disposable + two DEV OLD formation | 0 | 0 | 0 | 60 | 0 |
| S1 evaluation, two roots | 128 | 96 | 224 | 0 | 80 |
| reachout, two roots | 18 | 64 | 0 | 0 | 0 |
| four R continuations/NEW formation | 0 | 0 | 0 | 16 | 0 |
| S2 evaluation, two roots | 256 | 320 | 100 | 0 | 160 |
| **total** | **1,106** | **576** | **324** | **76** | **280** |

The decompositions are fixed:

- zero-fit: 640 delayed plus 160 reachout tasks; only 64+32 use the linked
  service;
- S1/root: 64 EVENT reads, 32 LINK/held-out-LINK reads, 16 refusal reads; 16
  AUTH +16 ATOMS +16 AUTH-cut service routes; 16 each AUTH/ATOMS/TWIN/PERMUTE
  native routes;
- reachout/root: one primary + eight native-panel calls; eight each
  AUTH/cut/OFF/wrong-root service tasks;
- S2/root: 32 OLD +12 NEW +6 OLD_REPLAY-held-out-NEW direct reads; 32 FULL old
  retention +32 FULL delayed +64 OLD/NEW cuts +32 OFF/wrong service tasks; 32
  FULL +32 OLD_REPLAY +32 cross-mount +32 OFF/wrong native tasks.

This binds the four endpoint ambiguities without duplicating a scientific
denominator: S1 EVENT_TWIN and LINK_PERMUTE redirection are native-only; S2
OLD-route retention is service-only; pooled OLD_REPLAY is native-only. Each
remains the passed panel size. The twelve direct OLD_REPLAY held-out-NEW calls
(three addresses x two views x two roots) close its already-required
zero-usable-false-row check; they do not score route success.

The S2 OLD-retention roster is no longer implicit. For each FULL adapter it is
exactly sixteen calls: the first eight registered S1 EVENT-panel cells (one
`READ EVENT e0..e7`, paired to `W0..W7`) plus the complete eight-cell registered
S1 LINK panel, with the exact same requests, wrappers, item identities, and
generation seeds used for the S1_AUTH reference. Thus it is 16 calls per FULL,
32 per root, and 64 total; the `within 1/16` comparison is paired cell by cell.

A service-loop task has at most 13 actor generations (12 READ decisions plus
one ROUTE), at most 12 memory calls, 2,048 cumulative actor output tokens, and
4,096 cumulative returned-memory tokens. The 96 zero-fit service tasks use a
deterministic text backend, not a model memory worker. All other service loops
(480 tasks) can therefore cause at most 5,760 memory-worker generations.
Including 324 direct reads, the maximum is 6,084 memory-worker generations.
Total actor-side generation transactions are at most
`1,106 + 13*576 + 76 + 280 = 8,950`.

Formation is independently finite:

```text
28 EXPLORE calls x 128 tokens = 3,584
28 EVENT calls   x 192 tokens = 5,376
20 LINK calls    x 256 tokens = 5,120
TOTAL              76 calls    = 14,080 output tokens maximum
```

No malformed formation output creates a retry. Actor scientific tasks retain
the passed 2,048-token cumulative limit; direct memory calls are capped at 512
output tokens; canaries at 128. Actor contexts are capped at 16,384 input
tokens, direct-memory prompts at 512, formation contexts at 16,384, and canary
prompts at 1,024, with no truncation. The preparer must materialize one
immutable row
per logical task/call with prompt hash, model state, seed, token ceilings,
allowed ancestry, and stage/GPU identity. Its recomputed totals must equal this
table or preparation stops.

The scientific inference schedule has exactly 31 cold engine loads at maximum:
eight zero-fit shards, one disposable-formation worker, two DEV-OLD workers,
eight S1-evaluation workers, two reachout workers, four R-continuation workers,
and six S2-evaluation workers. C0 canary calls run inside the zero-fit workers;
candidate canaries run inside their corresponding S1/S2 evaluation workers.
No extra engine load may be invented for retry or convenience. The four fixed
calibration classes below add exactly four charged preparation loads and are
separately present in the immutable request ledger: 35 inference-side cold
loads in the complete maximum schedule.

Before any scientific generation, run exactly four excluded-data shape profiles,
each with a cold load and verified release: (A) single-call native actor; (B)
one complete 12-read actor+LoRA-worker service loop; (C) one standalone LoRA
memory read; and (D) formation/canary, using the slower of the fixed 256-token
LINK shape and 128-token canary shape. Longest means tokenizer length only,
with canonical hash as the tie-break; it cannot use an answer or scientific
model behavior. Record both ordinary fixed-decoding completion and a forced-cap
stress timing, and record load/release seconds separately from generation. No
safety multiplier, historical throughput constant, or assumed batching gain is
introduced.

Calibration device time itself is charged. The preparer reports both ordinary
profile multiplication and the deliberately pessimistic forced-cap joint
envelope against the exact inventory. The latter is a stress diagnostic, **not
a launch gate**: Section 14 of the controlling protocol caps actual aggregate
device time but never states that all per-task token safety ceilings must be
jointly consumed inside that cap. Treating the stress envelope as controlling
would add a new, likely impossible assay gate from an accounting memo.

Actual charged inference residence—including the four calibration loads and
at most 31 scientific loads—has the controlling hard abort at 36,000
A40-seconds. The request ledger, call/token ceilings, and load count must be
complete before launch, but only incomplete accounting, a non-A40 device, or
actual charged-time exhaustion is `VS_RESOURCE_CAP`. Do not shrink denominators,
lower per-task safety maxima, reuse a scientific output, raise throughput
assumptions, or migrate hardware in response. Natural EOS may leave the fixed
token allowance unused; that is ordinary execution, not denominator tuning.

## 10. Resource unit

The unit is physical node-2 NVIDIA A40 device-seconds divided by 3,600. Sum
time over devices; parallel wall time is never substituted. Training is charged
separately under the frozen 7 A40-hour cap and includes fit load/save/cleanup.
Inference includes its calibration, engine load/unload, formation, zero-fit,
service, native, reachout, and canary device residence. CPU preparation and
reduction are reported but not converted into GPU-hours.

An A100 is not an A40-equivalent in this protocol. If any bound UUID reports a
different product, preparation stops. Using the A100 node would require a new
prospective resource-unit amendment and actual A100-hour reporting; it cannot
silently satisfy this register.

## Final preparation gate

The preparer emits one hash-bound `binding_manifest.json` containing the
literal template hashes, first-valid opaque inventory and token receipts, PAD
bytes/counts, all seeds, exact full GPU UUIDs, instantiated task/request hashes,
the complete request inventory, calibration artifacts, and projected/actual
resource arithmetic. It must be sealed before the disposable formation call.

The register is intentionally mechanical. It adds no memory semantics, target,
answer, candidate, parent, or new fitted arm. Once its PREPARE-BIND fields are
filled, an implementation has no legal choice conditioned on scientific
outputs.
