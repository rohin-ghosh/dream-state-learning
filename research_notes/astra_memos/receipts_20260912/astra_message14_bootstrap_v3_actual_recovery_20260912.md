# Message 14 — actual bootstrap-v3 recovery, 2026-09-12

Read-only recovery began **16:58:05 UTC**; remote reads completed 17:00:46; evidence validation completed 17:02:52. No GPU/model/tokenizer calls, inference, launch, kill, lease, remote writes, source changes, or training-data rewriting. Other owners' pretests and Main's pending native panel were untouched.

## Findings that replace the earlier uncertainty
- **Canonical corpus found on node1:** `~/v6_out/bootstrap_v3/`. No `~/v6_out/bootstrap*` directory found on node2 in the bounded inventory.
- **Actual counts and order verified:** 470 sidecar rows = 470 training q/a pairs, exactly equal in order and content; 206 metaflow, 94 opening, 70 contrast, 65 review, 35 full. Counts match `corpus_meta.json`.
- **Training is not merely queued:** node1 has `TRAINED`, `adapter/DONE`, `adapter/train_meta.json`, and an 80,792,096-byte adapter weight file. Training metadata records 470 texts, 940 steps, 519,686 tokens, rank 8, 2 epochs, lr 3e-5, final loss 0.6754022836685181. Weight bytes were NOT fetched or loaded; this establishes recorded completion/artifact existence, not adapter validity or scientific usefulness.
- Metadata names author **`Qwen/Qwen2.5-32B-Instruct-AWQ`**, seed 3, 500 selected episodes, and sole source **`~/v6_out/src_classrooms`**, not enumerated `lineage3_*` roots. Every row has only `q,a,path,src,eid`, with `src=src_classrooms`.
- **Positive raw-source recovery:** both nodes' `src_classrooms/ledger.jsonl` are identical, and node2's sorted original classroom ledgers concatenate to those exact bytes. This is stronger than a target-blind label, but does not authenticate every generated answer or all exposure history.

## Preserved files and query exits
Evidence root `R` = `/tmp/astra_message14_bootstrap_v3_receipts/recovery_20260912T165805Z/`.
- Disambiguated originals: `R/node1/files/` and `R/node2/files/`, retaining relative remote paths. All writes used exclusive creation; no prior recovery file was overwritten.
- Recovered **141 files, 3,209,276 original bytes**: node1 corpus/sidecar/metadata/completion markers, small producer output and current producer source; node2 round manifests, parent-mode records, admissions, and seven parent ledgers/playbooks.
- Node1 producer evidence includes `files/v6_out/bootstrap_v3.out` (974 bytes), `files/train_bootstraps.sh`, and `files/dream-state/organism_v6/bootstrap_corpus.py`. Current producer source matches the repository file; this is NOT proof that identical bytes generated the historic corpus.
- `R/node1/01_fetch_v3.manifest.json` and `R/node2/04_source_metadata.manifest.json` preserve file sizes, SHA256, stable-stat checks and missing-file lists. All transferred hashes were independently rechecked.
- **Eight remote queries, eight exit 0, zero stderr bytes.** Exact query scripts plus timestamped `*.exit.json`, `*.stdout`, `*.stderr` are under `R/node{1,2}/queries/`; script hashes are in exit receipts. No full runtime/training logs or weights were copied.
- The 90 MB staging ledger and original source ledgers were streamed/read remotely, not fetched; compact hash/line-match receipts are `R/node{1,2}/queries/03_match.stdout`.

## Exact original source reconstruction
- Each staging file: **90,188,126 bytes**, **89,991 JSON rows**: 45,141 act; 16,223 thought; 27,379 note; 1,248 parent.
- Staging SHA256 on BOTH nodes: `5e9ea6ae679f73045bdb8670c4dbab80154fca4459480d0e570199a4c8168bae`.
- Node2 has **13 source lineages × 3 rounds × 8 classroom files = 312 ledgers**. Sorting lineage directories and their `round_*/ledger_c*.jsonl` paths, then concatenating raw bytes, yields exactly the staging hash. Matching staging line offsets/raw-row hashes were independently validated.
- Exact run roots beneath node2 `~/v6_out/`: `lineage3_self_s{8000,8001,8002,8003,8005,9000}_e40` and `lineage3_server_s{8000,8001,8002,8003,8004,8005,9000}_e40` (brace notation lists the actual seed set).
- **All 312 ledger SHA256 values match the saved 39 round `manifest.json` files.** See `R/source_manifest_binding_audit.json`. These manifests declare `gym_exposure="none (rule-game only)"`; declaration is not independent exposure authentication.
- Node1's seven local `lineage3_*` directories are NOT the staging source concatenation. Same run basenames on different nodes must not be merged. The byte-identical staging copy points to node2's complete source set, not to node1's partial/different runs.
- The recovered staging has exactly those source bytes; no extra nursery rows are present in that file. A staging-construction command/source receipt was not located in the checked small-script locations.

## Per-row recoverable evidence versus unresolved dependencies
Full 470-row table: `R/row_provenance_audit.csv`; detailed candidate bindings: `R/row_provenance_audit.jsonl`; aggregates: `R/audit_summary.json`.
| Property | Actual result | Interpretation |
|---|---:|---|
| q + eid uniquely matches an original thought record | 266 rows | Exact source file, line, tick, raw-row/file hash recoverable |
| q + eid matches 13 original thought records | 204 rows | All candidates retained; selected source instance unresolved |
| No matching primary prompt | 0 rows | Every q is recoverable in the original source pool |
| Unique matches from self/server sources | 113 / 153 | Original teaching is not uniformly stronger-model parenting |
| Unique server cases with matching parent-intervention receipt | 153 / 153 | Parent turn located by admission-pair evidence IDs; model label is 14B |
| Unique cases with admission true / false | 196 / 70 | Do NOT silently filter away the 70 false-admission sources |
| CONTRAST rows with recorded second-source dependency | 0 / 70 | All 70 secondary dependencies remain unresolved |
| CONTRAST answers containing recognizable episode-ID hints | 17 / 70 | Text hints retained, not promoted to producer dependency receipts |

The JSONL records q/a hashes, form/eid, staging lines, every node2 candidate, source ledger hash, manifest match, admission index/flag, and parent-intervention line/timestamp when available. `UNIQUE_PRIMARY_PROMPT_MATCH` certifies the q match only—not every proposition in generated a.
All 470 retain `rendering_provenance_status=UNRESOLVED` for missing author-request/revision/support binding and unauthenticated complete exposure history. This does NOT discard the positive source recovery. The 204 ambiguous q matches and 70 unrecorded CONTRAST dependencies have additional explicit reasons.

## What remains missing, without inventing ancestry
- The corpus sidecar has no source-instance counter, original ledger path/hash, author request ID/revision, or second CONTRAST source. The current compiler drops these bindings (`organism_v6/bootstrap_corpus.py:175,177,199,226`); seed 3 cannot substitute for the missing per-rendering receipt.
- Thirty-nine `parent_mode.json` records exist: 18 self/null-model and 21 server/`Qwen/Qwen2.5-14B-Instruct`. Root parent ledgers expose intervention evidence IDs, but do not bind producer code/model revisions or historic playbook versions to every turn.
- The 39 manifests are real hash-binding evidence; no nonexistent stronger manifest was fabricated. Missing `lineage_manifest.json`/`snapshot.json` filenames are recorded as missing, not confused with the existing `manifest.json` files.
- A bounded literal screen of BOTH q and a found **zero rows** matching CompilerGym/compiler_gym, benchmark://, cbench/mibench, LLVM, or selected LLVM pass names. This is a negative lexical diagnostic, NOT proof of no hidden-rule leakage, author/parent task exposure, selection contamination, or semantic support.
- Actual node1 v3 directory lacks the checked `DEV_UNVERIFIED_PROVENANCE` and `QUARANTINE_TASK_EXPOSED` marker files. Missing markers do NOT lift the repository's unresolved-provenance ruling.
- Baseline record remains `research_loop/coordination/20260910_bootstrap_v3_unverified_provenance_quarantine.md`; operational STOP lifting did not authenticate these missing dependencies. No clean-child or deployment-gym non-exposure claim is made here.

## Integrity and bounded next step
- Corpus SHA256: `3dc1d2ffc2806b3a7cbfac50ded563f9ca4b0c020d975e5fb7afdd8f8b8d92ff`.
- Sidecar SHA256: `87db51be270d5f2c12b0789534fd1477049324a8dcafe3bc216d2ffb536d3492`.
- Metadata SHA256: `d9736f39c0ba6513ef464765d9f7b97e62161f7b09fce1127123785e13276cab`.
- `R/validation_receipt.json` records ordered source offsets/raw-row hashes, all transferred hashes, stable read stats, table size and successful query exits.
- Next recovery, only if separately requested: locate original author request/selection records and staging producer receipt; join those to the already preserved table. Without them, retain the 204 source-instance ambiguities and 70 missing CONTRAST dependencies. No new corpus, training-data repair, formal C11 guard, model run or launch follows from this report.
