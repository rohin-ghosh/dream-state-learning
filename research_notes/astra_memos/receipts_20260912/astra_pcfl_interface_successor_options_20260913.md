# PCFL interface successor options — bounded design / EDITSTOP

Date: 2026-09-13. Local read-only review; only this note was written. No code,
model/tokenizer call, GPU, remote access, launch, fit, or old-output rescoring.
Main retains the current EVENT-only readout critical path. This is a proposed
next diagnostic, not execution authorization or an implemented new CLI.

## Decision

**Priority update after Main's 5ac0d402 handoff:** recommend the newly proposed
**eight-task answer-free must-READ smoke first**, with the single conditional
64-task continuation specified below. It is smaller and changes less than
either fitting an interface or replacing A3 turn framing. No implementation
is approved yet. Queue this decision **after Main completes and seals the
current 56-read comparison**, not during its critical path. EVENT-only CPU
preparation and fitting now work; do not repeat infrastructure work or add
another learning fit merely to address the next interface bottleneck.

Retain the separately named, zero-fit, externally phased scratchpad → strict
ROUTE diagnostic as the concrete **A3 alternative**, not a second automatic
test after A1. It tests whether removing the demand that the model invent the
correct turn boundary makes that interface usable; it does not assume this
fixes graph traversal. A3 combined THINK/ROUTE remains a byte failure with
zero valid turns. A2 remains graph 0/64 despite 54 strict terminals. Do not
proceed to A4 under the old closure.

Keep the inherited Level-1/birth teaching route as a separate, legitimate
development option, not an adapter to hot-mount into C0 or an explanation
that retroactively turns the failed clean-base runs into successes. A tiny
interface diagnostic is cheaper and more diagnostic now than fitting a
broader curriculum before locating the surviving failure.

## 1. Evidence and what it does not establish

Counts below are from the existing inspection receipts, not a new replay or
relaxed reduction. Their examples are selected stored examples, not an audit
of every underlying native response. I read current parser/driver source to
interpret the fields; I did not independently revalidate native custody.

| Stage | Actual calls | Strict terminal /64 | Graph success /64 | Recorded stop reasons |
|---|---:|---:|---:|---|
| A1 disclosed READ | 64 | 0 | 0 | 48 INVALID_TURN, 16 LENGTH; 0 served-read tasks |
| A2 supplied graph | 64 | 54 | 0 | 54 ROUTE, 10 INVALID_TURN |
| A3 required typed THINK | 64 | 0 | 0 | 40 INVALID_TURN, 24 LENGTH; 0 accepted THINK tasks |

A3 consumed 13,642 actor tokens; A2 consumed 2,530. These are actual receipt
totals, not the 448-call possible A3 ceiling. COMPLETED/returncode zero is
infrastructure completion, not a science gate pass.

**A3 framing failure is concrete.** The three stored examples each contain
`THINK ...` followed by LF and `ROUTE ...` in the same response. The driver
requires a full-response single-line THINK and explicitly prohibits combining
THINK and action. None of those samples reaches a second actor turn. The
second example also places bare/truncated node-like identifiers in the port
list (`DPH5JSJYDT,IPQ2WLA2DK,_APBZHN7V4U`). Thus even the examples are not
uniformly "a correct answer plus an extra newline." Do not count 40 such
combined responses from these three examples: 40 is the aggregate invalid-turn
count, not an audited subtype count. LENGTH is a budget/termination failure,
not a scored wrong route; it takes precedence over parsing in current source.

**A2 is a separate correctness bottleneck.** For 54 responses, the original
whole-response ROUTE grammar already passed, but graph success did not.
`score_route` checks the task start/goal, then executes each port from the
current node and checks arrival. Consequently these 54 failures cannot all be
explained by forbidden LF or output format. The inspection summary does not
split wrong endpoints, invalid port-at-current-node, and legal wrong arrival;
do not invent that decomposition or claim that all 54 were legal traversals.
They establish wrong task-route execution beyond grammar, not an intrinsic
inability of the base under every possible interface.

**A1 remains unresolved.** Zero served reads does not demonstrate that the
service cannot work; it demonstrates no successful handshake under this
interface. Its zero `invalid_read_tasks` is not a pass: non-READ prose/length
failures never become valid READ attempts. A supplied-graph successor will
not establish autonomous retrieval or repair this missing evidence.

The v2 closure §6 requires at least 60/64 joint accepted THINK + strict
terminal, with no invalid/cap failure, before A4 is eligible when traversal
still fails. A3 has zero such tasks. A4 is prohibited. Historical raw bytes,
counts, failures, and capture/release records remain immutable.

## 2. Options compared against the inherited path

| Option | What changes prospectively | What it can diagnose | Why not mistake it for more |
|---|---|---|---|
| Restate "no newline / one command" yet again | Prompt wording only | Another adherence attempt | Current BASE_SYSTEM/THINK_API already state both; weak next isolation and invites wording search. |
| **A1 answer-free must-READ** | Explicitly require the behaviour the handshake gate already demands | Whether omission of a public requirement explains zero service use | Smallest NEXT test; not READ-address teaching or traversal qualification. |
| Permit multiline typed THINK | THINK payload grammar only; ROUTE still strict | Whether LF prohibition blocks accepted thought | An embedded ROUTE must remain inert. Merely accepting it as thought may consume turns without producing a terminal. Never extract its last line. |
| **Externally phased scratchpad then strict action** | Controller declares one prose-only phase and one terminal phase | Whether explicit phase separation supports usable output and correct supplied-graph execution | Changes the interface and adds a generation/history versus direct control; not an isolated reasoning or memory effect. Alternative only, not an automatic follow-on. |
| Existing Level-1/birth adapters or a new serialization curriculum | Weight intervention from sourced authored targets | Acquisition and transfer of a taught interface/procedure | Not zero-fit C0, own-wake consolidation, autonomous teaching, or a rescued ladder result. Existing corpora are not PCFL interface training. |

Actual inherited components matter:

- `organism_v6/birth_skill_corpus.py` labels its examples AUTHOR_SOURCED
  DEVELOPMENT ONLY. Its perception exercises select supplied public events;
  reflection restates a supplied correction. They are not PCFL route lessons.
- `organism_v6/birth_conditional_corpus.py` creates 256 training and 128 dev
  cases: PROSPECT/REVISE plus truthful ADDITION/COPY. AUTH versus DERANGED
  changes conditional targets. `train_items` masks context and supervises
  authored responses; constraints specify a fresh single rank-8 adapter, not
  clean child's own-wake learning. Current source explicitly supplies no L1
  verdict. Opaque action strings and COMPARE/POLICY/NEXT are not
  READ/THINK/ROUTE turn-taking.
- The second-roster claim audit describes 96 authored rows, fresh rank-8 fits
  across three learner seeds, 48 held situations and 12 canaries per skill.
  Its legitimate interpretation is execution of an explicitly stated authored
  procedure. It is not evidence here that an existing adapter solves PCFL.
  This review did not inspect Level-1 efficacy outcomes or select a winner.
- The existing birth protocol-alignment options already identify the right
  distinction: serialization of *supplied* fields is not choosing actions or
  inferring hidden rules. That design pattern can be reused, but its RuleGame
  PREDICT/TRY/QUIZ/record targets cannot be relabelled a PCFL-ready corpus.

If later teaching is chosen, source a separate small PCFL serialization set
from public grammar: supplied opaque fields → exact command, plus turn-end
examples and held spellings/wrappers. No solved path, useful read address,
edge-following algorithm, hidden answer, or old failed-output correction enters
these targets. Teach route transcription only when the ordered fields are
explicitly supplied and label it transcription, never graph solving. OFF and
locality canaries are necessary; a matched target-map control is needed for a
claim about evidence-conditioned teaching, but it is not automatically a
syntax control because both maps may be grammatical. Reuse existing tokenizer,
LoRA fitting, and cold readout machinery, not their phase-specific success
markers. This is a fallback design direction, not an extra fit in the next test.

This preserves Rohin's Level-1 → Level-2 intent: birth can establish behaviours
that make subsequent prompted learning usable (raw thesis messages 24, 26,
28); a clean-base interface failure does not disprove that path. Conversely,
authored interface acquisition is not H1 retention or H2 faster learning from
own experience. The frozen-base/LoRA, provenance, control, parent-blindness and
evidence invariants in launch prompt §15 remain in force. No final C11 guard
or broader qualification system is proposed.

## 3. NEXT: minimal A1 must-READ smoke, conditional full panel

Directly relevant new authority for this proposal is
`research_notes/analysis/2026-09-13_pcfl_a1_zero_read_minimal_successor.md`.
Its account says all 64 A1 first responses began with ROUTE. That added detail
is attributed to the note, not a new 64-response raw audit here. Source agrees
that A1 discloses READ availability but never explicitly requires a READ.
Unlike another "no newline" reminder, this supplies a previously absent
behavioural requirement, without a path-solving procedure.

Add only the note's exact requirement to a newly named development prompt:

```text
Before any ROUTE, you must issue at least one READ. Use only the public START
and exact identifiers returned by memory; never invent a READ address.
```

Do not include a recommended READ form, a filled-in command, registered
address, route, early row, or correction. Keep root/task/service/parser/scorer
bytes, seeds, token caps and lifecycle unchanged. Before any output, Main
must freeze both the eight exact smoke task IDs (four exposed roots × both
goals, with O/R/D choices fixed rather than selected from responses) and the
full 64-task panel. No new roots or implementation are created by this note.

- Run the smoke once: **8 tasks, at most 104 calls**. Continue only with at
  least **7/8 legal registered non-MISS READ handshakes with no invalid turn**.
  Retain cap failures under the unchanged reducer; do not count an eventual
  failed/capped task as a successful completed handshake.
- If that gate passes and custody/release is valid, run the frozen full
  **64-task panel once, at most 832 calls**, with its unchanged 60/64 joint
  handshake gate and zero malformed-READ requirement. No smoke-row splicing;
  overlapping tasks remain disclosed repeated exposed-root development,
  not 72 unique tasks or unseen confirmation. Total possible calls across
  both stages: **936**, not a promised actual count.
- Any smoke gate miss stops this candidate. Zero/near-zero legal READs
  specifically ends prompt-prose iterations; the note's possible symmetric
  structured-action interface is a later design decision, not permission to
  implement it now. A full-panel miss also stops, without repeat or selection.
- Report handshake and route counts separately. A handshake pass is service
  use under an instruction, not graph competence, full ACTIVE ceiling, or
  promotion. A2's correctness failure survives this proposal. No A4 release.

Main binds finite existing detached-stage clocks and six-hour lease margin
before launch; neither stage may borrow an open-ended extension. No birth
fit, A3 alternative, dynamic-link redesign or broad guard work is bundled
into this next test. Partial AUTH readout news supplies no paired promotion;
Main owns the complete 56-read comparison. This note does not inspect or
interpret those outputs or condition interface selection on unseen scores.

## 4. Concrete A3 alternative — only if separately selected

Proposed name: **PCFL-IFACE-PHASED-DEV-1**. New prospective run, not A3 retry,
not A4, no downstream stage release. Needs a small new phase adapter before
execution; the existing `A3_THINK` CLI does not implement this contract.

1. Freeze the complete paired 64-task roster before the first call. Preserve
   the same original excluded/0..3 root file, graph/goal user bytes, O/R/D
   ordering, seeds, model revision, temperature and row semantics as A2/A3.
   Main supplies/verifies the actual preserved root path and file hash;
   this note creates or reselects none. Freeze both new phase prompts and
   the unchanged direct-control prompt, source hashes, parser/scorer hashes,
   offline-tokenizer rendering/count receipt and output directory identities.
2. **DIRECT control:** fresh C0 process, existing A2 direct contract, one
   generation/task, at most 256 output tokens. All 64 tasks run once.
3. **PHASED:** fresh C0 process, no LoRA, no READ service. Two physical actor
   slots/task. Retain the same graph/goal and semantics, replacing the global
   one-line-for-every-response instruction with phase-specific disclosure:
   "This task has two response phases. The first response is scratchpad text,
   not an action; line breaks are allowed. After it ends, a separate request
   asks for the final action. Only that second complete response can execute."
   First request: "Write the scratchpad response for this task."
   Require a non-whitespace strict-UTF8 response ending normally (`stop`),
   at most 256 generated tokens. Preserve the entire response unchanged as
   assistant history. Do not parse, extract, execute or judge action-looking
   text inside it. This is not accepting an old combined THINK/ROUTE as a route.
4. Then append exactly: "Now emit exactly one complete ROUTE response under
   the declared final-action grammar. No other text."
   The final-action contract retains the original exact grammar, opaque IDs,
   comma spacing, no CR/LF including terminal LF, and no prose/fences. Request
   at most 256 tokens. Run the existing whole-response `score_route` only on
   this new final response. No endpoint correction, stop-string clipping,
   whitespace removal, route feedback, retry, or reordering of fields.
5. A first-slot empty response or LENGTH stops that task without a second
   call. A final LENGTH is also a budget stop, even if its visible prefix
   resembles a route. Record unsupported terminal READ/THINK as invalid;
   never dispatch it. Keep all 64 tasks in each arm's denominator. Continue
   other fixed tasks after ordinary task failures; infrastructure failure
   stops the arm and leaves remaining tasks explicitly unrun.

No worked graph, intermediate-node recommendation, candidate route, "follow
edges"/backtracking plan, useful READ hint, or answer-dependent continuation
is added. These prompts teach only phase/byte use. Do not retain the old
contradictory global prohibition on prose/LF for the scratchpad phase.

**Finite budget:** two cold one-stage runs, at most 64 + 128 = **192 calls**,
0 fits/updates/reads. Maximum generated actor tokens: **49,152**, with maxima
256/task DIRECT and 512/task PHASED. This deliberately does not spend the old
2,048-token/task allowance; it is a one-shot interface screen, not a sweep.
Retain the 14,336 input-token cap and verify rendered input plus output
headroom before every call. Allow at most **1,800 seconds per arm including
60 seconds reserved for cleanup** (3,600 seconds total); no extension/retry.
Main binds allocation and finish at least six hours before lease end, uses
the existing verified owned-process close/cleanup/release pattern, and keeps
raw failures if infrastructure fails. No separate foreground finalizer.

DIRECT is a contemporary descriptive control, not token-dose matched: a
positive PHASED contrast combines phase disclosure, additional generation and
self-produced history. Do not call it an isolated reasoning benefit. The
historical A2 remains historical even if new DIRECT differs.

**Report:** raw captures and actual tokens/calls first, then arm-specific
counts /64 for normal scratchpad completion (PHASED only), strict terminal,
correct endpoints, legal execution, graph success, invalid terminal,
LENGTH/input-budget stops and unrun tasks. Joint PHASED interface completion
requires normal nonempty scratchpad plus normal strict terminal with no cap
failure; graph success is counted on that same task. Break down by root
(/16), O/R/D cell (/8) and goal index (/32), without treating the 64 tasks as
64 independent worlds. Use the same raw scorer, retain custody/release status
separately, and label `full_assay_qualified=false`.

## 5. A3 alternative stop conditions, not another ladder

- **Infrastructure invalid/missing custody or release:** stop; preserve
  partial costs and unrun slots. No score-based selection or automatic retry.
- **PHASED joint interface <60/64:** stop this candidate. Report remaining
  framing/length/identifier failures separately. No A4 or automatic prompt
  search, token increase or fit. A separately scoped serialization-teaching
  proposal is then more motivated than claiming the graph algorithm failed.
- **Interface >=60/64 but joint graph success <60/64:** stop. Serialization
  alone is not enough; diagnose task correctness separately. Do not rename
  a traversal curriculum "grammar teaching," and do not transfer this new
  gate to old A4 eligibility.
- **Joint graph success >=60/64:** report only a successful supplied-graph
  excluded-root interface diagnostic. Stop after the paired screen. A1
  retrieval is still unproved; any later READ-handshake test needs its own
  frozen contract. No full assay, CONF, clean lineage, H1/H2, C11, causal
  learning or ceiling qualification follows from this development result.

Thresholds are proposed operational screen thresholds, not newly observed
facts or an amendment to the immutable ladder. Main decides whether to
implement/freeze this successor; none of these branches adds work to the
current EVENT-only readout.

## Local evidence references / read-time pins

Paths are repository-relative unless absolute. Hashes below pin the files
read for this note, not an assertion that current working source equals
every historical native run's source.

- `research_notes/astra_memos/receipts_20260912/astra_pcfl_interface_a3_inspect_20260913_attempt2.json`
  SHA256 `e5dba924948254c43983536c470afa7ed119180a11092d0ade2567486e8b6e00`.
- `research_notes/astra_memos/receipts_20260912/astra_pcfl_interface_a2_inspect_20260913_attempt1.json`
  SHA256 `5e6ccc04f60e570c39dda36c37aa5da13875cc467601bd281ecfc98de2287dde`.
- `/tmp/astra_pcfl_interface_a1_inspect_20260913_attempt1.json`
  SHA256 `8383049c083c60b49472e6a6252f87fdcd1f618df4b323e6a0b5b2ea5e2c3c6b`.
- `gpu/astra_pcfl_interface_dev.py`, particularly `summarize`/`run_stage`:
  SHA256 `e31d9ee43705c3eb2754bcc8085ed5d739771acea15e13fda4dfe19b0dc26f10`.
- `organism_v6/pcfl_vertical_dev.py`, `parse_route`/`execute_route`/`score_route`:
  SHA256 `ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e`.
- `organism_v6/birth_conditional_corpus.py`:
  SHA256 `43bf074938e8c4e3a995e43d747ff24f2c6cf70252359cb35134391ff88da74b`.
- `organism_v6/birth_skill_corpus.py`:
  SHA256 `078ceba07141b5f6fb2159a12e21f1eccc0901ba9f51f52d1793d988927812f6`.
- `research_notes/analysis/2026-09-13_pcfl_c0_dev_interface_repair_v2_closure.md`, §§2,6.
- `research_notes/analysis/2026-09-13_pcfl_a1_zero_read_minimal_successor.md`:
  SHA256 `1bb9db8d069f2d22485778992ff32dc6c1c43c71807ae173bd562969a48a3e5b`.
- `research_notes/analysis/2026-09-13_level1_second_roster_result_blind_claim_audit.md`.
- `research_notes/analysis/2026-09-13_level1_birth_disposition_minimum_protocol.md`.
- `research_notes/analysis/2026-09-13_level1_to_pcfl_authentic_formation_bridge.md`.
- `research_notes/astra_memos/receipts_20260912/astra_birth_protocol_alignment_options_20260913.md`.
- `research_notes/THESIS_RAW_ROHIN_2026-09-11.md`, messages 24,26,28;
  `research_notes/ASTRA_LAUNCH_PROMPT_2026-09-12.md`, §§15–16 only.

No manuscript or external literature was consulted. No code/tests were
changed or run for this design-only task. Existing concurrent tracked edits
were left untouched. EDITSTOP.
