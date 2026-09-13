# PCFL paired structured-action diagnostics: terminal independent audit

**Date:** 2026-09-13 PT  
**Role:** fresh documentation-only result audit  
**Scope:** read-only inspection and CPU replay of preserved artifacts; no source,
model, tokenizer, benchmark, adapter, GPU, or remote-state mutation

## Verdict

The paired diagnostic supports one useful but narrow result:

> A generic structured action grammar by itself did not make the frozen actor
> consult memory. Externally requiring the **first action kind** to be READ made
> all eight actors issue an exact `READ EVENTS_AT <public START>`, and each then
> carried out a model-chosen, multi-turn sequence of further reads over exact
> service returns. This qualifies the typed local-memory transport under a
> scheduled-first-READ ceiling. It does **not** qualify autonomous retrieval or
> goal-directed route composition: all eight final routes still missed.

`STRUCTURED_FIRST_READ_SMOKE`'s recorded `stage_gate_passed=true` is only its
predeclared READ-handshake gate. It is not a route-success gate.

The route failures are now sharply localized. Four answers were coherent
two-edge prefixes of a required five-edge path and stopped early. The other
four spliced ports observed on different branches, making the route illegal at
its second edge. Every submitted port had appeared in an exact service return;
the remaining problem is state/branch/goal composition, not missing transport
or final-port hallucination.

The smallest next experiment is therefore **LF-framed recurrent THINK over the
same exact graph and the same five-hop tasks** (`A3B_NEWLINE_FRAMED`), not an
immediate scheduled-READ+THINK combination. This isolates the one unqualified
component in at most 56 calls. Only after recurrent exact-graph composition
passes should scheduled READ be combined with THINK.

## 1. Frozen artifacts and identities

Authoritative node-2 roots:

```text
/localhome/local-rohing/astra_diagnostics/
  pcfl_interface_structured_action_smoke_20260913_attempt1
  pcfl_interface_structured_first_read_smoke_20260913_attempt1
```

Immutable helper archive:

```text
gpu_artifacts_local/pcfl_structured_action_20260913_attempt1/evidence.tar
SHA-256 a3745deee039131c037ac2e645e6ab54e6d437eaebd848b8452bc5cad7bdd37c
size 10,086,400 bytes
```

The helper's post-outcome aggregation is commit
`0930d30f5369e69f06913116acc7b4c06d190508`; its frozen analysis payload is
SHA-256 `85e7be53d0eeb10608d8a12b7dd20dda55a35f231b55b92a3ebd9b6dc57430a2`.

Both runs used the bound frozen `Qwen/Qwen2.5-7B-Instruct` revision
`a09a35458c702b33eeacc393d103063234e8bc28`, temperature zero, no LoRA, zero
fits, and zero updates. They used four researcher-authored excluded roots and
only the `old=0, relevant=0, distractor=0` cell from each root, with its two
goals: eight recurring development tasks total. Material origin is explicitly
`RESEARCHER_AUTHORED_EXCLUDED_ROOT_CEILING_NOT_CHILD`; `full_assay_qualified`
and `clean_lineage_certified` are both false.

The paired tasks had byte-identical initial model messages and identical
private cell, goal, and generation seed. The only model-time difference was
the structured decoder's first-slot grammar.

## 2. Exact protocol difference

Both arms declared, per task:

| resource | cap |
|---|---:|
| READ actions | 12 |
| THINK actions | 0 |
| model calls | 13 |
| generated tokens per physical turn | 256 |
| generated tokens cumulative | 2,048 |
| returned memory tokens | 4,096 |
| input tokens | 14,336 |

`STRUCTURED_ACTION_SMOKE` used the following answer-free generic regex on the
first and later slots:

```text
(?:READ (?:EVENT E_[A-Z2-7]{10}|EVENTS_AT N_[A-Z2-7]{10}|LINKS_FROM E_[A-Z2-7]{10})|ROUTE N_[A-Z2-7]{10} N_[A-Z2-7]{10} : P_[A-Z2-7]{10}(?:,P_[A-Z2-7]{10})*)
```

`STRUCTURED_FIRST_READ_SMOKE` replaced only the first-slot regex with:

```text
READ (?:EVENT E_[A-Z2-7]{10}|EVENTS_AT N_[A-Z2-7]{10}|LINKS_FROM E_[A-Z2-7]{10})
```

Later slots returned to the common action regex. Thus the host constrained the
first **action family** to READ; it did not inject a generated string or
enumerate any concrete address, port, event, or answer in the regex. Because
the public START was the only usable concrete address initially visible and
the system forbade invented addresses, the first address choice had essentially
no autonomous search content. Call it scheduled-first-READ, not learned or
autonomous retrieval.

`THINK` was explicitly unavailable in both arms.

## 3. Exact terminal measurements

| endpoint | generic structured action | scheduled first READ |
|---|---:|---:|
| tasks | 8 | 8 |
| model calls | 8 | 48 |
| READ calls | 0 | 40 |
| non-MISS READ calls | 0 | 30 |
| MISS calls | 0 | 10 |
| exact EVENT row instances returned | 0 | 46 |
| returned-memory tokens | 0 | 2,218 |
| strict terminal ROUTEs | 7 | 8 |
| graph-legal ROUTEs | 0 | 4 |
| goal-reaching ROUTEs | 0 | 0 |
| successful READ handshakes | 0/8 | 8/8 |

The 40 scheduled-arm reads comprised 38 `EVENTS_AT`, two `EVENT`, and zero
`LINKS_FROM` calls. All 48 model responses were exact single physical lines
without CR or LF. All 40 READ addresses were already visible in the public
task or a previous service return. Every non-MISS service response matched the
registered EVENT bytes and its source-row SHA-256 list; every MISS had empty
support. No output was stripped, repaired, or extracted.

The generic arm's exact outputs were:

```text
ROUTE N_S6JZXHYXBT N_HJZRZAYWOT : P_3245672345,P_7654324567
ROUTE N_S6JZXHYXBT N_6TUR2VALJP : P_2345677234,P_3456723456
ROUTE N_F2NEPOJWOO N_W2GYE4FYXE : P_3456723456
ROUTE N_F2NEPOJWOO N_P4ISYQYYUR : P_VXZQKUOZUQ,P_4IYQYYURZU,P_ZQKUOZU4IY
ROUTE N_NCCWGHXEMX N_HGKGOBGRFN : P_3245723456,P_6543256734
ROUTE N_NCCWGHXEMX N_O3IJBLKA4Q : P_2345677234,P_3456772345,P_4567723456,P_5677234567,P_6772345672,P_7723456723,P_7234567234,P_2345672345,P_3456723456,P_4567234567,P_5677234567,P_6723456723,P_7234567234,P_2345672345,P_3456723456,P_4567234567,P_5677234567,P_6723456723,P_7234567234,P_23456723
ROUTE N_4IZIXCRYYO N_Z5UNBWSFET : P_7K3L2QWVXZ
ROUTE N_4IZIXCRYYO N_SZQKRRZJBO : P_7K3L2N5QXW,P_ASYTQVZUOE,P_KJHGFDSAPO
```

The sixth output hit the 256-token cap and is incomplete; the other seven
strictly match ROUTE syntax and the public START/GOAL but contain no legal
path.

The scheduled-first arm's exact action traces were:

```text
0: READ EVENTS_AT N_S6JZXHYXBT
   READ EVENTS_AT N_IPQ2WLA2DK
   READ EVENTS_AT N_DPH5JSJYDT
   ROUTE N_S6JZXHYXBT N_HJZRZAYWOT : P_7MGNA5ALJT,P_4RWKAJVRXP

1: READ EVENTS_AT N_S6JZXHYXBT
   READ EVENTS_AT N_IPQ2WLA2DK
   READ EVENTS_AT N_DPH5JSJYDT
   ROUTE N_S6JZXHYXBT N_6TUR2VALJP : P_7MGNA5ALJT,P_4RWKAJVRXP

2: READ EVENTS_AT N_F2NEPOJWOO
   READ EVENTS_AT N_3XMKTRCOAO
   READ EVENTS_AT N_HQQ5UNL7YW
   READ EVENT E_K5POAYPVLH
   ROUTE N_F2NEPOJWOO N_W2GYE4FYXE : P_CU72HSSTHQ,P_PG3IQT75KG

3: READ EVENTS_AT N_F2NEPOJWOO
   READ EVENTS_AT N_3XMKTRCOAO
   READ EVENTS_AT N_HQQ5UNL7YW
   READ EVENT E_K5POAYPVLH
   ROUTE N_F2NEPOJWOO N_P4ISYQYYUR : P_CU72HSSTHQ,P_PG3IQT75KG

4: READ EVENTS_AT N_NCCWGHXEMX
   READ EVENTS_AT N_MYGAQW6HGQ
   READ EVENTS_AT N_DH6YQLK5FT
   READ EVENTS_AT N_IQZJID3SEE
   READ EVENTS_AT N_V7JDYLIKJ2
   READ EVENTS_AT N_JKGQFEUMDQ
   ROUTE N_NCCWGHXEMX N_HGKGOBGRFN : P_DSFWIYNL3V,P_U6CRRINMLI

5: READ EVENTS_AT N_NCCWGHXEMX
   READ EVENTS_AT N_MYGAQW6HGQ
   READ EVENTS_AT N_DH6YQLK5FT
   READ EVENTS_AT N_IQZJID3SEE
   READ EVENTS_AT N_V7JDYLIKJ2
   READ EVENTS_AT N_JKGQFEUMDQ
   ROUTE N_NCCWGHXEMX N_O3IJBLKA4Q : P_DSFWIYNL3V,P_NXINQGYHG4,P_BXHVFSUI45,P_U6CRRINMLI,P_BZOTFNJ5FE

6: READ EVENTS_AT N_4IZIXCRYYO
   READ EVENTS_AT N_RLJKBILNJ2
   READ EVENTS_AT N_Y5DKX2EZGE
   READ EVENTS_AT N_GO2AIQ5YGW
   READ EVENTS_AT N_RHIPLQNGT5
   READ EVENTS_AT N_BVWPSYRDMM
   READ EVENTS_AT N_AKDYDWJMQJ
   ROUTE N_4IZIXCRYYO N_Z5UNBWSFET : P_PYBULW2CX6,P_CI4HD5GFH6,P_FK4GQNFXOT

7: READ EVENTS_AT N_4IZIXCRYYO
   READ EVENTS_AT N_RLJKBILNJ2
   READ EVENTS_AT N_Y5DKX2EZGE
   READ EVENTS_AT N_GO2AIQ5YGW
   READ EVENTS_AT N_RHIPLQNGT5
   READ EVENTS_AT N_BVWPSYRDMM
   READ EVENTS_AT N_AKDYDWJMQJ
   ROUTE N_4IZIXCRYYO N_SZQKRRZJBO : P_PYBULW2CX6,P_R2GBO7FYMF,P_CI4HD5GFH6,P_FK4GQNFXOT
```

One representative exact service join was:

```text
READ EVENTS_AT N_S6JZXHYXBT
->
EVENT E_L2PYYYRITJ AT N_S6JZXHYXBT DID P_7MGNA5ALJT GOT N_IPQ2WLA2DK EVIDENCE R_SPXUEL47N4
EVENT E_ZSZG3AE6MH AT N_S6JZXHYXBT DID P_CFZQL5YFH3 GOT N_DPH5JSJYDT EVIDENCE R_OLXUB2NOHT
```

Independent replay joined all 40 request/return pairs in this way, including
the terminal LF on EVENT rows.

## 4. Why exact reads still produced zero routes

Every correct task route has five ports. The failures divide cleanly:

### Tasks 0--3: valid prefix, premature commitment

The actor found the first two correct transitions and then stopped at the
intermediate `H` node:

| task pair | required prefix | emitted ports | endpoint |
|---|---|---|---|
| root 0, goals 0/1 | `P_7MGNA5ALJT,P_4RWKAJVRXP,...` | same first two only | `N_APBZHN7V4U` |
| root 1, goals 0/1 | `P_CU72HSSTHQ,P_PG3IQT75KG,...` | same first two only | `N_IAUHFPHW5L` |

It had just received the intermediate node identifier, but instead of asking
`EVENTS_AT H`, it inspected the alternate node exposed by the START result,
received MISS, and committed the incomplete prefix. The exact read trace and
route were identical across the two goals within each root.

### Tasks 4--7: cross-branch state binding failure

The actor first followed one START edge to a node whose `EVENTS_AT` returned
MISS. It then queried the alternate START branch and recovered most or all of
the route structure. At commitment, however, it began with the first dead-end
branch's port and appended ports returned on the other branch. Independent
graph replay therefore fails at port two:

```text
task 4: N_MYGAQW6HGQ has no outgoing P_U6CRRINMLI
task 5: N_MYGAQW6HGQ has no outgoing P_NXINQGYHG4
task 6: N_RLJKBILNJ2 has no outgoing P_CI4HD5GFH6
task 7: N_RLJKBILNJ2 has no outgoing P_R2GBO7FYMF
```

The actor thus transported and copied exact local facts but did not maintain a
coherent current branch, reconstruct a five-edge path, or choose the
goal-specific final edge. Within every root pair it performed the same READ
sequence despite the different GOAL. It never used `LINKS_FROM`; LINK was
available but not necessary because EVENT source/destination fields already
define the directed graph.

With THINK forbidden, the model had no typed state/scratchpad action in which
to keep competing branches separate or verify a route before committing. This
does not prove THINK will solve the failure, but it identifies the next
unconfounded question.

## 5. Visibility and leakage audit

The harness-side roster necessarily contains private cells, the exact fixture
bank, and the materialized query table for service dispatch and scoring. Those
objects were not placed in model messages.

For all 16 initial requests across the pair, scanning the actual rendered model
prompt found exactly two concrete opaque identifiers: the public START and the
public GOAL. The generic structured regexes contain no concrete opaque ID. For
the scheduled-first arm:

- all eight first outputs were generated model bytes equal to
  `READ EVENTS_AT <public START>`;
- all 32 later READ addresses were already present in prior visible messages;
- later prompts equal the initial public messages plus exact prior assistant
  actions and exact service returns—no additional message was injected;
- every final route port had appeared in a prior service return; and
- independent scoring exactly reproduces all stored strict/legal/success bits.

Therefore no useful address, route candidate, port sequence, or answer was
leaked beyond the public START/GOAL and rows requested through the service.
The first action **type** was externally constrained, which is why this is a
ceiling rather than an autonomy result.

## 6. Replay, custody, hashes, and release

The node artifacts independently passed:

- canonical payload self-hashes for roster, manifest, report, and completion;
- every completion inventory entry (60 files in the generic arm; 300 in the
  scheduled-first arm);
- exact request/render/raw/response joins for all 56 calls;
- exact conversation-prefix reconstruction, generic structured sampling
  policy, token decode, service return, and independent route-scoring replay;
- separate `custody.json` receipts with
  `native_actor_custody_verified=true` for both actors.

Important receipt semantics: `replay.json` deliberately records
`local_replay_valid=true` but `native_custody_verified=false`; custody is
certified by the later separate custody receipt. Likewise the stage completion
records `gpu_released=false` with `outer_release_required=true`; release must
be read from the detached outer, not inferred from the stage file.

The immutable helper outer receipts independently show:

- workers `200113` and `200181` returned exit code zero;
- each owned process group ended with no members and
  `owned_group_released=true`;
- each bound GPU UUID was empty afterward;
- direct queue state matched empty; and
- CVD inspection was clear with no unresolved owner. Complete CVD visibility
  is false only for the preapproved unreadable non-worker `systemd`/`sd-pam`
  initialization pair; this limitation is preserved.

Exact file-level hashes:

| file | generic arm | scheduled-first arm |
|---|---|---|
| manifest JSON | `139507309739dc871bd6cf02f40802cc8caba0dc23df61148270f1d715bd2f0f` | `016a6162337b80591b27d5baa038f67f6517e6a53fe18fafe68a8f7a267f2c36` |
| report JSON | `81c3578e56cd65b5c02752235f99144a34438e3fd2e8759eb6a5730257e48c2a` | `4c160efb0c2c6873ae87eb888522422385d3f36bcee267d4a8078b115215621f` |

The report payload hashes are respectively
`9dc65c251c10a89f31736584e1485d4aa0b87a179581b625d7cf19e36e4fc4d6`
and
`de7af5de2ae519f45d9be1276f158dc8b65f5ea483f86f628f27079214bbddd0`.

## 7. Supported and unsupported statements

Supported:

- generic structured decoding can make one exact physical READ/ROUTE action
  realizable without output repair;
- requiring a first READ is sufficient for an `8/8` served handshake on this
  exposed smoke;
- after that scheduled first step, the frozen model can choose additional
  previously visible addresses and consume exact multi-turn service returns;
- the memory service, conversation transport, capture, replay, scoring, and
  release plumbing work in this diagnostic; and
- exact atomic facts reaching context are not sufficient for five-hop
  goal-directed composition without a usable reasoning policy.

Not supported:

- autonomous decision to retrieve or autonomous useful first-address search;
- graph traversal, connected-memory use, LINK use, or correct goal selection;
- LoRA acquisition, retention, selectivity, generalization, or learning;
- superiority to active text, RAG, full context, or any other memory baseline;
- any child-life, parenting, lifetime-improvement, compression, full-assay,
  or whole-organism claim.

## 8. Smallest non-narrowing successor

Run `A3B_NEWLINE_FRAMED` first:

1. Preserve the same four exposed roots, two goals per root, five-hop task,
   exact graph bytes, public task, temperature-zero seeds, and cumulative
   actor budget. Do not shorten the path or disclose a route candidate.
2. Configure LF as the physical generation stop and exclude LF from returned
   bytes. Preserve and fullmatch the exact pre-LF bytes; never strip, salvage,
   or extract a line.
3. Allow at most six exact `THINK <one line>` turns followed by one exact
   terminal ROUTE: at most seven calls/task and 56 calls total.
4. Each accepted THINK receives only the fixed, information-free `CONTINUE`.
5. Require first-turn exact THINK on at least `7/8`, zero malformed/mixed
   accepted turns, exact terminal ROUTE on at least `7/8`, and separately
   require graph success on at least `7/8` before calling composition usable.

This does not narrow the benchmark: the graph, roots, goals, and route depth
remain unchanged. It makes the evidence maximally available only to isolate
whether recurrent state construction can solve the existing task.

If the physical THINK interface passes but graph success does not, use only
the already-predeclared answer-free generic traversal scaffold under the same
LF frame. If graph success passes, then run one combined
`SCHEDULED_READ_THINK_SMOKE` on the identical eight tasks: generic forced READ
on the first physical turn, thereafter LF-framed model-selected
THINK/READ/ROUTE, with the existing 12 READ, six THINK, 4,096 returned-token,
and 2,048 generated-token caps.

Running scheduled READ+THINK first is less informative: a failure would again
mix route reasoning, branch-state maintenance, and retrieval-policy errors and
would consume up to 152 rather than 56 calls. The exact-graph A3B isolates the
missing reasoning interface before recomposing the two demonstrated pieces.
