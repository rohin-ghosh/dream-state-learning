# Node1 → node2 preservation plan — September 12, 2026

**PLAN ONLY; no remote checks, backup, restore, or transfer executed.** The procedure below is non-destructive and uses existing wrappers. It is **not yet sufficient to certify complete preservation**: Main must supply the live, recursively enumerated file selection, consistency boundaries and capacity approval identified below. Only this document was written. **Backup and verification deadline: September 13, 2026, 23:14 UTC. Node1 expiry: September 14, 2026, 23:14 UTC.** The documented September 14, 17:14 UTC finish cutoff is neither of those deadlines.

## 1. Reuse and coverage, without another inventory

Authority is the supplied `research_notes/astra_memos/receipts_20260912/astra_lease_evidence_inventory_20260912.md`, especially §§2–5. Its observations span September12 21:35–21:40 UTC, not a consistent present snapshot. Its `.py` only performs bounded shallow metadata reads; it does **not** generate full preservation manifests or verify weights. I read it but did not run it.

**Select all required evidence beneath node1 `~/v6_out`, plus the two executed source snapshots**, rather than trusting the old adapter-only mirror. Partition this selection into disjoint manifest-defined batches, prioritizing:

| Priority | Source coverage to put in the new version | Reason / disposition |
|---|---|---|
| 1 | All eleven inventory-listed missing scopes under `~/v6_out`: `ENV`, `analysis`, both `astra_B0_slot_{A,B}_seed9100_20260912_attempt2` roots, `brief_baseline`, `disjoint_panel`, `noise`, `pretest_write_ab_AC`, `src_classrooms`, `src_seed3`, `xnode` | Copy complete selected contents, not just weights. The brace notation expands to the two exact inventory names; it is not a new source path. Node2 native same-name trees are not substitutes. |
| 2 | Entire `~/v6_out/pretest_write_ab/` and the AC scope already in priority1 | Covers seven missing ordinary lives, omitted variants including `R2_B_seed1/adapters/C_tmem/`, and corpora/markers/probes/group metadata in otherwise mirrored lives. Deduplicate by exact relative path, not basename. |
| 3 | Remaining required `~/v6_out` root files and life trees, including `RP_B_seed402`, `R3_B_seed500`, `R3_B_seed501`, `R4_B_seed605`, `R4_B_seed606` | Preserve ledgers, all required checkpoint ancestors/intermediates/finals, configs, probe/raw outputs, gate/selection/parent receipts, rejected/partial writes and original markers. Final-weight samples do not cover these trees. |
| 4 | `~/astra_sources/0babc3ccbe1f2378a61dd0dac6f18f7371b82176/` and `~/astra_sources/125ba29df6e1060e4e412742459dd75217193d2e/` | Preserve actual executed source/configuration bytes and recorded dirty-state evidence without running Git. Screen credentials before export; do not copy home, model caches or connection configuration wholesale. |

The six sampled missing weight filenames can be resolved exactly from inventory §2, but **the full descendant paths/bytes of the eleven scopes and required runtime dependencies are absent from that shallow inventory**. Main must enumerate them; this plan invents none. Preserve B0-A's observed absent checkpoint and the old missing DONE markers as absences in the coverage ledger—not as files to create. No successful/complete-adapter label follows from directory presence.

Existing node2 `~/mirror/node1_adapters_2026-09-12`, dated receipt parts, `~/node1_mirror`, and native `~/v6_out` remain untouched. Reusing old coverage instead of copying a selected file requires matching exact source-relative identity and payload SHA256, not a checksum-sidecar hash, mtime, or historical count. The actual historical receipt payload paths use `.tgz.part_aa`; do not assume an unsuffixed node2 archive exists.

## 2. Main's required live checks and consistent cut

Before packing, Main records:

1. Available bytes, inodes, quotas/reservations and competing growth on node1 staging, node2 mirror, and any relay filesystem; tool availability and wrapper access with existing host-key verification. No new hostname, credential inspection or key enrollment is specified here.
2. A recursive **metadata-only** census of the selected roots: relative path, type, size, allocated blocks, mtime_ns, link count and symlink disposition; all eleven required scopes explicitly covered. Record failures/timeouts, newly discovered roots/dependencies and exclusions. Reject escaping/special files; never follow an unreviewed symlink. Credential screening includes source/runtime bundles and logs, not just filename suffixes. Do not silently exclude scientifically required bytes: list unresolved dependencies.
3. Owner-confirmed terminal/checkpoint boundaries. No kills or queue changes. A live tree plus pre/post hashes is not an atomic multi-file checkpoint. Preserve a stable checkpoint with its contemporaneous metadata; never combine old weights with a newer DONE. For active logs, capture an owner-approved immutable byte-prefix snapshot with source size/cutoff/hash, or mark pending for the next version. Record every changed/unreadable file as unresolved, not quietly omitted.
4. Fresh source and per-file SHA256 manifests for approved stable data; archive space and actual transfer/hash throughput on one small complete batch before scheduling the remainder. Known wrappers support a VM relay; node1→node2 direct authentication is **unverified**, so no direct host command is guessed.

Example **Main-only** read commands, from `/data/home/rohing/dream-state`; do not interpret a timeout as a complete census:

```bash
timeout 90 bash gpu/a40_ssh.sh -T -o StrictHostKeyChecking=yes -o UpdateHostKeys=no \
  'timeout 70 bash -c '\''df -B1 "$HOME" "$HOME/v6_out" "$HOME/archive"; df -i "$HOME"; command -v tar sha256sum python3; du -sx -B1 "$HOME/v6_out" "$HOME/astra_sources/0babc3ccbe1f2378a61dd0dac6f18f7371b82176" "$HOME/astra_sources/125ba29df6e1060e4e412742459dd75217193d2e"'\'''
timeout 60 bash gpu/ovx_ssh.sh -T -o StrictHostKeyChecking=yes -o UpdateHostKeys=no \
  'df -B1 "$HOME/mirror" "$HOME/v6_out"; df -i "$HOME/mirror"; command -v tar sha256sum python3'
```

Also measure apparent sizes and sparse/hardlink expansion; `du` alone is not the transport-byte forecast. Existing inventory helper may refresh shallow discrepancies, but does not replace checks2–3 or authorize a copy of a mutable checkpoint.

## 3. Versioned executable transport pattern

These are **commands for Main to run later**, not commands executed by this sidecar. All new paths below are explicitly proposed fresh namespaces under already evidenced parents. Commands must run under Main's normal permissions/approvals. Choose one operator per version. Each failed receiving attempt gets a **new version**, retaining partials and failure receipts; never rerun SCP/redirection into an existing payload.

```bash
set -euo pipefail
umask 077
# A small local receipt directory, not a payload cache; confirm this parent's capacity/access.
relay=$(mktemp -d /data/home/rohing/astra_node1_preserve_20260912.XXXXXXXX)
version=${relay##*/}
case "$version" in *[!A-Za-z0-9._-]*) exit 2;; esac
s1() { timeout 1800 bash gpu/a40_ssh.sh -T -o StrictHostKeyChecking=yes -o UpdateHostKeys=no "$@"; }
s2() { timeout 1800 bash gpu/ovx_ssh.sh -T -o StrictHostKeyChecking=yes -o UpdateHostKeys=no "$@"; }
s1 "umask 077; mkdir -- \"\$HOME/archive/$version\""
s2 "umask 077; mkdir -- \"\$HOME/mirror/$version\""
```

**Preparation interface not supplied by the old inventory helper:** Main produces, in the new node1 staging directory, disjoint `batch-NNNN.files.nul` files and bound metadata manifests. Every listed entry is a regular file, relative to node1 HOME, beneath the approved roots, with no symlink ancestor, traversal, secret or future-generated dependency. Enumerate empty directories separately if required for reconstruction. Include complete checkpoint bundles in a batch where practical. Prefer ≤2GiB apparent payload batches; a larger indivisible file gets its own measured batch, not truncation. A file cannot appear in two batches unnoticed. The full coverage ledger must account for every required source entry and every deliberate exception.

Packing template for **one approved stable batch**; `batch-0001` is a new batch label, not an existing artifact claim:

```bash
part=batch-0001
s1 "bash -s -- '$version' '$part'" <<'NODE1'
set -euo pipefail
set -o noclobber
umask 077
stage="$HOME/archive/$1"; part=$2
cd "$HOME"
test -s "$stage/$part.files.nul"
while IFS= read -r -d '' path; do sha256sum -- "$path"; done \
  < "$stage/$part.files.nul" > "$stage/$part.files.sha256"
# Fresh destination; preserve nonzero exit and source-change warnings as failures.
tar --create --sparse --hard-dereference --format=pax --file=- \
  --no-recursion --null --verbatim-files-from --files-from="$stage/$part.files.nul" \
  > "$stage/$part.tar"
sha256sum --check -- "$stage/$part.files.sha256"
cd "$stage"
sha256sum -- "$part.tar" "$part.files.nul" "$part.files.sha256" > "$part.bundle.sha256"
NODE1
```

The tar is uncompressed: avoid assuming weight compression or adding compression CPU contention. `--hard-dereference` stores each selected hardlinked file's bytes; record that restored inode sharing is not preserved and budget apparent expansion. Do **not** use symlink dereference. A successful command still needs the recorded before/after file-set/stat comparison and stable-cut approval; check failures are not waiver signals.

Stream immutable single files between known wrappers without staging payloads on this VM:

```bash
# Repeat for the four files, then separately transfer the approved metadata/cut ledger.
for suffix in bundle.sha256 files.nul files.sha256 tar; do
  name="$part.$suffix"
  set +e
  s1 "exec cat -- \"\$HOME/archive/$version/$name\"" | \
    s2 "umask 077; set -C; cat > \"\$HOME/mirror/$version/$name\""
  status=("${PIPESTATUS[@]}")
  set -e
  printf '%s source_rc=%s destination_rc=%s\n' "$name" "${status[0]}" "${status[1]}"
  test "${status[0]}" -eq 0 && test "${status[1]}" -eq 0 || exit 1
done
s2 "cd \"\$HOME/mirror/$version\" && sha256sum --check -- '$part.bundle.sha256'"
```

Retain command stderr, both pipeline statuses and timestamps in Main's versioned receipt log. Compare the **actual received** bundle-manifest hash to node1's independently read manifest hash; preserve that hash in the local receipt directory too. This is corruption/custody checking through configured SSH, not protection against a malicious source.

If streaming is unsuitable, `gpu/a40_scp.sh 'NODE:archive/<VERSION>/<FILE>' <fresh-local-directory>/` then `gpu/ovx_scp.sh <local-file> 'NODE:mirror/<VERSION>/'` are the existing single-file alternative: substitute only the generated version/manifest-listed filename, precheck absence and retain failures. They require measured local payload capacity. Never use a guessed address or recursive Mac openrsync tree transfer. No cleanup is part of either route.

## 4. Verify every batch, then sample restore

After archive SHA256 verification, Main's CPU verifier must open tar members **without extraction**, require unique exact approved relative paths and regular-file types only, reject traversal/absolute paths/symlinks/hardlinks/specials, and stream SHA256 of **every member's content** against the source file manifest. Compare member sizes, selected path set, counts and summed bytes; validate recorded metadata against the source census. Run this through node2's existing SSH wrapper with an explicit timeout and retain its result. **No such full verifier exists in the inspected shallow inventory helper**; Main must provide/reuse a reviewed archive verifier rather than treating `tar -tf` or sidecar equality as sufficient. No credential-bearing source bytes may reach transport awaiting later screening.

Then restore a verified small complete batch into a new node2 directory; this is a rehearsal, never a resume into native `~/v6_out`:

```bash
# Only AFTER regular-member/path/content validation above succeeds.
s2 "bash -s -- '$version' '$part'" <<'NODE2'
set -euo pipefail
umask 077
base="$HOME/mirror/$1"; part=$2
mkdir -- "$base/restore-$part"
tar --extract --file="$base/$part.tar" --directory="$base/restore-$part" \
  --keep-old-files --no-same-owner --no-same-permissions
cd "$base/restore-$part"
sha256sum --check -- "$base/$part.files.sha256"
NODE2
```

Choose the sample to include a newly missing checkpoint **bundle** (weights/config/train/provenance/actual markers) and associated ledger/corpus/probe metadata; also sample an executed-source file and a preserved partial/absent-marker case, using additional fresh restore directories if necessary. Check JSON/JSONL/schema readability and checkpoint header/size consistency with a CPU parser; do not import a model, synthesize DONE or launch inference. This proves byte restoration for the sample, not GPU reload or resumability. Full member-hash verification covers every batch; sampling never substitutes for it.

Completion receipt binds version, owner/cut times, all source/destination manifests, bundle hashes, transfer/verification/restore statuses, received bytes, and unresolved/excluded paths. Mark **selected-cut verified** only if every required entry is resolved; never mark the whole node complete based on eleven root names. No source, old mirror, partial, or rehearsal directory is deleted or overwritten.

## 5. Capacity, scheduling and remaining uncertainty

Use the inventory's **1,395,912,350-byte / 47-file measured missing-sample lower bound**, not a new estimate or complete delta. Its 4,203,873,758-byte shallow non-weight census overlaps that bound; do not add them. Historical 76,194,875,875-byte transfer size is another reference, not today's payload. No fresh measurements were made here.

At the supplied cut, node2 had **652,925,091,840 bytes** available (mirror and native v6_out share one volume); VM `/data`131,790,536,704 and `/tmp`8,869,920,768 bytes. These are not reservations. Node1's2,748,110,340,096 free bytes are staging only, not surviving custody. For archive bytes A, retained sample-restore size S, retained failed-attempt bytes F, expected concurrent growth G and Main's explicit safety reserve R, require node2 free capacity **≥ A+S+F+G+R**. Node1 needs all retained source-stage archives plus snapshot overhead; streaming keeps local payload staging near zero. A full restore instead requires its full apparent restored size, not just S. If all SCP relay payloads are retained locally, local capacity must cover A; bounded chunks alone do not solve cumulative storage when nothing is deleted.

At a hypothetical25MB/s, the measured lower bound takes0.93min payload-only; historic76.195GB takes50.80min. Neither predicts a full backup. Main must measure packing, source hashing, two-hop streaming, destination member hashing and sample restoration; throughput is limited by the slower hop/IO and competing work. Reserve retry/verification time **before September13 23:14 UTC**, not until lease expiry. Start a small missing-scope batch first, then scale using observed costs and current free space.

Maintain later immutable delta versions for writes after the first cut. Reconcile at the September14 17:14 UTC finish cutoff and verify the final off-node delta before September14 23:14 UTC; do not silently claim the first backup covers later activity. Node2 is itself temporary: arrange and verify an independent durable copy before its documented September20 08:43 UTC backup deadline / September21 08:43 UTC expiry. No durable destination path/capacity is established by these sources; Main must supply it.

## 6. Non-negotiable exclusions and source bindings

**Never invoke `gpu/migrate_node1_to_node2.sh` for this plan:** it kills processes, packs mutable trees, extracts over node2 native v6_out and checks only counts/markers. Reuse only its single-file-relay concept. Never invoke `gpu/v2node_sync.sh`: its `rsync --delete` is a source sync, not evidence preservation. No delete/remove-source/in-place overwrite, legacy cleanup, bootstrap, restart, GPU query, lease extension or node3 action is included. Other agents' files remain untouched.

Inspected inventory SHA256 `fad0815da36086cd219e10be08467c8d010f7c04fd0a5c943e24c498999078f2`; helper SHA256 `5b9f192e52e9218bd104a43aaa045074cb6bb776b102dc50747680f537531bbd`. Additional local sources: `gpu/migrate_node1_to_node2.sh:1`, `gpu/a40_ssh.sh:1`, `gpu/ovx_ssh.sh:1`, `gpu/a40_scp.sh:1`, `gpu/ovx_scp.sh:1`, `gpu/v2node_sync.sh:1`, and setup/runbook notes. No `hosts.env` or credential contents read. Exact missing descendant lists, live consistency/size, quotas, transfer speed and durable onward custody remain **Main live-check requirements**, not guessed facts. **EDITSTOP.**
