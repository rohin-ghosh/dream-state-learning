# Bounded interface DEV independent review — 2026-09-13

Static source/test/handoff review only. No tests, driver, tokenizer, model,
GPU, native-artifact, remote or lifecycle execution. Only this review is
written. Command/outer integration remains Lagrange-owned; native operations
remain Main-owned. Findings below are concrete integration risks/corrections,
not a replacement launch gate or a request for a new guard framework.

## 1. COMPLETE does not mean64 model responses or64 wrong answers

**Integration action required.**
`gpu/astra_pcfl_interface_dev.py:247` classifies an oversized rendered prefix
as task reason `INPUT_TOKEN_CAP`, without an actor call. Lines307–317 still
mark that task SCORED and can mark the entire stage COMPLETE. The existing
`tests/test_astra_pcfl_interface_dev.py:327` test deliberately expects
COMPLETE with zero calls when actor max_input_tokens is10. Its stage gate is
false, so this is not a false-positive gate, but a wrapper must not describe
it as64 observed wrong model answers or a successfully exercised interface.

**Smallest correction:** command preparation measures all64 sealed initial
message pairs with the actual tokenizer and rejects an incompatible initial
input/context cap before starting a stage. Keep later history-induced cap
exhaustion as a separately named task-budget outcome; do not relabel it route
incorrectness. Preserve64 denominators and UNCALLED slots. Do not introduce
padding calls or salvage a final after budget exhaustion.

For integration, fixed upper bounds are A1=832, A2=64, A3=448,
ACTIVE_THINK=1216 calls, not a common mandatory actual-call count. Each comes
from64 cases ×13/1/7/19 slots. Actual calls vary with terminal answers and
budget stops. Reads/thinks have separate12/6 caps where enabled; actual actor
tokens are capped at2048/task and256/response, delivered memory at4096/task,
input at min(14336, actor cap). The command must not require actual calls to
equal possible_calls, or assume that19 full256-token replies fit2048 tokens.

## 2. The stage summary/replay intentionally accepts injected evidence

**Integration action required before a native-result label.**
`gpu/astra_pcfl_interface_dev.py:167` accepts identity.kind NATIVE **or**
INJECTED_CPU_TEST. Raw.kind must match it, but COMPLETE and
summary.stage_gate_passed do not distinguish those origins. The synthetic
NativeActor-loader test at `tests/test_astra_pcfl_interface_dev.py:119`
explicitly gets a true stage gate. replay_validate also correctly leaves
native_custody_verified false; successful replay is not native admission.

**Smallest correction:** the native command's completion check requires
NATIVE identities/raw captures for every actual attempt, with the one stable
identity already enforced by the core. Keep the injected path for CPU tests,
but do not promote its report by checking only COMPLETE/replay/gate flags.
Similarly bind the supplied original root-file bytes, not just the four
excluded labels or roots_sha256. build_roster validates64 preserved-wire cube
cases, but has no independent original-file authority. The handoff correctly
assigns that byte pin to preparation; do not omit it in the new command.

## 3. Core completion precedes native close and outer release

**Documented integration obligation, not a new core defect.**
`gpu/astra_pcfl_interface_dev.py:136` captures config/identity and call
sidecars, not load.json or close.json. run_stage writes its report without
closing the actor. The test at `tests/test_astra_pcfl_interface_dev.py:139`
explicitly checks that the session is still open. The returned COMPLETE report
and stage_gate_passed therefore cannot be the command/outer terminal result.

**Smallest correction:** retain Main's existing installed-engine shutdown
seam, call close in the command's finally path, and bind original load/close
and outer worker-exit/group/GPU receipts to the same stage/config/identity.
Require successful close and consumed-call accounting to agree with attempts;
this core adds no count_tokens calls. Failed backend/capture work remains
FAILED/ABORTED/UNCALLED even if cleanup later succeeds.

Use the fresh default NativeActor, not LFNativeActor: `_verify` at line178
requires unconstrained default sampling, and final ROUTE/READ/THINK require
whole single-line responses without trailing LF. Reusing the own-write LF
scaffold would be a configuration/capture failure, not a model wrong answer.
Do not call start/count_tokens before run_stage: it explicitly requires an
unstarted actor output directory at line343. If checking cold timing, compare
generation_started with load.ready_at, not operation_started; default native
lazy loading occurs inside the first generation operation.

Default NativeActor.close delegates to session.close (`native_actor.py:471`);
its shutdown-method flags alone are not GPU-release proof. No new cleanup
implementation is requested from the interface core.

## 4. Failed-capture token totals are not complete usage totals

**Reporting advisory.**
`gpu/astra_pcfl_interface_dev.py:259` verifies the response/capture before
incrementing result.actor_tokens at line266. A generation followed by a
capture-join failure can therefore leave result.actor_tokens at0 although an
attempt and raw response exist. The stage correctly aborts and preserves the
attempt; the zero is not evidence that no computation or output occurred.

**Smallest correction:** downstream cost reporting keeps failed-stage usage
separate and uses only independently valid native receipts for actual token
counts. If that count cannot be verified, report unavailable/partial, not
zero. Outer elapsed intervals remain costs, not GPU-active time. Do not turn
an ABORTED/UNCALLED record into a scored wrong answer to complete a usage sum.

## 5. Fixed CONTINUE invites another THINK even after the sixth

**Prompt advisory, not a scoring leak.**
`gpu/astra_pcfl_interface_dev.py:23` says “think again”; lines270–276 append
that same message after the sixth accepted THINK, although a seventh THINK
is rejected. The initial system discloses the six-THINK cap, so the policy is
recoverable, but the immediate invitation is unnecessarily inconsistent at
the boundary.

**Smallest optional correction before freezing new prompt bytes:** a fixed,
counter-independent continuation such as “CONTINUE: follow the declared turn
budgets and commit the final action when ready.” It must remain independent
of path correctness, hidden world state and the score. No route feedback,
counter-dependent coaching or extra turn is needed. Otherwise preserve the
current literal and disclose this minor ambiguity; do not silently alter it
inside the command wrapper.

## Exact reviewed bytes

All source/test hashes match the named EDITSTOP handoff. Tests were inspected,
not rerun; its20-test PASS remains the author's report.

```text
0cb07c0a02770ee8d9aeae0e105957eff1bff56042c4daf7ab7401a1ee3f68b3  gpu/astra_pcfl_interface_dev.py
1298fe2ec390b0564407113d022f53a95871f2e5c6d7b2cdf8c78dc6c3c38b25  tests/test_astra_pcfl_interface_dev.py
ea31f485dcea95a75cada96ae54b607c3ee7a4d860a335b53a01818f0e475100  /tmp/astra_pcfl_interface_dev_handoff_20260913.md
915b27d4dfe51623535bae588e54e1e35654a956f164aa23eba74a925a4a23ff  gpu/astra_pcfl_native_actor.py
ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e  organism_v6/pcfl_vertical_dev.py
```

No parser, scorer, root inventory, task threshold or whole-response scoring
change is requested. In particular, keep THINK text in assistant history,
return only the fixed continuation or authorized exact READ content, and
score the entire terminal raw string without extraction or normalization.
