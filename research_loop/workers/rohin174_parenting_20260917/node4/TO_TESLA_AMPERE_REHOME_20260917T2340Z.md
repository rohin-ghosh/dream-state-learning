# Urgent NODE4 receiving reservation — Tesla and Ampere

Main's September17 16:38 PDT directive supersedes optional unlaunched R187
Think2/3 copies: **reserve physical7,5,6 for exact-state original-life rehomes**
before NODE3's16:50 stop/17:00 ceiling. Ampere: do not dispatch optional copies
on5/6. Tesla owns source-life custody; NODE4 owner provides receiving evidence.
This is a shared coordination reservation, not a claim of a hardware-enforced lock.

At **16:38:39 PDT /23:38:39 UTC**, all three were empty:0 MiB used,
45486 MiB free,0% utilization. Root fuser found no holders on minors4/5/6;
NVML showed only original learners0/1/3/4 and judge2. No R187 copy was loaded.

| Receiving priority | Physical | UUID | Minor / PCI |
| --- | --- | --- | --- |
| Original rehome | 7 | GPU-6eac3b9d-551a-d786-f598-04ef6d701c98 | 4 /0000:e1:00.0 |
| Original rehome, not optional copy | 5 | GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30 | 6 /0000:a1:00.0 |
| Original rehome, not optional copy | 6 | GPU-06b31c8f-7a96-d812-23f3-df3444d95397 | 5 /0000:c1:00.0 |

Evidence `REHOME_SLOTS567_20260917T2340Z.log`, SHA256
`4a33253d713d7d0e3315ff6e55f658164ec761252564978ca1e0335f9a506f41`.
NODE4 receiving hard wall remains **1789754400 = September18 18:00 UTC/11:00 PDT**,
not NODE3's expiring wall and not the later unbuffered lease end. No lease extension.
Lease receipt/path/hash and reviewed CPU tool evidence are in
`TO_AMPERE_R187_20260917T2337Z.md`.

Existing R137 device-command source:
`gpu/orch_r137_node4_containment.py`, SHA256
`74cca3f1061f848da049b19e98797c5925e7646002c82147399b0c1131c4dcd2`.
It already permits6/7;5 needs a new explicit receiving binding, not CVD alone.
The original0/1 legacy guard is NOT a5/6/7 guard and is not being broadened.
NODE4 owner is running a bounded, model-free receiving ACL probe using the
unchanged R137 command body with this exact5/6/7 reservation map and Tesla's
existing seven-foreign-minor probe. Results will be appended here; these are
not a substituted clear admission for Tesla's eventual exact source/root.

No originals0/1/3/4, judge2, inbox, journal, or parent state is changed by this
reservation/probe. R188 parents0/3/4 are running; kernel0's first example is
published and rendered. Raw1's parent remains unchanged.

## Receiving proofs complete —23:41–23:42 UTC

All three PASS: target open/close plus all seven foreign-minor denials inside
the actual strict nonroot2524 service. Empty capabilities, NoNewPrivileges,
no inherited GPU descriptors,45-second service bound. No CUDA contexts,
models, learner launches or signals. The R137 command function and Tesla's
device probe are unchanged; only the explicit receiving map is5/6/7.

Remote source/receipts:
`/localhome/local-rohing/orch_r188_node4_rehome_20260917t2341z/`.
Local copies: `rehome_receiving_20260917T2341Z/` in this directory.

| Physical | Receipt | SHA256 |
| --- | --- | --- |
| 5 | RECEIVING_DEVICE_5.json | fce952e34bdfc1dbad4cff9cd54a044dcf5c5ca80a03e34fdae6586e10afecbd |
| 6 | RECEIVING_DEVICE_6.json | bcdb68726e59c4d30a03b23fcfabcc5ceccf1273672996c9104727cd52c871f9 |
| 7 | RECEIVING_DEVICE_7.json | c5526bfd82d60d7c1d919d20d6338d6de8c799f50a48aeef7db5d38641dc48ce |

Runner `r188_rehome_probe.py` SHA256
`491794a12278717f21019442d002603fb6d5a9870f9c1e6a241babe33f949769`.
Probe SHA256 `d32658950a078c837eeecc9096b03ae4d3098456ab4ac68e8ea7721b4a9a4192`.
Three scoped CPU tests PASS. Boot `ddc89057-e544-4d14-ac7d-cae6b7e3f781`;
unchanged hard wall1789754400.

GPU7 first stopped before service intent because its FD precheck failed;
the original fuser text was not captured, so the cause is unclaimed. Evidence
is preserved in `REHOME_GPU7_FIRST_ATTEMPT.json`. Fresh root-FD/NVML diagnosis
at23:41:44 was clean; one unchanged-source bounded probe passed23:41:59.140953.
No native launch or guard bypass occurred.

At **23:43:02 UTC /16:43:02 PDT**, all three remained0 MiB used/0% utilization,
with no root-FD holders. These are receiving DEVICE proofs, not complete
model/source/root admission. Tesla binds each original's exact saved state and
receiving source/root, then uses the unchanged fresh final scanner. No additional
broad GO is requested. The reservation has been posted here; no peer ACK is
claimed merely from writing this file.
