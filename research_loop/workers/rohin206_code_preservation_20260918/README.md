# Caption code preservation — bounded sidecar, not committed

Snapshot cut: September18 2026 04:21:53.988563 UTC. All source bytes were
unchanged at final re-verification. Main owns commit/push from the fresh detached
worktree; this operator did not commit, push, fetch, change branches/index, edit
source owners' files, or publish anything to a learner.

## Exact allowlist

- 11 `gpu/ny_caption*.py` implementation files.
- 11 `tests/test_ny_caption*.py` test files.
- 103 R177 Python files and40 Markdown source/notes/reference files.
- 9 explicitly selected public aggregate/provenance reports; no model configs.
- Total174 files,2,097,447 bytes. No matching R177 shell files were present.

`ALLOWLIST.txt` contains exact destination paths. `snapshot/` contains independent
regular copies at those paths; `CODE_ONLY.tar` contains precisely those174 files,
with no symlinks, hardlinks, extra members, recursive directory staging, or data
dependencies. `MANIFEST.json` binds per-file hashes/bytes/modes and the observed
working-tree HEAD; that HEAD is provenance, not Main's proposed merge/commit base.

Manifest SHA256:
`5408d6018c05d62e02a8eb6467ca272a950e08d3b8fde2a6b43c52136b0e0405`

Archive SHA256:
`de734cb8894a16e60a592d1f183dcb972e947a4cb81ceeb118f2a965a28a4fa6`

## Scan and exclusions

`SECRET_SCAN.json`:175 candidate files examined;174 allowlisted. No unresolved
credential or private-payload finding. Three byte-bound findings were reviewed:
two schema-key allowlists and one deliberately invalid synthetic URL in a test.
`REVIEW_DECISIONS.json` gives only reasons/hashes/locations, never raw matches.
The extra provider model metadata JSON is withheld as unnecessary, preserving
its existing public source receipt reference instead. `VALIDATION.json` confirms
eight synthetic scanner-rule checks and all174 snapshot-file hashes.

Excluded before traversal: private/, portable/, data/, payloads, rows, weights,
credentials/secrets, private SSH, .env/non-allowlisted files, modelcfg/reference
panels, sealed/final directories, caches, virtualenvs and site-packages. Public
notes/reports may contain overt path/SHA references: none was followed into its
private payload. No private dataset was opened, candidate program executed,
actual caption/reference panel copied, or fixture/credential content logged.
The scan is static pattern/structure review, not a guarantee against arbitrary
secret encodings or undisclosed provenance. Original failures and data remain
untouched at their owners' paths.

## Main import boundary

Verify `ARTIFACT_SHA256.json` and every manifest entry, then import only the
explicit allowlist into Main's separate fresh detached worktree. Never stage
the entire untracked R177 tree or the sidecar directory recursively. Do not
bring in referenced private/evaluation data, portable/model artifacts, payloads,
credentials, this workspace's git index, or runtime/learner state. No code in
this snapshot has been run as part of preservation; no new science/test result
or judge-quality claim is created. All commit and push actions remain Main's.
