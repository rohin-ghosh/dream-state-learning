# Retry1 CPU attachment gate

[Builder] 2026-09-18 19:44 UTC — Non-material P3 retry1 CPU transport
continuation, within the explicit retry-prefix write-set. Local retry suite:
29 tests PASS; receiving CPU suite: the same 29 tests PASS; Main's unchanged
lease-parent loader regression: 5 tests PASS. A separate fresh process loaded
and validated the actual renewed original-parent policy and verified the
existing seed/turn ledger. The provider key was present in the inherited
environment; no credential was printed or stored and no provider call occurred.

Only the five named retry CPU Python files were copied into the existing
recovery CPU directory. Their exact hashes are in `P3_RETRY_DEPLOYED.json`.
Native source/control, Main's helper and loader bytes, the original journal,
attempt1 receipts, GPU processes and leases were not changed by this sidecar.

The single waiter uses an exclusive lock, 30-second read-only polls, and the
authorized September 25, 2026 18:00 UTC bound. This is the authorized experiment
bound, not independent provider-expiry verification. It accepts only the retry1
source, same journal and COMPLETE5243/sleep153, authenticated recovery/LOAD/WALL,
live PID/startticks/command/guard, and guard-pinned source/plan/lease. Attempt1
LOAD5299 is explicitly ineligible. A process scheduling-state change is not a
new incarnation. A failed or ambiguous attachment does not automatically retry.

After actual retry LOAD, attachment retains the original xhigh model-parent
policy, seed/turn ledger, one-response cadence, original parent lock and
publication lock. The endpoint accepts only poll/publish, supports both exact
immutable recovery events, and rechecks the native identity and wall inside
the publication lock. It does not repeat an opener. A spawned parent is not
proof of a provider answer, inbox delivery or rendering; those remain separate
post-LOAD evidence. No native signal, GPU launch or new journal is performed.

Exact local commands:

```sh
python3 -B -m unittest discover -s research_loop/workers/rohin233_recovery_20260918 -p 'p3_retry_test_*.py' -v
python3 -B -m unittest discover -s research_loop/workers/rohin233_recovery_20260918 -p 'test_p3_lease_parent.py' -v
```

Receiving command, within the existing recovery CPU directory:

```sh
python -B -m unittest p3_retry_test_cpu -v
```

This scoped entry is supplied for Main's coordination log; the sidecar does
not edit the shared coordination file.
