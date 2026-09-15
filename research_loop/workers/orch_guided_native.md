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

2026-09-15 00:21UTC: author-side live A100 integration receipt check passes.
UNPARENTED cycle1 same initial child in experience/sleep;26updates produce
f2013ae1; fresh completed readout and cycle2 experience load that exact child.
Mounted-state receipts retain basea2367093, four separate process identities;
output adapter-file hashes rechecked, next-cycle manifest binds original
native-source559d8e6e.52subsequent call files observed, no outcome counts read.
No code compatibility failure found. No GPU/model calls, process changes or
tensor rehash here; existing native receipts are evidence, not independent
verification or a learning-benefit claim. Saved scoped observation1 JSON.
Initial wrong-node read found no files; corrected from authoritative A100
BOARD/interface rather than inferring absent runs. Concurrent notebook merges
preserved both parent sequences. No completed stage restarted.

2026-09-15 01:20UTC: checked the concrete compatibility hypothesis that native
projection caused SHORT's zero updates. No recorded projection errors across
SHORTC1–C3, UNPARENTEDC1 and LONGC1; every semantic admission survives encoding.
SHORT154turns:148fail necessary conditions;5UNRESOLVED;1semanticFAIL.
The five unresolved C2 candidates have empty reviews after JSONDecodeError
and evaluator_failed_no_fallback:1, not negative content judgments. No new
parser, retroactive admission or duplicate run. Existing parent worker owns
transport and already uses the strict envelope helper. Exact receipt/episode
hashes and count assertions saved under own projection_diagnostic1 JSON/MD.
No native-seam code repair indicated; no model calls/fits/PID changes.

2026-09-15 02:24UTC: added opt-in orch_guided_native_generation.generate over
the already bound child with explicit prompt/new-token budgets. Addresses
legacy2048/768 caps for future replay callers, without changing those defaults,
any active driver, loader or peer INTENSITY generator.26CPU tests pass0.503s,
including8new fake-generation checks. Positional budget bound is not measured
GPU memory/runtime; existing pre-call deadline hook is not an interrupt.
Handoff: orch_guided_native_20260915_generation_handoff.md. Main must adopt
prospectively with resource bounds; no native call, task generation, allocation
or launch by this contributor. Independent focused static review requested.

2026-09-15 02:25UTC: Linnaeus returned no concrete correctness regressions;
8generation CPU-fake tests independently pass. No fixes requested. Reviewer
closed; caller still owns boundary tensor verification and prospective use.
