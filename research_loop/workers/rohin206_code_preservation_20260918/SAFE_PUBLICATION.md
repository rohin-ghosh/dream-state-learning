# Finished snapshot publication — 2026-09-18

This publication uses only the worker snapshot completed at
2026-09-18T06:09:35.135485+00:00. It does not rerun `preserve_latest.py`,
capture fresh C2 content, read learner processes, or launch any computation
on a GPU. The original workspace and raw evidence remain unchanged.

## Non-material audit repair

The first publication audit timed out without a completion receipt. The
repair treats changed or missing derivatives as manifest-only omissions,
never recaptures their sources, and never admits orphan files by recursive
staging. Duplicate-content caching and a bounded email matcher avoid
repeated expensive scans. Atomic derivative/manifest writes reduce the
interruption window; an interrupted mismatch still fails closed.

Private, sealed, final, reference-panel, credential, and dataset paths are
excluded conservatively. Ambiguous judge payloads are not presumed public.
Structured/nested private payloads, embedded panels, key material, and long
encoded blobs receive additional screening. Redaction covers known hosts,
host fields, addresses, URL authorities, contact addresses and credentials.
No sensitive match values are printed. Public aggregate labels alone do not
authorize publication of caption rows or reference material.

## Receipts and scope

Final content screening passed at 2026-09-18T06:56:44.157248+00:00:
132,773 admitted derivatives, 1,975,624,247 derivative bytes, and 115,070
unique content blobs (1,896,804,673 bytes). Git can deduplicate 17,703
identical-content paths without removing provenance paths. Of the initial
134,625 text candidates, 1,694 were withheld by the first audit and another
158 by the independent screen: 1,852 additional publication omissions in all.
These are exclusions, not a claim that every withheld file is private or
that local files were deleted. Original capture-time omissions remain
separately recorded. All 26 CPU regression tests pass.

- `PRESERVATION_RECEIPT.json` preserves capture-time totals and source hashes.
  Those totals are **not** final public-file counts.
- Each worker's `PRESERVATION_MANIFEST_20260918.jsonl` retains original hashes,
  published derivative hashes where admitted, and explicit omission reasons.
- `PUBLICATION_ALLOWLIST.json` enumerates the only admitted derivative paths.
- `PUBLICATION_CONTENT_AUDIT.json` gives final derivative counts, bytes,
  unique-content counts, additional omissions and publisher-script hashes.
- `PUBLICATION_SUMMARY.json` distinguishes original capture omissions,
  subsequent publication exclusions, and the legacy audit count field.
- Publisher scripts are deliberately included; their inclusion does not
  authorize rerunning the snapshot or accessing omitted inputs.
- `COORDINATION_SNAPSHOT_DERIVED.md` retains the exact audited coordination
  derivative as an immutable worker artifact. The live top-level coordination
  file is not changed by this bulk publication; its current contents and
  concurrent Main updates are not falsely covered by the snapshot hash.

Tests use constructed fixtures, not real private inputs:

```sh
python3 -B research_loop/workers/rohin206_code_preservation_20260918/test_audit_publication.py -q
```

Only positive hash-verified derivatives, manifests, audit receipts, this
report, and deliberately audited publisher scripts may be staged. Raw roots,
archives, private panels, binaries, and omitted/orphan derivatives are not
included. Git deduplicates identical file blobs without deleting provenance
paths. Pattern/structure screening is conservative but is not proof against
undisclosed encodings or mislabeled content.

Remote publication uses a normal fetch/rebase/push from the isolated detached
worktree, retaining concurrent origin changes; no force push or root reset.
The final response provides the actual commit and remote-verification hashes.
