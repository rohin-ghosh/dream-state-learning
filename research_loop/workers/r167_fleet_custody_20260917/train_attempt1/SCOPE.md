# Additional bounded TRAIN authority, fresh preserved attempt

Latest user explicitly authorizes full TRAIN journal/resume-state reads:
64 MiB TRAIN/life, 32 MiB TRAIN/file, 32 MiB source metadata/life.
No sealed/readout/evaluation/fingerprint files, model calls, signals, or remote
writes. Only parsed custody metadata/hashes leave source node.

Reuse Bernoulli's native_custody.py reader/record/intent/checkpoint/identity
algorithm and five tests, copied into this owned directory. Narrow changes:
node5 seven-life scope, cumulative prior metadata accounting, require exact
last sleep receipt, untouched initial rows, TRAIN history and original birth
continuity; preserve explicit pending alias binding for repo_reader instead
of stopping before TRAIN reads. No native runtime imports or mutation.

Authenticate birth record0 separately plus the complete reverse journal
suffix from the listing-time tail back to latest SLEEP_COMPLETE. This is not
a full replay/hash scan of every intervening birth-to-frontier record.
The latest completed boundary must bind exact COMMIT/state/receipt/history.
Registry PLAN birth equality is reported separately and blocks its use if
false. Adapter tensors/optimizer/RNG remain presence-only, never read.
