# PCFL V11 final packet fresh preflight audit v1

Date: 2026-09-10

Status: **PASS — proposal-only, post-initialization audit evidence**.

This advisory records a fresh exact preflight of the initialized V11
architecture-deliberation packet. It is not a workflow context, directive,
source-authoring input or grant, candidate-byte ratification, preparation
authority, implementation, execution receipt, scientific result, claim,
release, or submission. Creating this after-init audit does not change any
workflow source binding.

## 1. Exact audited identities

| artifact | path | live SHA-256 |
|---|---|---|
| final workflow | `research_loop/workflows/pcfl_m0_mtext_bound_v11.deliberation.json` | `49ccf21b5ebfeb9a63e2abbdce5792d356558e9ba7a27fa41338c30453ee70ff` |
| initialized hidden state | `.research_loop/intake/chg_20260910_pcfl_m0_mtext_bound_v11.deliberation.state.json` | `aebac44020a31eac615b5636d7c43da20ed203f759b6c3bd1e6cf5a17780aeea` |
| exact human directive | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/human_directive.txt` | `42a678a04fb6be507f7f2adec781c1d9b72f3e7d205387d3fdc79945751cceff` |
| controlling candidate v4 | `research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate_v4.md` | `a57bae8a0a0d29d1779c1fec86e09226c1f851419f1c46df1fcdb6edd5a1af3a` |
| controlling guard/plan closure v3 | `research_loop/advisory/20260910_pcfl_v11_controllerless_guard_closure_v3.md` | `96a392cd487d2d399d76873d3fe633e581eb372e0f6bec5bf4254617c31cbd02` |
| controlling source plan v2 proposal | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan_v2.json` | `1b7d618c79379494e98a674e56cae46a8c9346412a4e68d9575b911a9c17076a` |
| deliberation-only scope | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/scope_proposal.json` | `ddc4235cacdd5c2fdd27efe97d9ef76756aa8525baaa32e941afac2ba96f381b` |

All values above were independently recomputed from current bytes. The
workflow and hidden state remained at those hashes after all read-only checks.

## 2. Loader and workflow schema: PASS

The repository's architecture-deliberation loader accepted the exact workflow
and returned name `pcfl-m0-mtext-bound-v11`, the workflow digest above, and 90
contexts. The workflow has exactly the loader-supported top-level fields:

```text
schema_version workflow_kind name workspace change_id directive_file
context_files output_dir state_path intake_state_path run_dir roles
```

It has `schema_version:1`,
`workflow_kind:"architecture_deliberation"`, the exact C11 change ID, a valid
repository workspace, distinct output/state/intake/run paths, the exact
directive path, no unsupported field, and every required role prompt/schema
resource. The directive is not duplicated in `context_files`.

Every context file exists and is a regular file. No context exceeds its
configured 300,000-character per-file limit; the largest has 97,475 bytes, so
it is below that ceiling even before UTF-8 character counting.

## 3. Exact candidate-v4 context array: PASS

Candidate v4 section 2.1 contains a literal list of exactly 90 paths. Direct
ordered comparison against `workflow.context_files` is equal at every index:

- workflow context count: `90`;
- candidate-v4 literal count: `90`;
- workflow unique-path count: `90`;
- missing context paths: `0`;
- unexpected, reordered, or duplicate paths: `0`.

The list includes the V10 zero-attempt state; the V11 corpus and exact human
evidence; both corpus candidates, the provenance repair, and sole corpus
precedence closure; the integration-preflight repair; plan v1 and plan v2;
the predecessor candidate/closure evidence selected by the 90-for-90 rule;
the controlling closure v3 and candidate v4; current scope; and the final
workflow's own path. Closure v2/candidate v3 remain transitively hash-bound
predecessors rather than additional current context rows, exactly as candidate
v4 specifies.

## 4. Initialized state and source bindings: PASS

The hidden state has exactly the runner-required field set and these exact
control values:

```text
phase = "advocate_pending"
status = "running"
human_required = true
implementation_authorized = false
last_error = null
attempts = []
artifacts = {}
attempt_counts = {
  advocate:0, systems:0, benchmark:0, critique:0, consensus:0
}
```

`status:"running"` is the loader's initialized pre-run status; it is not an
attempt or model-call receipt. `human_required:true` and
`implementation_authorized:false` are intact.

There are exactly 91 recursively closed `{path,sha256}` source bindings. Their
paths equal exactly this directive-first sequence:

```text
[workflow.directive_file, workflow.context_files[0], ...,
 workflow.context_files[89]]
```

A fresh SHA-256 of every one of the 91 current files equals its state row.
There is no missing, stale, extra, aliased, reordered, or duplicate binding.

The three workflow identities are equal:

```text
live workflow SHA-256 =
  49ccf21b5ebfeb9a63e2abbdce5792d356558e9ba7a27fa41338c30453ee70ff
state.workflow_sha256 =
  49ccf21b5ebfeb9a63e2abbdce5792d356558e9ba7a27fa41338c30453ee70ff
self-path source-binding SHA-256 =
  49ccf21b5ebfeb9a63e2abbdce5792d356558e9ba7a27fa41338c30453ee70ff
```

The self-reference is noncircular because the workflow stores only its path;
the runner computed both state hashes after workflow bytes were sealed.

## 5. Predecessor and denial-corpus stack: PASS

All extant immediate predecessor files named by candidate v4 and closure v3
rehash to their declared identities:

| predecessor | SHA-256 |
|---|---|
| integration candidate v3 | `76754fbdd3d8bba5f26924e2cc0125f0ae8f803d9559285be84275687652218a` |
| guard/plan closure v2 | `a768682b68e0bbab93dc50e6ea6011894a10b75475f55c18b4df0a187678a5e1` |
| integration candidate v2 | `82dc79fe88dd7204898b123c02ce7cabb78761f38b0be0bfc97a248fe8579ffd` |
| controllerless closure v1 | `37b4098f7cb809a86c3217a4c1267cad62dd799f3403a75c2b871c9f7d2f8f3b` |
| integration candidate v1 | `586500e72c6e03da5f9e4e9800094017888e1e4648bb656a2caad82335a8b5bc` |
| integration-preflight repair v1 | `a9dc887e8acdf5eacb9a5eca6a2f4586e84269b8d15befd110bcf09a9f669f4e` |
| source plan v1 | `46263de44eefccc9face8b9cf76fd48986a55e7a527cce1bd32b1bc731ae92ce` |
| V10 authority/delayed-baseline head | `27668f5816958342b84a322c317281dc10131732153eeee387a228f67eea86ae` |
| V10 provenance/resource/guard head | `d969fca712d18affed60879be63a96b2aa5d75596d7240c615a5b647dff4337e` |

Candidate v3's recorded `e0b9583d...` workflow identity is expressly labeled
the historical pre-successor digest. It is not treated as a live workflow or
state binding; candidate v4 and closure v3 require the final externally
computed identity, which is the exact `49ccf21b...` value above.

The complete directly bound denial-corpus ratification stack also rehashes
exactly:

| stack artifact | SHA-256 |
|---|---|
| normative denial corpus | `4bd08a8ee761e59f9655d69354bb396dd09632f44be812fe63b0c9d3bea8c799` |
| exact human ratification evidence | `3934b01d022ff6b463def3003408d2fb5822c9991764b4bc386aa5bcc2385b58` |
| corpus candidate v1 | `492980e15c8c35a16adcf6067aba0acdb0877944bb3d40a53c5bacf346b54357` |
| corpus candidate v2 | `c1d109309804a6defadd1643c5259eeaec6a0471ca74bf659800e50234339f81` |
| corpus/provenance repair v1 | `8d0c28201cec2e695d2a615ca2d8b9230bfee28c032b887096b24332d7431e65` |
| sole corpus precedence closure v1 | `a540470046064196d04dfa9602ab5aa9f8090706bf3e5e266ee630945ef580c2` |

The evidence's exact sentence binds the corpus path, hash, 3,880-byte
JCS-plus-one-LF identity, closure digest, and named
`V11-EMBEDDED-ARTIFACT-SUPERSESSION`. The directive independently binds and
quotes that evidence while retaining proposal-rework-only authority.

Plan v2 is valid JSON with exactly 25 unique, bytewise path-sorted rows: 23
manifest members, one nonmember manifest output, and one nonmember governance
guard source. It retains the exact singleton governance input for the corpus.

## 6. Five-role deliberation boundary: PASS

The workflow has exactly one executor for each and only each of the five
architecture-deliberation roles:

| role | provider | model | effort |
|---|---|---|---|
| advocate | `codex` | `gpt-5.6-terra` | `high` |
| systems | `codex` | `gpt-5.6-luna` | `high` |
| benchmark | `codex` | `gpt-5.6-sol` | `high` |
| critique | `codex` | `gpt-5.6-sol` | `xhigh` |
| consensus | `codex` | `gpt-5.6-terra` | `high` |

Timeouts, two provider attempts, provider-attempt timeouts, and 300,000
context characters per file are unchanged from the inherited configuration.
There is no source-authoring, guard, preparation, implementation, benchmark,
training, or GPU executor.

The directive and scope authorize only packet proposal rework. They do not
authorize running the workflow or making a model call; a separate exact human
authorization over the final workflow bytes remains required. If later
authorized, the workflow's maximum effect is the five non-scientific
architecture-deliberation roles and their durable artifacts through
`human_required`. Even favorable consensus may only recommend that the human
consider a separate plan-v2-bound source-authoring grant. It cannot issue that
grant or authorize implementation/execution.

## 7. No source or execution side effect

Every one of the 25 plan-v2 `entries[*].logical_path` outputs is absent,
including all 23 source members, the normative manifest, and
`governance/v7_boundary_guard_controller_v1.py`. Consequently no proposed
source member, manifest, or guard byte exists to import, compile, review,
ratify, or execute. The change directory contains only the directive, scope,
two plan proposals, corpus, and human corpus evidence.

The initialized state has no attempt, artifact, error, or role output, and no
run-specific deliberation directory exists. This preflight invoked no
deliberation run, model, candidate source, proposed guard, checker, test,
tokenizer, benchmark, training, parenting, preparation, materialization,
fixture/root/data generation, GPU, resource acquisition, evaluation, claim,
release, or submission operation. Loader construction and hashing were
read-only governance checks.

## 8. Verdict

**PASS.** The exact final V11 packet is loader-valid, complete, uniquely and
currently hash-bound, zero-attempt, and scoped only for a separately
human-authorized five-role deliberation ending at `human_required`. No packet
repair is required before the human reviews whether to authorize those
exact deliberation bytes. This PASS is not itself that authorization.
