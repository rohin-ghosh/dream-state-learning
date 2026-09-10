# PCFL M-TEXT V4 roster and endpoint adjudication — v1

Date: 2026-09-10

Status: **source-only advisory; not ratified and not executable**. This file
authorizes no implementation, materialization, CPU benchmark, tokenizer/model
execution, GPU use, scientific claim, release, or submission.

## Ruling

Use an **18-condition, 546-slot-per-root** M-TEXT roster. This is the repaired
fixed-delayed-entry (the former “589”) design after dropping the redundant
43-slot `TRUTHFUL_NULL_RECURRENT` condition. Do not use the 601 family, do not
add a twentieth model-executed all-path mask, and relabel the one-shot arm
`AUTH_NO_FEEDBACK_TAPE`.

The scientific score surface has three disjoint layers:

1. substrate-neutral task success, used for every comparison across AUTH,
   ATOMS, no-memory, raw context, RAG, and native graph;
2. authentic connected-trace diagnostics, used only where authentic returned
   atom/link capabilities exist; and
3. derived cross-condition counterfactuals, never misrepresented as fields of
   one `(root, condition)` cell.

Every endpoint has type `0|1|NA`. An unexecuted or inapplicable phase is `NA`,
not zero and not an inherited AUTH result. A registered gate rejects `NA`.

## Exact adjudications

### Drop `TRUTHFUL_NULL_RECURRENT`

An endpoint-preserving null leaks AUTH adjacency. An endpoint-null record is
not reachable under the original common-reader index and, after repair, adds
no unique scientific estimand: ATOMS tests absence of links,
PASSIVE_SIGNATURE tests a condition-independent null envelope, and DERANGED
tests matched but wrong organization. Retain endpoint-null EMPTY only as an
M0 conformance/mutation fixture; do not spend model calls on it.

### Retain the fixed-delayed-entry family

Define one immutable, model-independent `DELAYED_ENTRY(k,h)` from the root's
authentic old carrier plus the canonical admitted new atom/link for the
ordinary correct acquisition outcome. It has empty scratch, workspace,
capabilities, transcript, cache, and session state. The delayed goal is
released only after the sterile reset.

`REACHOUT_OFF`, `OLD_CUT`, and `NEW_CUT` fork from this fixture and never
borrow an AUTH model output. Their acquisition, belief-revision, retention,
and end-to-end endpoints are `NA`. `OLD_CUT` and `NEW_CUT` apply exactly one
post-entry transform. `REACHOUT_OFF` applies its reader-dispatch transform to
its own path starts and standardized delayed entry.

For a successful live AUTH acquisition, the private post-reset semantic state
must hash-equal `DELAYED_ENTRY(k,h)` before any cut comparison is scored.
Mismatch invalidates the instrument. This makes abbreviated delayed cells
factorial probes while preserving the full AUTH arm as the end-to-end life.

`NO_PERSIST_NEW` remains condition-local: it runs uncertainty/acquisition,
emits the ordinary acquisition event when correct, then removes both the new
atom and link at reset.

### Retain bridge cut, not a twentieth mask condition

`BRIDGE_CUT` removes every authentic old link incident to the necessary
bridge `p4`, which intersects every registered path class. Use its
substrate-neutral behavioral effect together with the correct
`TWIN_REDIRECT` terminal switch. A private deterministic all-path deletion may
check dependency-graph integrity, but is not a model condition and adds no
calls.

### Relabel the one-shot arm

`AUTH_NO_FEEDBACK_TAPE` is an open-loop interactivity lower bound, not a
matched scratch-recurrence comparator. It receives one call per phase with
the same *maximum generated-token allowance* as that recurrent phase, but it
does not observe within-phase returns or outcomes before fixing later
commands. Future capability handles are invalid.

The combined uncertainty/acquisition tape sees a frozen union opportunity
catalog `{e0,e1,e2,e3,c0,c1,abstain}`. Execution remains stage typed: optional
legal READs, exactly one experiment opportunity, then exactly one fixed commit
opportunity. A cataloged command used in the wrong stage terminates adversely;
ordinary `NO_EFFECT` and post-action `BLOCKED` remain public policy outcomes.

Bind tape decoded-byte ceilings by the existing eight-byte-per-allowed-token
ratio: 26,624 bytes for a 3,328-token path tape and 8,192 bytes for the
1,024-token uncertainty/acquisition tape.

Two separate optional claims replace “recurrence necessity”:

- explicit scratch-carriage value: AUTH versus AUTH_SCRATCH_OFF, which holds
  repeated observations fixed; and
- closed-loop outcome-feedback value: AUTH_SCRATCH_OFF versus
  AUTH_NO_FEEDBACK_TAPE, clearest on experiment, commit, and downstream task
  endpoints.

The second contrast includes the value of repeated interaction and cannot be
called pure internal recurrence.

## Exact MTextCondition roster

| Conditions | Count | Maximum slots/root each | Generated allowance/root each |
|---|---:|---:|---:|
| AUTH, ATOMS, DERANGED, NO_MEMORY, PASSIVE_SIGNATURE, RAW_CONTEXT, RAG_RAW, NATIVE_GRAPH, AUTH_SCRATCH_OFF | 9 | 43 | 11,008 |
| BRIDGE_CUT, TWIN_REDIRECT | 2 | 26 | 6,656 |
| UNCERTAINTY_SHAM | 1 | 17 | 4,352 |
| REACHOUT_OFF | 1 | 39 | 9,984 |
| OLD_CUT, NEW_CUT | 2 | 13 | 3,328 |
| NO_PERSIST_NEW | 1 | 17 | 4,352 |
| TARGET_ONLY_ANSWER_PRIOR_TAPE, AUTH_NO_FEEDBACK_TAPE | 2 | 4 | 11,008 |

The 43-slot life is `13 + 13 + 4 + 13`. The 39-slot arm is two path
phases plus standardized delayed entry. The 17-slot arms are combined
uncertainty/acquisition plus delayed. Every recurrent slot allows 256 generated
tokens. Each four-call tape has three 3,328-token path allowances and one
1,024-token combined-phase allowance.

## Endpoint definitions

All task endpoints ignore carrier-specific citations:

```text
probe_task_g = reached released goal g and FINISHed there
probe_plan_g = last pre-action plan equals one complete registered minimum path
two_goal_task = probe_task_A & probe_task_B & join_clean
two_goal_plan = probe_plan_A & probe_plan_B
acquisition_task = correct c_h emitted the ordinary new atom
delayed_task = reached D and FINISHed there after reset
full_sequence_task = two_goal_task & acquisition_task & delayed_task
```

These are the only endpoints used for cross-substrate success, shortcut,
benefit, adverse-effect, and practical-baseline gates.

Mechanism diagnostics are separate:

```text
connected_constructive_g = successful path whose every STEP cites its returned
  atom and whose adjacent STEP pairs cite prior returned AUTH links
connected_two_goal_use = connected_constructive_A & connected_constructive_B
delayed_connected_integration = delayed_task & constructive_delayed &
  old_atom_used & old_AUTH_link_used & new_atom_used & new_AUTH_link_used
trace_support_integrity = private all-path deletion invalidates the cited trace
```

`trace_support_integrity` is deterministic revalidation, not model behavior.
For raw/RAG/native/no-memory/ATOMS/DERANGED comparisons, authentic connected
diagnostics are `NA`, never a structurally forced zero substituted for task
failure.

The behavioral connected-use endpoint is derived across conditions:

```text
connected_trace_dependence(root) =
  connected_two_goal_use(AUTH)
  & trace_support_integrity(AUTH)
  & bridge_behavior_change_on_A_and_B
  & twin_redirect_correct_terminal_switch_on_A_and_B
```

Here `bridge_behavior_change` means the normalized world-action trace changes
under BRIDGE_CUT; the independent task-benefit gate below determines whether
that causal change is useful. A twin switch is one only if the redirected arm
reaches the decisive state and selects the redirected correct terminal action.

Information endpoints remain distinct: `separating_choice`,
`realized_target_information`, `belief_revision`, and `acquisition_task`.
Because the public uncertainty object exposes calibrated outcome counts, this
supports an information-use claim, not a connected-memory claim.

## Applicability matrix

`P` is path task/plan, `I` is information/acquisition, `D` is delayed task,
`F` is condition-local full-sequence task, and `M` is authentic connected-use
diagnostics.

| Condition group | P | I | D | F | M |
|---|:---:|:---:|:---:|:---:|:---:|
| AUTH, AUTH_SCRATCH_OFF | yes | yes | yes | yes | yes |
| ATOMS, DERANGED, NO_MEMORY, PASSIVE_SIGNATURE | yes | yes | yes | yes | NA |
| RAW_CONTEXT, RAG_RAW, NATIVE_GRAPH | yes | yes | yes | yes | NA; own-substrate traces reported separately |
| BRIDGE_CUT, TWIN_REDIRECT | yes | NA | NA | NA | only as derived counterfactual inputs |
| UNCERTAINTY_SHAM | NA | yes | yes | NA | NA |
| REACHOUT_OFF | yes | NA | yes from fixed entry | NA | only as derived access counterfactual |
| OLD_CUT, NEW_CUT | NA | NA | yes from fixed entry | NA | only as derived delayed counterfactual |
| NO_PERSIST_NEW | NA | yes | yes | NA | delayed trace diagnostic if reachable |
| TARGET_ONLY_ANSWER_PRIOR_TAPE | yes | yes | yes | NA | NA |
| AUTH_NO_FEEDBACK_TAPE | yes | yes | yes | yes | NA for connected-use claims |

RAW/RAG/native deliberately preserve alternative external memory across their
own reset projection. They are eligible for task comparison but ineligible as
evidence for the carrier sole-channel claim. Native graph is a labeled ceiling,
not part of the raw/RAG superiority maximum.

## Prospective gate matrix

For endpoint `e`, retain the exact twin-block census:

```text
b_e(k,c) = min(e(k,0,c), e(k,1,c))
R_e(c) = sum_confirmation_k b_e(k,c) / 16
D_e(c1,c0) = sum_confirmation_k [b_e(k,c1)-b_e(k,c0)] / 16
```

No p-values or population interpretation apply.

Use the cross-critique's frozen stratified split, not contiguous `k` ranges:

```text
DEV:          0,6,8,14,17,23,25,31
CONFIRMATION: 1,3,5,7,9,11,13,15,16,18,20,22,24,26,28,30
RESERVE:      2,4,10,12,19,21,27,29
```

Both `h` twins remain together. Reserve is a post-confirmation robustness
follow-up, not replacement confirmation.

1. **Task headroom:** AUTH `two_goal_task`, `delayed_task`, and
   `full_sequence_task` are each at least `12/16`.
2. **Connected path benefit:** AUTH exceeds each of ATOMS, DERANGED,
   BRIDGE_CUT, and REACHOUT_OFF by at least `4/16` on `two_goal_task`.
3. **Connected use:** AUTH `connected_two_goal_use >= 12/16` and derived
   `connected_trace_dependence >= 12/16`.
4. **Information use:** AUTH separating choice, realized target information,
   belief revision, and acquisition are each at least `12/16`.
   UNCERTAINTY_SHAM target-information, revision, acquisition, and delayed task
   are each at most `4/16`; AUTH exceeds sham acquisition by at least `8/16`.
5. **Delayed old/new reliance:** AUTH delayed connected integration is at
   least `12/16`. OLD_CUT, NEW_CUT, and NO_PERSIST_NEW delayed task are each at
   most `4/16`. For each intervention `x`, at least `8/16` blocks satisfy AUTH
   acquisition, AUTH delayed task, and failure of `x` delayed task. Fixed-entry
   cut scoring additionally requires the successful AUTH entry hash match.
6. **Shortcut bound:** NO_MEMORY, TARGET_ONLY, and PASSIVE_SIGNATURE each have
   `two_goal_task` and `delayed_task` at most `5/16`. These gates no longer pass
   automatically because of missing citations.
7. **Zero-net-harm:** every registered adverse bound is the exact integer
   condition `sum_k(b_AUTH-b_comparator) >= 0`; do not call it a five-point
   tolerance.
8. **Practical text-memory advantage:** for task endpoint `e`, define
   `b_best(k,e)=max(b_RAW(k,e),b_RAG(k,e))`. AUTH must have
   `sum_k[b_AUTH-b_best] >= 1` separately for `two_goal_task` and
   `delayed_task`, with zero net harm on the other primary task endpoints.
   Native graph is reported as a ceiling only.
9. **Explicit scratch value (separate optional claim):** AUTH exceeds
   AUTH_SCRATCH_OFF by at least `4/16` on each prospectively named task
   endpoint, with zero net harm elsewhere.
10. **Closed-loop feedback value (separate optional claim):**
    AUTH_SCRATCH_OFF exceeds AUTH_NO_FEEDBACK_TAPE by at least `4/16` on
    acquisition and downstream full-sequence task, with zero net harm on the
    other applicable task endpoints.

The supplied-connected-text claim does not require either optional recurrence
claim.

## Exact resource envelope

```text
maximum request slots/root
  = 9*43 + 2*26 + 17 + 39 + 2*13 + 17 + 2*4
  = 546

allowed generated tokens/root
  = 9*11,008 + 2*6,656 + 4,352 + 9,984
    + 2*3,328 + 4,352 + 2*11,008
  = 159,744
```

| Scope | Roots | Maximum request slots | Allowed generated tokens |
|---|---:|---:|---:|
| DEV | 16 | 8,736 | 2,555,904 |
| confirmation | 32 | 17,472 | 5,111,808 |
| DEV + confirmation | 48 | 26,208 | 7,667,712 |
| sentinels | — | 24 | 6,144 |
| approved main envelope | 48 + sentinels | **26,232** | **7,673,856** |
| dormant reserve | 16 | 8,736 | 2,555,904 |

At the 8,192-token input ceiling, the main maximum is **214,892,544 input
tokens**. If reserve is later authorized, all 64 roots plus sentinels total
34,968 slots, 10,229,760 allowed generated tokens, and 286,457,856 maximum
input tokens.

These are exact **slot maxima**, not exact emitted calls. Any early terminal
seals every suffix slot as `NOT_REACHED`; receipts separately report emitted
calls and actual input/output tokens. No retry, timing probe, tokenizer call,
ceiling model, or mask run may be hidden in this registry. Use physical A40
GPU-hours, or freeze a device-specific conversion before approval; an
undefined “A40-equivalent” is not exact. Governance-review waiting must not
consume the scientific execution clock.

## Maximum claim

If all mandatory gates pass, the maximum claim is:

> In one frozen 7B policy and one registered finite topology, supplied
> authentic atom-plus-link text improved substrate-neutral goal and delayed
> task success relative to atom-only, corrupted, bridge-cut, and inaccessible
> controls. Valid returned-link traces plus bridge and binding
> counterfactuals identified goal-specific connected-content use. Separately,
> calibrated public evidence supported a separating experiment and belief
> revision, and a persistent supplied old-plus-new carrier supported delayed
> behavior after a sterile reset.

Raw/RAG superiority, explicit scratch value, and closed-loop feedback value
are separate claims requiring their own gates. The result is not DREAM or
SLEEP authorship, a learned write, LoRA transport, continual learning,
accumulation, compression, parenting, lifetime improvement, topology
generalization, or a flywheel.
