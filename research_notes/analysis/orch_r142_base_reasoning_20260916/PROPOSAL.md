# R142 BASE-only permission versus direct elicitation

**Non-material, exploratory PUBLIC TRAIN prompt control.** At
**2026-09-16 04:40:05 UTC**, final source is CPU-tested locally and on ovx3;
no production seed/plan, admission, model call, launch, signal, Git operation,
or shared-ledger change was performed by this worker. Main owns new allocation
and publication. Root AGENTS.md applies; no nested scope overrides were found.
The implementation and CPU tests are author-side work, not a fresh independent
review or independent ratification.

## Source-grounded hypothesis and exact intervention

The frozen contract already permits reasoning, reconsidering uncertainty, and
allocating budget. Therefore the initially suggested extra permission cue was
redundant and **was not implemented or staged**. Main reports all95 complete
R141 responses were single-line without prefinal text. This motivates testing
direct elicitation, not claiming that the earlier control lacked permission.

Hypothesis: explicitly requesting visible work may change immediate functional
revision by the same frozen BASE relative to its existing permission-only
prompt. It is not a learning, retention, internal-reasoning, or historical
prompt-matched result. Success is not assumed from the requested text appearing.

| Prompt arm | Effective model | Steering | System-message delta |
| --- | --- | --- | --- |
| PERMISSION_ONLY | BASE_NO_LORA | permission_only | None: exact CURRENT_R141 |
| DIRECTED_REASONING | BASE_NO_LORA | text_requested | One newline plus the exact cue below |

Frozen treatment wording:

```text
Before the final JSON, work through the task in your own words. If uncertainty or feedback gives you a reason to change your plan, explain what changes and why. Stop when you have enough evidence; do not pad the response.
```

UTF-8 SHA256 of the cue alone, without a leading/trailing newline:
`a3dedffab51ac4413c20a6c682c58e59c2818f8efc3bce4c0de59ecf37810356`.

The cue is appended to the existing R141 system message in draft and both
forks. There are no other model-visible changes: task/user content, existing
JSON-string example, helper contract, real feedback, and neutral-review text
remain exact. The cue supplies no helper, constants, composition, solution,
verification fact, forced branch count, reasoning template, or minimum length.
DIRECTED_REASONING is **text_requested**, not unhinted or purely discretionary.

## Frozen experimental boundaries

- **16 new Main-hash-excluded PUBLIC TRAIN tasks**, shared across the two prompt
  arms. Each arm produces its own draft; its feedback and neutral continuations
  share that exact raw draft. Drafts are not shared between prompt arms.
- **96 calls maximum**: 16 tasks ×2 prompt arms ×3 stages. Both prompt-arm order
  and feedback/neutral order alternate by task position exactly as in R133/R141.
- Same greedy decoder, 2048 new-token cap per call, 32768 context limit, no
  context trimming, and the exact frozen parser/scorer/safe helpers/task generator.
- No FULL experimental arm. Both arms use the original Qwen2.5-7B base with
  LoRA actually disabled, with no optimizer updates, ingestion, admitted rows,
  external parents, held-case access, replay, or retries.
- Actual feedback remains the attempted expression's public execution result
  or diagnostic, without expected answers or correctness labels. Neutral gets
  no execution evidence. No sealed material or old model responses are read.
- Historical R133/R136/R141 scores and source bytes remain untouched. This
  fresh two-prompt comparison is not a four-way benchmark or a matched comparison
  against historical tasks/prompts. A material scientific-claim, benchmark,
  visibility, or invariant change still requires its separate deliberation path.

## BASE-only execution and caller-visible provenance

`gpu/orch_r142_base_reasoning_collection.py` uses a bounded explicit episode
loop rather than rebinding model labels inside the old two-model loop. PLAN,
INTENT, CALL, per-response MEASURE, and COMPLETE receipts distinguish
`prompt_arm`, `effective_model=BASE_NO_LORA`, and the declared steering. Native
LOADED records only BASE in `model_states`, both prompt arms, their effective
BASE mapping, and the disabled-adapter collection context.

The original pinned loader still loads the fixed18404 checkpoint as the same
adapter identity carrier used by R141's BASE path. This is **not a FULL arm**.
One continuous frozen `readonly_model(..., BASE_NO_LORA)` context disables LoRA
before LOADED and covers all96 calls and intervening episode work. Every native
generation checks that all LoRA modules remain disabled and all parameters
remain frozen, both before and after generation. Unknown arm labels, adapter
enable drift, trainability drift, and context overflow fail closed. The frozen
context restores its entry state only after leaving the collection; there are
no further model calls. The original weight-unchanged check gates native COMPLETE.

All18 inherited R136/R141 producer/helper/guard/test pins are enforced before
preparation/verification. The new plan records exact cue, arm mapping, steering,
budget, decoder, source/task/exclusion hashes, and R142 schema. Cross-reading
R141 and R142 plans fails in both directions. Task IDs retain the original R133
generator namespace to preserve the unchanged ID-hash exclusion algorithm.

`gpu/orch_r142_base_reasoning_guard.py` reuses the frozen guard functions and
the R141 physical7/deadline check. The supervisor changes exactly one pinned
code constant, the native module name, before argv construction. Its recorded
command hash therefore covers the actual R142 argv. A mocked end-to-end test
checks this before the startup token and after completion. No runtime subprocess
rewriter or source mutation is used; scanner dispatch uses this adapter's source CLI.

## Observable outcomes, not internal chain-of-thought claims

The entire response, including visible text before the final JSON, is saved
unchanged in CALL. The original parser still parses only the final line.
MEASURE separates format validity, safe expression status, finite-check
correctness, completeness, and eligible success. It is written for each returned
response even if a later call prevents completing its triplet.

COMPLETE retains the exact R141 before→after metrics: raw text, parsed expression
text, and validated AST changes; format recovery; strict failed-to-passed;
and the narrower safe-expression semantic-correction field. Invalid expression
comparisons remain unavailable, not silently "unchanged." Incomplete pairs
cannot count as successful corrections. No alternate unquoted-expression
extraction or rescue scoring is introduced.

Future reduction must report all planned denominators, completeness/cap hits,
visible prefinal text as **observable output only**, and paired real-feedback
versus neutral outcomes separately within each prompt arm. Sandbox-to-pass
recoveries must not be confused with the narrower semantic-correction field.
Visible explanations are not proof of faithful internal reasoning; no internal
chain of thought, retained learning, or learning mechanism is inferred.

## CPU verification and immutable staging

Local: **126 tests passed, 14.755seconds**. Staged node CPU: **126 passed,
3.370seconds**. These comprise22 new R142 tests plus104 unchanged compatibility
tests. Tests use synthetic temporary-directory tasks and mocked native loading,
signals, subprocesses, and weights; they create no production plan or GPU call.

Coverage includes exact cue/steering and sole prompt delta, real/neutral feedback
isolation, old schema/source/cue/budget rejection, fresh exclusions,96-call order
and limits, per-arm draft hashes, unchanged saved visible text, failure/no-retry,
truncation, one BASE-disable context across both arms, enable/gradient drift,
unknown-model rejection, context limits, native load identity/weight barriers,
physical7/deadline constraints, startup barriers, and actual argv/hash equality.

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= python3 -B -m unittest tests.test_orch_r142_base_reasoning_collection tests.test_orch_r142_base_reasoning_guard tests.test_orch_r141_code_interface tests.test_orch_r141_code_interface_guard tests.test_orch_r133_code_feedback_collection tests.test_orch_r133_code_feedback_guard tests.test_orch_r119_public_feedback tests.test_orch_r109_l1_public_feedback -q
```

```bash
bash gpu/ovx3_ssh.sh 'CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/localhome/local-rohing/orch_r142_base_reasoning_20260916_attempt1/source_r142_v1 python3 -B -m unittest tests.test_orch_r142_base_reasoning_collection tests.test_orch_r142_base_reasoning_guard tests.test_orch_r141_code_interface tests.test_orch_r141_code_interface_guard tests.test_orch_r133_code_feedback_collection tests.test_orch_r133_code_feedback_guard tests.test_orch_r119_public_feedback tests.test_orch_r109_l1_public_feedback -q'
```

Final source:
`/localhome/local-rohing/orch_r142_base_reasoning_20260916_attempt1/source_r142_v1`.
All2,649 Python files from R141 `source_v2` were copied and checked against
its pinned guard before/after copying; four new Python files were added.
No historical files, R141 audit backups, or Main R142 metadata were overwritten.

The **2,653-file** Python source-set SHA256, calculated as
`sha256(json.dumps(source_pins, sort_keys=True).encode())`, is
`af88a2a03b7680d8036a7d0875981fdc2d9ac5e30932ebad74b6ed8f7faf11db`.

| New source | SHA256 |
| --- | --- |
| gpu/orch_r142_base_reasoning_collection.py | d12aef6b52d4565d597c470786ac0da5a35ab0cfc6bd2f2a2fa461ddcbec2aa0 |
| gpu/orch_r142_base_reasoning_guard.py | 1968684744f6bf1192d00eba97986be26357766e902230e017c80d5dcbfa9641 |
| tests/test_orch_r142_base_reasoning_collection.py | 851756ec3ed8af1291abae76a83f32603e0d7303a2822af7e76b82d444de64c2 |
| tests/test_orch_r142_base_reasoning_guard.py | 3bb1fb6a09a619f112bcf1b7de0906f8ec5244fdf8a845f8674219ad8966d351 |

Main's node-local metadata matches:

- EXCLUSIONS.json:
  `b502d012c5657f7649de44c141ea70359c5ed63ea4459d779609ef2baf5c3576`.
- INVENTORY_PROJECTIONS.json:
  `cac8da8d85404ffc3816e6aa24beb9e06d4fe19638e315f591539d4e66d8def9`.
- 102 spec hashes,128 ID hashes,3 used seeds; Main states the union includes
  all16 R141 planned tasks. Coverage is bounded, not globally semantic.
- Main's `PREPARATION_FAILURE.json` remains present and unchanged. No inventory
  was reconstructed, regenerated, or corrected by this worker. The R142 module
  exposes the unchanged `exclusions` function explicitly for Main's use.

## Main-only next steps; not executed by this worker

At04:40:05 UTC, `run1` did not exist. Main may prepare one fresh production
output only after review, using its hash-only inventory and a new seed:

```bash
stage=/localhome/local-rohing/orch_r142_base_reasoning_20260916_attempt1
export CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$stage/source_r142_v1"
seed="$(python3 -B -c 'import secrets; print(secrets.token_hex(32))')"
python3 -B -m gpu.orch_r142_base_reasoning_collection prepare --root "$stage/run1" --seed "$seed" --exclusions "$stage/EXCLUSIONS.json"
python3 -B -m gpu.orch_r142_base_reasoning_collection verify --root "$stage/run1"
```

If Main has since created `run1`, verify it rather than overwriting it. Do not
reuse a consumed seed or restart a started directory. Plan verification rejects
an obsolete permission cue or any mapping to FULL.

Main must create new GUARD/AUTHORIZATION/ALLOCATION/PUBLICATION bindings for
the R142 plan, exact2,653-file source set, source_r142_v1, and fresh output.
Keep the frozen guard/authorization/allocation schemas, unchanged base and
fixed18404 carrier identity, Main projection union, prior-release evidence,
timer, and lease checks. R141 config/plan hashes are not R142 authorizations.

Only ovx3 physical7 / `GPU-9e6cdf73-7181-4405-2aec-787cc73a3e5b` is allowed.
Hard end is no later than **September16 05:40 UTC** (`1789537200`), with the
**06:00 UTC** reservation (`1789538400`), original bounded wall and six-hour
lease margin unchanged. Main owns publication, dated Builder entry, and fresh
privileged exclusive admission. No worker GPU check or reservation is implied.

The future guarded entry is
`python3 -B -m gpu.orch_r142_base_reasoning_guard supervise --config /localhome/local-rohing/orch_r142_base_reasoning_20260916_attempt1/GUARD.json`
with `source_r142_v1` PYTHONPATH and initially empty CUDA visibility. It has
**not been run by this worker**. Do not invoke native directly, dispatch the
R141 guard against this plan, extend the ceiling, or switch to another slot.
