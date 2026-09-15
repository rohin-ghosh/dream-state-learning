# Prospective parent serialization repair — September 15, 2026

## Diagnosis, not retrospective relabeling

Actual archived SYSTEM receipts already stated the hard lane caps. F3 C042_E1_OPEN_PARENT (SYSTEM SHA256 `1a098280cb2c34687a2e8cff42dde6b9167072da3e10b462daa91867b1cba17b`) and F4 P0083 (`5c2b5c855bd90efecc52c82f4121e2c72e87d0859f4907b0d6abfbc929a262e8`) remain MISSING `lane_guidance_limit_no_cropping`. Neither SYSTEM stated the exact accepted class-character pattern. Prior observations included 203/206-word CODE and 93-word GRID guidance; those exceed the unchanged 200/90-word caps. A prompt clarification does not guarantee future compliance.

## Exact prospective change

The mandatory SYSTEM transport contract now specifies uppercase ADD/STOP/SHIFT, JSON null or a 1–80-character ASCII class matching `[a-zA-Z0-9 _-]+`, exact four keys, and nonempty guidance/rationale. It instructs the parent to count whitespace-separated guidance words and leave room under the existing cap. This contract follows any optional asynchronous head note and immediately precedes the untrusted TRAIN transcript. It is also present without a head file or NEXT_GUIDANCE. The fixed principles, mutable Fn files, visibility, validators, thresholds, LOW effort, branch locks, lane-deadline-minus-30 cutoff, caps and actual terminals are unchanged. No cropping, credential operations, retries, failed-claim conversion, or child/GPU changes.

`python3 -m unittest discover -s tests -p test_orch_r110_claude_broker.py -q`: **99 local + 99 immutable-native PASS**. Tests cover all-family caps, absent prompt/head cases, ordering after head note, exact metadata syntax, unchanged boundary validation and rejection at observed overflow lengths. Overflow fixtures are synthetic length regressions, not manufactured provider captures.

## Actual deployment and first delivery

Native snapshot: `/localhome/local-rohing/orch_r124_parent_transport_contract_20260915_v1/source`.

| Branch | Settled broker PID | Historical claims preserved at handoff | Binding |
|---|---:|---:|---|
| F1 | 3825740 | 77 | Existing R121 independent terminal |
| F2 | 3825744 | 68 | Existing R123 recovery terminal, unchanged |
| F3 | No restart | 205 observed before migration | Actual GUARD_TERMINAL present; requires owner successor |
| F4 | 3825784 | 97 | Existing R119 grid independent terminal |

F1/F2/F4 were migrated only at idle boundaries, with exact predecessor identity, no unpublished claims, exclusive branch-provider lock, settled PPID1, and every historical claim-file hash preserved. Latest F2 R123 predecessor3714429 was used, not the retired F2 epoch. Native `F1/READY.json`, `F2/READY.json`, and `F4/READY.json` beneath the snapshot runtime bind current identities and unchanged real terminals. F3 terminal SHA256 is `409b5f0e4ed36f7f5728125c6b1baf8771fc0397602f22fb9635e724287e33ac`; no synthetic terminal bypass or new lifecycle was invented.

**F4 P0098 COMPLETE**, finished **19:06:07.554955 UTC**, actual `claude-fable-5-1`, 21.153 seconds elapsed, 54 guidance words. New policy SHA256 `56ef813a745eb862fbf020e976f9d34ba27fbae4f4b0dea444316d56caf8215e`; SYSTEM `ee11579ea0928d9ddd64cdd187a6dc0feba8b4ffcdee1000b3bdfa5fd2c4e5bf`; transport contract `d7210e61c95a04c9254418ecbce059a50637857acb30585c14d6f2c880bc28cd`; published response `2a1ab81228060a65b1ff04d186c7c989c7f321399235f9259d1a7fe72aefa980`. Exact contract inclusion and policy hash were independently verified, as were all 11 node-local transcript file hashes. Native received/applied files exist, but their application joins were not audited here: consumption remains UNKNOWN in this compact report. Publication is not evidence of learning.

At the immutable 19:06:12.961434 UTC cut, F1/F2 had no new requests in this source epoch; F4 had one new claim and one COMPLETE, no MISSING/SILENT. These are bounded first-delivery observations, not a throughput or fleet-wide success claim. Raw prompts, outputs and credentials stay off the VM; only compact references and counts are published. Main alone handles Git.
