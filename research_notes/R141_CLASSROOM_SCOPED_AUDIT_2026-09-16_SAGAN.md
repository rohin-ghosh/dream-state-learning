# R141 bounded classroom exposure audit — Sagan

September16,2026, bounded follow-up after Main's13:40Z audit. No sleep wait,
runtime changes, process signals, child resets or held-readout access.

## Result

Scoped classroom evidence passes. The unchanged original all-eight-process
audit still fails at its final identity sweep because non-classroom
teach-perception PID1802290 is absent. This is not an all-eight-identities-pass
receipt. Its crash investigation remains with Mencius.

| Receiver | New reservations | New publications | Strict rendered REQUEST exposures | Alternating senders |
|---|---:|---:|---:|---|
| A1005 brain | 5 | 5 | 4 | 6,7,6,7,6 |
| A1006 creative | 6 | 6 | 6 | 5,7,5,7,5,7 |
| A1007 support | 6 | 6 | 6 | 5,6,5,6,5,6 |
| Total | 17 | 17 | 16 | One A1005 publication not yet exposed at snapshot |

56 inherited attempts remain separate old-phase custody; total73 of the
original1000 attempt budget. No uncertainty receipts were present. Counts are
from the bounded audit snapshot, not a claim that no subsequent delivery occurs.

## Verified evidence and invariants

-17 exact TRAIN REQUEST→RESPONSE→COMMITTED source chains,17 actual sender
 SLEEP_COMPLETE bindings and17 post-phase receiver-sleep bindings validated.
-16 consumption receipts reverified against the exact environment event in
 visible history AND the exact rendered REQUEST message; registration alone
 does not count. Peer text remains attributed environment, not parent sharing.
-One reservation per receiver sleep, strict alternating peer order, unique
 source/receiver pairs, no inherited-pair retry and original total budget pass.
-All14 transitions between consecutive receiver reservations satisfy prior
 verified exposure followed by a later receiver sleep. No induced child turns.
-Complete predecessor custody hashes still match the pre-handoff preservation
 manifest. All three classroom native identities2036898/2058507/2047929 exactly
 match original HANDOFF_INTENT baselines. Relay2670302 matches its original
 launch argv and remains live. Old relay2087568 remains absent.

Exposed REQUEST indices:

- A1005:869,965,1064,1166; selected receiver sleep epochs774,962,1061,1163,1268.
- A1006:777,870,966,1065,1167,1272; sleep epochs774,867,963,1062,1164,1269.
- A1007:587,652,718,787,857,930; sleep epochs585,649,716,784,855,927.

These are REQUEST-exposure results, **not behavioral uptake or benefit**.
Latest-eligible-at-dispatch cannot be independently reconstructed without a
dispatch-head snapshot; that policy is not upgraded to an observed claim here.

## Method and retained evidence

Executed the existing staged `VERIFY_EXPOSURE.py` unchanged. On its exact
late FileNotFoundError at line120 (`/proc/1802290/stat`), inspected validated
locals from that audit frame, then performed bounded read-only classroom
identity, relay identity, no-retry/budget and backpressure checks. No function
was patched, no original assertion suppressed and no receipt falsely marked
all-eight-pass. The original requested `EXPOSURE_AUDIT_R141_1340.json` does not
exist because that run failed before its writer; it was not created or replaced.
The final bounded attempt likewise did not create an original success receipt.

Original staged script SHA256:
`281c95bef4bc788aec1c5bedcaf4c72295333f3e15089c0592894aea52c90709`.
Original identity baseline SHA256:
`98103b8f80d32dc040314cfa809cf56eb5e218c3ebfec9a5cf93bac89c770bbf`.
Unchanged phase SHA256:
`c43ffeef0b50f1748e66b4d55ce8f720dfe09e17ddd71a97bc90c306767a9d29`.
Unchanged CONFIG SHA256:
`7100831fd2583bc49115e28a92478ab986b07aab87cd31c316e2f31123d5a2f7`.

All original source, slot, publication and consumption receipts remain at:
`/localhome/local-rohing/orch_r140_classroom_pacing_20260916_attempt1/PACING_STATE/`.
The complete original-failure reproduction traceback is preserved locally at
`research_notes/analysis/orch_r141_classroom_readonly_20260916_sagan1/ORIGINAL_AUDIT_REPRO.log`.
The bounded read-only tool result preserves individual exposure references and
full expected/observed identity evidence. This note is a scoped summary, not an
original-script success receipt or replacement for the preserved failed audit.

No new implementation was completed or deployed. Before the final bound, an
attempt to patch an additive copy failed because that copied file was read-only;
the subsequent discovery ran0 tests, **not a passing test gate**. That abandoned
copy and log are not used as evidence for these results. Existing live code and
the original audit remained unchanged throughout.
