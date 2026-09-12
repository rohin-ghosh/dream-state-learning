# Independent narrow review: semantic carrier diagnostic

Date: 2026-09-12 UTC. Scope: `organism_v6/semantic_carrier_diagnostic.py`, `tests/test_semantic_carrier_diagnostic.py`, and the actual local helpers they call. Read-only repository review; this report is the only retained file written by the reviewer. Main owns selection and launch. No GPU access, model loading, CompilerGym execution, experiment jobs, or git mutations occurred.

## Recommendation

**REQUEST CHANGES for the bounded-cleanup safety contract; otherwise the inspected logic is suitable for a DEV exact-row surface diagnostic, subject to real prepared-input preflight.** This is not a training approval, scientific-result certification, or C11 final-custody decision. The CPU suite passes, but it mocks the cleanup helper and does not establish the process-lifetime guarantee.

## Blocking safety finding

### R1 — P1: worker lifetime is not reliably bounded when the controller is terminated

Evidence: `organism_v6/semantic_carrier_diagnostic.py:409` launches a separate-session worker; `organism_v6/semantic_carrier_diagnostic.py:414` protects `wait()` with a Python exception handler, but there is no SIGTERM handler or independent lifetime supervisor in this module. The worker checks parent identity only at startup (`organism_v6/semantic_carrier_diagnostic.py:343`), and checks deadlines before model loading and between requests (`organism_v6/semantic_carrier_diagnostic.py:348`, `organism_v6/semantic_carrier_diagnostic.py:356`), not during a blocking model load/generation/forward call.

Consequently, terminating just the controller with ordinary SIGTERM does not take the Python exception cleanup path. Its separate-session worker can continue executing. A stalled inference call then has no surviving controller timeout to enforce the deadline. SIGKILL of the controller has the same orphaning limitation. This is a concrete gap in the requested execution-safety contract, not a claim that normal successful execution leaks a worker.

There is a second, related gap in the actual helper: `organism_v6/multikey_writer_gateway_simple.py:1085` checks only the leader's `poll()`/`wait()`. It sends group SIGKILL only if the leader itself survives SIGTERM. If the leader exits but an owned descendant survives, no subsequent group cleanup occurs; if the leader has already exited, the helper sends no signal at all. The caller also performs no cleanup on a normal nonzero worker exit (`organism_v6/semantic_carrier_diagnostic.py:421`). This matters whenever a worker has descendants; the review did not observe or launch any actual descendants.

The existing timeout test patches `stop_owned_process` itself (`tests/test_semantic_carrier_diagnostic.py:256`), so its passing assertion proves only that the helper is called on a simulated `TimeoutExpired`, not that cleanup completes or handles signals/descendants.

Minimal correction:

- Handle controller SIGTERM by entering an owned-worker cleanup/finally path; retain partial artifacts and failure evidence.
- Make cleanup verify the owned group rather than only its leader, escalating surviving owned members within the existing bounded grace period and handling exit races. Never use global process-name kills or touch unrelated GPU users.
- For a hard guarantee across controller SIGKILL or loss, have main bind execution to an independently enforced owned process-group/cgroup deadline, or add an equivalent independent supervisor. A Python SIGTERM handler alone cannot provide this guarantee.
- Add CPU/mock regression coverage for controller cancellation, leader exit with surviving descendants, already-exited leader, and signal/exit races. Where the main launcher already supplies the hard lifetime bound, present that exact evidence instead of assuming it exists.

This report does not modify the shared helper or prescribe changes to unrelated experiments.

## Experimental validity and interface checks

- **Fresh fixed material and all 64 items:** `organism_v6/semantic_carrier_diagnostic.py:103` creates a deterministic new namespace; `organism_v6/semantic_carrier_diagnostic.py:112` constructs two roots × two mappings × eight tools × two modes = 64 semantic items. Each of the four cells is 8/8 balanced. The 32 complementary pairs change only the binding's action, not task or identifier. No prior artifacts, adapters, fits, or benchmark scores are inserted into prompts. This is fresh researcher-authored material, not evidence of uncontaminated model provenance.
- **Coverage:** `organism_v6/semantic_carrier_diagnostic.py:170` creates generation plus scoring for every semantic item, and generation for 16 copy canaries: 144 records, 80 generations, 64 scoring requests, 128 candidate forwards. `organism_v6/semantic_carrier_diagnostic.py:274` rejects missing, duplicate, or mismatched record IDs. Tests cover balanced cells and all worker calls (`tests/test_semantic_carrier_diagnostic.py:53`, `tests/test_semantic_carrier_diagnostic.py:183`).
- **Actual generation interface matches:** `organism_v6/semantic_carrier_diagnostic.py:358` supplies the flat request expected by `organism_v6/writer_interface_calibration.py:236`. That helper constructs a fresh greedy `GenerationConfig`, applies the requested 32-token cap and tokenizer EOS, and returns the exact fields checked at `organism_v6/semantic_carrier_diagnostic.py:248`. Audit metadata is not supplied to `model.generate`.
- **Candidate LF+EOS scoring is correctly shifted:** `organism_v6/semantic_carrier_diagnostic.py:131` tokenizes the whole rendered prompt plus candidate, rejects boundary-straddling/prefix changes, masks the prefix, and appends exactly one EOS after the LF-containing candidate. `organism_v6/semantic_carrier_diagnostic.py:322` scores each response token at index minus one, including LF and EOS. `organism_v6/semantic_carrier_diagnostic.py:261` sums rather than length-normalizes the continuation log probabilities; unequal candidate lengths are retained. Ties/nonfinite values become invalid choices rather than favorable scores. The mock teacher-forcing test checks these indices (`tests/test_semantic_carrier_diagnostic.py:337`).
- **Thresholds are conjunctive, not score-based rescue:** `organism_v6/semantic_carrier_diagnostic.py:312` requires at least 15/16 correct in each cell for both generation and scoring, at least 61 valid generations, zero truncated/multiple-action semantic generations, at least 29/32 correct complementary pairs for each operation, and all eight canaries for each root. Generation/score agreement is reported, not separately gated. Invalid individual scores can consume the explicitly allowed error budget; they are not automatic whole-assay aborts. Boundary and anti-pooling tests exercise this policy (`tests/test_semantic_carrier_diagnostic.py:292`, `tests/test_semantic_carrier_diagnostic.py:365`).
- **Actual tokenizer/model helpers match:** `organism_v6/multikey_writer_gateway_simple.py:894` provides `.tokenizer`, `.eos_token_id`, offsets and unnormalized decoding as used here. Its tokenizer loader is local-only, fast, and disables remote code (`organism_v6/multikey_writer_gateway_simple.py:908`). The model helper loads local bfloat16/eager weights without an adapter interface (`organism_v6/multikey_writer_gateway_simple.py:1149`); the diagnostic additionally freezes all parameters and checks no PEFT configuration (`organism_v6/semantic_carrier_diagnostic.py:350`).
- **Actual backend CLI matches:** `organism_v6/semantic_carrier_diagnostic.py:180` correctly uses `--list-actions` and `--passes=-mem2reg`/`--passes=-gvn`. These flags and JSON fields exist at `organism_v6/cgym_eval.py:14`, `organism_v6/cgym_eval.py:38`, and `organism_v6/cgym_eval.py:65`. The explicit `ok is True` check correctly catches backend errors even though the evaluator emits `ok:false` with exit code zero (`organism_v6/cgym_eval.py:73`). Registry coverage includes both candidate actions and all eight canary actions.
- **Normal controller timeout is bounded:** `organism_v6/semantic_carrier_diagnostic.py:399` limits the deadline to one hour and the configured deadline, which must precede the six-hour lease buffer (`organism_v6/semantic_carrier_diagnostic.py:70`). Its normal timeout reserves five seconds for the helper's two-plus-two-second waits. GPU identity/idleness helpers match the config but are specifically A40-only (`organism_v6/multikey_writer_gateway_simple.py:1066`, `organism_v6/multikey_writer_gateway_simple.py:1360`). An A100 selection fails closed; main must not assume this executor is GPU-type-generic.

## Limitations / nonblocking qualifications

1. **Real context headroom is implemented, not demonstrated by this review.** `organism_v6/semantic_carrier_diagnostic.py:153` checks candidate response including EOS ≤24 and total length ≤2048; `organism_v6/semantic_carrier_diagnostic.py:163` checks real encoded prompt length +32 ≤2048. Prepare/revalidation uses the configured real tokenizer rather than character counts. However, all tests here use a character fixture (`tests/test_semantic_carrier_diagnostic.py:20`). No actual snapshot/config was supplied or loaded. Main must retain the prepared real-tokenizer counts/masks and verify the pinned model's actual context capacity; `pin_inputs` checks architecture dimensions, not `max_position_embeddings` (`organism_v6/semantic_carrier_diagnostic.py:96`). Fixture maxima of 295 prompt tokens and 15 response tokens are not Qwen measurements.
2. **Generation is whitespace-tolerant, not LF-byte-exact.** `organism_v6/semantic_carrier_diagnostic.py:241` strips only surrounding ASCII space/tab/CR/LF. Thus `ACT: -gvn` followed immediately by EOS is accepted without a terminal LF; this is deliberate in `tests/test_semantic_carrier_diagnostic.py:121`. Candidate scoring still includes mandatory LF+EOS. A CPU probe replacing every generation's terminal LF with immediate EOS passes all 64 semantic generations. This is not a blocker for the implemented whitespace-tolerant surface diagnostic, but a claim of byte-identical LF+EOS greedy generation would be false; if that is required, compare against the exact candidate bytes and update the test.
3. **Sixteen canary calls, eight unique prompts.** The root index is audit-only for copy requests, so each action-copy prompt is repeated identically across roots (`organism_v6/semantic_carrier_diagnostic.py:124`). All 16 must pass, but these are not 16 independent canaries or a test of unfamiliar action contexts.
4. **Compiler preflight subprocess-tree bound is unproven.** `organism_v6/semantic_carrier_diagnostic.py:186` times out the direct evaluator at 30 seconds but does not start/clean a dedicated process group. The evaluator opens a CompilerGym environment and closes it only through its normal `finally` (`organism_v6/cgym_eval.py:27`, `organism_v6/cgym_eval.py:68`). If the provisioned backend leaves service descendants when forcibly terminated, this wrapper does not establish their cleanup. No actual CompilerGym service lifecycle was exercised. A dedicated owned-group wrapper or evidence of externally bounded service lifetime would close this qualification.
5. **Claim boundary remains narrow:** correct copying of one supplied row does not establish learned binding, retained memory, tool-policy quality, or compiler optimization benefit. Snapshot hashes/revision strings do not authenticate official model origin. These restrictions are correctly expressed by `organism_v6/semantic_carrier_diagnostic.py:35`. Byte inventories and exclusive artifact writes provide useful DEV replay protection, not adversarial custody. GPU idleness is a point-in-time check, not a reservation; main still owns lease and shared-node scheduling.

## Tests actually run

Command (CPU-only, no repository bytecode/cache writes):

```text
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES='' TMPDIR=/tmp python3 -B -m unittest discover -s tests -p test_semantic_carrier_diagnostic.py -v
```

Result: **19/19 passed**, 1.097 seconds. The first attempt with `python` did not run because that executable was unavailable; the explicit `python3` rerun above succeeded.

Additional in-memory CPU/mock probes (no worker/service subprocesses or real signals):

- All generated answers with LF removed still produce `SEMANTIC_EXACT_ROW_SURFACE_OK`, valid=64.
- Copy-canary cardinality is 16 calls / 8 unique prompts.
- Calling the real `stop_owned_process` with mocked OS signaling and a leader that exits on TERM sends TERM only; an already-exited leader causes no signaling/waiting. This confirms the helper control-flow gap, not a measured live orphan.
- Confirmed default SIGTERM disposition in the review interpreter; the diagnostic installs no handler.

No real tokenizer, model forward, GPU, backend smoke, real process-tree cleanup, or independent main-launcher supervision was validated.

## Reviewed bytes

SHA-256 values measured after the CPU suite; line references above are repository-relative:

```text
439986ceb3885b323f944a32c73e0d0c68a81cf6cf5a5374c6eae0982e05060d  organism_v6/semantic_carrier_diagnostic.py
fec36412d42f2c0c43bd278d8c7fb7fb73e70b481563b7a103e7f0f6bb92a1ce  tests/test_semantic_carrier_diagnostic.py
b9fd33c7c11b2f57395f08d609bb1df004d9663eeefd143060bb1a24a34f10c8  organism_v6/multikey_writer_gateway_simple.py
9ab582ebc935ae36b88bd412fd06d799044661612f89a0770e46b92ab1b066c7  organism_v6/writer_interface_calibration.py
531d137c3c288f44aef20fa8096cc6caf8663879c892b4d22463b2b01cf7a1bd  organism_v6/cgym_eval.py
```

Existing concurrent repository changes were left untouched. Re-review repaired bytes and relevant safety evidence before treating this recommendation as acceptance.
