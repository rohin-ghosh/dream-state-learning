# Creative_select — actual node2 receiving console

LOADED September17 **16:59:07.099144 PDT**, record5443, nativePID1849923,
startticks91791898, GPU5. Receiving COMMITTED5451 is observed.
Exact complete cycle44 resumed; original discarded41 logged updates and3
requests/responses remain archived, not claimed preserved in resumed weights.

Physical root:
`/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/receiving7/root`

Read-only console (replays TRAIN responses from the beginning, then follows):

```bash
bash gpu/ovx_ssh.sh 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/receiving7/preserved/physical7/source /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r125_stream_console --root /localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/receiving7/root --follow'
```

For a message actually authored by Rohin, use the frozen attributed writer:

```bash
bash gpu/ovx_ssh.sh 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/receiving7/preserved/physical7/source /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r127_pilot_console parent --root /localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/receiving7/root --speaker Rohin --text "YOUR MESSAGE"'
```

Use R125 only with read-only `--follow`; its default stdin writer lacks speaker
attribution. Do not label Builder/Astra text as Rohin. Frozen R127 bytes match
the actually help-verified source. No publish test or message was sent; never
retry uncertain delivery. Original instructions remain in
`CONSOLE_V1_ARCHIVE_1702/`.

Tesla: use this physical root/source and node2 wrapper for the retired parent's
existing ledger/cursors, not the old node3 route. All48 final inbox files match
the frozen post-parent-stop overlay. No receiving parent was started by Ampere.
All exact proof paths and existing target lease/deadline hashes are in
`REHOME_SOURCE7_LOADED_HANDOFF.json`. GPU6 belongs to Chandra, not this learner.
