# Enrollment and correction observer recovery

Non-material CPU observer restoration only. No GPU job, native life restart, adapter capture, backlog dispatcher, rescoring or evaluation is authorized or performed here. Enrollment references are not captured or evaluated checkpoints. Parent commands remain Main's separate work.

The `source/driver.py` and `source/enroll.py` copies are byte-identical to the two surviving implementations named in `EVERY_SLEEP_HANDOFF.md`. Original source files and correction-collector source/config are untouched. Source, registration, SSH wrapper and lease digests are pinned in `SOURCE_BINDINGS.json`.

`queue_launcher.py` acquires its own lifetime flock and both original canonical ENROLL locks while snapshotting metadata. It preserves the existing ledger locations, entries, pending ages, and monotone cursors. Only normal enrollment metadata updates resume in those two canonical ledgers; all new code, configuration, snapshots and startup receipts stay in this subdirectory. Original support/receipt pointers are not overwritten. Credentials remain in the existing runtime providers and wrappers, never in this configuration.

Each restart derives a fresh config from current states under both locks, rather than reusing the missing `/tmp` config or its obsolete initial-state hashes. The first baseline is immutable and checked on all subsequent launches. Locks are released just before the unchanged driver starts; the driver then acquires both original locks and independently checks the exact snapshot hashes before any ledger write. A competing writer or changed state fails closed, not a cursor reset. Two additional lock checks (launcher lifetime lock and driver original-ledger locks) prevent a duplicate writer.

The launcher remains the foreground CPU service and waits for the frozen driver. Its signal handler may stop only its own CPU reader child; it never signals a native, scorer, parent, process group or remote job. Both inherit the original September 30, 2026 17:59:30 UTC service limit; the original per-source lease-admission policy and 64-record pages remain unchanged. No lease is extended.

The existing correction observer is registered by exact verified host argv/PID/start/boot and adopted without starting or restarting it. Its original singleton lock and independently enforced source horizons remain unchanged.

Application registry files live in the parent's `services.d/`. Systemd installation remains blocked/uninstalled and boot enablement remains false. Main's parent-manifest work is not changed by this follow-up.
