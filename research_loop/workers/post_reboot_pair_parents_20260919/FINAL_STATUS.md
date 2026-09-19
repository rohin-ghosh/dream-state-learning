# Pair restoration and future-only rebind handoff

Real-host verification: **2026-09-19 01:26:52 UTC**. Both CPU/model parents are
restored, live and exclusively locked; no provider/task blocker is reported
in this snapshot (both are OBSERVING). Model/scaffold, learner/frozen policy,
all-authentic rows and sealed-score blindness remain unchanged.

| Arm | Live CPU PID/start | Unchanged ovx4 native PID/start | Supervisor |
| --- | --- | --- | --- |
| learner | 345404 / 792480 | 493500 / 10070880 | RUNNING_ADOPTED_NO_SIGNALS |
| frozen | 345405 / 792480 | 471737 / 9987073 | RUNNING_ADOPTED_NO_SIGNALS |

Supervisor399392/start891869 has both exact entries **enabled and adopted**
through `1790791200` (September 30, 2026 18:00 UTC). This is foreground
supervision, not OS boot installation: `boot_enabled=false`,
`installation_status=BLOCKED_UNINSTALLED`. Averroes handoff: `TO_AVERROES.md`.

## Actual publication and delivery evidence

| Arm | Queued | Canonical INBOX | Rendered REQUEST | Verified following ACT | Literal ACT-prompt exposure |
| --- | --- | --- | --- | --- | --- |
| learner | 4 | 4 | 3 | 3 | 3 |
| frozen | 4 | 3 | 3 | 1 | 0 |

Counts are the separate receipt observations at the stated snapshot, not claims
that unobserved work failed or that every later ACT has been independently audited.
Latest actual model is unchanged `openai/openai/gpt-6-astra` on both arms.
Latest learner publication `641e47cf4df4411993711c6048eb4e36` was queued at
01:23:49.098738 UTC by current CPU345404; INBOX6440 is recorded and its rendered
REQUEST/ACT are not yet recorded. Latest frozen publication
`b1f1dbc20f3a49ad9483fe5fd564a047` was queued at01:25:36.578323 UTC by current
CPU345405; its canonical INBOX/render/ACT are not yet recorded.

First restored learner chain: INBOX6259 -> rendered REQUEST6261 -> ACT
REQUEST6268/RESPONSE6269/COMMITTED6270/STAGE6271/event6272; direct correction
exposure true. First restored frozen chain: INBOX3619 -> rendered REQUEST3629 ->
ACT REQUEST3638/RESPONSE3639/COMMITTED3640/STAGE3641/event3642; following ACT
proven but correction exposure false after compaction. Zero direct exposure is
not zero restoration; neither chain proves retention, uptake or improvement.
Historical first publication authors326038/754381 and326039/754385 are not the
current CPU parents. Public receipts retain this distinction.

## Future receiver rebind, not an action now

`PARENT_REBIND_CONTRACT.md` and `PARENT_REBIND_CONTRACT.json` bind a single future
arm/old native/actual receiver LOADED/preserved ledger/new CPU-owner transaction.
Require later explicit main activation, bounded deadline, exact COMPLETE and
checkpoint/state parity, real old-native exit, handoff/source-adoption evidence,
fresh verified receiver identity and sole publisher ownership. Banach's
`PAIR_RETENTION_PARENT_DEPENDENCIES_V1` owner fence/zero-inflight/ledger-pin proof
must precede native handoff and remain valid through post-LOADED rebind.

Carry all parent ledger state and original publication IDs; never reset the
cursor/stage or replay an opening or already-sent correction. Reconcile known
remote receipts read-only. Unknown dispatch/provider outcomes stay blocked;
only the unchanged bounded explicit-429 policy permits provider retries.
No actual fence, dependency proof, receiver dispatch or rebind was performed.
Current parents still correctly refuse a changed native. The future binding
adapter and its tests remain separate work requiring explicit activation.

## Stable foreground commands and nonsecret environment

Working directory: `/data/home/rohing/dream-state-orch`.

```sh
/usr/bin/python3 -B /data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_pair_parents_20260919/parent_service.py --arm learner
/usr/bin/python3 -B /data/home/rohing/dream-state-orch/research_loop/workers/post_reboot_pair_parents_20260919/parent_service.py --arm frozen
```

Original launch environment: `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`,
`CUDA_VISIBLE_DEVICES=""`; provider credentials are inherited, never persisted
in manifests or printed. Exclusive locks: `private/learner/PUBLISHER.lock` and
`private/frozen/PUBLISHER.lock`. Exact registered manifests are in
`../post_reboot_services_20260919/services.d/pair-curriculum-learner.json` and
`../post_reboot_services_20260919/services.d/pair-curriculum-frozen.json`.

## Receipts within this worker

- `FINAL_ADOPTION_VERIFICATION.json`: fresh real-host process/lock/native/registry check.
- `SUPERVISOR_ADOPTION_RECEIPT.json`: original confirmed adoption; earlier registration-only status is historical.
- `public/learner_REQUEST_TO_ACT.json` and `public/frozen_REQUEST_TO_ACT.json`: first delivery, exposure distinction, latest actual model publications.
- `SUMMARY.json` and `STATUS.json`: refreshed pair evidence with queue/render/ACT separate.
- `TEST_RECEIPT.json`: 26 passing current recovery/inert-contract tests; no claim of future rebind integration tests.
- `PARENT_REBIND_CONTRACT_RECEIPT.json`: contract/source/test/adoption hashes, with activation and actual rebind false.

This finalization does not change live parent code, native bindings, weights,
learning, leases or old archives. No signals, native/parent restarts, duplicate
launches, commit or push were performed during finalization.
