# Structured-action supplied-memory DEV smoke — prospective design

2026-09-13. Read-only local source survey; only this memo written. No implementation, native/model/tokenizer/GPU call, remote access, external papers, outcome fetch, rescoring, or commit. Main's report of eight INVALID_TURN responses/zero READs and the separate closure failure is taken as supplied, not independently re-audited here. Lagrange retains command/test ownership.

## Recommendation

Run at most one separately named **STRUCTURED_ACTION_SMOKE**, with the same eight preserved cases, using a **constant pre-generation READ-or-ROUTE regex on every actor call**. Keep the existing READ-required public prompt, supplied-memory service, budgets, strict final parser/scorer, and no-retry behavior. No THINK, scratchpad phase, panel, new fit, address suggestion, graph injection or additional prompt persuasion.

This tests whether externally supplied action syntax permits the instructed retrieval handshake. It does not test learned serialization, acquired retrieval behavior, autonomous discovery or PCFL/full-assay success. The grammar supplies syntax explicitly; do not call the intervention information-neutral. Historical unconstrained failures are descriptive history, not a fresh matched control. The original failed smoke and failed fixed64 closure remain unchanged.

**Do not force READ on the first turn.** Keep both READ and ROUTE available throughout. Otherwise a valid first READ would partly be host-selected behavior rather than evidence that the child followed the instruction. Likewise, do not force ROUTE at the last slot or narrow the grammar after successful reads. A first-turn ROUTE still terminates under the existing scorer and fails the READ-handshake endpoint; it is not repaired or followed by another invitation.

## Exact syntax and sampling seam

Proposed constant regex bytes, matching the current public READ/ROUTE grammar and forbidding trailing LF, CR, prose, fences and multiple commands:

```text
(?:READ (?:EVENT E_[A-Z2-7]{10}|EVENTS_AT N_[A-Z2-7]{10}|LINKS_FROM E_[A-Z2-7]{10})|ROUTE N_[A-Z2-7]{10} N_[A-Z2-7]{10} : P_[A-Z2-7]{10}(?:,P_[A-Z2-7]{10})*)
```

Prospective policy name: `pcfl.supplied_memory.structured_action_smoke.v1`. Bind literal regex bytes/hash and policy before any generation. Keep all existing native sampling fields, task seed and the remaining-output cap; add only:

```python
sampling = {**native.SAMPLING,
            "seed": request["seed"], "max_tokens": limits["output_tokens"],
            "structured_outputs": {"regex": REGEX}}
```

`gpu/astra_pcfl_native_actor.py` already exposes `NativeActor._sampling(request, limits)`, archives its JSON output in the render receipt, and converts an exact one-key regex dictionary to `vllm.sampling_params.StructuredOutputsParams` before constructing `SamplingParams`. No default-actor change is needed. A small separately pinned subclass can supply this policy. Require the new actor source and sealed scoped request-plan binding before generation; reject unknown request IDs rather than falling back to unconstrained generation. Bind every possible slot ID to this same regex, policy and seed, not to an answer. Native request messages remain the exact public task/transcript; request IDs and task case labels are metadata, not added prompt contents.

The existing LF actor is an example of the hook/source-pin pattern, **not** the adapter to use: it is restricted to formation IDs and requires terminal LF, while READ/ROUTE fullmatch forbids LF. No post-generation conversion, stripping, completion, span extraction or fence repair is permitted. Installed regex support must accept these exact bytes; an unsupported pattern/backend is a failed setup, not permission to silently substitute a weaker grammar. A length finish remains failure even if a prefix or complete-looking action parses.

## Why choices remain child-selected / visibility boundary

- The regex enumerates **no concrete node, event, port, receipt, registered query or route**. It accepts syntactically valid nonexistent identifiers, wrong START/GOAL and wrong port sequences. Those remain child errors under the unchanged service/scorer.
- The child chooses READ versus ROUTE, which READ family, the entire address, number/order of further reads, route endpoints and port sequence. The public START and GOAL are still available in the unchanged task; EVENT/port identifiers become available only through actual service returns. No filled `READ EVENTS_AT <actual START>` is injected.
- The grammar may depend only on the static disclosed action syntax. It must not inspect `task.queries`, `source_rows`, `cell`, O/R/D bits, goal metadata, `ideal_rows`, graph reachability, previous scores, or target strings. All cases produce byte-identical regex. Do not compile registered-address enums, restrict routes to known edges, insert correct endpoints, or update regex alternatives from service contents.
- Identifier prefixes/alphabet/width are supplied syntactic assistance from the existing parser contract, documented in new config/report. They are not hidden graph knowledge and must not be credited as learned schema. Even public-context address allowlists would add host address-copying assistance; exclude them from this minimal diagnostic.
- Keep `ACTIVE_LINKED_TEXT`: `core.render_task` supplies task START/GOAL but no memory graph upfront. Only exact `core.read_query` returns append to that task's own history; MISS stays MISS, with no recommended replacement. Syntactically valid but unregistered queries remain possible and consume the existing READ budget. Never consult the private query map to make the child's choice valid.
- This service uses researcher-authored excluded-root ceiling rows, not child-authored EVENT experience. The driver explicitly labels `RESEARCHER_AUTHORED_EXCLUDED_ROOT_CEILING_NOT_CHILD`; preserve that label.

## Fixed cases and finite budget

These are **four preserved root wires × two goals**, not eight independent roots. Reuse the original root-file bytes/hash and compare the old smoke's case/seed/public-message/service bindings without regenerating root identities or selecting a new sample. Main supplies those exact artifact bindings; this survey did not retrieve a run manifest or invent a root-file hash.

`build_roster(..., "READ_REQUIRED_SMOKE")` currently selects indices `(0,1,16,17,32,33,48,49)` from the original64 order. Since `expand_cube` uses product `(0,1)^3`, these are:

```text
excluded/0/0/0/0/0  excluded/0/0/0/0/1
excluded/1/0/0/0/0  excluded/1/0/0/0/1
excluded/2/0/0/0/0  excluded/2/0/0/0/1
excluded/3/0/0/0/0  excluded/3/0/0/0/1
```

Freeze those eight case IDs, root wires, task seeds, public messages, supplied query/source-row hashes and13 possible slot IDs per task before generation, under a new experiment/source/output identity. Preserve the old must-READ instruction exactly; it is presently an instruction plus handshake scoring, not a decoder-forced first action.

Ceilings: **8 tasks ×13 calls =104 possible calls**, at most12 READs/task,256 output tokens/call with2048 cumulative actor tokens/task,4096 returned-service tokens/task,14336 input tokens/call. No THINK calls, no fit/update/teacher calls, no automatic second batch. Histories reset per task; failed/length/cap tasks and uncalled slots remain in the denominator. Use the existing finite cold-load-through-close/release controller and lease margin with Main's fresh allocation; no new lifecycle framework.

## Small implementation seams and concrete tests

1. **New small actor policy module/test**, e.g. `gpu/astra_pcfl_structured_action_actor.py`, following the existing source-pinned `_sampling` hook. Test exact sampling dictionaries and installed dict→StructuredOutputsParams conversion through the existing native loader seam; default NativeActor remains unchanged. Regex tests must accept arbitrary wrong-but-well-typed identifiers/ports, all three READ families and multiport ROUTEs; reject absent fields, bad namespaces, extra text, fences, LF/CRLF and combined commands. Vary hidden cell/query contents while holding the public request fixed: regex bytes must not change.
2. **Scoped interface execution/replay seam**, owned/coordinated with the current driver/command worker. Existing `interface._verify` hard-codes default sampling, so simply injecting a constrained actor into `run_stage` will correctly fail its capture check. The new scoped verifier must compare against the sealed structured policy; reuse the rest of `_render`, exact capture/decode/chronology checks, `core.parse_read`, `core.read_query`, `core.score_route`, histories and finite result handling. Prefer one narrow explicit policy seam with old default behavior preserved, or a separate scoped derivative if old bytes are frozen; no runtime monkeypatch/global replacement or general plugin framework. Both execution and `replay_validate` must use the same expected policy and reject missing/changed regex or unbound IDs.
3. **New-version closure/count binding**, not an old-receipt rewrite. Current `gpu/astra_pcfl_interface_outer.py` has `completed.summary.denominator == 64`; the driver smoke summary legitimately has8. For this new smoke require the sealed roster to contain exactly the fixed eight cases, denominator8, possible_calls104, and actual attempt count consistent with retained104 slot statuses. Do not merely drop denominator checking or accept arbitrary8/64. Regression: real-shaped eight-task completion can close;64-task/missing-case/spliced/extra-attempt receipts cannot. Original failed64 closure remains archived.
4. **Injected offline round trip**: (a) child chooses a registered READ, receives exact rows, emits a strict terminal ROUTE; (b) direct ROUTE has zero handshakes; (c) a typed unknown address returns MISS without hints; (d) malformed/combined output is rejected even if a mocked decoder violates its constraint; (e) length/cumulative-token/READ caps retain failures and no retries; (f) no prior task's transcript enters the next task; (g) a wrong graph route remains wrong despite perfect format. Replay exact raw request/sampling/token/finish/service records, including failures and uncalled slots. No target or ideal route is fed to actor generation.

Main's separate command/outer integration should archive the regex/policy/request-plan pins and use this new scoped count contract; command/test files are Lagrange-owned. This memo makes no edits to them and does not authorize patching live/frozen attempts.

## Endpoint, symmetry and stopping

Reuse the existing eight-task handshake definition: a counted task has at least one **registered, delivered non-MISS READ**, no invalid READ, and an eventual whole-response strict ROUTE; graph correctness is reported separately. Existing smoke gate is at least7/8 such tasks with zero invalid-READ tasks and structurally complete evidence. Malformed/length/capped tasks cannot count as successful handshakes or disappear. Report all eight reasons, READ/MISS/served counts, strict terminals, strict graph successes, token use, raw outputs, possible versus actual calls and closure status.

**Stop after this one smoke regardless of sign.** A gate miss ends this candidate; no prose iteration, forced-READ fallback, prefix/address narrowing, rerun, panel or adapter fit. A pass supports only externally scaffolded interface usability on these repeatedly exposed cases. It does not repair the original assay, establish graph competence or release A4. Any extension is a separate Main decision, not automatic continuation.

If later comparing model/memory arms, apply the **same constant action grammar, source-pinned sampler, public syntax, READ availability, budgets, task order and strict scorer to every matched arm**, not only the favored one. No hidden arm-specific valid-address/route filters. An arm with different tool availability is not an identical-interface contrast; declare that separately rather than slipping in a narrower decoder. This proposal adds no comparison arm now and claims no learning effect from format gains.

## Inspected source pins

- `gpu/astra_pcfl_native_actor.py`: `915b27d4dfe51623535bae588e54e1e35654a956f164aa23eba74a925a4a23ff`.
- `gpu/astra_pcfl_interface_dev.py`: `7774b59e2015fb0db7befd2054a1cf4adc2c9fe413dacc22b4c1634c37f1a33b`.
- `organism_v6/pcfl_vertical_dev.py`: `ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e`.
- Prior options memo `/tmp/astra_pcfl_interface_successor_options_20260913.md`: `b00fc4bb318423516f69fbf39a7bf5d7d5f275c6d5b303c62a2e8958788b0392`.

These record the read-only inspection, not a new execution bundle or artifact identity. No regex compilation against the installed native backend, new tokenizer measurement or model run was performed here.
