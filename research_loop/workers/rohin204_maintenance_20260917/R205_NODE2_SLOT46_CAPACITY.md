# Node2 slots4/6: current CPU-only capacity proof

Observed **September 18, 2026, 03:53:12.888308 UTC**, using the existing node2 SSH helper, `/proc` identities, the process mount namespaces, existing TRAIN journals, and read-only NVIDIA driver metadata in `/proc`. No NVML/nvidia-smi, GPU API/model calls, process controls, or remote writes.

| Physical slot | Verified current PID / state | Matching LOADED | Latest REQUEST / tokens | Only open numbered GPU device | Journal advance since03:48:02 |
| --- | --- | --- | --- | --- | --- |
| node2/4 | 2204408 / R | 5847 | 6036 /7339 | `/dev/nvidia4` | 6020→6078, same PID |
| node2/6 | 2204538 / S | 5847 | 6067 /5420 | `/dev/nvidia6` | 6041→6112, same PID |

For each process, its **CUDA_VISIBLE_DEVICES UUID matches the driver's GPU UUID and Device Minor4/6**, respectively; exact GPU UUID/PCI metadata and PID/start/UID/cwd checks are in `R205_NODE2_SLOT46_CAPACITY.json`. Other environment variables and full command lines were not logged. Both identities remained valid after device-binding reads.

These are occupied, loaded, advancing native lives—not capacity to allocate based on an “empty” visual reading. CPU state S does not establish an empty GPU. Instantaneous GPU memory/utilization was deliberately not queried, so this is not a utilization percentage or memory-size claim. Route any conflicting capacity display to **Leibniz/NODE2**, the sole operator; this audit performs no stop/restart/reassignment.
