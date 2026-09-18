# Node3 recovered-life console routes

September 17, 2026. Original logical roots are archival on the host; the live
native sees a private mount of the recovered backing root. Use the backing
root below for future console and parent messages. Do not resend historical
messages. Check `RECOVERY_LOADED_<physical>.json` for actual load confirmation;
the presence of a prepared directory alone does not establish liveness.

| Physical GPU | Life | Live backing root suffix | R179 source suffix |
| --- | --- | --- | --- |
| 0 | support_free | control0/run1 | physical0/source |
| 1 | creative_reread | control1/run1 | physical1/source |
| 2 | brain_free | control2/run1 | physical2/source |
| 3 | brain_guided | control3/run1 | physical3/source |
| 4 | creative_free | control4/run1 | physical4/source |
| 7 | creative_select | control7/run1 | physical7/source |

Backing prefix: `/localhome/local-rohing/orch_r179_node3_recovery_20260917t1818z_2/`.
Source prefix: `/localhome/local-rohing/orch_r179_node3_context_20260917t1715z_1/`.

Exact example for support_free, with the human's actual message substituted
for `Your message here`:

```bash
bash gpu/ovx2_ssh.sh 'cd /localhome/local-rohing/orch_r179_node3_context_20260917t1715z_1/physical0/source && /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r127_pilot_console parent --root /localhome/local-rohing/orch_r179_node3_recovery_20260917t1818z_2/control0/run1 --speaker Rohin --text "Your message here"'
```

For another life replace both `physical0` and `control0` with its physical
number in the table. Publication creates an attributed parent inbox entry;
it is not a receipt that the child has already consumed or responded to it.
Parent/console text remains masked from training. Native state, archived
journals and previous inbox entries are not changed by this routing repair.

The current internal stop is September 17 at 16:50 PDT, with the machine
ceiling unchanged at 17:00 PDT. These commands do not extend either deadline.
