# Fleet prospective custody: bounded metadata-only acquisition

Scope: September 17, 2026 user-authorized passive wrapper reads, seven node5
(`ovx3`) lives C1/C2/C3/C4/continual_run1/pilot/repo_reader. C5 is pending
Banach's separate committed-recovery/source-owner release; no C5 namespace
is opened. The other thirteen registry lives are outside this first pass.

Per-life receipt: fresh process PID/startticks/boot, historical PID comparison,
exact current config/PLAN/source-file hashes, root distinctions, historical
registry birth PLAN hash, initial COMMIT hash and adapter-file presence,
journal header and bounded most-recent SLEEP_COMPLETE envelope/intent,
latest sleep COMMIT hash. Byte counts, observation times and failures retained.

Caps: 8 MiB per whole regular file, 32 MiB whole-file plus envelope reads per
life; 16,384 directory entries, 1,024 source pins, 256 recent journal envelopes
at 512 bytes each. Separate one-shot process census: at most 4,096 processes,
256-byte comm and 4,096-byte stat/cmdline caps; no environment reads. Wrapper
execution bounded to 180 seconds; no remote output/temp files or imports of
project runtime modules. Source/config files must be regular, non-symlink,
stable while read. Only declared `.py` source pins are opened as source.

Do not read response/loss/history documents, held/readout/evaluator artifacts,
fingerprints, model/optimizer/RNG payloads. Journal reverse-byte reads stop at
the canonical envelope `index` field, after `document`; declared journal
digests are explicitly not raw-file hashes or recomputed payload hashes.
No full causal frontier, birth-history binding, adapter-byte integrity, or
loaded in-memory source attestation is claimed from this restricted pass.
These missing items are explicit, not fabricated queue-ready observations.

No signals, model calls, child/source writes, queue mutation, source-copy
authority or GPU GO. Only this new local directory receives artifacts.
