# Node3 caption parents — 2026-09-19 01:16:06 UTC

PID clarification:324210 was deliberately replaced at00:58:07.628787UTC for the
CPU-only HTTP429 repair. Current provider330973/start764197 remains live, PPID1,
on nvl-ai boot80d71f45-6f0c-4479-b0e5-77a9611c793e. Real-host verification is
01:16:05.991328UTC. Supervisor311614 heartbeat01:16:02.887847UTC already adopts
the correct330973 identity; no registry repair, restart or signal is needed.
Latest actual publication at01:16:06.938732UTC is perspective0037 at
01:12:52.975223UTC, parent9254e24c4c7946e5a2a482ac252d1bf8. This clarification
changed metadata only and performed no additional process actions.

## Final cadence and registration

At01:14:48UTC the same five native incarnations remain bound. Parent cadence
continues: next model turns are actually published for observation01:10:22,
perspective01:12:52, revision01:07:30 and selfderive01:11:13; the historically
unparented fork's latest publication remains its first restored turn01:00:09,
which reached ACT7346. No synchronized or fixed wall-clock interval is imposed.

**Judgment cadence is not healthy.** The latest three authenticated ACTs per
fork (15total) all report `ENVIRONMENT_OUTCOME_UNKNOWN_NO_RETRY` with
`ConnectionRefusedError`, `executed=null`, zero feedback and zero successful
judgments. This is a Main/judgment-transport owner blocker, not caption-score
evidence. No retry of an ambiguous judgment, scorer action, transport repair,
native change or signal is performed by this task. `FINAL_CADENCE.json` binds
the exact ACT hashes, per-request journal start times, latest parent publication
hashes and this bounded current sample. Its ACT file-mtime fields are explicitly
filesystem metadata, not timestamps embedded in the journal record.

Application supervisor311614 adopted provider330973/start764197 at01:13:11UTC:
`RUNNING_ADOPTED_NO_SIGNALS`, one exact match, unchanged September24 18UTC horizon.
`SUPERVISOR_REGISTRATION.json` records the verified registration. The old disabled
manifest is preserved. `TO_MAIN_AND_AVERROES.md` and the services directory's
`NODE3_PARENT_HANDOFF.md` provide the shared handoff addressed to Averroes
(`01a0b71d-1231-7012-91cf-073230080a6d`) and Main; no direct-message acknowledgment
is claimed. OS boot installation remains blocked/uninstalled, boot_enabled=false.

All metadata work is complete. No further tasks, probes, launches or signals are
part of this recovery. The already-running provider retains its existing cadence.

## First-turn delivery proof

**All five first restored model-parent messages have verified INBOX → masked
ACT REQUEST → authenticated own RESPONSE → ACT chains.** All five were
published by01:00:09UTC; the final native consumed its message after its normal
learning/readout cycle. Every audit verifies the original exact incarnation.
Real-host VM provider330973 is detached (PPID1, SID330973); it replaced only
this recovery's CPU provider324210 to add tested explicit-HTTP429 backoff.
Original node-local publishers1973233/1973234 remain unchanged and locked.
No native signals/restarts, math-parent duplication, row filtering, or sealed
evaluation/key exposure occurred. Twelve focused CPU regression tests pass.

| Caption fork | Published UTC | Parent ID | Exact current receipt |
|---|---|---|---|
| observation | 00:56:43 | `174d2eaad1dd46238132082c05f0a7b6` | INBOX7551 → ACT_REQUEST7560 → RESPONSE7561 → ACT7564 |
| perspective | 00:56:46 | `b72bdc83752e4927b308bc91f4880e14` | INBOX7931 → ACT_REQUEST7940 → RESPONSE7941 → ACT7944 |
| revision | 00:56:48 | `86a632da6e464a62aa67bae9bbd29afe` | INBOX7134 → ACT_REQUEST7145 → RESPONSE7146 → ACT7149 |
| selfderive | 00:58:56 | `4ff33ae01f5c46d8b753d3a89a66f3d3` | INBOX6695 → ACT_REQUEST6704 → RESPONSE6705 → ACT6708 |
| unparented (historical name; parented) | 01:00:09 | `b117fb7485124f1cbec3d38a3c918a86` | INBOX7333 → ACT_REQUEST7342 → RESPONSE7343 → ACT7346 |

Each first turn acknowledges the operator gap after the September18 22:50:45UTC
VM reboot, responds to actual visible child/judge evidence, and requests one
concrete caption. Native readout/sleep cycles continue normally; inbox consumption
is not forced. Parent delivery/linked ACT is **not task uptake, judging success,
training evidence, or caption improvement**.

The earlier first THINK REQUEST indices are7553/7933/7136/6697/7335 respectively;
the table uses the directly linked ACT REQUEST, not merely a later ACT after
an unrelated prompt. The actual parent text is present and history-masked in
each ACT REQUEST. The first four linked replies were also inspected privately:
observation still uses `print(...)`, perspective continues the earlier naming
fragment, revision is literally `continued`, and selfderive includes code and
mixed-script text. These do not establish uptake of the concrete one-caption
instruction. No rows are removed or rewritten because of this assessment.

The initial selfderive rejection and three fifth-fork rejections are preserved
as explicit HTTP429 failures. Successful attempts use separate retry directories;
unknown/ambiguous dispatches are not replayed. No operator action is required.
The detached provider continues the original publisher-driven cadence; only
the five caption mailboxes are serviced. No commit or push was performed.

Current exact binding/provenance: `BINDINGS.json`. Latest independently refreshed
receipt: `AUDIT_LATEST.json`; immutable cuts: `receipt_history/`; first verified
chains: `first_verified/`. The provider's `STATUS.json` can lag during calls;
check its timestamp/PID rather than treating startup as current success.

Main boot command, inheriting the existing provider key securely in environment:

```sh
bash /data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_node3_parents_20260919/restart.sh
```

Run one instance only. `locks/SUPERVISOR.lock` and the five exact-life locks
are held for its lifetime; leave the original node publisher locks untouched.
Do not launch the old all-eight provider alongside it. Credentials remain VM-only.
