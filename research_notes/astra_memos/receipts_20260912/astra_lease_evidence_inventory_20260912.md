# Node1 expiry evidence inventory and Main-only backup proposal

**2026-09-12 — EDITSTOP. Planning only; no backup was executed.** Current
completeness is **NOT VERIFIED**. The named node2 adapter mirror lacks whole
source scopes and selected newer weights. Historical receipts provide a useful
baseline, not permission to discard node1. Main remains sole operational
writer/launcher; node3 and its current GPU2 work were not contacted or touched.

## 1. Time, scope, and safety

Native observations: **September 12, 2026, 21:35:01–21:40:46 UTC**. This is a
changing, non-atomic metadata snapshot. Lease dates below are user-supplied and
runbook-corroborated, not freshly verified against a leasing control plane.

| Node | Required backup deadline | Documented finish cutoff | Lease expiry |
|---|---|---|---|
| Node1 | **2026-09-13 23:14 UTC** | 2026-09-14 17:14 UTC | **2026-09-14 23:14 UTC** |
| Node2 | 2026-09-20 08:43 UTC, documented 24h buffer | 2026-09-21 02:43 UTC | **2026-09-21 08:43 UTC** |

At the 21:39:10 UTC forecast receipt, node1 had **25.58 hours to tomorrow's
backup deadline**, 43.58 hours to finish cutoff, and 49.58 hours to expiry.
Do not confuse the September 13 backup deadline with September 14 lease
expiry. A later CLEAN/reimaged lease is not continuity of this filesystem.

Only two owned files were written: this report and optional read-only helper
`/tmp/astra_lease_evidence_inventory_20260912.py`. All remote commands were
bounded metadata reads through `gpu/a40_ssh.sh` and `gpu/ovx_ssh.sh`, with
`StrictHostKeyChecking=yes`, `UpdateHostKeys=no`, and timeouts. No recursive
weight-tree inventory, weight-content hashing, archive-payload hashing,
models, GPU queries, process/queue inspection, launches, kills, transfers,
remote writes, repository edits, or Git writes. No `hosts.env` or credential
contents were inspected or printed; established wrappers internally load
their existing connection configuration. No host addresses are recorded here.

## 2. Current path coverage

The exact shallow recount is **67 node1 `~/v6_out` directories versus 56 node2
`~/mirror/node1_adapters_2026-09-12` directories**, with no mirror-only names.
The earlier quick reference to 68 source directories was not the exact
recount: **68 is node2's separate native `~/v6_out` directory count**. The
67/56 comparison is confirmed by two helper receipts. [N2-A, N12-D1/D2]

### Eleven names absent from the named node1 adapter mirror

All source paths below are relative to **node1 `~/v6_out/`**:

```text
ENV/
analysis/
astra_B0_slot_A_seed9100_20260912_attempt2/
astra_B0_slot_B_seed9100_20260912_attempt2/
brief_baseline/
disjoint_panel/
noise/
pretest_write_ab_AC/
src_classrooms/
src_seed3/
xnode/
```

This is absence from the **named adapter mirror**, not proof of absence from
every archive, laptop, or other destination. Seven names also exist in node2's
native `~/v6_out` (`ENV`, `analysis`, `brief_baseline`, `disjoint_panel`,
`pretest_write_ab_AC`, `src_classrooms`, `xnode`); **basename equality is not
node1 provenance or byte equality**. Never merge or substitute those native
node2 experiments as backup evidence without exact lineage/hash binding.

### Nested pretest coverage is materially incomplete

| Relative source path set | Source directory coverage | Named mirror coverage |
|---|---:|---:|
| `pretest_write_ab/<life>/` | 11 lives | 4 lives |
| Its immediate `adapters/<variant>/` directories | 63 | 27 |
| `pretest_write_ab_AC/<life>/` | 2 lives | 0 |
| Its immediate adapter-variant directories | 8 | 0 |

The four mirrored ordinary pretest lives are `R2_B_seed0`, `R2_B_seed1`,
`R2_B_seed5`, `R2_B_seed6`. Missing ordinary life scopes are `R3_B_seed500`,
`R3_B_seed501`, `R3_B_seed502`, `R4_B_seed604`, `R4_B_seed605`, `R4_B_seed606`,
and `RP_B_seed402`. Source ordinary `R4_B_seed604/606` have no adapter-variant
directories in that branch; their separate AC scopes exist. The two missing
AC lives are `R4_B_seed604`, `R4_B_seed606`, each with `A`, `A_v3`, `C`,
`C_tmem` directories. Within an otherwise mirrored ordinary life,
`R2_B_seed1/adapters/C_tmem/` is additionally absent. The **44 extra variant
directories are not a count of completed/valid adapters**. [N1-C, N2-B, N12-D2]

Source pretests include `corpora/`, `markers/`, `probes/` and group-level
metadata; the sampled mirrored pretest scopes contain only `adapters/`.
Those excluded materials require receipt/archive coverage, not weight-only
coverage. Group-level files in R2 seed1 and seed5 postdate the old adapter
mirror even where an ancestor directory already exists. [N12-D1/D2]

### Six specifically sampled weight paths missing from that mirror

Only these newer samples and five old final-checkpoint samples were statted;
no payload was opened or hashed. Each listed new weight had a source `DONE`
file present, which is a marker observation, **not** integrity certification.

| Source relative path ending in `adapter_model.safetensors` | Bytes | Source modification, Sep12 UTC |
|---|---:|---|
| `pretest_write_ab/R2_B_seed1/adapters/C_tmem/…` | 6,491,184 | 05:11:10 |
| `pretest_write_ab/R3_B_seed500/adapters/A/…` | 323,014,168 | 08:38:12 |
| `pretest_write_ab/R4_B_seed605/adapters/C/…` | 323,014,168 | 14:07:32 |
| `pretest_write_ab_AC/R4_B_seed604/adapters/A/…` | 323,014,168 | 09:59:45 |
| `pretest_write_ab_AC/R4_B_seed606/adapters/C/…` | 323,014,168 | 18:35:51 |
| `astra_B0_slot_B_seed9100_20260912_attempt2/sleep_0032/adapter/…` | 80,792,096 | 07:31:25 |

The first five filenames are directly inside the displayed adapter-variant
directory. Sum: **1,379,339,952 bytes across six weights**. Add the two new B0
roots' **41 root-level metadata files / 16,572,398 bytes** (A: 19 files,
8,132,212 bytes; B: 22 files, 8,440,186 bytes): a concrete nonoverlapping
**47-file / 1,395,912,350-byte lower bound absent from the named mirror**.
This excludes many nested corpora/probes, configs/markers, and other missing
adapters. Heterogeneous sizes show why “number of adapters × ~78 MB” is not
an adequate forecast. [N1-C, N1-E, local arithmetic receipt]

B0 A's corresponding `sleep_0032/adapter/adapter_model.safetensors` and `DONE`
were absent **on source too**; preserve its records without inventing an
adapter or classifying source absence as a transport loss.

### Additional scope that must survive

- **Whole selected `~/v6_out` evidence**, not just adapter directories: ledgers,
  prompts/corpora, source banks, parent/gate metadata, probe inputs and outputs,
  manifests, partial/error receipts, configs, logs, and markers. The bounded
  depth≤2 census finds **5,845 regular non-weight-suffix files, 4,203,873,758
  apparent bytes**; 150 have mtimes after the Sep11 23:30:41 archive and 43
  after Sep12 03:17. This is a **shallow census**, not full metadata size or
  a verified delta; deeper ongoing pretest outputs are outside that count.
  Root-level files alone: **151 / 22,297,343 bytes**. [N1-B, N12-D1]
- Five sampled old lives (`RP_B_seed402`, `R3_B_seed500/501`, `R4_B_seed605/606`)
  each have 32 sleep directories and an 80,792,096-byte final weight on both
  sides; their source root ledgers are absent from the adapter mirror. Source
  `R4_B_seed605/ledger.jsonl` is **211,605,731 bytes**, modified Sep12 00:24:55,
  after the historical receipts archive. Size/mtime agreement for a sampled
  weight is not content verification. Final `DONE` is absent on **both** sides
  for R3 seed500 and R4 seed606—do not fabricate markers on restore. [N12-D2]
- Node1 immutable source snapshots:
  `~/astra_sources/0babc3ccbe1f2378a61dd0dac6f18f7371b82176/` and
  `~/astra_sources/125ba29df6e1060e4e412742459dd75217193d2e/`.
  Node2's sampled `~/astra_sources` contains a different snapshot name,
  `f2e5b65e9c5dc3f7b7cdf15cb1b97b114ad4994d`; no matching copy was established.
  Repository availability elsewhere is not a verified copy of executed source
  bytes, dirty patches, or runtime configuration. Exclude credential files
  explicitly from any future source/runtime bundle. [N1-A, N12-D1]

## 3. Historical archives and what was actually verified

| Node2 surviving path | Current stat bytes | Payload status |
|---|---:|---|
| `~/mirror/node1_receipts_2026-09-11/v6_out_receipts_2026-09-11.tgz.part_aa` | 273,137,568 | Not freshly hashed/opened |
| `~/mirror/node1_receipts_2026-09-12/v6_out_receipts_2026-09-12.tgz.part_aa` | 313,335,968 | Not freshly hashed/opened |
| `~/node1_mirror/node1_v6_out_receipts_2026-09-10.tar.gz` | 1,034,793,648 | No current payload verification |

These three payloads total **1,621,267,184 stored bytes**; they overlap in time
and do not represent disjoint evidence. Node2's first two destinations contain
the **`.part_aa` files**, not the corresponding unsuffixed `.tgz` files at those
paths. Node1 has both names. Each manifest records the same digest for full
archive and sole part, and their sizes agree; Main must verify payload bytes
before treating the part as a complete archive. [N1-A/C, N2-A/B]

The **2026-09-12-labelled** source archive actually has mtime
**2026-09-11 23:30:41 UTC**; the date label is not a fresh-cut timestamp.
Its small status receipt says `tar_exit=0`, but exit status alone is not a
consistent-snapshot or restore proof. [N1-A, N1-F]

Freshly hashed **202-byte checksum sidecars** match across node1/node2:

| Archive label | SHA256 of the sidecar itself | Payload SHA256 recorded inside, not reverified |
|---|---|---|
| Sep11 | `d5375bb4a3c82bd045198a9d9b660bd112680ead488930bfffdf1b2fbd4b2fc7` | `46551bf332ccf48e8ad3ad57209b229cd8db25fbb01c68c613876f96418d16ba` |
| Sep12 | `395a12378e0b328b7245f8aa3773ba6f5c4aabe294ec17eb9d21a90c2eb4fdc2` | `d7e07590da359c76e57368a5e94121de9b10f75b52815b29fb2e1311d3382804` |

The old source `~/adapter_mirror_list.txt`, mtime Sep12 03:13:52, has
**3,719 lines and 698 exact `adapter_model.safetensors` path entries**;
SHA256 `e3ae65f5ab5618189b2aa1197bc63858d35e372ba2cc9af3d58a1fb23472f5fc`.
The old transfer log ends `MIRROR_RC=0`, **76,194,875,875 bytes**, **2m44s**,
displayed **442.86MB/s**, at 03:16:36. The notebook's “699 adapters” is a
historical report, not the current inventory; its count discrepancy is not
resolved by assuming one adapter lost. Neither list nor log supplies a fresh
per-file content comparison. No adapter-mirror verification manifest was found
in the bounded depth≤3 name search; deeper/unexamined evidence may exist.
[N1-C, N2-B; `research_loop/COORDINATION.md:1238`]

Historical laptop receipts are reported in the handoff/notebook, **not
independently verified here**. Receipt archives exclude model tensors per the
handoff. Neither historic laptop presence nor directory mtime establishes
current node1 backup completeness.

## 4. Surviving storage and transfer forecast

Fresh filesystem counters, not reservations or quotas:

| Location | Available bytes | Meaning |
|---|---:|---|
| Node2 filesystem containing both `~/mirror` and `~/v6_out` | **652,925,091,840** (608.084 GiB) | Survives node1, but node2 expires Sep21; same shared volume, not two capacities |
| This VM `/data` | **131,790,536,704** (122.740 GiB) | Possible bounded staging; persistence/retention policy and competing growth unverified |
| This VM `/tmp` filesystem | **8,869,920,768** (8.261 GiB) | **Cannot stage the historic ~76 GB mirror as one file** |
| Node1 filesystem | 2,748,110,340,096 | Source-side staging headroom only; does not survive node1 expiry |

Node1 total filesystem used is 273,266,548,736 bytes, including OS/cache/other
data—not `v6_out` size and not an archive-size bound for sparse/hardlinked
files. Node2 currently has substantial apparent room, but actual selected
evidence bytes, quotas, growth, sparse expansion and staging overhead remain
unknown. Laptop/off-site free capacity and node2-to-durable onward copies were
not checked. Node3 is not an assumed backup target. [N1-A, N2-A, LOCAL-S]

**No transfer benchmark was run.** Hypothetical payload-only time, using
decimal MB/s and excluding inventory, hashing, packing, verification and
contention:

| Payload reference—not a current complete-backup estimate | 25 MB/s | 100 MB/s | 250 MB/s |
|---|---:|---:|---:|
| Historic 76,194,875,875-byte transfer | 50.80 min | 12.70 min | 5.08 min |
| Current shallow 4,203,873,758-byte census | 2.80 min | 0.70 min | 0.28 min |
| Explicit 1,395,912,350-byte missing-sample lower bound | 0.93 min | 0.23 min | 0.09 min |

Rows are **not additive forecasts**: the shallow census includes B0 metadata
and overlaps older evidence. The old fast rsync is historical, not tomorrow's
assured rate. Full selected payload size, changed-byte count, direct-link
auth/connectivity at copy time, compression ratio, per-file overhead, read/write
bandwidth under ongoing work, hashing throughput, and onward-storage time are
**unknown**. Do not infer readiness from a short payload-only estimate.

## 5. Concrete safe proposal for Main — NOT EXECUTED

1. **Choose and record the scope now.** Include the named missing paths,
   ordinary and AC pretests, complete required checkpoint lineages, all their
   corpora/ledgers/probes/markers, relevant top-level logs, and the two executed
   source snapshots. Preserve partial/error/absent-marker evidence too. Reuse
   validated immutable old backups only with explicit relative-path/hash
   coverage; a 699-adapter claim or matching file size is insufficient.
2. **Create a new versioned destination**, e.g.
   node2 `~/mirror/node1_evidence_20260913T<UTC>/`, and separate unique source
   staging under node1 `~/archive/`. Never overlay node2 native `~/v6_out`,
   mutate the existing dated mirror, or delete either old or source evidence.
   Inventory relative paths, file types, sizes, mtimes and content hashes for
   the **selected** evidence; reject traversal, escaping symlinks, credentials,
   and unexpected files. Do not include entire model caches or home directories
   by default. Preserve base-model identifiers/inventories; separately decide
   whether any irreplaceable local base bytes actually require export.
3. **Respect ongoing writers.** Main chooses a consistent terminal/checkpoint
   boundary, not a kill. For active append-only logs, declare a byte-prefix
   snapshot and cutoff rather than pretending the changing whole file is final.
   Check required files/metadata before and after snapshot/hash; changed files
   remain explicitly pending for a later evidence delta. Do not combine a
   newer marker with older weights or manufacture `DONE`. Do not change queues
   to perform this inventory/backup.
4. **Use safe archive/chunk transport or node-side Linux rsync.** The legacy
   runbook warns about macOS openrsync tree corruption. Prefer already
   configured node1→node2 transport if Main verifies it; otherwise relay
   immutable single-file chunks through existing SCP wrappers. Use fresh
   namespaces, per-chunk hashes, a full ordered archive manifest, captured
   exit codes and enough reserved staging headroom. Avoid a ~76 GB `/tmp`
   relay; `/data` staging or bounded chunks requires Main's capacity check.
   No `--delete`, `--remove-source-files`, in-place live-tree overwrite, job
   stop/restart, or cleanup. Do not extrapolate compression or link speed.
5. **Verify, then certify the scope—not the whole node.** Independently
   enumerate destination members and match exact selected relative path set,
   count, byte total, types and file hashes against the stable source manifest.
   Hash the actual archive/chunk/weight payloads required for that selected
   backup, not just copied `.sha256` text. Check archive integrity and a safe
   temporary restore/manifest reconciliation without launching a model. Record
   source/destination manifests, tool exit statuses, timing, discrepancies,
   excluded paths and unresolved active files. No all-covered receipt while
   any required item remains unresolved.
6. **Meet Sep13 23:14 UTC**, with verification and recovery margin included.
   Record a growth/final-delta plan for evidence written afterward; retain the
   Sep14 17:14 work-finish margin and verify final off-node deltas before
   Sep14 23:14 expiry. An initial backup never silently covers later writes.
   Arrange a durable second destination before node2's own Sep21 expiry (its
   documented backup deadline is Sep20 08:43). Laptop presence must be verified,
   not inherited from the historical receipt claim.

**Immediate narrow decision:** Main should select a versioned node2 evidence
destination and a required-path/cutoff ledger, prioritize the demonstrably
missing scopes, and reserve copy **plus verification** time. This sidecar does
not authorize or execute those writes; it does not duplicate node3 work.

## 6. Legacy scripts reviewed, never run

- `gpu/migrate_node1_to_node2.sh:1`, SHA256
  `dc3f7399dffc2a8edea9a28b01e6d63f0806e8c99003ae87a2f3fe342e31bd4e`:
  unconditionally `pkill -9` on the requested life, then kills orphaned
  `EngineCore` processes; uses hardcoded Mac relay paths, packs a mutable tree,
  extracts over destination `~/v6_out`, and checks counts/markers rather than
  content hashes. **Not a read-only backup tool; do not run it blindly.**
- `gpu/v2node_sync.sh:1`, SHA256
  `4f20bef1aaec4b6792890c2e14ea03bef1331dbf3b80cb61baccf91c115ade6f`:
  working-tree push with `rsync --delete` and artifact exclusions—not evidence
  backup. Also not run.
- Read the SSH/SCP wrappers, `gpu/V2_NODE_SETUP.md`, `gpu/codex/README.md`,
  launch prompt §10/§15, handoffs and prior operational inventory. Old
  housekeeping/launch recommendations do not override this read-only task or
  Main's current sole operational ownership.

## 7. Command receipts and reproducibility

All times below are **2026-09-12 UTC**, all listed remote calls returned 0.
Manual metadata calls used the wrapper envelope:

```text
timeout 75 bash gpu/{a40,ovx}_ssh.sh -o StrictHostKeyChecking=yes \
  -o UpdateHostKeys=no 'timeout 55 bash -s'
```

| Receipt | UTC | Bounded commands / evidence |
|---|---|---|
| N1-A | 21:35:01 | `df -B1 "$HOME" "$HOME/v6_out"`; `stat` named roots; `find` depth1 under v6_out/archive/astra_sources; named home manifest/log file metadata |
| N2-A | 21:35:10 | `df -B1` home/v6_out/mirror; `find` depth≤2 under mirror/node1_mirror; native v6_out depth1 directory count |
| N1-B | 21:35:46 | Full depth1 source directory names; root-file count/byte sum; old list/log metadata; selected old/new run-root file and sleep-directory metadata |
| N1-C | 21:36:15 | `wc -l` and adapter-filename count on existing mirror list; SHA256 list and two checksum sidecars; sidecar text; normalized final old transfer-log lines; pretest depth2 names; two new B0 ledgers/checkpoint stats |
| N2-B | 21:36:16 | SHA256 and text of the corresponding two sidecars; mirror directory count; bounded verification-filename search depth3; pretest depth2 names |
| N12-D1 | 21:37:43.403578–21:37:44.274862 | Optional helper: node1 9,276 and node2 1,423 directory entries inspected; exact top-level set comparison, shallow byte counts, selected stats, manifest hashes |
| N12-D2 | 21:38:05.492996–21:38:06.144439 | Same helper; confirmed 67/56 roots, pretest variant sets and source/mirror final-checkpoint/ledger metadata |
| N1-E | 21:39:10 | `find -maxdepth 2` on five explicitly named new variant directories, filename-filtered weight/config/meta/DONE **stats only**; root-level B0 counts |
| N1-F | 21:40:46 | ≤256-byte read of known archive status receipt: `tar_exit=0`; outer/inner timeouts 45/25s |
| LOCAL-S | 21:36–21:40 window | `df -B1 /tmp /data/home/rohing/dream-state`; UTC deadline arithmetic, transfer scenarios and size sums; script/migration hashes and in-memory syntax compilation |

The first transfer-log tail encountered carriage-return progress text;
N1-C reran it with `tr '\r' '\n' | tail -5` to retain a compact final receipt.
Only the small existing log was read; no payload transfer or benchmark ran.

Optional repeatable inventory helper:

```bash
python3 -B /tmp/astra_lease_evidence_inventory_20260912.py
```

It emits JSON to stdout only, contacts nodes sequentially through their
existing wrappers, caps remote execution at 50s/host, local wrapper at 70s,
subprocess at 75s, entries at 30,000/host and 3,000/directory, checksum-sidecar
reads at 64 KiB, and receipt output acceptance at 1 MiB. It never imports
repository/model code, walks all checkpoint trees, hashes weights, copies data,
or writes remote artifacts. Two full executions and in-memory Python syntax
compilation succeeded; these are operational metadata receipts, not scientific
tests or a certification that tomorrow's changing evidence is complete.

Helper SHA256:
`5b9f192e52e9218bd104a43aaa045074cb6bb776b102dc50747680f537531bbd`.
**EDITSTOP — no migration, transfer, cleanup, queue action, or launch executed.**
