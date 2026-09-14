# Old Builder native-seam journal

2026-09-14 23:18UTC: recovered published be4d0e96 assignment and V1 interface
e5a4f919. Exclusive scope orch_guided_native prefixes only; no GPU, task
generation, actual fit or native launch. Peer bridge and released historical
drivers remain unchanged. Concurrent notebook merge preserved both complete
parent sequences. Model libraries are not installed on this VM; use CPU
mock-native integration, not claims of real model execution.

Implementation: reuse existing Engine with phase=readout for every initial
load; its train phase would create a new adapter. Measure mounted LoRA and
mounted normalized base tensors, then enable existing LoRA and instantiate
fresh declared AdamW only for training. Bind process/context at readout;
project actual captures and preserve native tokenizer/reference-loss semantics.
Tests in progress. No registry, new supervisor or campaign driver.

2026-09-14 23:25UTC: implementation complete;56 CPU tests pass64.894s
(18 new,22 peer bridge,7 replay layout,9 historical native-driver tests).
Tests exercise three cycles/three arms with fake native model tensors, actual
factory arguments and optimizer construction; one actual fresh subprocess
loads fake output files. No torch/model installed or used. Existing peer
bridge and historical executed driver diffs empty. Fixed a readout-isolation
risk before publication: inherited fork without exec now fails.
Handoff is research_notes/analysis/orch_guided_native_20260914_handoff.md.
Focused read-only reviewer checking native assumptions in parallel; no new
launch gate, process/GPU change or scientific result. Awaiting review report
before the final code handoff, not before other campaign work.

2026-09-14 23:27UTC: focused Feynman review returned no concrete native-seam
bugs; static only, no tests or model/GPU calls. Review worker closed. The old
ownership blocker is resolved by be4d0e96; this scoped implementation is now
delivered, while actual native execution and the full research mission remain
incomplete. Main owns GPU/protocol/candidate decisions and next integration.
