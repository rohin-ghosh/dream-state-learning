# Route actual release and terminal lifecycle — 2026-09-15

Native observation: 2026-09-15T12:20:36Z through `gpu/ovx3_ssh.sh`.

- F1 root `/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_0_attempt1`: `TERMINAL.json`, `SHARED_TERMINAL.json`, and root `CRASH.json` all absent.
- A1 root `/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_4_attempt1`: the same three files absent.
- Keep the actual legacy `ROOT/TERMINAL.json` lifecycle. The frozen successor `gpu/orch_r111_route_pair_shared.py`, SHA256 `c385db4fe1920ba645af8816327ddcbaebe10da3d1f42f3318330fa052ecb7ae`, writes this file at line763 and checks it at line1018. No `SHARED_TERMINAL.json` writer is claimed or introduced.
- Both brokers must watch their own root's `TERMINAL.json`, explicitly bound to the actual successor PLAN and frozen executable. Hubble owns F1 broker; route owner coordinates A1. No historical terminal is ignored/deleted. Recheck absence immediately before activation; if one appears, stop activation and preserve it for explicit lifecycle reconciliation.
- Original release controller errors/logs and uncharged administrative SIGTERM diagnostic captures remain preserved. The controllers exceeded their 30-second actor teardown wait; later exact identity absence/locks/unchanged boundary reconciliation certified release, without another signal or native replay. Exact exit timestamps are unknown; certificate verification timestamps are not exit claims.

## Actual releases available to Main

F1 completed cycle6, next cycle7; predecessor actor356208/supervisor356167 absent. Charged379native/60parent; latest actual1125optimizer steps,68231child tokens,20351anchor tokens. Parent wait120seconds unchanged.

- Release `/localhome/local-rohing/orch_r111_boundary_candidate_20260915_v2/readiness/F1/RELEASED.json`, SHA256 `ceac2c11fda32b0619c8473dec1d42305495ef6bd47ea07699ef424a9092f022`.
- Root `R118_SHARED_HANDOFF_BRANCH.json`, SHA256 `ca1d25f89eaa7f2b473d8418ef3430a5fe3a7cdcc93f93ecdc1aa400706a15e4`.
- Root `R118_SHARED_RELEASED_ADOPTION_INPUTS.json`, SHA256 `c74a3ef5c09ff9fcb98972defa97e83ed9c67510a1a26209e74be1ece50ae10d`.
- Cycle6 checkpoint manifest SHA256 `084f62110ca5e42fb55145675538f6f88e10ce684a9c8847c49d1c858df7d264`; optimizer SHA256 `848fc7a4488b37d04a64a145c027be8ecb49281767e2577024f76c3957748b53`.

A1 completed cycle3, next cycle4; predecessor actor459948/supervisor459875 absent. Charged194native/28parent. Its optimizer is preserved, never merged into F1.

- Release `/localhome/local-rohing/orch_r111_boundary_candidate_20260915_v2/readiness/A1/RELEASED.json`, SHA256 `0feb3157966745cff76cf99e0a03af10bdde55d229df9041ef4a8971f8641901`.
- Root `R118_SHARED_HANDOFF_BRANCH.json`, SHA256 `c9e47036c943138444b1a9c01f8fb67540f34ceee9eea077d0189e947f9a9ec6`.

Main common ADOPTION/CONFIG/INITIALIZED absent at this observation. No successor launched yet; no initialization by route owner. Main can adopt immediately when the remaining peer certificates arrive. No F1 release ETA remains: actual certificate exists now.
