# [Builder] 2026-09-17 18:12 UTC — exact C4 pre-load readmission

User explicitly assigned urgent C4 recovery with no additional Main gate after
Builder CPU/provenance checks. This is the same typed pre-load repair as the
working C1v2, not a new life, new architecture, wall change, guard relaxation,
request replay or retry of a consumed native dispatch.

Preserved original: `/localhome/local-rohing/orch_r179_context_C4_20260917_attempt3`.
Fresh attempt: `/localhome/local-rohing/orch_r179_C4_readmission_20260917_attempt1`.
Former actor/timer/supervisor/operator and drift PID1590413 are absent. Original
attempt contains only `ADMISSION.json`, `DISPATCH_ONCE`, `SERVICE_IDENTITY.json`;
there was no LAUNCH, native log, contained command or native model request.
The exact unchanged head is sleep36/optimizer3618, record4182.

- Working C1v2 basis SHA256: `d08f228dbd49e5ef506846b839132dcf5de8bc2518633bcb2e12e13849d98a9a`.
- C4 helper SHA256: `873ce150d12985fd7b9c73d050414f3cd5d0141c0a035d27316616d83dd6d63a`.
- Original operator SHA256: `e59649d3fd1fde7514f75e7af9d557d6f7f1ecee504403d47a610ccac5405b80`.
- Original retirement SHA256: `e154767127aa7a480ca31a5b74a130efb33e80bfe049a298a1a85074175c5db9`.
- Original refused admission SHA256: `5d51385785568ff775b7051dc7f3e86044c3c4f9067639dc5c925e31972c7ac3`.
- Exact saved record hash: `6f9cc2fdd4fbb032e07886c059f2075bdf2209da20fcd391702d0995e0df00b3`.
- Ready SHA256: `330fc9db4f03512d66f2dfa84f49491232576167b245f1d43b7a3a1f631e07b5`.
- Receiving state-proof SHA256: `53b9db5de993453ad4abd64d0c61539394df06649a46b4a8255094896d47749e`.
- Receiving device-proof SHA256: `9cb603e6e28a8ad563d7a0ae46c6eee94be672896021ec1b57daa27640032ecc`.

Six local and six receiving CPU tests pass, including marker-before-scan/
dispatch ordering and rejection of any prior native dispatch, changed boundary,
extra admission blocker or live former owner. Actual-source saved-state CPU
proof is PASS; optimizer3618 and full adapter/optimizer/RNG/history are restored
with CUDA uninitialized. Actual strict CPU service denies GPU minors0,1,2,3,5,6,7;
it imports no Torch and loads no model. New guard differs only in attempt path
and unique strict unit. Source, original model wall, invitations and guards stay
unchanged. Fresh final privileged admission remains mandatory and fail-closed.

`attempt/DISPATCH_ONCE` is created before scan/contained/native dispatch, as
required by the unchanged actual timeout-parent guard. Exactly one new attempt
is authorized by this logged Builder execution. No process is stopped by it.
At log creation, no new C4 model launch or loaded receipt is claimed.
