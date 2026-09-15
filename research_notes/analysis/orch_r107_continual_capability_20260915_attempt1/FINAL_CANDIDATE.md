# Final sanitized source/test candidate

Use only `STAGE_READY_FINAL.json` and its exact file allowlist. It supersedes
both previous staging manifests. Earlier native readiness/publication/status
and CPU receipts in this allowlist are historical provenance, not assertions
that current repository candidate bytes executed the completed readout.

## CPU fixture isolation repair

Only `tests/test_orch_r107_continual_capability.py` changed in this repair.
Its `prepared` fixture copies exactly `REQUIRED_SOURCES` into a per-test
temporary directory and monkeypatches `runner.SOURCE_ROOT` to that snapshot.
Concurrent edits elsewhere in the shared repository therefore cannot race
preparation's source-hash validation. No production guard was changed or
mocked out. The added regression deliberately changes a copied file and
confirms the existing hash guard rejects it.

Focused own tests plus Main's reducer disclosure tests:55 PASS in2.93s.
Combined own/paired/policy/reducer regression suite:179 PASS in4.07s.
These are VM CPU tests; no native model execution or native pytest claim.
Main's reducer source/tests were exercised but not edited or included as
owned source files in this allowlist.

## Source and runtime separation

Both sanitized production candidate files are unchanged by this fixture fix.
They retain the existing pinned host-hash binding without literal hostnames.
The final four-file candidate and every prospective publication receipt are
privacy-scanned and SHA256-bound in the final manifest.

Sanitized repository candidate != immutable original native runtime bytes.
The original private runtime/source-hash provenance remains node-local and
unchanged. The completed64-call diagnostic is not rerun; no model calls,
deadline reset, SSH collection, native edits, or git mutation occurred during
this repair. Main exclusively owns final reduction and scientific reporting.
