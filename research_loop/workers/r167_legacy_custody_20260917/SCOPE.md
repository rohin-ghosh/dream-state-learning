# Read-only legacy custody and delivery census

Owner: Bernoulli. Scope: registered fleet_generation1 lives on ovx2, a100,
and a40r only; Galileo owns node5 custody and Mendel owns community parents.
No queue bind/capture, model/adapter/optimizer reads, sealed evaluation files,
signals, remote writes, or source changes. Kernel4 stays on its original parent.

Read limits per life: 256 TRAIN record documents, 64 MiB total TRAIN bytes,
32 MiB maximum record, 1 MiB per metadata JSON/source file, 32 MiB other
metadata/source bytes, 20,000 directory entries. Stat-only adapter/optimizer
presence; never open their contents. A reached cap produces incomplete custody,
not an inferred completed frontier. Exact process/config and registered-root
checks precede TRAIN reads. Native boot ID/startticks are observed afresh, not
copied from historically inconsistent inventory startticks.

Delivery refresh separately reads at most 1,000 local RESULT receipts per
owned successor (1 MiB each). Render probes share a 64 MiB per-life budget and
inspect at most 64 TRAIN records per published reply, 256 total per life.
They return only publication IDs, record indices/hashes and match classifications.
Hashes concern TRAIN/source custody only, never evaluated object fingerprints.

All output is create-only inside this directory; prior rollout sources and
receipts remain untouched. This is source-owner metadata evidence, not a
source-read-copy GO, queue registration, or GPU authority.
