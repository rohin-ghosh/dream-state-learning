# Offline immutable-prefix reader candidate

Non-material, opt-in repair candidate; **not deployed, not startup-approved**.
Everything authored here is inside this worker. Existing sources, source epochs,
journals, parent services, GPU/native processes and leases are untouched.
The reservation maximum remains **30 seconds**. Synthetic test duration is not
a measurement or promise of actual receiving time.

## Status and blocking integration evidence

The implementation supports prehash at COMPLETE **A**, then an independently
approved exact COMPLETE **B >= A**, without hashing A's bodies again. Every raw
record and intent in **A+1 through B and the entire retained tail** is verified
using the original `hash_record`. New INBOX records between A and B are decoded
and advanced; cached INBOX state is used only through A. No changed selection is
inferred from a directory, child message, durable anchor, or self-signed cache.

**Actual namespace integration is held.** Main reports a read-only observation
at September 19, 2026 02:30:14 UTC: C2 node5 host `mnt:[4026531832]`, original
native PID `1139778` `mnt:[4026536303]`. This was supplied by main, not independently
probed here. They differ. This implementation deliberately refuses that reuse.
Same-namespace CPU observer success does not prove confined native startup.
Do not fill the proof with an invented consumer namespace, patch `environment`,
copy the producer's namespace into an allowlist, or drop the namespace check.

A supported deployment must establish that producer and actual consumer share
the same explicitly admitted boot/mount namespace and exact underlying source,
root, directories and files. Merely producing inside the *old* native's namespace
does not prove that a newly created systemd consumer will inherit that namespace.
Otherwise a separately reviewed, operator-pinned producer/consumer-context design
is still required. No cross-namespace authorization API is implemented here.

## Artifacts

- `prefix_port.py`: requires original reader SHA256
  `972456b7d6cb026cc922e067114701d4f157fa6ed775e4406ecb52c86eef7d3e`;
  seven exact replacement seams; returns candidate bytes, never edits its input.
- `checkpoint_tail_runtime.candidate.py`: generated port candidate, intended only
  for a separately reviewed **new** source epoch's `gpu/checkpoint_tail_runtime.py`.
- `immutable_prefix_proof.py`: proposed `gpu/immutable_prefix_proof.py` in that
  same new epoch; producer, strict guard loading, identity verification, bounded
  forward selection, and reader session.
- `prefix_cli.py`: CPU-only producer, final-selection guard candidate builder,
  and read-only receiving probe. Does not take a writer lock, publish journal
  events, load a checkpoint into a GPU, send messages, or launch/signal processes.
- `test_prefix_proof.py`: isolated synthetic tests against separately copied C2,
  pair learner, and pair frozen source/classes; not replacement classes or live
  checkpoint tests. Copies and generated journals stay within this worker.
- `TEST_RECEIPT_v3.json`, `TEST_RUN_v3.log`: final validation and exact code hashes.
  Earlier v1/v2 receipts are intermediate evidence, not the final artifact binding.
- `TO_BANACH_PASTEUR.md`: bounded receiving interface and unresolved admission gate.

## Trust boundary: conditional metadata proof, not cryptographic immutability

The producer hashes **all raw prefix record bytes** through A with the existing
reader's `hash_record`; that routine also verifies the original intent document.
The producer snapshots both record and intent before/after verification and again
at completion: dev, inode, size, mtime_ns, ctime_ns, mode and link count. It stores
the full header chain, raw hashes, and header-digest-bound INBOX documents. It
does not replace the authoritative COMPLETE checkpoint or serialize a frontier
cache. It does not replay historical learning transitions.

The fast consumer checks those exact identities twice; checks every component of
the original root path without following symlinks; binds the original records,
inbox, manifest and writer-lock objects; and hashes the full raw extension/tail.
Root/record directory timestamps are **not frozen** because legitimate appends
change them; directory device/inode/type/mode remain bound. Selected COMPLETE B
and required sidecar records still pass the original body decoder/validators.
New/unregistered mailbox files retain original `read_inbox` semantics.

**Required operator assumption:** trusted local Linux filesystem/kernel and
source process, no privileged metadata forgery, filesystem rollback, inode/time
ABA, or concurrent rewriting of the immutable prefix. Boot and mount namespace
must remain identical. This is an explicit assumption, not something `stat`
proves. Exact-source journal caches already use file-identity tuples in-process;
this candidate extends that assumption across a restart with external authority.
It is not equivalent to a fresh cryptographic hash against hostile storage,
silent bit corruption with unchanged metadata, coarse/lying metadata, or a
privileged attacker. If existing evidence-custody invariants require detection
of those conditions at every restart, **do not use this fast path**: trusted
immutable storage/verity or full rehash before exit remains necessary. Nothing
here establishes the actual node's filesystem/admission prerequisites.

The proof's digest is not its own authority. Authority is an exact **external**
operator-selected guard path and SHA256. That guard pins proof path and SHA256,
the complete producer binding, the exact resume selection B, and explicit raw
advance byte/record budgets. Source binding independently pins source root,
all supplied source-file hashes, journal class, and an existing immutable source
epoch artifact's separate path/SHA256. Source-epoch artifact contents remain
opaque here; the original admission code must validate their plan, wall, model,
anchors, class policy and provenance. This helper does not grant admission.

The original source-epoch artifact must not contain the eventual proof digest:
keep it separate to avoid a circular digest. Producer binding and proof are
immutable; a new final-selection guard references them. Source and epoch must
not be switched between producer and consumer. All loaded `gpu`/`organism_v6`
modules and semantic journal methods must come from the pinned source.
The operator must pin the trusted producer/CLI code as well; an attacker who can
choose the externally approved bytes can forge a proof. Public hashes alone do
not authenticate a producer.

## Exact integration API

Default remains `scan(journal, selection)`; original default/full audit code is
unchanged. Only an explicitly approved receiving call uses:

```python
state = scan(journal, selection_B, prefix_proof={
    'guard_path': operator_approved_absolute_guard_path,
    'guard_sha256': operator_approved_raw_guard_sha256,
})
```

Do not obtain this reference from the proof, journal, child, environment discovery,
or the newest file in a directory. Route it from the existing trusted receiver
guard/admission boundary. That guard must also pin the new source epoch exactly.
Keep full explicit audits outside this hook, just as the original reader does.
Existing receiving call sites are **not patched here**: without the explicit
keyword, the candidate continues to hash the full prefix as before.

For A-to-B reuse, only `complete_index` and `complete_sha256` may differ. All other
selection fields (policy, root, journal ID, life, tail limits, sidecars and anchor
persistence policy) must be byte-equivalent as JSON values. B cannot precede A.
The guard must pin B's exact hash, never merely permit any future COMPLETE.
`max_advance_records` bounds B.index - A.index; `max_advance_bytes` bounds raw
records A+1..B. Original tail limits separately apply to B+1..head. Actual bytes
are rechecked against these limits during hashing. Neither budget is a wall-time
extension. A large interval must be refused or prehashed again **before** exiting
the old native; no automatic whole-prefix fallback is permitted.

All proof/guard/epoch/source/metadata failures propagate. Do not catch them and
retry unproved/full recovery after exit. A newly persisted COMPLETE later in
the run does not acquire authorization from an old guard; guard mismatch refuses.
Original exclusive writer locking and initialization remain the admission
owner's responsibility; `prefix_cli probe` is only a read-only CPU observation,
not a receiving LOADED receipt or dispatch approval.

## Input shape and bounded offline commands

Build a reviewed new candidate source tree separately. Never run these commands
with an immutable/live source as their output. The producer's pinned request is:

```json
{
  "schema": "R233_PREFIX_PRODUCER_REQUEST_V1",
  "journal_type": "gpu.orch_r125_stream_journal:StreamJournal",
  "source": {
    "root": "/absolute/new/epoch/source",
    "epoch": {"path": "/absolute/immutable/source_epoch.json", "sha256": "EXTERNAL_EPOCH_SHA256"},
    "pins": {"gpu/checkpoint_tail_runtime.py": "CANDIDATE_SHA256", "...": "ALL_REQUIRED_SOURCE_PINS"}
  },
  "selection": {"...": "EXACT_ORIGINAL_CHECKPOINT_TAIL_SELECTION_AT_A"}
}
```

Use the actual original pair type `gpu.r232_recovery:LearnerJournal` or
`gpu.r232_recovery:FrozenJournal` for those arms, not the C2 base or each other.
Supply real 64-hex digests and full exact schemas, not the placeholders shown.
Include every imported source module in `pins`; missing pins refuse.

```bash
WORKER=research_loop/workers/post_recovery_prefix_proof_20260919

# Candidate bytes only; the output must not already exist.
python3 -B "$WORKER/prefix_port.py" "$ORIGINAL_READER" "$NEW_READER_CANDIDATE"

# Outside reservation, on node, in a SUPPORTED bound namespace only.
timeout 180s env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  python3 -B "$WORKER/prefix_cli.py" produce \
  --request "$REQUEST_A" --request-sha256 "$REQUEST_A_SHA256" \
  --proof-output "$NEW_PROOF" --guard-candidate-output "$NEW_GUARD_A"

# Bind the independently approved exact later selection without prefix rehash.
# The output remains a candidate: original admission must pin its exact bytes.
timeout 10s env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  python3 -B "$WORKER/prefix_cli.py" bind-resume \
  --proof "$NEW_PROOF" --proof-sha256 "$PROOF_SHA256" \
  --selection "$SELECTION_B" --selection-sha256 "$SELECTION_B_SHA256" \
  --max-advance-records "$APPROVED_ADVANCE_RECORDS" \
  --max-advance-bytes "$APPROVED_ADVANCE_BYTES" \
  --guard-candidate-output "$NEW_GUARD_B"

# CPU-only pre-exit timing/equivalence probe; NOT a 30s reservation extension.
timeout 30s env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  python3 -B "$WORKER/prefix_cli.py" probe \
  --guard "$APPROVED_GUARD_B" --guard-sha256 "$APPROVED_GUARD_B_SHA256"

# Synthetic tests only; new receipt name must not already exist.
timeout 180s env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  python3 -B "$WORKER/test_prefix_proof.py" --receipt "$WORKER/NEW_TEST_RECEIPT.json"
```

Timeouts fail the operation; they never authorize a retry, exit, fence or launch.
These separate timeouts are not additive allowances inside a reservation. Main
must retain the **single existing 30s overall reservation budget**, including all
other checkpoint, admission, namespace, parent and receiver work. Output files
are exclusive-create. An interrupted producer may leave an unapproved output;
inspect it, never auto-discover/adopt it. Keep proof, raw journals and full hashes
on the node; return only bounded summaries/SHA references to the VM.

## Remaining proof requirements

1. Banach/Pasteur/main settle the actual original-admission consumer namespace;
   the supplied C2 observation currently demonstrates a mismatch, not support.
2. Independent review accepts the stated metadata/evidence-custody trust model
   on the actual filesystem. No code assertion can replace that judgment.
3. Original guard admission pins a separately prepared, tested new source epoch,
   immutable epoch artifact, proof, exact B selection and explicit advance caps.
4. Main verifies actual checkpoint/history byte equivalence, required sidecars,
   pending/mailbox preservation, separate C2/pair policies, and the complete
   receiving path within the unchanged 30s reservation **before old-native exit**.
   This worker does not duplicate main's actual checkpoint/source probes.
5. Original parent fencing/LOADED/rebind approvals remain separate; these helpers
   neither implement nor invoke any of those actions.
