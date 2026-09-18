# Original C2: SymPy environment cause and tested repair option

## Cause
- Actual ACT interpreter: `/usr/bin/python3 -I /job.py`, Python3.12.3; external dispatcher/bridge uses `/localhome/local-rohing/v2/venv/bin/python` but does not lend that interpreter or its site-packages to the job.
- Pinned profile: `R125_CPU_CONFINEMENT_PROBE_V1`, sourceSHA9117c4d72cdbb700e351f4625e763f96cf94341a3cf6d2a2cf3445687bfae48b. It binds read-only `/usr` into a private root, clears the environment, uses isolated system Python and leaves `/localhome` unavailable.
- Both sympy and mpmath are absent from system Python. Host venv contains SymPy1.14.0 and mpmath1.3.0. The failed original receipt has returncode1/ModuleNotFoundError; this is not a fabricated tool result.
- No SymPy-specific package/import prohibition exists in the examined pinned request parser/dispatcher/profile. Sandbox isolation is intentional; the unmet rich-environment requirement is a dependency-exposure gap, not an intentional prohibition of symbolic mathematics. Host-package presence alone did not establish learner access.

## Smallest tested option
- Keep system Python3.12.3, `-I`, all existing privileges, device/network blocks and limits. Add only a SHA-manifest-pinned read-only SymPy/mpmath package bundle at `/opt/r188-c2-math` and a fixed launcher that adds that directory then executes unchanged `/job.py`.
- Bundle28,879,403bytes/1662files; no full host venv, `.pth`, native extension or GPU stack exposure. Only the CPU-profile source file differs in the staged source copy. No system installs/downloads.
- Retained bounds:128MiB memory, no swap,8tasks,25%CPU,15s runtime,8MiB scratch,1MiB file limit. No parent/model/prompt/state-parser changes.
- Six local command/provenance regressions PASS. Five actual confined probes PASS. Real isolated math imported both packages, solved a synthetic unrelated equation to7 and verified symbolic differentiation. Package writes rejected; Torch and host home unavailable.
- Synthetic `//` input remains a real SyntaxError/PROCESS_FAILED, stdout empty. No correction of C2 code and no replay of either original failed attempt. Every synthetic cgroup removed.

## Phase boundary and ready bytes
- NOT DEPLOYED. Original42–44 window is complete and pinned: complete44 record5337 at16:48:33.530 PDT, recordSHA30002558e2a5f620f642d5e7843e3f9eb7c41f7a174bf2d4a0f54345e077b078. Old profile, active bridge config and both failure receipts unchanged.
- Future use must be labelled `R188_ORIGINAL_C2_MATH_ENVIRONMENT_REPAIR_V1`, only after complete44, at a quiescent CPU-bridge boundary, and before its first affected ACT. Do not attribute subsequent changes solely to plasticity. Frozen copies excluded.
- Candidate remote root: `/localhome/local-rohing/orch_r153_cpu_smoke_20260917t2350z`.
- ProfileSHA81408d62fb926f4c61411084c56a7e08db842095dfc2b0d354b9b1cd95caa474; bundle manifestSHA38381e95b6d810e8fb40a1e3466a747e54673f2c205cf757efd029e624fe686d.
- Gate: `/localhome/local-rohing/orch_r153_cpu_smoke_20260917t2350z/gate`, digestc7821ed5b02651ed624c6dbe29a488bd15496440b59364e98e52ff2afe705e82.
- Actual RESULT SHA1cabe76f2e851fd9eb381bf0e36598566ff76424965d35b80cf8d1275c06fbbd.
- Ready bindings: `research_loop/workers/rohin174_parenting_20260917/node5/C2_ENVIRONMENT_REPAIR_READY.json`.
- Test evidence: `research_loop/workers/rohin174_parenting_20260917/node5/C2_MATH_CANDIDATE_TEST_1789689024811327844.json`.
- Preserved window/failures: `research_loop/workers/rohin174_parenting_20260917/node5/C2_ENVIRONMENT_PRESERVATION_1789689105123151174.json`.
