# Source contract v3: two-SLEEP own-experience junction

**Date:** 2026-09-13 PT  
**Name:** `TSJ-v3`  
**Status:** source/CPU-checker contract only. If adopted, this document permits
authoring and CPU-testing source/checkers against synthetic dummy bytes. It
does **not** permit scientific-root materialization, real tokenizer/model
execution, training, adapter work, GPU use, claim, or release.  
**Preserves:** the XOR causal geometry, paired DEV estimand, authentic lineage,
controls, and claim boundary of TSJ-v2.  
**Closes:** P0.1--P0.6 of
`2026-09-13_two_sleep_own_experience_junction_v2_fresh_source_readiness_audit.md`.

## 1. Exact dependency without circular GO

The upstream dependency path is exactly:

```text
research_notes/analysis/2026-09-13_m_combine4_stage2a_binding_successor_v2.md
```

It is content-bound at commit
`654b54dc` and SHA-256
`dd1f57693dfc09fae20691e1f53f11bc3b6a6d491bcb5e437aa4ed346d65df74`.
CPU source must require that exact hash and test rejection of missing/wrong
bytes. Before any scientific materialization, the root must adopt that exact
file and write one append-only `TSJ_V3_UPSTREAM_RECEIPT` containing its SHA-256, commit,
system/decode/tokenizer/base/adapter hashes, selected D1-or-D2 checkpoint hash,
selected 256-unit manifest hash, exact presentation/batch/mask/padding tape
hash, and preservation-panel hash. Two CPU checkers must reproduce the receipt.
A missing, moving, or non-source-ready upstream contract stops TSJ-v3.

This is not circular: source/checker authorship is GO against the content-
addressed contract and fail-closed receipt schema now; materialization/model/
fit remain NO-GO until a selected checkpoint and tapes fill the receipt. The
receipt may bind artifact bytes but may not change TSJ
topology, conditions, gates, order, or arithmetic.

The numerical writer acquisition report (`3/3` at A200) is an entry receipt.
The inadmissible follow-up retention attempt is neither evidence nor an entry
condition; TSJ's own two writes test the relevant longitudinal property.

## 2. Literal construction contract

### 2.1 Seeds, IDs, worlds

Master ASCII bytes, no final LF:

```text
TSJ-V3/TWO-SLEEP/XOR/2026-09-13
```

Public identifiers are ASCII:

```text
node TS3N_[A-Z2-7]{12}   port TS3P_[A-Z2-7]{12}
event TS3E_[A-Z2-7]{12}  link TS3L_[A-Z2-7]{12}
receipt TS3R_[A-Z2-7]{12} provenance TS3V_[A-Z2-7]{12}
```

For `kind,domain,world,serial`, serial starting at 0:

```text
d = SHA256(master || NUL || kind || NUL || domain || NUL ||
           uint8(world) || uint32_big_endian(serial))
id = prefix(kind) || first_12_RFC4648_base32_chars(d)
```

Reserved all-A suffix/collision is fatal; do not skip or reseed. Pools are
created before semantic roles. Sort IDs by
`SHA256(master||NUL||"pool"||NUL||id)`, sort canonical ASCII role keys by
`SHA256(master||NUL||"role"||NUL||role_key)`, then zip. Domains are exactly
`auth`, `control_filler`, `confirmation_reserved`. Concrete IDs are disjoint
from the upstream receipt and every named prior/future namespace; normalized,
role-graph, and tokenizer overlap scanners are mandatory.

Authentic role inventory/world is exactly 13 nodes
`S,M0,M1,F0,F1,H0,H1,D0,E0,J0,D1,E1,J1`, 10 ports
`a0,a1,b0,b1,q0,q1,u0,v0,u1,v1`, 10 EVENTs
`s0,s1,t0,t1,i0,i1,i2,i3,n0,n1`, 6 LINKs
`LS0,LS1,IL0,IL1,NL0,NL1`, 10 action receipts, 6 LINK receipts, and 16
provenance handles. These checker role strings never become public tokens.

Literal checker-private worlds:

```text
W0: O=0 T=1 N=0 primary_old_goal=F1 start_slot0=s0 start_slot1=s1
W1: O=1 T=0 N=1 primary_old_goal=F0 start_slot0=s0 start_slot1=s1
```

Every singleton EVENT is slot 0; slot 1 is MISS. Every LINK is slot 0;
slot 1 is MISS. Display order is ascending
`SHA256(master||NUL||"display"||NUL||public_id)`. W0 always precedes W1.

Writer seeds are literal unsigned 64-bit values:

```text
W0 0x54534a3300000000
W1 0x54534a3300000001
```

`seed(world,stage,stream)=low64(SHA256(master||NUL||world||NUL||stage||NUL||
stream))` in big-endian order. Exact stream labels are `dropout`, `optimizer`,
and `collator`. Every arm in a world/stage reuses these numerical RNG starts;
the arm name never enters a seed. S1 arms clone exact BIRTH tensors; S2 uses
the explicit ancestry map. No decode RNG is consumed because decode is greedy,
though the upstream receipt's recorded decode seed remains logged.

### 2.2 XOR topology

```text
s0: S --a0--> M_O          s1: S --a1--> M_(1-O)
t0: M0 --b0--> F_T         t1: M1 --b1--> F_(1-T)
n0: F0 --q0--> H_N         n1: F1 --q1--> H_(1-N)
```

OLD first action for Fg is `a_(g xor O xor T)`; delayed first action for Hh
is `a_(h xor O xor T xor N)`. There are also two task-inaccessible,
role-isomorphic two-EVENT OLD islands. Authentic S1 is exactly 8 EVENT+4 LINK;
authentic S2 is exactly 10 EVENT+6 LINK. Each relevant LINK has two distinct
receipt-bearing indispensable parent EVENTs. Goals, expected actions, H rows,
and future routes never enter authentic training targets.

The complete authentic route oracles are fixed:

```text
F_g: STEP a_(g xor O xor T), STEP b_(g xor T), STOP
H_h: STEP a_(h xor O xor T xor N), STEP b_(h xor T xor N),
     STEP q_(h xor N), STOP
```

O/T/N conditions substitute only the named complemented bit in these formulas;
goal twins substitute g/h. READ order may be self-chosen, but the first
irreversible STEP and complete physical route must equal the oracle.

### 2.3 Filler and transforms

`CONTROL_FILLER_POOL` is generated solely in `control_filler`: four fixed
`2E+1L` blocks and two fixed `2E+2L` blocks per world. It has no authentic
receipt semantics. Private provenance is `SYNTHETIC_CONTROL`; its model-visible
`PROVENANCE TS3V_*` surface matches authentic rows. Fillers are selected in
ascending block hash, once, without replacement. Relevant and irrelevant cuts
use the same first `2E+1L` block; atom-only uses the second/third LINK fillers;
S2 OLD+filler uses the first `2E+2L` block.

Each S1 filler block `cj` has private nodes `cj.x0,x1,x2`, ports `p0,p1`,
EVENTs `x0-p0->x1`, `x1-p1->x2`, and their valid forward LINK. Each S2
filler block has two synthetic EVENTs whose public SOURCE fields are authentic
F0/F1, whose DESTs are control-only `z0/z1`, and two synthetic crossing LINKs
from the authentic tail EVENT ending at F0/F1 to the corresponding filler
EVENT. Thus its exact row shape matches the NEW addition while no H identifier,
N destination, or factual receipt appears.

`CONTROL_TRANSFORM(bit)` preserves row ID/type/order/slot/field count/token
length/provenance-field surface and changes only the named destination plus
logically entailed LINK EVENT IDs/VIA. O transforms both start EVENT
destinations and the two start LINK pairings; T transforms both tail EVENT
destinations; N transforms both NEW EVENT destinations. A transform receipt
lists every before/after byte diff and rejects any other diff. Synthetic bytes
never enter AUTH.

## 3. Exact wire, writer, and decode pins

All text is UTF-8 ASCII, LF only, no terminal LF unless stated. Actor output
must full-match one permitted line after removing at most one terminal LF; no
other trimming/repair is legal.

Actor system:

```text
You navigate an opaque public world. Return exactly one permitted line and nothing else. THINK may reason, READ recalls one local record, STEP changes public state, and STOP is legal only when CURRENT equals GOAL.
```

Initial user:

```text
START {START}
CURRENT {CURRENT}
GOAL {GOAL}
LIMITS THINK=8 READ=10 STEP=3 STOP=1
PERMITTED
THINK <text>
READ EVENT_AT <current_node> SLOT <0-or-1>
READ LINKS_FROM <event_id> SLOT <0-or-1>
READ EVENT <event_id>
STEP <public_port>
STOP
```

THINK response is `CURRENT {CURRENT}`; STEP response is `CURRENT {CURRENT}`
or `INVALID`; READ response is one canonical row or `MISS`. Actor limits are
8 THINK, 10 READ, 3 STEP, 1 STOP, 22 calls, and 4,096 generated tokens/rollout.
Each actor call requests exactly
`min(256, 4096-cumulative_generated, 16384-context_tokens)` new tokens. A zero
allowance or length finish terminates the rollout as failure unless valid STOP
already ended it.

For INLINE, append to the initial user bytes exactly:

```text
ACTIVE_MEMORY
{CANONICAL_ROWS_IN_ASCENDING_SHA256_ORDER}
END_ACTIVE_MEMORY
```

using one LF before ACTIVE_MEMORY and between every displayed line, no final
LF. READ is then invalid. ACTIVE uses the ordinary initial user bytes with no
appendix and enables the deterministic service. Before every scored rollout,
the actor process/KV/context is fresh and contains only its exact system and
initial user message. No autobiographical text/vector/event store is mounted;
the sealed public environment persists. In ACTIVE/NATIVE/FORK, the first
non-THINK action must be child-issued READ and indispensable reads must precede
the first irreversible STEP.

The public outcome after a scheduled OLD STEP or goal-neutral NEW PROBE is:

```text
PUBLIC_OUTCOME
SOURCE {SOURCE}
PORT {PORT}
DEST {DEST}
RECEIPT {RECEIPT}
```

Those are the only bytes that reveal that destination. The later EVENT call
receives the exact EVENT user template and receipt; it is a separate fresh
call, never host-completed.

Reader system:

```text
You recall one local experienced record. Return exactly one canonical EVENT line, one canonical LINK line, or MISS. Return no explanation.
```

Requests are exactly `READ EVENT_AT {CURRENT} SLOT {0|1}`,
`READ LINKS_FROM {EVENT_ID} SLOT {0|1}`, or `READ EVENT {EVENT_ID}`. EVENT_AT
rejects a noncurrent node. Every response is one row or MISS; no aggregate,
candidate list, goal, ranking, repair, retry, or host choice exists. S1 full
two-branch search costs 6 READs; S2 costs 10.

The indispensable registry is exact. At S, EVENT_AT slot0/1 returns s0/s1.
For each `s_j`, LINKS_FROM slot0 returns `LS_j`, whose SECOND is
`t_(j xor O)`; direct EVENT of that ID returns the tail row. Those six reads
are the complete S1 two-branch witness set. For each returned tail `t_k`,
LINKS_FROM slot0 returns `NL_(k xor T)`, whose SECOND is `n_(k xor T)`;
direct EVENT returns that NEW row. These four additions are the complete S2
witness set. Every slot1 LINK request and every singleton EVENT_AT slot1 is
MISS. O/T/N registries apply the coherent Section-2.3 transform to this whole
map, never to an isolated answer row.

Canonical records:

```text
EVENT {E} SOURCE {N} PORT {P} DEST {N} PROVENANCE {V}
LINK {L} FIRST {E} SECOND {E} VIA {N} PROVENANCE {V}
```

Scheduled action, EVENT-record, and LINK-record prompts/targets are the exact
TSJ-v2 Section 4.1/5.4 bytes from whole-file SHA-256
`155d22dc66527a4fafec54c6936eb20cfeca45b654227cdd079b9fc331060a02`,
imported by exact extracted-byte SHA in the source manifest;
source copies bytes rather than retyping them. Each LINK is a separate call;
admission requires its two authentic parents and FIRST.DEST=SECOND.SOURCE=VIA.

Generation pins: upstream-imported exact base/tokenizer/chat-template and EOS/
pad IDs; no stop string; `do_sample=false`, one sequence, temperature 0,
top_p 1, top_k disabled, repetition penalty 1; caps action 64, EVENT 128, LINK 160, reader 160, actor
4,096. No retry/best-of/resample.

Writer pins: upstream-imported model/LoRA module set; rank 8, alpha 16,
dropout .05, bf16, AdamW beta1 .9 beta2 .999 eps 1e-8 weight_decay .01,
constant LR 3e-5, no warmup, no scheduler decay, batch 4, grad accumulation 1,
max sequence 16,384, response-plus-EOS loss, right padding with imported pad
ID, no ordinary example packing, truncation, split, skipped batch, gradient
scaler, or gradient clipping; gradient checkpointing enabled. LoRA bias none,
causal-LM task, amsgrad/maximize/capturable/
differentiable false, `foreach=false`, `fused=false`. A fresh optimizer begins
each TSJ sleep while named adapter tensors continue. Library/container hashes
come from the upstream receipt; mismatch stops before materialization.

## 4. Corpora, views, ancestry

`AUTHENTIC_CORPUS` contains only exact admitted child bytes and receipt-grounded
meaning-preserving views. `CONTROL_TRANSFORM` is separately and privately
labeled synthetic. The compiler cannot repair or invent AUTH.

Each canonical row uses the exact eight view prefixes frozen in TSJ-v2
Section 6.1, each repeated 25 times; target is always the exact row. Therefore
each memory unit has 200 presentations. S1: 12 units=2,400 presentations=600
memory updates. S2: 16=3,200=800.

Selected BIRTH replay is imported exactly: D1 1,024 presentations/256 updates;
D2 2,048/512. Its internal batch order/masks/padding remain byte-identical.
Memory batch order is `(repeat 0..24, view 0..7, SHA256(row))`; BIRTH and memory
batches use the exact proportional weave defined in TSJ-v2 Section 6.2.

Ancestry—not “same S1 tensors everywhere”—is:

```text
S2 AUTH       <- S1 AUTH       S2 N_SWAP     <- S1 AUTH
S2 OLD_FILLER <- S1 AUTH       S2 O_SWAP     <- S1 O_SWAP
S2 ATOM       <- S1 ATOM       S2 RAW        <- S1 RAW
```

All share the same BIRTH ancestor. Exact S1 tensor sharing applies only to
AUTH/N_SWAP/OLD_FILLER. Causal twins at the same ancestry node share their
named RNG/presentation schedule; different S1 treatments do not falsely claim
identical S2 initialization.

## 5. RAW R0--R15 exact serialization and feasibility

Define `CHAT(S,U,A)` as the exact upstream chat-template tokenization of roles
system=S,user=U,assistant=A, ending in exactly one imported EOS. Assistant
content and that terminal EOS have loss=1; every other token has loss=0. A
RAW chronology unit is the literal concatenation below; no host separator or
additional EOS is added.
This declared two-call chronology is one RAW treatment unit; the general
no-example-packing rule forbids combining any two different R units.

For OLD edge i=0..7:

```text
Ri = CHAT(S_ACTION, U_ACTION_i, A_STEP_i) ||
     CHAT(S_EVENT, U_EVENT_i_WITH_PUBLIC_OUTCOME, A_EVENT_i)
```

For OLD LINK j=0..3:

```text
R(8+j) = CHAT(S_LINK, U_LINK_j_WITH_THEN_AVAILABLE_EVENTS, A_LINK_j)
```

For NEW frontier k=0..1, in primary-first order:

```text
R(12+k) = CHAT(S_ACTION, U_GOAL_NEUTRAL_PROBE_k, A_PROBE_k) ||
          CHAT(S_EVENT, U_EVENT_k_WITH_PUBLIC_OUTCOME, A_NEW_EVENT_k)
```

For crossing LINK k=0..1:

```text
R(14+k) = CHAT(S_LINK, U_NEW_LINK_k_WITH_THEN_AVAILABLE_EVENTS, A_NEW_LINK_k)
```

Every symbolic S/U/A is the exact raw message already received/emitted in the
corresponding authentic call, byte-for-byte; the manifest stores each role,
byte SHA, token SHA, loss-run intervals, and provenance receipt. R12/R13 begin
in separate goal-neutral observation calls after the old-goal route ends, so
they contain no goal/evaluator/future answer.

RAW S1 is R0..R11; RAW S2 is cumulative R0..R15. A tokenizer witness must be
created after upstream binding and before scientific materialization. A
deterministic integer program chooses the lexicographically smallest positive
multiplicity vector and lexicographically smallest batch assignment matching
compiled presentation count, supervised target tokens, padded tokens, and
per-batch FLOPs exactly. If no witness exists, the entire TSJ-v3 source version
stops `RAW_UNSAT` before any fit. RAW cannot be dropped and DREAM language
cannot survive under this version.

## 6. Coherent response forks

Response twins use the ledger-named actor checkpoint: P30 uses S1 AUTH, P50
uses BIRTH with the authentic ACTIVE bank, and P70 uses S2 AUTH. First run
the AUTH goal rollout. For each world/goal/bit, select mechanically the
earliest AUTH READ whose registered transform changes its response. Save:
`prefix_sha256` through the exact actor request, request bytes/address/slot,
auth response bytes, transformed response bytes, allowed-diff receipt, and
the hashes of both complete service registries.

The fork replays the exact prefix and request. It returns the same addressed
row/type/syntax/line count/token count/provenance-field surface with only the
registered semantic diff, then **switches all subsequent READs to the complete
coherently transformed service registry**. It never mixes transformed and
authentic rows after the fork. Greedy continuation begins after the response.
If AUTH issued no affected READ before its first STEP, that AUTH condition and
fork fail; the checker may not choose a later/favorable request.

S1 runs response-T. POST-NEW and POST-S2 run response-O and response-N. Each
must yield the exact bit-counterfactual first STEP for both goals in each
world. The fork is request-valid, not an invalid-return alarm.

## 7. Canonical executable phase ledger

This table is the sole source of execution, truth, and resource ledgers.
`G={0,1}` expands in ascending goal order; `P={g*}`. Conditions expand in
listed order, W0 before W1. Rollout ID is `R-{phase}-{world}-{condition}-{goal}`;
model calls inside it are `.C00` through `.C21`. Fit IDs similarly use `F`.
For P10/P30, G denotes F0,F1; for P50 and the delayed P70 rows it denotes
H0,H1; P70 AUTH_OLD_RETENTION explicitly uses F0,F1.

Services: INLINE puts the complete named bank in the initial user message and
disables READ; ACTIVE is a perfect deterministic one-row service over the
same bank; NATIVE generates each row from the mounted adapter; FORK is Section
6. Actor is BIRTH unless a fitted state is named.

|phase|ordinals/world|condition (count)|actor mount|service/bank|goals|expected|role|
|---|---|---|---|---|---|---|---|
|P00 OLD formation|F001-F020|8 action,8 EVENT,4 LINK|BIRTH|public world/accepted rows|none|exact yields|S1 gate|
|P10 PRE-S1|R001-002|SUPPLIED_INLINE (2)|BIRTH|INLINE AUTH-OLD|G|`a(g xor O xor T)`; 2/2|gate|
||R003-004|SAME_AUTH_HISTORY_ACTIVE_TEXT_CEILING (2)|BIRTH|ACTIVE AUTH-OLD|G|self-READ then `a(g xor O xor T)`; 2/2|gate|
||R005-006|ATOM_TEXT (2)|BIRTH|ACTIVE AUTH events/no links|G|<=1/2|diagnostic|
||R007-008|O_TEXT (2)|BIRTH|ACTIVE O transform|G|`a(g xor (1-O) xor T)`; 2/2|gate|
||R009-010|T_TEXT (2)|BIRTH|ACTIVE T transform|G|`a(g xor O xor (1-T))`; 2/2|gate|
||R011|RELEVANT_CUT_TEXT|BIRTH|ACTIVE rel cut|P|fail/change|gate|
||R012|IRRELEVANT_CUT_TEXT|BIRTH|ACTIVE irr cut|P|success/same|gate|
|P20 S1 fits|F001-F007|AUTH,O,T,ATOM,REL_CUT,IRR_CUT,RAW|BIRTH ancestor|named tape|none|fit/cold gates|gate|
|P30 POST-S1|R001-002|AUTH|S1 AUTH|NATIVE AUTH|G|`a(g xor O xor T)`; 2/2|gate|
||R003-004|O|S1 O|NATIVE O|G|`a(g xor (1-O) xor T)`; 2/2|gate|
||R005-006|T|S1 T|NATIVE T|G|`a(g xor O xor (1-T))`; 2/2|gate|
||R007-008|ATOM|S1 ATOM|NATIVE atom|G|<=1/2|gate|
||R009-010|BIRTH|BIRTH|NATIVE BIRTH|G|<=1/2|gate|
||R011-012|FOREIGN|other world's S1 AUTH|NATIVE foreign|G|<=1/2|gate|
||R013-014|RAW|S1 RAW|NATIVE raw|G|oracle action `a(g xor O xor T)`; report|diagnostic|
||R015-016|RESP_T|S1 AUTH|FORK T|G|exact T-counterfactual; 2/2|gate|
||R017|REL_CUT|S1 REL_CUT|NATIVE cut|P|fail/change from AUTH|gate|
||R018|IRR_CUT|S1 IRR_CUT|NATIVE cut|P|AUTH action/success|gate|
|P31 preservation|C001-C280|32 interventions,8 chains<=29 calls,16 canaries|S1 AUTH|upstream exact|upstream|Section 9|gate|
|P40 NEW formation|F001-F006|2 PROBE,2 EVENT,2 LINK|S1 AUTH child|public world/accepted rows|primary first|exact yields|S2 gate|
|P50 POST-NEW|R001-002|SUPPLIED_INLINE (2)|BIRTH|INLINE AUTH OLD+NEW|G|`a(g xor O xor T xor N)`; 2/2|gate|
||R003-004|SAME_AUTH_HISTORY_ACTIVE_TEXT_CEILING (2)|BIRTH|ACTIVE AUTH OLD+NEW|G|self-READ then `a(g xor O xor T xor N)`; 2/2|gate|
||R005-006|ATOM_TEXT (2)|BIRTH|ACTIVE atoms|G|<=1/2|diagnostic|
||R007-008|O_TEXT (2)|BIRTH|ACTIVE O|G|`a(g xor (1-O) xor T xor N)`; 2/2|gate|
||R009-010|N_TEXT (2)|BIRTH|ACTIVE N|G|`a(g xor O xor T xor (1-N))`; 2/2|gate|
||R011-012|OLD_FILLER_TEXT (2)|BIRTH|ACTIVE OLD+filler|G|<=1/2|gate|
||R013-014|RESP_O_PRE (2)|BIRTH|FORK AUTH active|G|`a(g xor (1-O) xor T xor N)`; 2/2|gate|
||R015-016|RESP_N_PRE (2)|BIRTH|FORK AUTH active|G|`a(g xor O xor T xor (1-N))`; 2/2|gate|
|P60 S2 fits|F001-F006|AUTH,N,O,ATOM,RAW,OLD_FILLER|named S1 ancestry|named tape|none|fit/cold gates|gate|
|P70 POST-S2|R001-002|AUTH|S2 AUTH|NATIVE AUTH|G|`a(g xor O xor T xor N)`; 2/2|gate|
||R003-004|N|S2 N|NATIVE N|G|`a(g xor O xor T xor (1-N))`; 2/2|gate|
||R005-006|O|S2 O|NATIVE O|G|`a(g xor (1-O) xor T xor N)`; 2/2|gate|
||R007-008|ATOM|S2 ATOM|NATIVE atom|G|<=1/2|gate|
||R009-010|RAW|S2 RAW|NATIVE raw|G|oracle delayed action; report|diagnostic|
||R011-012|OLD_FILLER|S2 OLD_FILLER|NATIVE filler|G|<=1/2|gate|
||R013-014|FOREIGN|other world's S2 AUTH|NATIVE foreign|G|<=1/2|gate|
||R015-016|RESP_O|S2 AUTH|FORK O|G|exact O-counterfactual; 2/2|gate|
||R017-018|RESP_N|S2 AUTH|FORK N|G|exact N-counterfactual; 2/2|gate|
||R019-020|S1_NOWRITE|S1 AUTH|NATIVE AUTH-old|G|<=1/2; diagnostic only|diagnostic|
||R021-022|AUTH_OLD_RETENTION|S2 AUTH|NATIVE AUTH|old F goals|`a(g xor O xor T)`; 2/2|gate|
|P71 preservation|C001-C280|32 interventions,8 chains<=29 calls,16 canaries|S2 AUTH|upstream exact|upstream|Section 9|gate|

Within each compressed P30/P70 row, conditions expand exactly in written
order and goal 0 then 1; primary-only cuts use g*. P40 primary PROBE/EVENT
precedes complementary PROBE/EVENT, then LINK0,LINK1. This ledger is emitted
as immutable JSON; human tables, truth tables, and cost reports are generated
from it, never independently hand-maintained.

P00 role order is `s0,s1,t0,t1,i0,i1,i2,i3`: for zero-based k, F(2k+1) is
its scheduled action and F(2k+2) its EVENT call; F017..F020 are
`LS0,LS1,IL0,IL1`. P40 F001/F002 are primary PROBE/EVENT, F003/F004 are
complement PROBE/EVENT, and F005/F006 are NL0/NL1. P20 F001..F007 map exactly
to AUTH,O,T,ATOM,REL_CUT,IRR_CUT,RAW. P60 F001..F006 map exactly to
AUTH,N,O,ATOM,RAW,OLD_FILLER.

P20 fit `F00j` is followed immediately by cold calls
`Q-P20-{world}-{fit}-001..060`; P60 uses
`Q-P60-{world}-{fit}-001..070`. Query order is EVENT rows ascending, querying
EVENT_AT at that row's SOURCE slots 0,1 even when a SOURCE repeats; then
LINKS_FROM EVENT IDs ascending slots 0,1; then direct EVENT
IDs ascending; four invalid requests in fixed order EVENT_AT invalid/0,
EVENT_AT invalid/1, LINKS_FROM invalid/0, direct EVENT invalid; then canaries
in upstream ordinal order. Expected response is the exact registered
row/MISS/canary target. P31/P71 `C001..C032` are interventions;
`C033..C264` reserve 29 consecutive calls for each of eight chain ordinals;
`C265..C280` alias, rather than re-execute, that stage's AUTH cold-canary
Q-call IDs. Unused reserved chain calls remain zero-cost manifest slots.

The primary P30 AUTH g* route reaches F and ends without PROBE. P40 W0's
primary goal-neutral PROBE is the first model-visible N outcome in the whole
version; within each world, its primary PROBE precedes every other reveal of
that world's N. PROBE is unavailable in all earlier grammars/services.

## 8. Noncompensatory truth predicates

In **each** world: supplied/active ceilings and AUTH are 2/2 with goal
redirection; O/T/N whole-bank and response twins are 2/2 on their exact
counterfactual first action; BIRTH, FOREIGN, ATOM, S1_NOWRITE, and OLD_FILLER
are each <=1/2 on the respective dependent goals; relevant cut fails/changes
its primary action while irrelevant cut passes unchanged; S2 AUTH is 2/2 on
delayed goals and 2/2 on retained OLD goals. RAW is separately reported and
AUTH may claim DREAM advantage only if it exceeds RAW by >=1 success in each
world at both stages. No world can rescue the other.

`SUPPLIED_INLINE` is an inline exact-row ceiling with BIRTH and no READ.
`SAME_AUTH_HISTORY_ACTIVE_TEXT_CEILING` is BIRTH plus the one-row ACTIVE
service and required self-issued READ. Neither is an on-policy independent
text-memory agent; strong-baseline comparison is deferred.

## 9. Cold and controller gates

For every S1 fit, cold READ coverage is exactly: EVENT_AT both slots once per
8 EVENT rows=16 (repeated SOURCE queries remain counted), LINKS_FROM both
slots for 8 EVENTs=16, direct EVENT for 8=8, four separate invalid MISS=4,
and 16 canaries: `60` calls/fit. Seven fits give 420. S2 is 10 EVENT rows*2=20,
10 EVENTs*2 LINK slots=20, direct EVENT 10, MISS 4, canary16=`70`/fit; six
give 420. Every registered row/slot/MISS must
be exact 1.00 and canaries >=15/16.

The upstream receipt freezes preservation ordinals: intervention indices
0,2,4,6 for each of four skills=32 one-turn calls; autonomous task indices
0,4,8,12,16,20,24,28=8 tasks at <=29 calls; all 16 canaries. S1 AUTH and S2
AUTH must meet upstream minima and lose no more than one count per metric from
the exact frozen BIRTH baseline. The 16 canaries are shared with that stage's
AUTH cold gate, so incremental preservation cost is `32+8*29=264`/stage.
Rejected authentic writes stop; no rollback descendant substitutes.

## 10. Derived resource ledger

Fits remain 7 S1+6 S2=13/world=26/pair.

|selected birth|updates/fit S1/S2|updates pair|presentations pair|
|---|---:|---:|---:|
|D1|856 / 1,056|24,656|98,624|
|D2|1,112 / 1,312|31,312|125,248|

The phase ledger contains `12+18+16+22=68` route rollouts/world. Actor calls
are `68*22=1,496`; actor tokens `68*4,096=278,528`. Native model-reader
rollouts are 16 at P30 (all except the two deterministic FORK rollouts) and 18
at P70 (all except four deterministic FORK rollouts), hence
`(16+18)*10=340` model-reader calls. INLINE, ACTIVE, and FORK services are
deterministic and add no reader-model call. Cold/canary calls are 420+420=840. Formation is 26.
Incremental preservation is 528. Therefore:

```text
model calls/world = 1,496 + 340 + 840 + 26 + 528 = 3,230
model calls/pair  = 6,460
```

At output caps, formation tokens=2,880 and route-reader=54,400. Cold output is
`7*(44*160+16*256) + 6*(54*160+16*256) = 154,368`. Incremental preservation
is `2*(32*256+8*4,096)=81,920`; its canaries were already charged cold. Thus
generated tokens are:

```text
278,528 + 2,880 + 54,400 + 154,368 + 81,920 = 572,096/world
1,144,192/pair
```

Maximum padded training tokens are D1
`98,624*16,384=1,615,855,616`; D2
`125,248*16,384=2,052,063,232`. The tokenizer witness supplies the lower exact
number. The hard training-FLOP cap is
`8 * imported_parameter_count * exact_padded_training_tokens`; profiler FLOPs
and padded tokens must remain below it. Total GPU cap is 248 GPU-hours, CPU
preparation cap 8 hours, elapsed scientific wall cap 72 hours. Every partial
fit/call counts. There is no scientific retry. The sole allowed restart is a
verified pre-model-call/pre-side-effect infrastructure restart of identical
bytes; it consumes no model-call budget, is logged, and may occur once for the
whole version. Any later/uncertain infrastructure failure invalidates and
stops; no replacement world/seed exists.

## 11. Authorization, stops, and claim

`GO_CPU_SOURCE=true` only after adoption of this exact document. CPU authors
may implement schemas, deterministic generation over dummy IDs, both oracles,
ledger expansion, transform-diff checks, RAW constraint solver, arithmetic,
and fail-closed hash checks. They may not materialize scientific IDs/roots or
invoke a real tokenizer/model.

`GO_MATERIALIZE/MODEL/FIT/GPU=false` until: upstream receipt filled and
reproduced; two independently authored CPU checkers agree; fresh source audit
passes; target-disjointness and literal leakage scans pass; tokenizer-bound
RAW witness exists; custody/resource receipts pass; authentic OLD formation
is 8/8 EVENT+4/4 LINK/world; every P10 gate passes. S2 additionally requires
unchanged S1 pass, P31 preservation, primary-first N, NEW 2/2 EVENT+2/2 LINK,
and every P50 gate.

All malformed/stopped/rejected/scientific failures are ITT zero with no
replacement. Complete requires every root-local predicate, native carriage,
both preservation panels, and complete receipts.

Maximum claim remains:

> Conditional on one selected target-disjoint birth controller, one continued
> adapter in each of two complementary DEV worlds stored exact records and
> child-authored indispensable-parent links from its own public outcomes over
> two sleeps, then used self-issued single-record recalls for OLD-dependent and
> OLD+NEW-dependent held actions after clean resets, with coherent content
> interventions redirecting those actions while the selected controller was
> preserved.

No reliability, parenting, lifetime improvement, strong active-text
superiority, autonomous OLD exploration, physical compression, general
continual-learning, emergence, or whole-flywheel claim is licensed.

## 12. Designer self-audit

|audit blocker|closure|
|---|---|
|P0.1 upstream|exact future path plus fail-closed content-addressed receipt; CPU source GO is noncircular, science remains blocked|
|P0.2 phase truth/order|one canonical executable phase ledger generates calls, truth, and resources|
|P0.3 forks/ancestry|earliest changed legal READ, exact prefix/diff, coherent service switch; BIRTH ancestor distinguished from S1 tensor sharing|
|P0.4 literal pins|master/seed derivations, IDs, W0/W1, slots, fillers, messages, model imports, writer/decode settings, and distinct ceilings fixed|
|P0.5 RAW|R0-R15 exact role/message/mask serialization; tokenizer witness mandatory; RAW_UNSAT stops whole version|
|P0.6 resources|68 rollouts, old retention, exact cold coverage, calls/tokens/updates/presentations/FLOP/GPU/wall/retry caps all derived|

**Designer verdict: GO_CPU_SOURCE; NO-GO for scientific materialization,
model/tokenizer execution, fit, GPU, or claim pending the gates above.**
