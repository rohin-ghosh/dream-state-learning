# Creative_free — actual node2 receiving console

LOADED September17 **16:57:00.977653 PDT**, record5295, nativePID1849180,
startticks91779127, GPU7. First receiving RESPONSE5298 and COMMITTED5299 exist.
Native remains on the exact preserved source/checkpoint, with the explicit
receiving-budget transition; no claim that source-side partial work was saved.

Physical root:
`/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/receiving4/root`

Read-only console (replays TRAIN responses from the beginning, then follows):

```bash
bash gpu/ovx_ssh.sh 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/receiving4/preserved/physical4/source /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r125_stream_console --root /localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/receiving4/root --follow'
```

For a message actually authored by Rohin, use the frozen attributed writer:

```bash
bash gpu/ovx_ssh.sh 'env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/receiving4/preserved/physical4/source /localhome/local-rohing/v2/venv/bin/python -B -m gpu.orch_r127_pilot_console parent --root /localhome/local-rohing/orch_r188_node2_rehome_20260917t2344z/receiving4/root --speaker Rohin --text "YOUR MESSAGE"'
```

Do not publish with R125/default stdin: it omits the speaker and is not
Rohin-attributed. Keep R125 `--follow` read-only. Do not label Builder/Astra text
as Rohin. The R127 module and `parent --help` were actually verified in frozen
source; no publish test or message was executed. Never retry uncertain delivery.
The superseded instructions are preserved in `CONSOLE_V1_ARCHIVE_1702/`.

Tesla: use this physical root and `gpu/ovx_ssh.sh` for the existing parent's
transport. Keep the old node3 parent/route retired; reuse its existing ledger,
cursor and in-flight/publication accounting without a new parent baseline.
All67 final inbox files match the frozen post-parent-stop overlay; no message
was re-authored or resent. No receiving parent has been started by Ampere.

Existing receiving hard1789776000 / ceiling1789776600 and lease receipt hash are
bound in `REHOME_SOURCE4_LOADED_HANDOFF.json`, together with actual source,
guard/plan, LOADED, original-parent-stop and final-inbox evidence.
