# Post-reboot curriculum pair parent restoration

Non-material operational repair, authorized September 19, 2026 UTC. All source,
tests, private provider artifacts and new recovery receipts are confined to this
worker. The earlier birth and recovery workers are read-only dependencies, not
resumed output directories. No GPU native is signaled, restarted, reconfigured,
or relaunched. No training row, learning recipe, weight, allocation or lease is
changed. Both parents remain blind to sealed scores and to the other child's
transcript. Existing all-authentic-row policy is unchanged.

## Exact targets

| Arm | Native PID | Start ticks | Journal |
| --- | --- | --- | --- |
| learner | 493500 | 10070880 | 038f85cbde5c4abfb749ea4d59da6897 |
| frozen | 471737 | 9987073 | 30fa18c869b34fd496a2758a4a28e197 |

Every remote read/publication verifies native PID/start, command, config root,
journal and a freshly observed remote boot ID. A changed binding fails closed.
The original `parent_io.py` handles publication and idempotence. No new remote
source files are installed. `remote_io.py` is sent as an SSH Python command.

The legacy parents' preserved error receipts actually stop at September 18
22:30:10 UTC (learner) and 22:25:44 UTC (frozen), before the user-reported
22:50:45 UTC VM reboot. They record SSH transport timeouts. Restoration does
not attribute that earlier failure to the later reboot.

## Reused scientific contract

`r232_pair/PARENT_SOURCE.py`, the birth specification, the R232 environment
epoch, provider `strong()` and finite allocation authority are reused read-only.
Model: `openai/openai/gpt-6-astra`; existing configured NVIDIA Responses
provider; reasoning low; no provider tools; English-only messages, at most 90
words. The stage schedule remains 1/1/1/2/3/on-request. Stage advancement still
requires the original evidence conditions, with missing assessment cycles not
counted as consecutive successes. No stage advancement is inferred from a
restoration or an unassessed interval.

The initial cursor is bound to the last archived assessed ACT. All subsequent
canonical records are hash-chain checked; all actual ACT text, including errors
and non-English text, is retained as evidence. No semantic row exclusion is
introduced. The resumed parent catches up before offering fresh feedback on the
latest ACT, rather than replaying obsolete openings or issuing a burst of stale
corrections. The first fresh provider message must acknowledge the publisher
gap, then provide concrete feedback and an actionable task on the current object.

## Host launch and boot-supervisor handoff

Run on the **real VM host**, not a sandbox/private PID namespace. Working
directory: `/data/home/rohing/dream-state-orch`.

One independent foreground command per arm:

```sh
/usr/bin/python3 -B /data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_pair_parents_20260919/parent_service.py --arm learner
/usr/bin/python3 -B /data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_pair_parents_20260919/parent_service.py --arm frozen
```

Required nonsecret environment:

```text
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1
CUDA_VISIBLE_DEVICES=
HOME=/home/rohing
```

Inherit `NVIDIA_API_KEY` through the existing secure environment; do not put its
value in argv, source, receipts, logs, or this document. The existing
`~/.codex/nvidia-astra.config.toml`, `gpu/hosts.env`, and SSH identity must remain
available to the service account. No credential values are copied here.

Exclusive `flock` locks (held throughout the process lifetime):

```text
/data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_pair_parents_20260919/private/learner/PUBLISHER.lock
/data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_pair_parents_20260919/private/frozen/PUBLISHER.lock
```

`launch.py` is a guarded one-time bootstrap for both initially absent parents,
not a periodic restart command. A boot supervisor should manage the per-arm
foreground commands, preserve their `private/<arm>/STATE.json` files, and avoid
starting legacy `resume_parent.py` concurrently. A launcher timeout is not proof
of failure: inspect the recorded PID/start, lock and status before doing anything.
No native-control action belongs in that supervisor.

The preserved parent ceiling is **September 30, 2026 18:00 UTC**
(`1790791200`); this repair neither grants nor extends a lease. After that ceiling
the parent exits normally. Do not configure a supervisor to restart it forever
after expiry or after a native-identity binding rejection.

## Evidence and validation

`private/LAUNCH_*.json` records the real-host launch. Each arm's
`PROCESS_*.json` binds its fresh process, source hashes, environment names and
native identity. Provider attempts preserve INPUT, API_REQUEST, DISPATCH, raw
stdout, RESULT and stage/metrics receipts in unique new turn directories.
Read-only SSH failures preserve attempt artifacts and retry with backoff.
Provider retries are narrower: only an explicit HTTP 429 rejection permits
automatic redispatch, with 1/2/4/8-second backoff and at most five rejected
attempts before an operator-visible block. Timeouts, other HTTP failures,
unvalidated responses and interrupted unknown provider attempts block further
provider calls; observation of already queued messages continues. There is no
model or scaffold fallback. A completed provider response is persisted before
publication. A publication transport error now blocks redispatch until read-only
reconciliation by the operator. Read-only journal polling permits at most five
consecutive failures, then records BLOCKED_TRANSPORT and exits without more
error logs. Every failure immediately updates STATUS with its phase, health,
count, and disposition. Old archives are never rewritten.

`private/<arm>/DELIVERY_<id>.json` is written only after exact source/text-matched
INBOX registration, actual REQUEST rendering, and the corresponding committed
ACT response, stage and R184_ACT origin are bound. Mere publication is not
delivery, and delivered feedback is not evidence of causal improvement.

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s research_loop/workers/post_reboot_pair_parents_20260919 -p 'test_*.py' -v
```

[Builder] 2026-09-19 00:46 UTC: 13 scoped CPU regression tests passed before
parent launch. Real-host preflight at 00:56 UTC verified both exact natives and
hash-checked the first 160 resumed records per arm. This starts CPU parents only,
not a GPU science run. Live delivery receipts are required separately.

[Builder] 2026-09-19 01:00 UTC: 16 scoped CPU tests passed, including explicit-429
budget, unknown-attempt resume blocking, and no implicit timeout redispatch.
Only the CPU publishers were replaced to adopt this explicit follow-up: learner
326038/754381 → 337684/776822; frozen 326039/754385 → 337687/776823.
All initial publications, cursors, locks and native bindings were preserved.
`private/<arm>/RETRY_GUARD_ADOPTION.json` records the exact CPU-only transition.

[Builder] 2026-09-19 01:02 UTC: adopted the requested final 1/2/4/8-second
explicit-429 retry budget, finite read-only transport retries, immediate truthful
failure status, and no ambiguous publication redispatch. Quiet CPU handles only:
learner 337684/776822 → 345404/792480; frozen 337687/776823 → 345405/792480.
Both original queued publications and the exact native PID/start bindings were
retained. The adoption receipts have suffix `_bounded_transport.json`.
The subsequent 17-test suite includes an actual mocked service-loop regression
that stops after exactly five transport failures and leaves BLOCKED_TRANSPORT.

Run `python3 -B research_loop/workers/post_reboot_pair_parents_20260919/report.py`
on the real host for text-free `STATUS.json`, with queue, INBOX, rendered REQUEST
and committed ACT separately reported. `FIRST_PAIR_DELIVERY.json` is created
only when both initial delivery chains are proven and both publishers are live
with held locks. Re-running the report never starts a publisher or a native.

## Verified result

Both initial delivery chains were independently verified at September 19
01:08:30 UTC. See `TO_MAIN.md` and `FIRST_PAIR_DELIVERY.json`. The frozen parent
text rendered in REQUEST 3629 but did not survive compaction into ACT REQUEST
3638; its following ACT is event 3642. This is explicitly labeled a chronological
following-ACT proof, not direct ACT-prompt rendering or retention. Learner text
rendered in REQUEST 6261 and ACT REQUEST 6268, with ACT event 6272.
`verify_following_act.py` adds this read-only distinction without changing the
live parents, curriculum, native context policy, or original strict receipts.
Twenty scoped tests now pass, including the compaction distinction.

The subsequent requested public-summary and supervisor-registration follow-up
adds `SUMMARY.json`, `public/*_REQUEST_TO_ACT.json`, and `TO_AVERROES.md`.
These separate current parent from publication author, following ACT from
correction-visible ACT, and registration from enablement/adoption. Two exact
foreground entries are registered with Averroes's live supervisor but disabled
pending its1790791170 cap being reconciled with the existing requested pair
horizon1790791200. The supervisor acknowledged both names; no boot installation
is claimed. This explicitly requested registration adds only the two owned
manifest files outside this worker; no other supervisor source or entry changes.
The current suite has23 passing tests.

At01:22:51 UTC the cap mismatch was resolved by Averroes: both enabled entries
are `RUNNING_ADOPTED_NO_SIGNALS`, same current CPU/native identities, deadline
1790791200. See `SUPERVISOR_ADOPTION_RECEIPT.json`. Earlier disabled registration
receipts are historical. `PARENT_REBIND_CONTRACT.md` supplies main/Banach's
prospective exact-COMPLETE/LOADED, ledger-preserving, no-duplicate-send contract.
Its JSON metadata is inert; no actual rebind or live runtime change was made.
