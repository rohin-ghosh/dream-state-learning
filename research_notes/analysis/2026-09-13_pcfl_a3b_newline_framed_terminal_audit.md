# PCFL A3B newline-framed terminal audit (2026-09-13)

## Scope and verdict

This is an independent, documentation-only audit of the terminal node-2 run:

```text
/localhome/local-rohing/astra_diagnostics/
  pcfl_interface_a3b_newline_framed_smoke_20260913_attempt1/
```

No builder/runtime source, model, tokenizer, adapter, benchmark, process, or
GPU state was changed.

**Verdict: A3B fixes the physical mixed-turn defect from A3, but does not yet
provide a stable typed thought-to-action interface and provides no scored
semantic improvement over A2.** Specifically:

- all `8/8` tasks produced at least one accepted, physically separate `THINK`;
- the run made exactly `25` of at most `56` calls and accepted `17` THINK
  turns in total;
- only `4/8` tasks ended in a strict `ROUTE`; the other `4/8` ended
  `INVALID_TURN`;
- all four strict routes were graph-illegal, so legal routes and exact graph
  successes were both `0/8`; and
- the joint smoke gate failed (`4/8`, required `>=7/8`).

It is now valid to say that **externally LF-framed recurrent thinking
occurred in this exposed C0 supplied-graph diagnostic**. It is not valid to
say that recurrent thinking improved graph traversal, that the base can use a
connected experiential graph, or that any learning occurred. A3B used a
researcher-authored ceiling graph, no READ service, no adapter, zero fits, and
zero updates.

The smallest prospective successor is not A4 yet. It is one separately named
`A3C_STATIC_TYPED_SMOKE` that adds a **single symmetric, static THINK-or-ROUTE
grammar** to every turn, without listing any real identifier and without
changing the eight tasks, graphs, seeds, or budgets. Only if that makes the
physical interface pass while graph semantics still fail does the
predeclared answer-free A4 generic traversal procedure become eligible.

## 1. Bound artifact identities

Authoritative native root and stage:

```text
root:  /localhome/local-rohing/astra_diagnostics/
       pcfl_interface_a3b_newline_framed_smoke_20260913_attempt1
stage: A3B_NEWLINE_FRAMED_SMOKE
model: Qwen/Qwen2.5-7B-Instruct
rev:   a09a35458c702b33eeacc393d103063234e8bc28
mount: C0 (no LoRA)
GPU:   GPU-c70cba10-6ab6-a287-e2db-51dccd617ab0
```

Important hashes:

```text
root manifest payload: 6990680059d3a1656051885aaec5003729e80a116cbbe1a701cd3d5bc43e30ad
report payload:        abd2c722dfea577d748be3a386e27409b4138bf6d12495eb03d7c6fe8298e9c4
report file:           535cf07dbebd3d87a79253ae8ebd6e33cd8da07bd30c39fe6defc1ade9c2c393
completed file:        e94a22d8901bbfbd67707f88e1452c8b7305006021405b7c1df847e918412b45
actor identity:        e1ff8b30a11572c8f07458e3308e971d81904df3b1b8a54487499a2a75f5f3d4
driver source:         b07004bfc1f27e025ee4f611ac3c7d51219ea8bda751b1f399b6e87ac9ced8de
helper evidence tar:   fb4b074911f8d8190bd71caef846d6b1440ca56f9b8ad19003ec1ddcfdb391ae
```

The completed inventory lists one request, render, raw generation, and
response record for every call `0000..0024`. I independently reran the
builder's frozen CPU-only post-outcome audit over the helper archive. It
rehashes every file named by `completed.json`, reconstructs sampling from the
hash-pinned driver, checks every raw-token/decode/returned-byte relation, and
returned `POST_OUTCOME_NATIVE_FRAME_AUDIT_PASS`. Its reproduced output hash
was `e61632ca08c6415dfcc56ca0b4c0647abe76df9d144a27066fb998127ac1b039`.

## 2. LF framing and token receipts

The bound sampling policy is:

```json
{"stop":["\n"],"include_stop_str_in_output":false}
```

It is applied without structured decoding. Every returned `response.text`
and every hashed `raw_hex` represents exactly one physical line and contains
no LF. There are two legitimate native stopping cases:

1. **9/25 LF stops.** `finish_reason="stop"`, `stop_reason="\n"`. The full
   decode of the charged output-token IDs has exactly one additional terminal
   LF, while `raw.text`, `response.text`, and `raw_hex` omit that LF as the
   declared policy requires.
2. **16/25 EOS stops.** `finish_reason="stop"`, `stop_reason=null`; the final
   output token is Qwen EOS `151645`, and full decode equals the returned text
   with no LF.

No response ended by length. All generated tokens, including the token that
contained each stop suffix or EOS, remain counted. Exact totals are:

```text
native calls:   25
prompt tokens:  16,107
output tokens:   1,504
```

Thus the A3 mixed-output ambiguity is gone: a THINK and a ROUTE never occupy
the same returned response. Newline framing is a successful transport repair,
not a reasoning result.

## 3. Did recurrent thinking really occur?

Yes, under a narrow operational definition.

- First response: exact accepted `THINK` on `8/8` tasks.
- Accepted THINK counts by task: `1, 1, 3, 2, 2, 1, 3, 4`, totaling `17`.
- Every task therefore underwent at least one real model call, accepted THINK,
  fixed host `CONTINUE`, and a second model call over the extended chat state.
- Five of eight tasks produced multiple successive THINK responses before the
  terminal attempt.
- Calls used by task were `2, 2, 4, 3, 3, 2, 4, 5`, totaling exactly `25`.

The recurrent state was the accumulated public conversation. The only host
response to THINK was the fixed, answer-free string:

```text
CONTINUE: follow the declared turn budgets and commit the final action when ready.
```

So it is fair to report **recurrent typed thought turns occurred**. It would
be too strong to call this autonomous metacognitive control: the system prompt
required at least one THINK, the LF boundary was externally imposed, roots
were exposed, and no control removes recurrence while retaining the same
framing.

The stage summary's names need care. `thought_tasks=8` is the count with any
accepted THINK. `thought_interface_tasks=4` is not a contradiction: the code
defines it only over tasks that also reached a strict terminal ROUTE. The
smoke therefore passes thought production but fails the joint physical
thought-plus-action interface.

## 4. Exact path audit

Every selected task has one five-port solution of the form
`a0,b,q0,d,f{goal}`. The exact expected and submitted terminal sequences were:

| root/goal | THINKs | expected ports | submitted terminal | result |
|---|---:|---|---|---|
| 0/0 | 1 | `P_7MG...,P_4RW...,P_US3...,P_Z24...,P_RK7...` | `P_7MG...,P_JFT...,P_RK7...` | strict, illegal |
| 0/1 | 1 | `P_7MG...,P_4RW...,P_US3...,P_Z24...,P_FOP...` | destination-shaped `P_DPH...,P_IPQ...,P_APB...,P_6TU...` | strict, illegal |
| 1/0 | 3 | `P_CU7...,P_PG3...,P_Q5K...,P_O66...,P_QKU...` | missing prefixes, spaces, and destination token | invalid |
| 1/1 | 2 | `P_CU7...,P_PG3...,P_Q5K...,P_O66...,P_CLT...` | wrong branch plus spaced delimiter | invalid |
| 2/0 | 2 | `P_UKI...,P_NXI...,P_UF3...,P_BXH...,P_U6C...` | two destination-like bare IDs | invalid |
| 2/1 | 1 | `P_UKI...,P_NXI...,P_UF3...,P_BXH...,P_BZO...` | correct first two and last port, but replaces the two-edge bridge with a node-shaped port | strict, illegal |
| 3/0 | 3 | `P_Y4Y...,P_R2G...,P_G2B...,P_E6E...,P_FK4...` | first port followed by four destination-shaped ports | strict, illegal |
| 3/1 | 4 | `P_Y4Y...,P_R2G...,P_G2B...,P_E6E...,P_ELH...` | five destination-shaped bare IDs | invalid |

The raw thoughts show two distinct residual defects.

### 4.1 Syntax/role serialization failure

Four terminals violate the exact route grammar through missing `P_` prefixes,
spaces after commas, or space-separated identifiers. More importantly, many
responses treat a port identifier as a node (`N_RPRTAHQJHF`) or turn a
destination node into a synthetic port (`P_JKGQFEUMDQ`). LF framing controls
where the turn ends; it does not preserve identifier type.

### 4.2 Semantic/path-state failure

The four syntax-valid routes are all graph-illegal. Their errors include
skipping required bridge transitions, taking a dead branch, and concatenating
ports that do not join at the current node. Therefore merely making the other
four routes parse cannot establish graph use.

There is one qualitative signal worth retaining without promoting it. On
root 3, the multi-turn trace eventually names most of the correct node-level
path through `N_Y5DKX2EZGE -> N_GO2AIQ5YGW -> N_BVWPSYRDMM ->
N_AKDYDWJMQJ -> goal`. The terminal then serializes those destination nodes as
ports. This suggests a state-to-action type-binding problem on those two
tasks, but it is post-hoc, root-local evidence; the formal graph score remains
zero.

## 5. Comparison with A2

The exact same eight root/cell/goal tasks in A2 produced:

```text
A2: 7/8 strict ROUTE, 0/8 legal, 0/8 graph success
A3B: 4/8 strict ROUTE, 0/8 legal, 0/8 graph success
```

Therefore A3B offers **no scored semantic improvement over A2**. It proves
that thought can be split into recurrent calls; it neither improves legality
nor reaches any goal, and strict action formatting is worse. The deeper root-3
trace is a useful hypothesis about node/port binding, not an effect estimate.
Because A2 did not use the same LF framing and did not request THINK, this
smoke also cannot cleanly estimate the causal effect of extra thought.

## 6. Custody, replay, and release

- `custody.json` reports `native_actor_custody_verified=true`, exact actor
  identity, `actual_calls=25`, `count_tokens_calls=0`, and the exact token
  totals above.
- `replay.json` reports `local_replay_valid=true` and the expected report
  payload hash. It deliberately retains `native_custody_verified=false` and
  `full_assay_qualified=false`; those fields must not be rewritten as a full
  paper-grade replay claim.
- The stage `completed.json` similarly retains `gpu_released=false` and
  `outer_release_required=true`; the stage record itself is not the outer
  release receipt.
- `shutdown.json` records that
  `llm.llm_engine.engine_core.shutdown` returned successfully.
- At this audit, exact controller PID `205552` and worker PID `205563` were
  absent on node 2; the bound GPU UUID had no compute process and GPU 0 showed
  `0 MiB` used. This independently verifies terminal physical release.
- The helper-side archive hash above matches the builder's recorded VM/node
  archive identity. The builder disclosed that its first post-outcome audit
  invocation referenced a nonexistent helper and failed before producing an
  output; the corrected audit used the driver's actual THINK regex. It did not
  alter native data, scores, or the frozen endpoint.

This is sufficient terminal custody for this exploratory diagnostic, not a
full-assay/clean-lineage certificate.

## 7. Smallest prospective successor

### A3C_STATIC_TYPED_SMOKE

Run the same eight C0 tasks with the same exact graph, prompts except for the
sampling declaration, model, revision, seeds, temperature, token budgets,
six-THINK/seven-call cap, scorer, and one-shot terminal policy. Add one static
grammar, identically on every slot:

```regex
(?:THINK [^\r\n]+|ROUTE N_[A-Z2-7]{10} N_[A-Z2-7]{10} : P_[A-Z2-7]{10}(?:,P_[A-Z2-7]{10})*)
```

Properties that are essential:

- the same union is available on first and later turns; no host-selected
  first action and no slot-specific routing;
- the regex contains only the identifier *types*, never a real node, port,
  candidate answer, path length, route prefix, or list of visible IDs;
- no parser repair, retry, identifier normalization, or semantic candidate
  scoring;
- THINK still receives only the fixed CONTINUE;
- all returned tokens and unused slots remain counted; and
- keep the LF boundary as well if the bound decoding implementation supports
  LF stop plus static regex jointly. Otherwise the regex itself must enforce
  one physical line, and that transport difference must be explicitly logged.

This is syntax scaffolding, not answer scaffolding. Its physical gate is the
predeclared smoke gate: at least `7/8` first responses accepted as THINK and at
least `7/8` tasks ending with an accepted THINK history plus one strict
terminal ROUTE, with no repaired/mixed output and at most one malformed,
length, or cap failure. Graph success is reported separately.

Decision rule:

1. **Physical gate fails:** stop; A4 remains prohibited. Do not add more prose
   or increase the token budget.
2. **Physical gate passes and graph success is `>=7/8`:** expand A3C once to
   the frozen 64-task panel; do not run A4.
3. **Physical gate passes and graph success is `<7/8`:** A4 is eligible under
   the same static grammar and budgets, adding only the already-predeclared
   identifier-free generic path-search/check procedure. An A4-only pass means
   execution of a supplied algorithm, not spontaneous traversal discovery.
4. **A4 fails:** stop the fixed-7B PCFL reader path. Do not train routing into
   the LoRA and call that a writer result.

Do not combine local READ with A3C yet. Scheduled-first READ already proved
transport without routing. First qualify a complete-graph thinker; only then
test the joint READ/THINK interface. This keeps action syntax, graph
semantics, retrieval, and LoRA carriage as separate causal seams.

## Claim boundary

Supported now:

> Under an externally imposed LF turn boundary, the fixed 7B base produced
> accepted recurrent THINK turns on all eight exposed supplied-graph tasks.

Also supported:

> The recurrent loop did not yield a usable route interface: only four tasks
> reached strict terminal syntax, and none produced a legal or successful
> graph traversal.

Not supported: autonomous thought allocation, semantic improvement over A2,
READ use, connected experiential-memory use, LoRA transport, retention,
generalization, learning, parenting, lifetime improvement, or a whole-system
claim.
