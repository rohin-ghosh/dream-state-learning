# PCFL V11 cap15 transport preflight v1

Date: 2026-09-10

Status: **PASS — proposal-only external transport audit evidence**.

This advisory records a fresh read-only preflight of the cap15 successor to
the previously approved V11 deliberation packet. It is not a workflow
context, source binding, directive, authorization, deliberation artifact,
source-authoring input, candidate-byte ratification, preparation authority,
implementation, scientific result, claim, release, or submission. It does
not authorize running either state.

## 1. Exact audited identities

| artifact | path | live SHA-256 |
|---|---|---|
| cap15 workflow | `research_loop/workflows/pcfl_m0_mtext_bound_v11.deliberation.json` | `b7df3f6edd0f0549a21dcdac2f8b58a93e4167d499f733e24970c7e70493f053` |
| cap15 zero-attempt state | `.research_loop/intake/chg_20260910_pcfl_m0_mtext_bound_v11_cap15.deliberation.state.json` | `00560eb10c5b3f1ed4e852c60127e27946c77c4136587c3c3f1322b2dee73ba8` |
| retained failed predecessor state | `.research_loop/intake/chg_20260910_pcfl_m0_mtext_bound_v11.deliberation.state.json` | `ddf106bb204c046ecea23c4cceee1c18c035694f6759127783654810f37c0f34` |
| prior packet preflight | `research_loop/advisory/20260910_pcfl_v11_packet_preflight_fresh_audit_v1.md` | `7a2fabac4b432c322bec7b2aa3ee7e3dd0d6d48e1374fced5d769037fe2f778d` |
| exact directive | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/human_directive.txt` | `42a678a04fb6be507f7f2adec781c1d9b72f3e7d205387d3fdc79945751cceff` |
| controlling candidate v4 | `research_loop/plans/pcfl_m0_mtext_exact_v11_source_authoring_candidate_v4.md` | `a57bae8a0a0d29d1779c1fec86e09226c1f851419f1c46df1fcdb6edd5a1af3a` |
| controlling closure v3 | `research_loop/advisory/20260910_pcfl_v11_controllerless_guard_closure_v3.md` | `96a392cd487d2d399d76873d3fe633e581eb372e0f6bec5bf4254617c31cbd02` |
| controlling source-plan v2 proposal | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/source_authoring_plan_v2.json` | `1b7d618c79379494e98a674e56cae46a8c9346412a4e68d9575b911a9c17076a` |
| deliberation-only scope | `research_loop/changes/chg_20260910_pcfl_m0_mtext_bound_v11/scope_proposal.json` | `ddc4235cacdd5c2fdd27efe97d9ef76756aa8525baaa32e941afac2ba96f381b` |

All hashes in this section were recomputed from current bytes. The workflow
and both state files remained at the listed identities after the read-only
checks.

## 2. Exact non-material workflow delta: PASS

The cap15 workflow is loader-valid. An exact byte reconstruction reversed
only these three literal edits in its current byte stream:

1. one workflow-name replacement,
   `pcfl-m0-mtext-bound-v11-cap15` to
   `pcfl-m0-mtext-bound-v11`;
2. one state-path replacement, from the `_v11_cap15` state path to the
   predecessor `_v11` state path; and
3. five replacements of `max_context_chars_per_file:15000` with `300000`,
   one in each role executor.

Those replacement source literals occur exactly 1, 1, and 5 times. The
resulting reconstructed byte stream hashes to the previously approved exact
workflow identity:

```text
49ccf21b5ebfeb9a63e2abbdce5792d356558e9ba7a27fa41338c30453ee70ff
```

Therefore there is no fourth changed byte or semantic field. In particular:

- the exact ordered 90-path context array is unchanged and has 90 unique
  paths;
- it equals candidate v4 section 2.1's literal array at every index;
- the directive, change ID, workspace, output, intake and run paths are
  unchanged;
- the scope and every prior governance/context byte remain the same bound
  inputs; and
- the exact five roles, providers, models, efforts, timeouts and retry budgets
  are unchanged:

| role | provider | model | effort |
|---|---|---|---|
| advocate | `codex` | `gpt-5.6-terra` | `high` |
| systems | `codex` | `gpt-5.6-luna` | `high` |
| benchmark | `codex` | `gpt-5.6-sol` | `high` |
| critique | `codex` | `gpt-5.6-sol` | `xhigh` |
| consensus | `codex` | `gpt-5.6-terra` | `high` |

The only behavioral change is the per-file injected-context tail ceiling.
It changes transport serialization, not the bound source identities,
deliberation semantics, roster, budget, scope, or authority.

## 3. Prompt construction and client ceiling: PASS, with exact terminology

A read-only in-memory reproduction of `build_prompt` using the base advocate
prompt, the exact directive-first 91-source sequence and the configured
15,000-character tail rule is exactly **860,834 characters**. This reproduces
the stated transport-sizing check. It is **187,742 characters** below the
Codex input limit of 1,048,576 and **536,444 characters** below the prior
client-reported 1,397,278-character request.

For completeness, 860,834 is the base-prompt construction, not the literal
payload eventually supplied by the architecture runner. Before calling
`build_prompt`, `_execute_role` appends the mandatory bound stage brief to
the base prompt. The live brief is 13,840 characters plus two separating
newlines, so the exact first advocate executor payload constructed by the
configured runner is **874,676 Python characters** (874,890 UTF-8 bytes).
That stronger end-to-end measurement is still **173,900 characters below**
the 1,048,576-character ceiling. No transport repair is required for this
terminology distinction.

As a consistency check, reconstructing the old 300,000-cap staged payload
from the same live sources gives 1,397,285 Python characters; the retained
Codex client receipt reports 1,397,278 under its own request accounting, a
seven-character accounting difference. Both measurements establish the old
failure, while the current staged payload has ample headroom under either
counting convention.

The constructor successfully opened and decoded all 91 full bound source
files before applying any tail slice. Their total full text is 1,365,703
Python characters; the largest file is 97,467 characters. Thirty files
exceed 15,000 characters and receive the explicit
`[truncated to final 15000 characters]` injected-view marker; the other 61
are injected in full. The underlying files are not truncated or rewritten.

The role executor forces `allow_write:false`, and the Codex transport maps
that to its repository `read-only` sandbox. Thus the injected tail cap limits
only the initial serialized context. It does not remove the files or their
hash bindings, and it does not deny the deliberator's read-only repository
tools access to full source bytes when needed.

## 4. New cap15 state: PASS

The new state has the exact loader-required field set and binds the current
workflow identity above. Its control values are:

```text
run_id = pcfl-m0-mtext-bound-v11-cap15-20260910T175027-7ee24742
phase = advocate_pending
status = running
human_required = true
implementation_authorized = false
last_error = null
attempts = []
artifacts = {}
attempt_counts = {
  advocate:0, systems:0, benchmark:0, critique:0, consensus:0
}
```

It contains exactly 91 unique, directive-first source-binding rows. Their
ordered paths equal exactly the directive followed by the unchanged 90
workflow contexts, and a fresh SHA-256 of every live file equals its row.
The workflow self-binding, `state.workflow_sha256`, and the live workflow
SHA-256 are all exactly
`b7df3f6edd0f0549a21dcdac2f8b58a93e4167d499f733e24970c7e70493f053`.
There is no missing, extra, duplicate, stale, aliased, or reordered binding.

## 5. Retained failed state: exact history, no artifacts

The predecessor state is retained separately and was not reset, overwritten,
or adopted by the cap15 workflow. It remains:

```text
run_id = pcfl-m0-mtext-bound-v11-20260910T160644-0a3a72e6
workflow_sha256 = 49ccf21b5ebfeb9a63e2abbdce5792d356558e9ba7a27fa41338c30453ee70ff
phase = advocate_pending
status = paused
human_required = true
implementation_authorized = false
attempt_counts = {
  advocate:2, systems:0, benchmark:0, critique:0, consensus:0
}
artifacts = {}
```

Its `attempts` array contains exactly two durable failed advocate executor
ordinals and no other role attempt:

- ordinal 1 records no result and its transport log ends with failure to
  initialize the in-process app-server client (`Operation not permitted`);
- ordinal 2 records no result; its provider retry log records the explicit
  Codex `turn/start` rejection twice, once per internal provider retry:
  `max_chars:1048576`, `actual_chars:1397278`,
  `input_error_code:"input_too_large"`.

The retained run directories contain only transport diagnostics and generated
request scaffolding (`bound_prompt.md`, response schema and stdout/stderr
logs). They contain no `result.json`, validated role output, consensus, or
scientific artifact. The state-level `artifacts` map is exactly empty.

## 6. Authority and no-execution boundary

The cap edit does not broaden the previously preflighted authority. The
packet remains a five-role, non-scientific architecture deliberation which,
if separately authorized over these exact new workflow bytes, must stop at
`human_required`. It contains no source-authoring, guard, preparation,
implementation, model-science, benchmark, training, or GPU executor and
cannot ratify its own output.

This audit loaded JSON, hashed and read files, reconstructed the old workflow
bytes in memory, and constructed prompt strings in memory. It did not run or
resume either deliberation state, reserve an attempt, invoke a model or
provider, create a role output, edit workflow/state/packet bytes, author or
execute source, run the proposed guard, prepare data, execute a checker/test/
tokenizer/benchmark/training/GPU job, acquire resources, or make a scientific
claim. The only new file is this external proposal-only audit evidence.

## 7. Verdict

**PASS.** The exact cap15 successor is a loader-valid, source-identical,
scope-identical and roster-identical transport repair. Its new state is
fresh, live-bound and zero-attempt; the two failed predecessor advocate
attempts remain separately preserved with no artifacts. The actual staged
advocate executor payload is 874,676 characters and is safely below the
1,048,576-character ceiling. This PASS is not authorization to run it.
