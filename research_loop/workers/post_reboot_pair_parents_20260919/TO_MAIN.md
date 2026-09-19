# Pair parents restored — September 19, 2026 01:08:30 UTC

**Both actual model parents are publishing. Both first INBOX → rendered REQUEST
→ following committed ACT chains are verified.** Both have also produced a
second model-generated publication. These are real provider results, not
operator-authored substitute turns. The parents remain blind to sealed scores.

## Fresh processes and unchanged natives

| Arm | Current CPU parent PID / start ticks | Native PID / start ticks | Held lock |
| --- | --- | --- | --- |
| learner | 345404 / 792480 | 493500 / 10070880 | private/learner/PUBLISHER.lock |
| frozen | 345405 / 792480 | 471737 / 9987073 | private/frozen/PUBLISHER.lock |

The real VM host processes, exact argv, lock contention, open lock descriptors,
and remote native identity were checked at the stated observation. Do not use
sandbox `ps` to infer their absence. The first CPUs were 326038/326039; two
CPU-only rotations installed the explicitly requested failure-handling guards.
There were **zero GPU-native signals or restarts**. All queued deliveries and
cursor state survived those CPU rotations without republishing the first turn.

## First delivery evidence

| Arm | Publication ID | Queued UTC | INBOX | First rendered REQUEST | ACT REQUEST → RESPONSE → COMMITTED → STAGE → ACT |
| --- | --- | --- | --- | --- | --- |
| learner | a7e9f099211c4f5992a85f5911a3efd5 | 00:57:27.504894 | 6259 | 6261 at 01:04:30.012692 | 6268 → 6269 → 6270 → 6271 → 6272 |
| frozen | eabd8d4ebb3843dc9c911614f707fe6d | 00:57:38.959421 | 3619 | 3629 at 01:03:24.745856 | 3638 → 3639 → 3640 → 3641 → 3642 |

Learner ACT response completed at **01:05:07.247580 UTC**; frozen at
**01:06:14.233347 UTC**. The initial exact rendered messages begin by
acknowledging the publisher gap, then give individual feedback and a concrete
arithmetic task. Raw provider envelopes, usage, prompts and publications are
preserved privately in the new worker.

**Important frozen distinction:** the new parent text was exactly rendered in
REQUEST 3629, then omitted from ACT REQUEST 3638 after compaction. Its source
remains in canonical history. The frozen receipt proves the rendered-request
and following-ACT sequence, **not** direct parent-text rendering in the ACT
prompt, retention, uptake or causal improvement. Learner's ACT REQUEST also
contained the exact parent text. No native context policy was changed to force
a stronger result.

`FIRST_PAIR_DELIVERY.json` is the immutable paired receipt. Its per-publication
fields explicitly distinguish `ACT_request_contains_parent_text` true/false.
Private `FOLLOWING_ACT_*.json` proofs bind provider-response bytes, publication,
INBOX, request/response pending hashes, committed source, stage and ACT origin;
`CHAIN_SOURCE_*.json` preserves the independently re-read canonical evidence.
The learner additionally has the live service's stricter `DELIVERY_*.json`.

## Boot-supervisor start contract

Working directory: `/data/home/rohing/dream-state-orch`.

```sh
/usr/bin/python3 -B /data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_pair_parents_20260919/parent_service.py --arm learner
/usr/bin/python3 -B /data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_pair_parents_20260919/parent_service.py --arm frozen
```

Nonsecret environment: `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`,
`CUDA_VISIBLE_DEVICES=` (empty), `HOME=/home/rohing`. Securely inherit the
existing `NVIDIA_API_KEY`; no key values are in argv or these receipts. Preserve
the existing provider config, SSH access, and per-arm `private/STATE.json`.

Absolute lifetime-exclusive locks:

```text
/data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_pair_parents_20260919/private/learner/PUBLISHER.lock
/data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_pair_parents_20260919/private/frozen/PUBLISHER.lock
```

Use one foreground service per arm; the one-time `launch.py` bootstrap already
ran and should not be repeated. No implicit native adoption: a changed native
PID/start, boot, command, root or journal fails closed. The inherited parent
ceiling remains September 30, 2026 18:00 UTC; do not restart-loop after expiry.
No lease was purchased, renewed or extended.

## Failures and policy preservation

Initial provider failures were explicit HTTP 429 shared-token-rate rejections;
both succeeded on the unchanged `openai/openai/gpt-6-astra` model. No chosen
model or scaffold was lowered. The current service permits only explicit 429
provider redispatch, with 1/2/4/8-second waits and a five-rejection bound.
Ambiguous provider outcomes block new provider calls. Ambiguous publication
transport outcomes require read-only reconciliation, not automatic redispatch.
Read-only polling stops after five consecutive transport failures. Every error
immediately updates truthful STATUS, including phase and block disposition.
The current parents are not blocked; there is no continuing failure-log loop.

The archived parents' own final errors were SSH timeouts at September 18
22:25:44 (frozen) and 22:30:10 (learner), before the reported 22:50:45 reboot.
This repair does not incorrectly attribute those earlier errors to the reboot.

All code, tests and receipts are under this new worker. Old archives are
read-only, no semantic training-row exclusion was added, and no native,
learning recipe, weights, base model or lease was changed. No commit or push.
Twenty scoped regression tests pass; see `TEST_RECEIPT.json`. Independent
following-ACT verification is read-only and does not alter the running parents.

For a fresh host status, run `python3 -B
research_loop/workers/post_reboot_pair_parents_20260919/report.py`. This writes
`STATUS.json` only and never starts or signals a process. No immediate operator
action is required for delivery; main can now add the boot supervisor using
the contract above.

## Fresh summary and Averroes registration — 01:15 UTC

`SUMMARY.json` and `public/learner_REQUEST_TO_ACT.json` /
`public/frozen_REQUEST_TO_ACT.json` now explicitly separate following ACT from
correction-visible ACT, and current live CPU from the historical publication
author. Frozen following ACT is proven despite first ACT-prompt exposure false;
zero direct exposure is not a failed restoration.

At 01:15:14 UTC both current parents remain live, locked and OBSERVING:
learner345404/start792480 and frozen345405/start792480. Actual publications:
learner3, frozen2. Latest current-author model results are learner
`ef1319531b204597b4615a253d061d89` at01:14:38.255862 UTC, and frozen
`903b89c7be6b42fe99df0ab627bfe1e9` at01:06:54.442413 UTC. Both use the unchanged
model and policy. No native changes.

Per the explicit follow-up registration request, two exact foreground entries
were added atomically to the services registry, without altering supervisor
code or old archives. The existing global supervisor cap1790791170 rejects
the requested existing pair horizon1790791200. Therefore the named entries are
registered **disabled pending Averroes's cap reconciliation**, not falsely
claimed adopted. Supervisor311614/start717203 acknowledged both names at
01:15:12 UTC. Its generic `DISABLED_AWAITING_OWNER_ARGV` label does not mean argv
is missing: both full manifests, source hashes and lease evidence are supplied.

Exact registration paths and action: `TO_AVERROES.md`.
Receipts: `SUPERVISOR_REGISTRATION_RECEIPT.json`, `SUPERVISOR_REGISTRY_ACK.json`.
Main/Averroes must reconcile the cap and enable/adopt the existing healthy CPUs;
do not shorten the pair horizon or restart them. Boot installation remains
BLOCKED_UNINSTALLED. Twenty-three scoped tests pass after summary/registration
regressions; `TEST_RECEIPT.json` is refreshed.

## Enabled/adopted and future-only rebind contract — 01:22 UTC

Averroes corrected the supervisor ceiling. Both exact manifests are now enabled
through1790791200 and supervisor399392/start891869 reports
`RUNNING_ADOPTED_NO_SIGNALS` for learner345404/start792480 and
frozen345405/start792480, confirmed on the real host at01:22:51 UTC.
`SUPERVISOR_ADOPTION_RECEIPT.json` and refreshed `SUPERVISOR_REGISTRY_ACK.json`
are authoritative. The earlier disabled-cap status is historical. No current
parent or native was restarted or rebound; no duplicate was launched.

Main/Banach contract: `PARENT_REBIND_CONTRACT.md` and inert
`PARENT_REBIND_CONTRACT.json`. It binds one future arm/old native/actual LOADED
receiver/ledger/CPU owner; requires exact-COMPLETE, handoff, source epoch and
fresh LOADED identity; preserves every parent state and publication identity;
reconciles already-sent and ambiguous turns without duplicate sends; and keeps
following ACT distinct from ACT-prompt exposure. A later explicit activation and
separate tested binding adapter are still required. This document authorizes
no actual rebind, native action, or scientific-policy change.

## Final confirmation — 2026-09-19 01:26:52 UTC

`FINAL_ADOPTION_VERIFICATION.json` rechecks real host processes, exact enabled
manifests, native identities, held locks and the live supervisor heartbeat.
Both arms remain `RUNNING_ADOPTED_NO_SIGNALS`. See `FINAL_STATUS.md` for current
publications, separate queue/render/ACT observations and receipt paths.
Banach's required pre-handoff owner dependency proof is now explicit in the
future-only contract; no fence or dependency proof is manufactured now.
The refreshed `TEST_RECEIPT.json` covers 26 passing current/inert-contract tests,
not the unimplemented future binding adapter. Boot installation remains blocked.
