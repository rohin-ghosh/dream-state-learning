# Galileo / Main — final parent-only patch review

September 17, 2026, 08:32 UTC. **REVIEW READY; NOT ADOPTED.** Main's latest
instruction requires fresh final closure/custody GO before another takeover.
Current parents continue. C1's authorized manual turn was published once separately.

## Exact final candidate

Use **attempt3 only** under this directory. Earlier attempts are preserved failures
or superseded staging, not approved deployments.

| Item | SHA256 |
| --- | --- |
| `attempt3/INDEX.json` | `7369963ca25e3963101f40cb5eadaa9360bbde68e0321d049f7c7e990b4cc88d` |
| `attempt3/CPU_GATE.json` | `4d1e31e1cda3d9e5d3198dcd73054f701b29e1dfc9318cfcb95807d4f27c82e0` |
| `attempt3/PARENT_GATE_DRAFT.json` | `de6cd7a162470292a346b17091a9dd46eac5b4323e10347ca3ebd0281d48422e` |
| `attempt3/EXECUTABLE_PREFLIGHT.json` | `fca459a7c3419e09c461c5233c447c82133661020d2dc820fb862f24d7b3e52f` |
| `gpu/orch_r168_community_prompt_patch.py` | `07797c9c4518d276a495c27b90ea99eda7130454e0bae19311dffb6deb967cf2` |
| `tests/test_orch_r168_community_prompt_patch.py` | `ec816af171103b0526c4a4f419e226e24ba68cbf0ef16cf7b445dff63d50223e` |
| Original community module | `d2ac945fdaaf3a5613d103e53c5c31c7e6c5cbe9d4133b2dfdb296aca49bb661` |
| Patched community module (both copies) | `ee9c0af3a618695f51eea13c56ba2a139827c5abf8bc161dac51834662c11367` |

Author CPU regression: **102 passed in 1.64s**, including actual original community
tests, policy tests, watchdog tests and patch tests. Main separately reports
44 CPU tests on these helper/test hashes. Tests use synthetic CPU fixtures,
not real provider output, delivered teaching, or scientific proof.

## Narrow executable delta

`PATCH_PROOF.json` proves the entire module AST unchanged after removing:

1. One final instruction-string append at the end of `community.prompt`.
2. Three exact cadence literals, 3 -> 2, in `build_config`, `validate`, and `tick`.

No change to response schema, provider, decoder, attribution, publication,
awaiting-render guard, attempt reservation, ledger, `decision()`, or native code.
Final instructions require one brief concrete attention/teaching invitation at each
scheduled opportunity, English own prose, 90-word cap, actual shown child sources,
and genuine outcome receipts. Earlier project evidence is explicitly labelled
earlier; no invented current memory, verifier outcome, or fallback message.

`object_id` explicitly denotes a stable **mismatch/step within a project**. Existing
IDs and exhausted counts remain unchanged forever. A different evidenced step may
continue the same project; renaming the same mismatch to reset its count is forbidden.
The third-turn release applies to that repetitive move, not mandatory project disposal.
Semantic identification remains parent judgment, not a new automatic equivalence proof.

Silence/provider/validation failures remain failures or SILENT, never manufactured
publication. Cadence2 improves opportunity frequency; it does **not** guarantee a
rendered turn every two boundaries under asynchronous provider timing/failure.
No delivered-floor compliance claim is made. Old misses remain old misses.

## Full isolated source closure

`attempt3/local_source` and `attempt3/remote_source` contain all 65 source files plus
two empty package initializers. The earlier gate had only 16 files and omitted 49
transitive imported dependencies. They are now copied and pinned, **not modified**.
`ORIGINAL_REMOTE_VERIFIED.json` records original remote hashes and 979,113 bytes
actually read through `gpu/ovx3_ssh.sh`; old gate hashes were checked where supplied.
Newly pinned dependencies are explicitly listed, not falsely described as previously
independently pinned. Original local/remote dependency differences remain distinct.
Only the community parent module differs from each respective original closure.

Standalone `/usr/bin/python3` with cwd/PYTHONPATH restricted to the new local source
imports successfully and validates all five cadence2 configs. No provider/GPU calls.
The gate remains `AWAITING_MAIN_BOUND_GO`, and the remote source is **not uploaded**.
Proposed new remote parent source:
`/localhome/local-rohing/orch_r168_parent_prompt_final_20260917_attempt3/source`.
Native/guard source paths remain untouched. Each parent config changes only its
own `source_root` and `cadence_responses`; provider identity, child root, original
wall, programme, principles, output schema and old ledger remain preserved.

Attempt1's real-prompt reconstruction assertion failed on JSON key serialization
order after reading the sorted SOURCE artifact, not on instruction bytes or event
content. Attempt2 preserved the recorded payload and proved semantic equality but
failed standalone import due to missing original-gate transitive imports. Attempt3
addresses both; `C1_REBUILT_PROMPT_NOT_DISPATCHED.json` is clearly a CPU reconstruction,
not a provider request or a second dispatch of attempt96.

## C1 manual action and current custody

`MANUAL_C1_CUSTODY_ATTEMPT2/PUBLICATION.json`:

- Published **08:26:30 UTC**, author Main, speaker Astra, type MANUAL_TRAIN_PARENTING.
- Inbox ID `229eb2802b92494e82a346dd0287e666`.
- Inbox SHA `d8434c2e3542edaf6a29024cf767ca492b42490ec821a618f1d18877a584bdc6`.
- Publication receipt SHA `0cbd94ae5401b086c7697da88746aaf3e0cbfec1c3c15047b8488236e3a086a3`.
- Exact Main text and TRAIN source basis in `MANUAL_PUBLICATION_INTENT.json`.
- Original C1 attempt96 remains SILENT, hash `d373bc7c217234ce25eabd74095b9813d3852fb6e4c8323d35ed7762ceb85de8`.

First custody attempt deferred on an owned parent subprocess; watchdog CONT ran,
and no publication intent or parent termination occurred. A fresh clean-gap custody
attempt then proved all prior publications rendered, preserved every attempt file,
proved old parent pidfd exit and exclusive lock, published once, released lock,
and resumed **the same config/argv/output** as PID456729/start174060844. Native
PID2578597/start14835459 was verified alive and never signalled. Actual lifecycle
CPU receipt: `MANUAL_C1_CUSTODY_ATTEMPT2/CPU_GATE.json`, 41 tests PASS.

Latest observed **08:31:31 UTC**: manual publication not yet ingested or rendered.
Verified TRAIN suffix3423..3497 remains in sleep UPDATEs; latest REQUEST is3433,
segment95, preceding the manual publication. This poll read12,434,171 bytes, not
an inherited process read counter. Relative to the 08:29:17 suffix, only seven
UPDATE records / 6,745 additional journal bytes appeared; both polls reread their
bounded anchor suffix, so actual I/O was12,427,426 then12,434,171 bytes.
Receipt: `MANUAL_C1_CUSTODY_ATTEMPT2/RENDER_OBSERVATION_1789633891909373995.json`.
The suffix is chained to Main's exact record3423 bytes; not a fresh whole-history audit.

## GO / adoption seam

1. Review exact attempt3 closure/config/patch/CPU references and issue new bound GO.
2. Stage the remote closure create-only and verify all pins, without touching old source.
3. Recheck current child identity, live parent PID/start/config/source, unchanged wall,
   no competing scanner, and successor executable/gate/transport before any signal.
4. Keep watchdog-backed quiesce; busy/uncertain means CONT and defer. No provider interruption.
5. Preserve all `parent_*` bytes and reserved cursors in a fresh output; no old BINDING reuse.
   For C1 additionally preserve this external manual-publication identity: **wait for
   verified rendering before its next takeover**, unless Main separately authorizes
   an explicit pending-manual handoff. It is not a provider ledger row and must not be forged as one.
6. Only after clean parent exit/lock release start the exact gated successor, one leader.
   Report new PROMPT, provider RESULT/publication, and rendered REQUEST independently.

No direct agent-messaging interface is available in this session; Main can direct
Galileo to this shared review path. R164 remains parked; no other live roots are in scope.
