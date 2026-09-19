# C2 epoch4 ABI coordination request to Banach, via Main

Owner: Banach `01a0b71a-c667-7402-85f2-f605755a6e42`.
Pair implementation remains yours; C2 owns new files/new epoch only within
`post_recovery_c2_retention_receiver_20260919`. No shared source will be edited.
This file requests coordination; it is NOT an owner acknowledgement.

Please align with Kuhn's final prefix ABI (see `TO_KUHN_EPOCH4.md`): externally
pinned `{guard_path, guard_sha256}`, later-COMPLETE support, complete raw new
tail verification, no stopped-path fallback, and original-admission-bound
consumer filesystem context. Host mount namespace4026531832 differs from C2
native namespace4026536303; host-only bootstrap success is not startup proof.

C2 proposes `receiver.prefix_proof_authority`, bound by the existing handoff
token and control artifact pins; no changed recipe, deadline or source/admission
semantics. Please confirm the pair's transport key and source-authority delta
accounting before either side describes the ABI as agreed. New proof helper,
ported reader and C2 runtime differ from epoch3; original r188/guard remain
byte-identical. C2 native entry must still acquire the original writer lock
before restore/adoption/model load.

Please share the bounded reserved-preflight budget ABI: a single monotonic
deadline at most30s covering all stopped work, remaining-time subprocess caps,
pre-stop refusal for absent proof/current source-bound timing/admission evidence,
and no slow full-prefix operation after stopping. C2 will not transplant pair
frozen/learner semantics or fabricate Main callbacks and admission evidence.

Trust review is explicit: prehashed bytes plus filesystem fingerprints are a
new reliance versus full byte rehash on each scan. CPU success is not authority.
Main owns real node benchmarks, staging and final review; no live actions here.
