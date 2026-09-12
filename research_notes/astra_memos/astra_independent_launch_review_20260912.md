# Independent launch review — 2026-09-12

Advisory only. This reviewer does not have launch-pause authority. No repo
files were edited, no GPU work was run, and no commit was made. The author’s
parent-visibility patch is excluded from this review.

## Exact scope and evidence identity

- Commit: `e67c15fd854343a95b54605b4848dbe43ed66c12`, “Repair post-outcome
  isolation and explicit experiment seeding”, committed September 12, 2026,
  06:26:33 UTC (September 11, 23:26:33 Pacific).
- Reviewed that commit’s diffs and complete new
  `tests/test_builder_reproducibility.py`, plus the relevant existing callers.
  Target modules were loaded from `git show`, not the changing working tree.
- Separately reviewed the untracked standalone lineage API and its tests:
  - `organism_v6/lineage_guard.py` SHA256:
    `2404703eebeb152d944b6eb2ce16f8552a946907833dac7d36aba7b2139c2fc8`.
  - `tests/test_lineage_guard.py` SHA256:
    `1c01108512b65725e1dc6991fd2de70a4356740293f7c8fddc9b6251cc99aba4`.
  Both hashes were unchanged at the final source check.
- No review of concurrent preschool, batch-loop, gateway, seed-preparation, or
  other changes. The fake-world harness necessarily uses supporting modules;
  its imported parent module was the committed version, not the authored patch.

## Findings, highest consequence first

### F1 — P1, conditional on restart/reuse: old scanner receipts bypass the repair

Locations: `organism_v6/run_life_v2.py:202`, `:224`, and `:244`–`:260` at
the scoped commit. The new text coverage changes the meaning of “clean”, but
the incremental receipt has no scanner-policy version. Both the same-round
early return and the previous `scanned_rows` cursor still trust old receipts.

Reproduced with the actual pre-commit and post-commit scanner functions:

```python
rows = [{"kind": "note_after", "episode_id": "train/example",
         "text": "I chose -mem2reg."}]
```

The old `target_blind_check` writes an enforced clean receipt with
`scanned_rows=1`. The new direct `leak_scan_ledger(rows)` finds one hit, but:

- New `target_blind_check(..., round=1)` returns the old clean receipt.
- New `target_blind_check(..., round=2)` starts at row 1, scans nothing, and
  writes another clean receipt. No exception is raised in either case.

Thus a resumed childhood life can retain newly forbidden NOTE_AFTER text and
still pass the pre-sleep scan. The unchanged full-ledger held-out-ID check
does not rescue this example: its episode ID is an ordinary training ID.
This does not affect a genuinely fresh directory with no earlier receipts.

**Smallest correction:** version the scanner policy, exclude unversioned or
other-version receipts from BOTH cache lookup and cursor computation, and
write the version on new receipts. Preserve old receipts; append the new scan.
For example, in the existing function, before either cached-clean branch:

```python
SCAN_SCHEMA = "stored-child-text-v2"
prev = [record for record in prev
        if record.get("scan_schema") == SCAN_SCHEMA]
```

Add `scan_schema=SCAN_SCHEMA` to the existing `rec` dictionary. The constant
belongs next to the scanner policy. This makes a legacy receipt force a full
rescan without deleting evidence or redesigning the scanner.

**Minimal regression:** generate a real old-policy clean receipt over the
row above; require the new enforced checker to raise on both the same round
and a subsequent round. Verify clean, current-version receipts still permit
the intended incremental behavior.

### F2 — P1 at clean-lineage integration: eligibility can be fabricated

Locations: `organism_v6/lineage_guard.py:24`–`:39`, `:222`–`:249`,
`:264`–`:299`, and `:330`–`:337` in the hash-bound API snapshot.

This is a confirmed trust limitation, not a hidden contradiction of the API’s
documented contract. The guard checks declaration structure, hashes, recursive
references, declared exposure, and forbidden manifest/path strings. It does
not establish that an event happened, that artifacts were derived from the
cited sources, that all influences were declared, or that base bytes are
official weights. The documentation explicitly says so.

Reproduced using the supplied tests’ fabricated base/adapter fixtures, then
replacing a source’s bytes with:

```text
Invented event. QUARANTINE_TASK_EXPOSED CompilerGym -mem2reg.
```

After updating its hash and the local source references, while leaving the
manifest declarations `UNEXPOSED`, `validate_manifest` returned:

```json
{"eligible": true, "exposure_status": "UNEXPOSED"}
```

The real receipt also includes the explicit limitation in `scope`. Even an
`expected_sha256` computed from that fabricated entry manifest passes. A hash
supplied by the same untrusted declarant authenticates no history. Payload
bytes are hashed, not inspected for the forbidden markers used above.

**Smallest correction:** retain this API as a structural/declared-ancestry
checker, but do not let a launch caller use `receipt.eligible` alone as a clean
birth decision. Require a separately verified, complete inventory with a
manifest digest obtained from that trusted verification, verified base
identity, and verified origin/exposure evidence for the actual consumed
adapter/corpus bytes. Unknown or self-declared-only evidence is not eligible
for the clean lineage. Do not add a convenience fallback that manufactures
`UNEXPOSED` manifests from local paths or recomputed hashes.

No standalone scanner tweak can prove deliberately fabricated histories.
Scanning recognizable text markers could reject this particular payload but
would not fix renamed data, omitted ancestors, or invented events. Renaming
the receipt field alone would not fix the caller’s trust decision either.

**Minimal integration regression:** feed the fabricated bundle into the
actual clean-launch admission function and require rejection without trusted
provenance evidence, even though structural validation passes. Also reject a
trusted receipt when the launched adapter/corpus differs from its bound files.

The reviewed commit does not wire this standalone API into `run_life_v2`;
there is no demonstrated clean-launch admission implementation to approve in
this scope. This limitation does not disqualify an explicitly task-exposed,
disposable fresh-base scout that is not claimed as a clean ancestor.

### F3 — P2, conditional on artifact reuse: changing the seed does not validate existing fits

Locations: `organism_v6/run_life_v2.py:1008`–`:1035` and `:1048`–`:1055`.

The explicit seed is correctly forwarded for newly invoked fits. Existing
final/candidate adapters, or completed staged fits, follow the previous
idempotency path without checking that their recorded seed matches the new
argument.

Reproduction: the fake-world life completed two unseeded fits. Re-running
that same life directory with `--train-seed 23` succeeded with zero trainer
calls and reused the existing adapters. This is not a defect for ordinary
unchanged resumes; it becomes an experiment-validity problem if that reused
life is labeled as the seed-23 replicate.

**Smallest first-launch correction:** use distinct, fresh output/life
directories per source-identical seed replicate; never relabel an existing
life by changing this flag.

**Smallest code hardening for supported seeded resumes:** when an explicit
train seed is supplied, check every reused staged/candidate/committed fit’s
`train_meta.json` before consuming it. Missing seed metadata or a mismatch
must produce an explicit configuration/provenance error; do not overwrite or
silently retrain the existing artifact. Leave omitted-seed legacy behavior
unchanged. Add one changed-seed reuse rejection test and one matching-seed
resume test. This is conditional hardening, not a reason to idle a fresh run.

## What passed and does not need correction

- `run_life_v2.py:1054`: both new fake-world sleep fits receive exactly
  `--seed 23`, with rank 8 preserved. A separate default-life probe produced
  two fits with no trainer `--seed` argument.
- `train_adapter.py:16` and `:36`: explicit Python/Torch seeding happens before
  base loading and LoRA construction. Mocked trainer-main runs verified the
  event order `seed -> base -> lora`; omitted seed produced `base -> lora`
  with no manual-seed call.
- `train_adapter.py:74`: omitted seed retains `recipe=v1_frozen` and omits seed
  and determinism metadata. Explicit seed writes `v1_frozen_seeded`, seed 23,
  and the current deterministic-algorithms flag. Both mocked runs produced
  the expected completion marker. This is not evidence of GPU bitwise
  determinism, cross-node equivalence, or actual learning.
- `model_backend.py:42`: the single-call explicit seed reaches `batch` as a
  singleton seed list; omitted seed remains `seeds=None`. No default change
  or seed-dropping error was found in this route.
- `run_life_v2.py:524`: clone-group plus explicit train seed raises the stated
  unsupported error before clone-group construction/training. The focused
  fake-world probe observed no trainer invocation. Do not remove this check
  without implementing seed handling in the separate clone-training path.
- Fresh scans cover NOTE_AFTER’s actual stored `text` field, plus `prompt`
  and `note`. Additional probes found the token case-insensitively in each
  field and rejected NOTE_AFTER IDs in gate, exam, and canary families.
  The fixed held-out-ID regression also passes. Historical `text` fields in
  the other allowed text-row kinds are newly covered as intended.
- Selected lineage tests reject declared tainted ancestry and mismatched
  hashes, support a pinned structurally valid fresh root, and preserve files.
  None of these tests proves truthful declarations or authentic weights.

## Validation performed

CPU-only, no full existing suites:

1. All **9 new tests** from the scoped commit: passed.
2. **4 selected lineage tests**, not the full lineage suite: passed.
3. Focused default-seed, unsupported-clone, and changed-seed reuse probes.
4. Two legacy-cache reproductions using actual pre/post-commit scanner code.
5. One fabricated-ancestry reproduction with a pinned, self-authored digest.
6. Six extra scanner checks (three text fields, three held-out family kinds).
7. Two mocked trainer-main runs checking seed order and metadata defaults.

All fixtures and outputs were temporary CPU data. No full golden suite,
parent mock suite, GPU suite, launch, or remote action was performed. These
results are bounded to the commit and lineage hashes above; concurrent
working-tree changes are not implicitly reviewed or approved.

## Advisory disposition for the first launch

No seed-forwarding/default/clone-handling bug was found that requires changing
the fresh, non-clone seeded path before its first GPU use. Fix F1 for any
resumed childhood life; preserve genuinely fresh directories for the seed
comparison; and do not turn the lineage API’s declared eligibility into a
claim of verified clean ancestry without the separate evidence in F2.
The builder retains scheduling authority. This review is not a launch pause,
not scientific-claim ratification, and not approval of unrelated patches.
