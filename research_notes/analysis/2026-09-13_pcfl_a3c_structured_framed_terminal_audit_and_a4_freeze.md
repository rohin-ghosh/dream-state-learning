# PCFL A3C structured-framed terminal audit and conditional A4 freeze

**Date:** 2026-09-13 PT  
**Role:** independent result audit plus prospective documentation-only design  
**Scope:** exposed-root C0 interface development; no builder/runtime source,
model, tokenizer, adapter, benchmark, process, GPU, or remote mutation

## 0. Verdict

The terminal node-2 `A3C_STRUCTURED_FRAMED_SMOKE` result is valid on its
narrow terms:

- exactly `25/56` native calls were made;
- all `8/8` first responses were exact typed `THINK` turns;
- every task underwent a recurrent `THINK -> fixed CONTINUE -> next native
  call` interaction;
- all `8/8` tasks ended in a strict typed terminal `ROUTE`, so the joint
  physical interface gate passed;
- legal routes were `0/8` and graph-successful routes were `0/8`; and
- the run used the clean C0 mount, zero fits and zero updates.

Thus A3C closes the physical typing defect in A3B. It does **not** improve
graph use. The residual failure is now localized above turn framing: the
model does not reliably maintain a continuous path, backtrack from dead
branches, or preserve the distinction between node and port identifiers.

The evidence makes the one predeclared generic-procedure rung eligible. This
memo freezes the smallest `A4_GENERIC_PATH_STACK_FRAMED_SMOKE` below. A4 is a
single conditional localization, not a prompt sweep. If its eight-task graph
gate fails, stop the 7B PCFL supplied-memory reader branch.

## 1. Authoritative artifacts and identities

Native result root:

```text
/localhome/local-rohing/astra_diagnostics/
  pcfl_interface_a3c_structured_framed_smoke_20260913_attempt1/
```

Bound stage and actor:

```text
stage: A3C_STRUCTURED_FRAMED_SMOKE
model: Qwen/Qwen2.5-7B-Instruct
revision: a09a35458c702b33eeacc393d103063234e8bc28
mount: C0 (no adapter)
GPU: GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0
fits / updates: 0 / 0
material: RESEARCHER_AUTHORED_EXCLUDED_ROOT_CEILING_NOT_CHILD
```

Important hashes:

```text
manifest file:       c7a2f3841bd1beabfa03ee2b571baa46eb416c6960fe04f3f2d9dfd4220bbf40
manifest payload:    3ad5310f2958caf53501a793031d4a731a1e94b76c7a912e4ebc58a664e242a1
roster file:         3811b35148124cc7072cb05e208427f45cefb62bc6dd336b10863a93f9f40fc3
roster payload:      ddfbbef2240016e94e709105c12abf33f37fc964503f75991546fce98be287be
report file:         138a2a9344de7bcc720423b85705ae174facb3942d4844fca4fa827196a5f8a9
report payload:      62e925d4f30af962c9a9702fc561de42da4ec77c37874253f73a33d0ac710fae
completed file:      6aa24d43386f8c1f7ef8b5662d1ffb5dba7bc19d265a0da2e26f132965e45de5
completed payload:   f46978fbad06b52dd9a36a21171258e1c709fc12d69c78cf1f1df1019fcb4930
outer collection:    67a5d82b75c86e6f5265a39bdcc3790ae5fd78ec688fb3cf450d9831e1088f24
```

The completed inventory names `162` files. I independently SHA-256 rehashed
all `162`; there were zero missing files and zero mismatches. There are
exactly `25` attempt records, `25` attempt-request sidecars, and `25` complete
native request/render/raw/response quartets.

## 2. Static grammar and physical recurrence

The only A3C sampling constraint was the same static grammar on every slot:

```regex
(?:THINK [^\r\n]*[^\s\r\n][^\r\n]*|ROUTE N_[A-Z2-7]{10} N_[A-Z2-7]{10} : P_[A-Z2-7]{10}(?:,P_[A-Z2-7]{10})*)\n?
```

It describes lexical types only. It contains zero concrete `N_`, `P_`, or
`E_` identifiers and enumerates no registered ID, candidate route, route
length, answer, or first action. The same THINK-or-ROUTE union was available
on every first and later slot; `external_first_think=false`. This is syntax
scaffolding, not answer selection.

The eight A3B and A3C tasks have exactly identical case identities, root/cell
objects, goals, user graph bytes, system bytes, sampling seeds, and caps. The
sole scientific delta is the static typed-output grammar. Both use:

```text
temperature: 0
physical stop: first LF, omitted from returned text
per turn: 256 generated tokens
per task: 2,048 generated tokens
THINK cap: 6
call cap: 7 per task / 56 total
THINK response: one fixed answer-free CONTINUE
```

Native receipts show:

```text
calls:          25
THINK turns:    17
ROUTE turns:     8
prompt tokens:  16,107
output tokens:   1,503
LF stops:         9
EOS stops:       16
length stops:     0
```

Every one of the 25 returned strings contains no CR or LF and exactly matches
its native raw returned text. THINK counts by task remain
`1,1,3,2,2,1,3,4`; calls by task remain `2,2,4,3,3,2,4,5`. Therefore A3C
passes the predeclared physical gate: first THINK `8/8` and recurrent
THINK-plus-strict-terminal histories `8/8`.

This is operational recurrent thinking, not autonomous metacognition. The
system requests at least one THINK, the host supplies the LF boundary and
fixed CONTINUE, and the graph is fully visible.

## 3. Exact comparison with A3B and A2

The selected eight A2 tasks have the same case/root/cell/goal, user graph and
seed values. A2 differs in having no THINK instruction or recurrent budget.
The scored comparison is:

```text
                         strict terminal    legal route    graph success
A2 direct                    7/8               0/8             0/8
A3B LF recurrent             4/8               0/8             0/8
A3C typed + LF recurrent     8/8               0/8             0/8
```

All `17` A3C THINK strings, including their per-task grouping, are byte-for-
byte identical to A3B. Four of eight final ROUTEs are also byte-identical.
The grammar changed the other four final renderings enough to make them
strict, but did not change any thought or make any path legal. The exact ideal
and submitted port lists are below; these are the full identifiers, not
normalized labels.

| root/goal | ideal five-port route | A2 submitted ports | A3C submitted ports |
|---|---|---|---|
| 0/0 | `P_7MGNA5ALJT,P_4RWKAJVRXP,P_US3ABWJMJ3,P_Z24XENARRH,P_RK7VLTKHNM` | `P_7MGNA5ALJT,P_RK7VLTKHNM,P_FOPIRGXLPW` | `P_7MGNA5ALJT,P_JFTRJJNMXM,P_RK7VLTKHNM` |
| 0/1 | `P_7MGNA5ALJT,P_4RWKAJVRXP,P_US3ABWJMJ3,P_Z24XENARRH,P_FOPIRGXLPW` | `P_7MGNA5ALJT,P_CFZQL5YFH3,P_FOPIRGXLPW` | `P_DPH5JSJYDT,P_IPQ2WLA2DK,P_APBZHN7V4U,P_6TUR2VALJP` |
| 1/0 | `P_CU72HSSTHQ,P_PG3IQT75KG,P_Q5KBAFY6SQ,P_O66CHZFQQF,P_QKUOHFCFN7` | `P_CU72HSSTHQ,P_QKUOHFCFN7,P_P4ISYQYYUR` | `P_RPRTAHQJHF,P_LC57LINCXI` |
| 1/1 | `P_CU72HSSTHQ,P_PG3IQT75KG,P_Q5KBAFY6SQ,P_O66CHZFQQF,P_CLTAYE7KH3` | `P_RPRTAHQJHF,P_CLTAYE7KH3` | `P_RPRTAHQJHF,P_LC57LINCXI,P_CLTAYE7KH3` |
| 2/0 | `P_UKIGM5XADX,P_NXINQGYHG4,P_UF3VWEYYWN,P_BXHVFSUI45,P_U6CRRINMLI` | `P_UKIGM5XADX,P_SL7MPZHV2J,P_U6CRRINMLI` | `P_DSFWIYNL3V,P_V7JDYLIKJ2,P_JKGQFEUMDQ,P_U6CRRINMLI` |
| 2/1 | `P_UKIGM5XADX,P_NXINQGYHG4,P_UF3VWEYYWN,P_BXHVFSUI45,P_BZOTFNJ5FE` | `P_UKIGM5XADX,P_BZOTFNJ5FE` | `P_UKIGM5XADX,P_NXINQGYHG4,P_JKGQFEUMDQ,P_BZOTFNJ5FE` |
| 3/0 | `P_Y4YTR3GSDB,P_R2GBO7FYMF,P_G2BXGAQCJU,P_E6ERNF6OLY,P_FK4GQNFXOT` | `P_Y4YTR3GSDB,P_FK4GQNFXOT,N_Z5UNBWSFET` | `P_Y4YTR3GSDB,P_Y5DKX2EZGE,P_GO2AIQ5YGW,P_AKDYDWJMQJ,P_Z5UNBWSFET` |
| 3/1 | `P_Y4YTR3GSDB,P_R2GBO7FYMF,P_G2BXGAQCJU,P_E6ERNF6OLY,P_ELHF2YQISI` | `P_PYBULW2CX6,P_ELHF2YQISI` | `P_Y4YTR3GSDB,P_ELHF2YQISI` |

The result is not merely “wrong answer.” It has a stable structure:

- `7/8` A3C routes execute at least one legal prefix edge, but only one task
  reaches two consecutive legal edges; after that the path state breaks;
- `6/8` contain a `P_...` string absent from every visible port and matching
  the suffix of a visible node: the grammar made a node-shaped choice
  syntactically port-shaped without fixing its semantic role;
- the remaining `2/8` use only registered ports but splice non-adjacent
  transitions or omit bridge edges; and
- several THINK traces choose a legal first edge into a dead branch and then
  continue as though another branch's downstream nodes were adjacent.

So the remaining failure has three coupled parts:

1. **continuous path state:** the next edge is not consistently constrained
   to have source equal to the current destination;
2. **branch state:** a dead branch is not explicitly abandoned before another
   branch is spliced in; and
3. **typed semantic roles:** destination nodes are often emitted as if they
   were ports.

A3C proves the wire format can carry recurrent typed thought and action. It
does not support a claim that more thought improved reasoning: its thoughts
are exactly A3B's and all scored semantic outcomes remain zero.

## 4. Custody, replay and release

- `custody.json` says `native_actor_custody_verified=true`, binds the actor
  identity, and independently totals 25 calls, 16,107 prompt tokens and 1,503
  output tokens.
- `replay.json` says `local_replay_valid=true` with the report payload hash.
  It intentionally retains `native_custody_verified=false` and
  `full_assay_qualified=false`; neither may be promoted.
- `completed.json` is `COMPLETE`, but intentionally says
  `gpu_released=false` and `outer_release_required=true`. That stage-local
  flag is not a failed release; the outer controller owns the release proof.
- The outer worker exited with return code `0`; its owned process group was
  empty and `owned_group_released=true`.
- The outer post-run GPU query bound to the expected UUID was empty, the
  direct queue matched, and the CVD audit was clear. CVD status is
  `PASS_WITH_EXPLICIT_NON_WORKER_SERVICE_EXCEPTIONS` for the already disclosed
  systemd/PAM init pair, not for any model worker.

This is sufficient custody and release for this exposed-root exploratory
diagnostic. It is not a clean-lineage or full-assay certificate.

## 5. Frozen conditional A4 procedure

### 5.1 Eligibility and sole delta

A3C passed physical typing and failed graph semantics, so exactly one generic
procedure condition is now eligible. Name it:

```text
A4_GENERIC_PATH_STACK_FRAMED_SMOKE
```

It must use the exact same eight A3C cases, root/cell/goal objects, complete
EDGE rows and row order, user bytes, sampling seeds, model revision, C0 mount,
temperature, tokenizer/chat template, static THINK-or-ROUTE grammar, first-LF
transport, fixed CONTINUE, parser, route scorer, `256`-token turn cap,
`2,048`-token task cap, six-THINK cap, seven-call task cap, and `56`-call total
cap. `external_first_think` remains false. There are zero fits and updates.

The **only** scientific delta is appending these exact generic bytes to the
system message:

```text
GENERIC ROUTE PROCEDURE
Use THINK turns to track CURRENT NODE, PATH, and BRANCH STACK separately. PATH is an ordered list of complete source, port, destination edge triples; never use a node field as a port.
Begin CURRENT NODE at START with empty PATH and BRANCH STACK.
At a branch, keep untried outgoing EDGEs on BRANCH STACK. Append an EDGE only when its source exactly equals CURRENT NODE, then set CURRENT NODE to its destination.
If that choice cannot reach GOAL, remove it and every later EDGE from PATH, return CURRENT NODE to the newest earlier branch with an untried EDGE, and try that EDGE.
Before ROUTE, check every PATH triple against a visible EDGE row, check that each destination equals the next source, check that the first source is START and the final destination is GOAL, then emit exactly the PATH port fields in order.
```

This block contains no concrete identifier, scored route length, route prefix,
first port, answer, candidate list, worked example, hidden role or private
address. It teaches only generic depth-first path bookkeeping and final
edge-by-edge verification. Before launch, the builder should freeze and hash
the exact block and automatically assert that it contains no concrete
`[NEP]_[A-Z2-7]{10}` match.

### 5.2 Exact eight-task gates

All gates use the fixed denominator of eight; stopped and uncalled slots stay
in the artifact.

**Preflight gate:** exact parity with A3C for every item above; static grammar
hash unchanged; procedure block scan clean; maximum `56` calls; no retry,
repair, parser extraction, dynamic ID enumeration, candidate scoring, READ,
service return, adapter, or fit. A preflight miss means no model launch.

**Physical gate:**

- at least `7/8` tasks have an exact accepted first `THINK`;
- at least `7/8` tasks have a history containing accepted THINK and one strict
  terminal ROUTE;
- zero mixed or repaired responses are accepted; and
- at most one task ends malformed, length-limited, or budget-limited.

**Semantic gate:** at least `7/8` of the *same tasks* jointly satisfy accepted
THINK history, strict ROUTE, `legal=true`, and `graph_success=true`. Syntax and
semantic counts are also reported separately; they cannot compensate for one
another.

Decision rule:

1. If the physical gate fails, stop. Do not edit the algorithm, grammar or
   cap and retry.
2. If physical passes but semantic is `<7/8`, stop the A4 and 7B supplied-
   memory reader branch. Do not run a 64-task panel, active READ integration,
   LINK fit, or connected LoRA assay through an actor that lacks its supplied-
   graph ceiling.
3. If both gates pass, freeze every A4 byte and run it once over the complete
   exposed 64-task exact-graph panel. That panel requires at least `60/64` on
   the same joint THINK + strict + legal + graph-success intersection. The
   eight smoke cases are not added again or treated as an independent sample.
4. A full-panel miss is terminal for this interface version. A full-panel
   pass selects A4 as the supplied-graph reasoner used in the separately
   designed recurrent READ integration and later positive/null DEV panels.

There is no further prompt ladder after A4. Failure motivates a separately
declared stronger resolver or benchmark/readout redesign, not training the
LoRA to hide a broken evaluation interface.

## 6. Claim boundary

An eight-task A4 pass supports only:

> In an exposed-root smoke, the clean 7B base, under static lexical output
> scaffolding and a supplied generic path/branch procedure, produced recurrent
> typed thoughts and exact routes from a fully visible researcher-authored
> graph on at least seven of eight tasks.

It is eligibility evidence, not a paper ceiling. A later frozen `>=60/64`
panel pass can support a **supplied-generic-procedure exact-graph ceiling**.

Neither result demonstrates spontaneous traversal-policy discovery,
autonomous metacognition, local READ selection, incremental retrieval, use of
LoRA memory, child-authored LINK formation, connected parametric knowledge,
retention, generalization, compression, parenting, recurrence benefit, or
lifetime improvement. The static grammar and generic procedure must be
disclosed wherever the result is used.

