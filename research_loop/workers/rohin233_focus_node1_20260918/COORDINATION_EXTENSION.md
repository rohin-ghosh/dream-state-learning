
## [Builder] 2026-09-18 11:57 UTC — R233 node1 scope extends to exact repo_c3

User explicitly added repo_c3. gpu/talk.sh:17 defines the verified prefix and
:45 maps repo_c3 to logical node1/a100, r203_repo_evidence_c3/life. Actual active
control is r203_repo_evidence_c3_r213/control on GPU3, already normally exited
at 08:19:48 UTC, completed sleep81. Final cycle's ACT7792 -> execution7795 is
PROCESS_FAILED; LEARN7802 proposes different code but is not a checked success.
No source-bound movement in that bounded final cycle justifies retaining it.
No alias substitution, signal or restart. Apply the same independent all-records,
all-checkpoints/source/control archive and CPU optimizer/RNG validation. Nine
focused tests pass; 21 historical CPU-parent checks now find no live process.
The initial four full journals have passed. Their receipts are preserved while
the fifth journal is validated once by the existing StreamJournal constructor
plus unchanged-cache verification (avoids redundant second full replay).
