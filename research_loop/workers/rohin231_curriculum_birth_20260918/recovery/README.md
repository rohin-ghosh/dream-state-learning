# R232 bounded failed-pair recovery

Explicitly authorized recovery of the already-dead experimental pair, not original C2. This is a new runtime epoch with real downtime and asymmetric exposure. The old native/source/failure receipts remain immutable. There is no continuous/no-gap or causal-isolation claim.

## Repair and preserved state

Both use legacy context6144, pre-generation compaction4608 instead of4096/3072; generation512, frozen Qwen, private adapters, LR3e-5,16 new-only presentations, microbatch1, non-reentrant gradient checkpointing, existing parents and14:00UTC horizon are unchanged. The existing horizon is not proof of exact provider lease expiry. The only plan differences are context and byte-identical source-path relocation. Neither changes to learning dose nor text deletion are used as memory workarounds.

The epoch journal subclass admits precisely one context-only transition at a completed saved sleep with no pending operation/untrained rows. All other state fields must match exactly, including experiment, wall, model digest, history, working state, rows and pins. The entire previous raw tree is independently copied and hash-verified privately before transition. Original six-paragraph birth SHA7362d19a950779633067c81bacd0f0942e4243bbd62cf029463b61c264d66191 is unchanged. The later exploration message is not relabeled as birth or resent.

Learner resumes latest sleep2 optimizer96, frozen latest sleep2 optimizer0; both restore their own latest adapter/optimizer/RNG, not a baseline/initial checkpoint. The runtime bypasses the clone-only birth compaction hook on these same-identity resumes. All regular compaction, canonical journal checks, strict one-GPU confinement and privileged occupancy admission remain enabled.

## Validation

Eight focused CPU tests pass, including protected3637/3600 without truncation, rejecting non-context changes/pending operations/repeated epochs, and first+second frozen sleeps with forbidden optimizer.step. The receiver additionally verifies actual canonical and blocked-state renders: learner3869/3497 tokens; frozen3837/3465; no compaction edits required in these checks. Exact context epoch replays from the real journals.

At6144 tokens, before LOADED: learner performs one synthetic forward/backward, never optimizer.step; frozen measures full-context inference/KV, no gradients. Adapters/optimizers are checked unchanged, all CPU/CUDA/Python RNG restored, no child row is created. Peaks and modes are reported separately; this is measured receiving feasibility, not a guarantee for every future workload. Neither preflight is counted as training or genuine child exposure.

Two preparation-only checks failed before journal/native changes (relocated pin path and comparing serialized versus public working-state views); their private artifacts remain preserved. The first learner admission failed closed before any native creation; a fresh identical-source one-shot admission then passed. No live process was stopped and no admission invariant was relaxed.

`TO_MAIN.md` summarizes actual LOADED/PID/first-request/downtime. `LATEST.json` is a bounded sanitized observation, not a perpetual watcher. `observe_recovery.py` only reads journals/proc and reports hashes, IDs and counts, never transcripts. Private preservation manifests/raw trees and parent generation inputs are excluded from publication.
