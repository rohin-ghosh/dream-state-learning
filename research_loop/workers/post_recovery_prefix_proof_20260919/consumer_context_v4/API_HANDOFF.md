# V4 sealed offline candidate — ready for main's real CPU benchmark

Hash capture: September 19, 2026 02:47:13 UTC. **195 tests PASS**:
59 each against independent C2, pair learner and pair frozen classes, plus the
18 original default-reader regressions. All v3 sealed hashes remain unchanged.
No native, GPU, staging, supervisor, lease or parent actions were performed.
The original total reservation maximum remains **30 seconds**.

## Ready files

Copy only into a separately approved NEW candidate source epoch:

- `checkpoint_tail_runtime.candidate.py` -> `gpu/checkpoint_tail_runtime.py`.
- `immutable_prefix_proof.py` -> `gpu/immutable_prefix_proof.py`.
- `prefix_cli.py` is the offline CPU producer/binder/probe command; keep the v4
  helper beside it so its bootstrap import cannot accidentally load v3.
- `SEALED_RECEIPT.json` contains full SHA256 pins; `TEST_RECEIPT_attempt1.json`
  and `TEST_RUN_attempt1.log` are the successful final tests, despite the names.

This is implementable source, not namespace instructions or a startup approval.
Main owns actual source admission, filesystem/native-view inspection, exact real
checkpoint comparison and complete receiving timing. Keep full proof/journals
on node. Do not copy GB journal bodies to the VM.

## ABI: preserve original admission as the authority

Default full reader/audit remain unchanged. Opt-in strict proof mode still
defaults to `SAME_MOUNT_NAMESPACE`. New proof/guard schemas are V2; v3 files and
V1 schemas remain untouched. The cross-namespace call is:

```python
state = scan(journal, selected_complete_B,
    prefix_proof={"guard_path": approved_guard_path, "guard_sha256": approved_guard_sha},
    prefix_admission={"path": original_admission_path, "sha256": original_admission_sha,
        "field_path": ["receiver", "prefix_consumer_context"]})
```

`field_path` is an explicit list of keys in the independently pinned **original
admission document**. Main/Banach/Pasteur must pass this reference ONLY after the
existing guard/allocation/CPU-receipt chain validates it. Never accept either
reference from child messages, proof discovery, environment discovery or a
caller-created substitute admission. The helper validates bytes and scope; it
cannot independently establish who authorized the reference. Exposing both
references as untrusted API inputs would destroy the authority boundary.

The original receiving admission's clause must equal:

```python
clause = immutable_prefix_proof.admission_clause(final_guard, approved_guard_reference)
```

This function builds a **candidate clause**, not an authorization. Original
admission must adopt/pin the exact resulting bytes at the chosen `field_path`.
The clause binds its schema/mode, exact guard path/SHA, producer binding digest,
proof path/SHA, independent immutable source-epoch pin, 30s maximum and no wall
extension. A mode string in the guard is insufficient: cross mode without this
separate original-admission reference always refuses, even in the same namespace.

Build the final candidate guard for explicit A-to-B reuse as before, adding:

```python
guard = immutable_prefix_proof.guard_candidate(
    proof, exact_proof_path, proof_sha256,
    resume_selection=selected_complete_B,
    max_advance_records=approved_advance_records,
    max_advance_bytes=approved_advance_bytes,
    consumer_context_mode="SAME_FILESYSTEM_OBJECTS_ACROSS_ADMITTED_NAMESPACE")
```

Only the namespace equality requirement changes under this admitted mode.
Same kernel boot is mandatory. Every producer-pinned source/epoch file identity
and immutable source directory metadata, original root chain, records/inbox
directories, writer lock, manifest and EVERY prefix record/intent identity is
rechecked through the consumer's own path/FD view. Source contents are also SHA
verified. Root/ancestor and mutable journal directory stable dev/ino/type/mode
remain pinned; append-changing directory size/timestamps are not frozen. No
checks are omitted to accommodate bind mounts or private namespaces.

Producer and measured actual consumer boot/namespace identities appear in
`receipt["prefix_proof"]["consumer_context"]`, alongside mode and admission pin.
No expected future namespace is invented. A namespace change during the scan
refuses. Cross mode does not grant a namespace allowlist or filesystem-copy
exception. Exact B selection, INBOX handling, full raw interval/tail verification
and fail-closed/no-full-prefix-fallback behavior remain as in v3.

## Quiet-age / timestamp-granularity guard

Producer stat-preflights **all prefix records and intents before any raw record
hashing**, plus every pinned source/epoch file and immutable source directory.
Each mtime and ctime must be at least **3,000,000,000 ns older** than sealing
start. Young/future timestamps refuse; there is no sleep, auto-retry or bypass in
production. Stage/seal a new source and let it become quiet outside reservation.
Select an already quiet historical COMPLETE A. Later B/interval records need no
metadata shortcut: they are fully raw-hashed on consumption.

The policy and sealing clock are in the externally pinned proof. Consumer
revalidates the age relative to sealing start, checks start <= finish <= current
clock, and refuses a policy with a lowered window. Main's same-size immediate
rewrite/mtime-restoration collision is covered by a deterministic test that
aliases all metadata in the same clock quantum: production refuses the **young
proof before hashing**, rather than pretending to detect unchanged metadata.

**Concrete remaining trust requirement:** 3s is a conservative admission
assumption, not an automatic proof of filesystem granularity/cache behavior.
Admit only coherent attributes with timestamp aliasing strictly shorter than
the window, no wall-clock rollback, privileged metadata rollback/forgery, silent
storage mutation or concurrent immutable-prefix writers. A statfs ext2/ext3/ZFS
label alone does not establish those properties. If old metadata can remain
aliased/stale for >=3s, this guard is insufficient and the shortcut must not be
admitted. This worker does not claim to have proved the actual node property.

Positive unit fixtures inject a documented +4s logical clock to avoid hundreds
of seconds of fixture aging. Negative age/collision tests use explicit same-
quantum clocks and metadata aliasing, not sleeps. Real CLI tests wait 3.2s for
actual fixture quiescence. Simulated namespace tests do not claim real namespace
entry or actual receiving startup.

## Bounded commands

The producer request shape is v3's explicit selection/source/class shape, with
the NEW source pins and independent immutable source-epoch path/SHA. Produce
only after the 3s quiet-age requirement is satisfied, outside reservation.

```bash
V4=research_loop/workers/post_recovery_prefix_proof_20260919/consumer_context_v4

timeout 180s env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  python3 -B "$V4/prefix_cli.py" produce \
  --request "$REQUEST_A" --request-sha256 "$REQUEST_A_SHA" \
  --proof-output "$NEW_PROOF" --guard-candidate-output "$NEW_STRICT_GUARD_A"

timeout 10s env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  python3 -B "$V4/prefix_cli.py" bind-resume \
  --proof "$NEW_PROOF" --proof-sha256 "$PROOF_SHA" \
  --selection "$SELECTION_B" --selection-sha256 "$SELECTION_B_SHA" \
  --max-advance-records "$ADVANCE_RECORDS" --max-advance-bytes "$ADVANCE_BYTES" \
  --consumer-context-mode SAME_FILESYSTEM_OBJECTS_ACROSS_ADMITTED_NAMESPACE \
  --guard-candidate-output "$NEW_CROSS_GUARD_B"

# Only AFTER original admission independently adopts/pins the exact context clause.
timeout 30s env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  python3 -B "$V4/prefix_cli.py" probe \
  --guard "$APPROVED_GUARD_B" --guard-sha256 "$APPROVED_GUARD_B_SHA" \
  --admission "$ORIGINAL_ADMISSION" --admission-sha256 "$ORIGINAL_ADMISSION_SHA" \
  --admission-field-path '["receiver","prefix_consumer_context"]'
```

The probe is read-only, takes no writer lock, writes no journal events, and is
not LOADED/dispatch approval. Original locking/admission still applies to the
real receiver. These per-command timeouts do not add to or enlarge the single
existing 30s reservation. No failed command authorizes fallback or native exit.

## Banach/Pasteur critique requested via main

`TO_BANACH_PASTEUR_REVIEW.md` requests review of this exact original-admission
boundary; direct agent messaging is not exposed here and no acknowledgment is
claimed. Existing peer notes specifically disallow new arbitrary guard authority.
The new independent admission reference must enter their existing pinned chain,
not bypass it. Please route the request and this sealed ABI to both peers.

Concrete known integration concern: `BindPaths=copy_raw:plan.root` preflights
expose different journal objects. Original-journal proof MUST reject a clone.
Do not drop inode checks for that route or confuse a clone-bound synthetic test
with actual source-object evidence. Main's full native-view fingerprints are the
appropriate additional evidence for actual receiving context review.
