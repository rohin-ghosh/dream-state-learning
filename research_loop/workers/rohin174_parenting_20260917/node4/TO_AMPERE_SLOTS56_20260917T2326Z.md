# NODE4 handoff to Ampere — September 17, 2026, 23:26 UTC

**Later16:38 PDT allocation overrides optional-copy use:** physical5/6/7 are
reserved for original-life rehomes. See `TO_TESLA_AMPERE_REHOME_20260917T2340Z.md`.
Earlier ownership/preparation statements below are historical, not current allocation.

Scope: Ampere owns preparation/launch of the user-authorized C2 Thinkbudget2/3
copies on physical5/6. NODE4 owner will not interleave launches on these slots.
Physical7 is reserved for control/relocation. Preserve existing lives0/1/3/4
and judge2. This is capacity/provenance evidence, not a launch-admission receipt.

## Actual free-slot evidence

At **23:26:13 UTC**, fresh `nvidia-smi` showed both slots at **0 MiB used,
45486 MiB free, 0% utilization**. Root `fuser` found no holders of either
`/dev/nvidia5` or `/dev/nvidia6`. Do not confuse physical index with device minor:

| Physical | UUID | Device minor |
| --- | --- | --- |
| 5 | GPU-2e7eb3b8-9b0b-3729-f5ff-2bbdad6a4a30 | 6 |
| 6 | GPU-06b31c8f-7a96-d812-23f3-df3444d95397 | 5 |

The full three-sample privileged FD/CVD/compute census at23:05 UTC is
`R186_CAPACITY_FD_20260917T2305Z.json` in this directory,
SHA256 `a77e6745a5455be8e2528bf3975e8705fbef0a38337cc806ce6177a490e515ff`.
It reported no target holders/reservations/compute processes, no unknown
visibility, and no identity drift across the three samples. Its boot ID is
`ddc89057-e544-4d14-ac7d-cae6b7e3f781`.

`R186_FRESH_SLOTS56_20260917T2323Z.json` supplies newer NVML/root-FD corroboration,
but its quick environment reader reports ProcessLookupError visibility entries;
it is **not** a clean scanner/admission report. Preserve that limitation.
Run fresh unchanged privileged admission and strict receiving device proof for
your actual bound successor. CVD alone is not strict confinement.

## Existing lease ceiling — no extension

**Hard stop: September18,2026 18:00 UTC /11:00 PDT, epoch1789754400.**
Existing lease end1789776000 includes the unchanged21600-second safety margin.
Remote receipt:
`/localhome/local-rohing/orch_r132_kernel_child_20260916_attempt1/control1/LEASE_BUDGET.json`
SHA256 `ca4ead20b2b772c09e4d30e271c24988f0bbcc5f625665e6b63a441fe0e112a2`.
Receipt SHA was rechecked remotely at23:25 UTC. No extension is authorized here.

## Existing R153 gates — exact paths and scope

1. Remote `/localhome/local-rohing/orch_r153_node4_retirement_20260916t2208z/CPU_GATE.json`
   SHA256 `d70c252bd2df050b89897e781fc0967fca9297d27435ae2652a55f14ee141ec7`:
   PASS13tests+23subtests, **retirement operator CPU evidence only**.
2. Remote `/localhome/local-rohing/orch_r153_kernel_smoke_20260916t2215z/probes/GATE.json`
   SHA256 `cfd6768b1bc6bb8b63400e3066b88b5b3c952dfeae49a90f717cb105367e6814`:
   old R132 confinement gate for **physical2/minor1**; expired1789600444.022899.
   **Do not reuse as current physical5/6 admission.**
3. Local `kernel5_cpu_stage_20260917T2230Z/CPU_REVIEWED_20260917T2230Z.log`
   SHA256 `d3af42e4a447ad7891cc83a491570267e93d24ccd51557c9d68acd5c614be0b7`:
   198local+198receiving tests for reviewed forgiving-parser kernel executor,
   not a copy-source or current GPU-admission gate.

## Existing-life recovery

Kernel0 actually LOADED saved40 at23:23:34.303689 UTC, native1742549/start25551049,
journal4959 `6defda05459b419e3e12df21b1057bbc47221f749b23397a267e45f281114fb7`.
Its authorized R188 rollback preserves the full oldroot/journal/inbox archive;
this is **not exact in-flight continuation**. Raw1 also loaded COMPLETE42 at
23:22:14.142357 UTC, native1734752/start25543112. Raw3/kernel4 remain running.
No launch, reservation, or mutation of physical5/6/7 was performed by this owner.

## 23:29 UTC update

Fresh root-FD/NVML capture `AMPERE_SLOTS56_NVML_FD_20260917T2330Z.log` actually
observed23:28:58 UTC; SHA256
`43ac368ca8b8577c77e1124f2319f71ae443d67ca95114753462b1821e93c822`.
Both slots still0 MiB used/45486 MiB free/0% utilization, root fuser exit1 with
no holder output. A further direct check at23:29:58 UTC found the same state.
Kernel0 recovery completed sleep41 at23:27:15 UTC, record5011,
`85010186a2891f0e277507a69c127fc87a9ea51cfedafeb80f89ad4f3c9069e2`.
