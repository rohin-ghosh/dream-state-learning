# Read-only post-recovery sibling audit

Scope: this worker only. No learner/parent/policy writes, signals, model calls,
GPU operations, readout evaluation, new enrollment, or sealed-score access.
This is a one-shot bounded semantic review, not a recurring semantic daemon.
All semantic flags in `annotations.json` are explicit analyst judgments after
reading the actual feedback, own text, next ACT, later attempt and context.
`audit.py` verifies their source/order/span/masking/reminder constraints; it is
not a semantic classifier. Strongest levels apply only to captured windows.

## Reproduction

Tests need only the Python standard library:

```sh
python3 -B -m unittest discover -s research_loop/workers/post_recovery_pair_evidence_20260918 -p test_audit.py -v
```

`collect.py` uses only the existing `gpu/ovx4_ssh.sh` transport and a stdlib
reader streamed over stdin, with CUDA hidden and bytecode writes disabled. It
does not install/upload a remote file. It binds each current PID/starttick/LOAD,
journal ID and guard hash; at most750 record files and1GiB per arm are decoded.
The selected window starts at the fourth-last complete anchor and ends at an
immutable observed head, covering three complete sleeps plus any partial tail.
One initial frozen capture exceeded the original512MiB budget and failed closed;
only that reader budget was raised to1GiB. No incomplete capture became evidence.

Raw TRAIN text stays in ignored mode-restricted `private/`. The first exact cuts
remain intact in `private/{learner,frozen}.json`. `collect.py --reproduce` re-reads
those **same** fixed head indices/hashes into a new `private/reproduced/` directory,
verifies every projected record is identical, and checks parent backing files.
It refuses to overwrite existing captures. `reader.py` also accepts explicit
`--cut-index` and `--cut-sha256` together for an exact remote reconstruction.

Fixed reviewed head pins:

| Arm | End index | Canonical head SHA256 |
| --- | --- | --- |
| learner |4354|`7021fdd75ad81bf68bff05df6d4d131ee7438b1fcf6b015460de830b2fcc5ee3`|
| frozen |2787|`9e948ee6f9946f34642df9071322c7d41bb94d81feb85436bddf97706c543060`|

With the private fixed captures present, run `python3 -B
research_loop/workers/post_recovery_pair_evidence_20260918/audit.py` to reproduce
the evidence table. Its publication timestamp changes; record evidence and
manual classifications do not. Public JSON includes input cut/code/annotation
hashes and precise source references but not full private prompts or raw journals.

No level3 was found. Thus no new checkpoint preservation/copy is asserted.
Canonical COMPLETE checkpoint/adapter hashes are reported as record-bound pins,
not freshly rehashed files. Explicit full-history and first-ever claims are absent.
