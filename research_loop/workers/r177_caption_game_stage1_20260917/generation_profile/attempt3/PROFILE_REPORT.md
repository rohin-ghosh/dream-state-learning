# R177 attempt3 — six measured trials preserved; bookkeeping rejection recovered

## Final outcome

Six measured HF timing trials and two excluded warmups were durably saved before
a token-accounting guard rejected a genuinely sampled pad-token ID. All saved
trial counts, output digests, journal chains and rate denominators pass the audit
in `TOKEN_AND_RECEIPT_AUDIT.json` (2114 measured output tokens, not counting
warmups). The three journal copies per case are not three separate generations.

At2048 input tokens and a256 output cap, warm singleton throughput was
**23.239 tok/s**, and batch2 was **19.638 tok/s per sequence /39.276 aggregate**.
These are actual synchronized HF-call rates, not post-load timestamp estimates.
This attempt does not establish40 tok/s per life or complete the full matrix.

The false accounting rejection was repaired under the same authorized window in
attempt4 without changing generation/model/measurement settings. No third extra
attempt was made. Both owned units were confirmed stopped and GPU6 empty at
**21:04:53.561 UTC**, before the shared21:08:51 deadline; see
`../attempt4/GPU6_RELEASE.json`. Attempt3's original failure and exit receipts
remain intact. Its source snapshot is not overwritten by the repair.

## Historical preparation and gate

Preparing the first of at most two additional attempts authorized in
`../next20min_20260917T204851Z/AUTHORIZATION_WINDOW.json`. The shared absolute
deadline is **September17 2026 21:08:51 UTC**, including preparation and any
permitted bookkeeping recovery. The timer does not restart for another attempt.

The measurement recipe, public frozen model revision, synthetic rank8 fixture,
seed/backend, token budgets and hardware lease remain unchanged. Receipt filename
bookkeeping is repaired and regression tested. Strict physical6 UUID/minor/FD
admission remains mandatory. Prior sources, reports and receipts are preserved.

No throughput claim is drawn from attempt2's post-load timestamp-window rate.
Only newly persisted synchronized timing trials can support inference-rate claims.

[Builder] September17 2026 UTC —21 scoped CPU regressions passed against the new
immutable snapshot locally and on node4. Installed native-generation/encoding
compatibility passed with CUDA uninitialized. Exact measurement-loop and native
generate/encode ASTs match attempt2; model/decoder/token-budget policy is unchanged.
`BUILDER_GATE.json` binds the source/test hashes and shared absolute deadline.

Status: dispatch authorized for additional attempt1 of at most2. Actual launch
still requires fresh privileged admission and strict device validation. The
runtime limit is clamped to the remaining shared window, not reset to20 minutes.
