# PCFL scoped C0 native zero-fit: independent prelaunch audit

> **Correction, 2026-09-13 13:44 UTC.** The audit's statement that the
> attempt-1 `/tmp` manifest and allocation were absent was based on an
> observation made through the always-on helper VM, not node 2 where those
> paths live. Main subsequently rehashed both exact files on node 2; they were
> present and matched their recorded hashes. Retract the missing-file claim
> and the resulting second launch blocker. The stronger recommendation to
> preserve raw and canonical inputs before spawn remains good final-C11
> hygiene, but under Rohin's explicit directive it is not a blocker for this
> exploratory scoped C0 run. Attempt 2 additionally has an honestly labeled
> mid-run custody copy; it cannot be relabeled as pre-spawn custody. The exact
> service-process repair was implemented and tested in `9a6d91d6`, so the
> corrected prospective status is: service blocker closed; scoped C0 attempt
> 2 may be used as exploratory DEV evidence subject to the terminal audit.

**Date:** 2026-09-13  
**Audited implementation:** remote commit `ba2872cc` (`Bind tested C0 outer controller and native pre-GPU acceptance`)  
**Scope:** static and receipt audit only; no model, tokenizer, native backend, GPU, training, or test execution; no runtime/test edits

## Verdict

**Corrected verdict: ACCEPT exploratory scoped C0 after the exact
service-process repair in `9a6d91d6`; require the terminal audit before using
the result.** The original audit held `ba2872cc` for two repairs. The first was
real and is closed. The second arose from the wrong-host observation corrected
above and is reclassified as final-C11 hardening.

The scientific/runtime design is otherwise fit for its deliberately narrow purpose. It consumes one sealed, fixed inventory; exposes only the public task interface to one frozen Qwen2.5-7B-Instruct C0 actor; performs no fit, update, adapter mount, parenting, or retry; preserves the full 800-task denominator; and requires observed process/GPU release before a completed execution becomes usable.

The original audit identified two putative operational blockers, not
benchmark or model-design defects; the second is now retracted:

1. The real first preflight correctly failed closed on two unreadable, same-UID user-session daemons. A prospective exact-identity exception is needed for only those opaque processes; broadly ignoring `EACCES` is forbidden.
2. **Retracted:** the manifest/allocation absence observation was made on the
   wrong host. Durable pre-spawn snapshots remain a final-C11 hardening
   recommendation, not an exploratory launch blocker.

Attempt 1 must remain immutable. Any repaired execution is a separately named attempt 2 with a fresh outer directory, diagnostic output, outer claim, manifest, allocation, and deadlines. It may reuse the exact frozen roots, 212 choices, plan, and tokenizer measurements. It may not rerun opaque-ID selection, change a task, replace a root, or call the new execution a retry of a model call: attempt 1 made no worker or model call.

## Exact fixed lineage verified

I inspected the committed receipts and the retained node-2 artifacts directly.

| object | independently observed evidence |
|---|---|
| fixed roots | four roots in exact order `excluded/0..3`; `roots.json` byte SHA-256 `bcca78ae2abadb2a5f9680dc70ed55327185614198a4b873a5f3e487b2ed443e` |
| fixed opaque IDs | 212 accepted choices, all exactly 8 tokens, 212 unique texts and 212 unique token vectors; chosen salts range 0..10; `choices.json` byte SHA-256 `eccd2a7d854ebb8345b23a91957a4242bd502a264aa2122940b81074512c5a6c` |
| choices-to-roots join | the sorted 212 chosen texts exactly equal all 212 opaque values in the four root inventories; no missing or extra value |
| logical plan | internal seal `4ba1c08e4189bac8c8a3eb25c5d270470871bc11613dfdbdfcb93d96e68a3c6e`; four roots, 800 unique task IDs, 1,952 unique conditional actor-call IDs, 12-read/task cap, `fits=0`, `updates=0` |
| panel arithmetic | 640 delayed tasks = 4 roots x 16 cell/goal cases x 10 projections; 160 reachout tasks = 4 roots x 8 old/goal/render cases x 5 projections |
| call arithmetic | 704 one-shot tasks plus 96 `ACTIVE_LINKED_TEXT` service tasks x 13 possible generations = 1,952 maximum call slots; maximum turn is 12 |
| actual offline surface measurement | kind `ACTUAL_OFFLINE`, same plan seal, 4,533 unique measurements = 212 opaque IDs + 800 initial prompts + 1,760 READ queries + 1,760 returned blocks + one `MISS`; 29 complete equality groups; internal seal `3b5553d15cb12e551d7567f66c29ac8f37fecc63b84d9ee2f187f1b033b65d0c` |
| recovered-plan equality | the original inventory plan and recovered measurement plan are semantically identical and carry the same internal seal; their raw files differ only by the measurement copy's one terminal LF |
| recovery receipt | commit `53bc0fed` binds the same root-file hash and plan/measurement seals and states zero model calls and zero updates |

The original inventory attempt failed during used-surface measurement because Transformers returned a `Mapping` form the then-current renderer did not accept. Its retained failure explicitly says `UNQUALIFIED_NO_RESELECTION`, records 212 selected IDs, and binds the root/choice/plan artifacts. Commit `d2b5abe4` changed only the renderer's accepted container form. The recovery then measured the already preserved roots and plan. No selection algorithm was rerun in this chain.

For a fresh attempt, preparation may replay the frozen tokenizer transcript to require exact equality with the stored measurement. That is a validation of the same bytes, not permission to choose new IDs or produce a second measurement-selected inventory.

## No-learning and visibility audit

The execution path is structurally C0-only:

- `gpu/astra_pcfl_zero_fit_dev.py` imports the fixed world/runtime and native inference actor. It contains no trainer, optimizer, PEFT, checkpoint, corpus, compiler, or parent path.
- The manifest is closed over `full_v22_release=False`, integer `fits=0`, and integer `updates=0`. Its actor cap is exactly 1,952 calls and its logical denominator is exactly 800.
- The actor requires the public Qwen2.5-7B-Instruct revision and exact 14-file receipt, rejects any extra local model file and any path containing `adapter`, and verifies the full model file hashes before load.
- vLLM is bound to BF16, TP=1, eager execution, prefix caching off, remote code off, and `enable_lora=False`. Every generation supplies `lora_request=None` and mount `C0`.
- The only Torch context imported in the native path is `torch.inference_mode()` around generation.
- Public actor requests have exactly `id/messages/seed/mount`. They cannot carry cell, scorer, oracle, receipt, fit, adapter, or parent fields. The driver constructs those messages only from the sealed task's public system/user bytes and later model/READ-service turns.
- The fixed runtime used for `_task` performs generation, deterministic READ lookup, and scoring only. It does not write, fit, update, or call the full assay/training DAG.
- Researcher-authored ceiling material is explicitly tagged `RESEARCHER_AUTHORED_EXCLUDED_ROOT_CEILING_NOT_CHILD`; nothing here may be treated as an authentic child experience or inherited by a future child.

This supports a frozen supplied-memory **interface ceiling/failure** measurement only. In particular, `ACTIVE_LINKED_TEXT` here is an exact supplied service ceiling, not the post-DEV strong external-memory baseline.

## What `ba2872cc` gets right

### Sealing and one-shot behavior

- The outer receives exact manifest and allocation file-byte hashes, validates closed allocation fields, replays the manifest's internal seal, requires native rather than synthetic mode, and checks every source file named by the actor before spawn.
- The allocation binds the GPU ordinal and UUID, current boot ID and UID, interpreter, queue snapshot, lease end/margin, exact outer-source hash, and any permitted coordination-owner identities.
- The diagnostic output and outer directory must be fresh and disjoint from the model/source trees. A sibling `.outer_claim.json` is exclusively created before hardware preflight, preventing reopening the same diagnostic output under a new outer directory.
- The worker is invoked once with the exact manifest file hash, offline/telemetry settings, one GPU UUID in `CUDA_VISIBLE_DEVICES`, exclusive stdout/stderr, and `start_new_session=True`. There is no automatic second run or collection.

### Resource and lifecycle controls

- The direct queue must be exactly empty; managed mode must exactly match hashed pending/running entries. Finalization permits removal only, never a new or changed queue record.
- Current compute occupancy is queried by all-user GPU UUID, not by process name. Index-to-UUID drift, bad output, timeout, Boolean return code, or any compute PID fails closed.
- Worker cleanup targets only its verified isolated PID=PGID=SID. PID/start-tick/boot/UID/session checks precede group TERM/KILL; an unknown/reused identity is never blindly signaled.
- Worker wait reserves 30..120 seconds for cleanup. The total deadline is the minimum of wall cap, device-reservation cap, prepared actor deadline, and lease end minus margin; it includes validation, model hashing/load, all calls, close, cleanup, capture, and finalization.
- Capture and finalization are separate. A clean worker exit first produces `CAPTURED_AWAITING_RESERVATION_RELEASE`; only a later queue/CVD/GPU/group observation can produce the release attestation and call the driver's finalizer.
- A negative scientific panel does not become an execution error and is not retried. Conversely, an isolated `final.json` is insufficient without the cross-linked capture, release, and collection receipts.

### Output validation

Before capture, the outer requires all 800 task IDs in manifest order, every task scored, 800..1,952 actor attempts, one response per attempt, zero fits/updates, a native clean close, exact report/config/source/measurement seals, and release-inclusive clocks within cap. It then hashes every diagnostic output. Finalization rehashes that complete inventory and the captured outer files before attaching release evidence.

## Launch blocker 1: unreadable session-daemon environments

The first real attempt stopped after 2.678 seconds, before `Popen`:

- `preflight_queue.json`: exact empty direct queue, matched;
- `preflight_cvd.json`: no CVD owner and no unexpected owner, but unresolved `EACCES` for same-UID PIDs 36935 (`/usr/lib/systemd/systemd --user`) and 36938 (`(sd-pam)`);
- `controller_failure.json`: `pid=null`, `identity_verified=false`, error `CVD reservation unresolved/foreign`;
- no `spawn.json`, `worker_start.json`, actor output, or `preflight_gpu.json` exists.

The missing `preflight_gpu.json` matters for wording: attempt 1 itself does not attest GPU vacancy because the CVD failure occurred first. A separate Main observation found the node's eight GPUs and global compute-process inventory empty. Keep that external observation distinct from the immutable outer attempt.

The narrow repair should add a closed allocation field such as `opaque_environment_exclusions`. Each entry must prospectively bind the complete process identity `{pid,pgid,sid,start_ticks,boot_id,uid}` plus stable process descriptors available on this host (at minimum exact `comm`; preferably readable cmdline/cgroup and parent/session facts). Required semantics:

1. It exempts only `PermissionError` with `errno=EACCES` while reading that exact process instance's `environ`; it is not a CVD-owner allowlist.
2. Identity and descriptors are checked before and after the failed read. PID reuse, descriptor drift, a different exception, an absent required entry, or any additional unreadable PID fails closed.
3. If an allowlisted process becomes readable, its CVD is evaluated normally; a selected index/UUID remains an owner and blocks.
4. Preflight records the exact opaque set and retains exact queue plus all-user GPU vacancy checks immediately before spawn.
5. Finalization repeats the check. Only disappearance of a prospectively listed opaque process may be accepted as removal; no new opaque process is allowed.
6. Receipts must distinguish `opaque_environment_exclusions` from observed CVD owners and state that this is an exact session-daemon observability exception, not proof of kernel-atomic future GPU vacancy.

Minimum new regressions: exact listed-EACCES acceptance; wrong start tick/UID/boot/comm rejection; extra unreadable PID rejection; non-EACCES rejection; readable listed process with selected CVD rejection; missing listed process policy; finalization new-opaque rejection; and raw receipt preservation.

## Retracted launch blocker 2: manifest/allocation byte custody

Attempt 1's `context.json` records:

- manifest path `/tmp/astra_pcfl_c0_manifest_20260913_attempt1.json`, byte hash `8d52469dae0534abe0b8c1a8da23ec664b7a3634d4ce25876ec3498a6c94952f`;
- allocation path `/tmp/astra_pcfl_c0_allocation_20260913_attempt1.json`, byte hash `154593bfabfc0a220c42683c058ca8aac4cc06a12bad7fe7b429f013089e50bd`.

The original audit incorrectly reported both files absent on node 2. That
check actually ran on the helper VM. Main's direct node-2 check found both
files present with the recorded hashes. The following is retained only as the
stronger final-C11 hardening specification; it was not a valid reason to block
the exploratory scoped C0 run.

Before the final paper-grade C11 spawn, the outer must:

1. read and hash the raw manifest/allocation bytes once;
2. require each input to equal the project's canonical JSON encoding plus exactly one LF;
3. exclusively write byte-identical `manifest.input.raw.json` and `allocation.input.raw.json` into the fresh outer directory;
4. separately write canonical parsed snapshots and require raw-to-canonical equality;
5. include all four snapshots and their exact hashes in `capture_complete.json` and `collection.json`;
6. rehash the snapshots, not the original ephemeral paths alone, during finalization; and
7. bind the matching committed source identity/tree (or preserve a source-byte archive) so the manifest's source hashes remain independently resolvable after temporary staging disappears.

The outer may continue to require that the original input paths remain unchanged through finalization as an additional live-run check. They cannot be the only preserved copy.

Minimum new regressions: input path deletion after snapshot does not destroy later audit custody; a changed original still blocks during the live run; snapshot mutation blocks capture/finalize; noncanonical raw input is rejected; collection cross-links both raw and parsed snapshots; and a failed preflight retains the snapshots.

## Original fresh attempt-2 gate (item 1 closed; input snapshots deferred to final C11)

Before launch, require all of the following:

1. commit and hash the repaired outer/tests; no unrelated runtime/scorer change;
2. rerun the full existing outer suite plus the new opaque-process and input-custody adversarial tests;
3. create fresh canonical manifest/allocation bytes with a new output root and current deadlines;
4. require the new manifest's plan and measurement objects to equal the retained plan seal `4ba1c08...` and measurement seal `3b5553d1...` exactly;
5. require its four roots to equal `roots.json` (`bcca78ae...`) and its opaque values to equal the preserved 212 choices (`eccd2a7d...`); no allocator run or alternate salt/length/root;
6. preserve attempt 1's outer/launcher directories and the five observed receipts without modification;
7. run a new preflight into fresh attempt-2 roots; and
8. have a fresh reviewer check the repaired commit/receipts before interpreting output.

## Claim and post-run boundaries

Even after a clean attempt 2, the maximum claim is:

> On four excluded researcher-authored roots, the frozen C0 actor did or did not meet the registered interface ceilings/negative controls under one exact fixed 800-task plan and supplied-memory protocol.

It is not evidence for learning, retention, LoRA transport, recurrence, parenting, developmental improvement, H1/H2, G3, clean C11 ancestry, full v2.2 readiness, full allocator qualification, or external-memory saturation. The scoped measurement certifies within-render substitution groups only; RA/RB cross-render equality and any causal attribution to render order remain unavailable. The route construct passes, while the full construct is intentionally not claimed.

Post-run audit must independently verify all 800 result rows, all generation/request/raw/response joins, fixed denominators, no reused request IDs, no output-dependent repair, source/model/tokenizer pins, zero fits/updates, complete release evidence, and absence of a second attempt. `diagnostic_usable=True` means the execution is interpretable; it does not mean the registered performance thresholds passed.

## Conclusion

The native actor, zero-fit driver, and outer lifecycle form a coherent,
conservative C0 diagnostic. The first live preflight exposed one real guard
defect—the unreadable service-daemon handling—which `9a6d91d6` repaired
without changing the scientific inventory. The second alleged defect was a
wrong-host audit error. Pre-spawn input snapshots remain required hardening for
final C11, while the honestly labeled mid-run custody copy is sufficient to
retain attempt 2 as exploratory DEV evidence if its terminal integrity checks
pass. Do not promote this narrow supplied-memory ceiling into a learning or
whole-organism result.
