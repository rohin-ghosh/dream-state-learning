# Creative_reread — actual node2 receiving console

LOADED September17 **16:58:09.422854 PDT**, record5739, nativePID1849630,
startticks91786090, GPU0; new receiving COMMITTED5746 is observed.
Exact complete cycle46 resumed; original discarded42 logged updates and3
requests/responses remain archived, not claimed preserved in resumed weights.

Physical root:
`/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/receiving1/root`

Read-only console (replays TRAIN responses from the beginning, then follows):

```bash
bash gpu/ovx_ssh.sh 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/receiving1/preserved/physical1/source /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r125_stream_console --root /localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/receiving1/root --follow'
```

For a message actually authored by Rohin, use the frozen attributed writer:

```bash
bash gpu/ovx_ssh.sh 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/receiving1/preserved/physical1/source /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r127_pilot_console parent --root /localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/receiving1/root --speaker Rohin --text "YOUR MESSAGE"'
```

R125 is read-only `--follow` here; do not use its default stdin writer, which
omits the speaker. Do not label Builder/Astra text as Rohin. Frozen R127 bytes
match the actually help-verified source. No publish test or message was sent;
never automatically retry uncertain delivery. Original instructions are retained
in `CONSOLE_V1_ARCHIVE_1702/`.

Tesla: rebind only the existing retired parent's transport to this physical
root/node2 wrapper/source, preserving its ledger/cursors/publication accounting.
Do not restart publication to the old node3 root. All72 final inbox files matched
the post-parent-stop overlay; no messages re-authored or resent. Ampere started
no receiving parent. All proof paths and existing lease/deadline hashes are in
`REHOME_SOURCE1_LOADED_HANDOFF.json`.
