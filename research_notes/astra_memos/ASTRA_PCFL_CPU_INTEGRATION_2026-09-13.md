# PCFL CPU integration — September 13, 2026 12:15 UTC

Status: implemented partial CPU components; native experiment not ready.
This is simple engineering hygiene, not completion/enforcement of the deferred
final paper-grade C11 guard. Do not substitute synthetic fixtures for child
experience or silently choose the unresolved distractor topology.

## Main checks

Main independently ran:

- `python3 -B -m unittest discover -s tests -p 'test_pcfl_vertical_prepare.py' -v`:
  26 passed, 12.929s.
- `python3 -B -m unittest discover -s tests -p 'test_astra_pcfl_vertical_dev.py' -v`:
  22 passed, 14.185s, including 800 scripted tasks through real public scorers.
- `python3 -B -m unittest discover -s tests -p 'test_pcfl_vertical_train.py' -v`:
  35 discovered, 34 passed, one optional Torch numerical test skipped, 2.181s.

Initial pytest invocation failed because pytest is absent on this VM. No
dependency was installed; standard-library unittest executed the actual suites.
The writer's 200-update lifecycle test uses mocks, not numerical training.
The real unresolved-contract test rejects before encoding, output creation or
base-factory calls. Native-environment CPU numerical validation is still needed.

Tested source hashes:

| File | SHA256 |
|---|---|
| organism_v6/pcfl_vertical_prepare.py | e80266c4241116dc5701f8a394590645229ca089318903545ad064a1835e26a4 |
| tests/test_pcfl_vertical_prepare.py | e66832d1891e9f83b7591ee454c5d7d93a3d6007e1df2da4607d9d5d23038862 |
| gpu/astra_pcfl_vertical_dev.py | 026c6a8c50f551d874a605e1975f5fe2189643fcbd5e6694c0ad2d2fea0544b1 |
| tests/test_astra_pcfl_vertical_dev.py | 5a5e81688d2c9598d6cbc9d1e285b10d7258589e9d358ea509475b19fbf12af5 |
| organism_v6/pcfl_vertical_train.py | cf3cbe57886e9d283ac40760d129e0f3065def192064c846eefeaedb496fe68c |
| tests/test_pcfl_vertical_train.py | c4ba2b43d154057c2930b1977b2571468f70c91077f72e64a94e8a60f024377b |

Handoffs are archived in `receipts_20260912/`. Core ownership remains with
Beauvoir until its explicit EDITSTOP; do not silently pin an in-progress version.

## Prospective writer binding

For this DEV implementation, Main selects `pooled_response_token_mean` with
`four_unpadded_forwards_one_backward`: sum response-plus-EOS cross-entropy
over four independently forwarded sequences, divide by their combined active
target token count, and perform one backward and optimizer step. This makes
the ordinary batched masked-CE weighting explicit, without target-token
equalization or synthetic PAD examples. It is not a mean of sequence means.
The rule is fixed before any PCFL fit or readout; no historical result is
reinterpreted. Rank/base/provenance/parent visibility and thesis remain unchanged.

## Immediate queue

1. Finish core handoff and actual cross-component CPU checks. Tokenizer
   allocation is a separate deterministic offline module; complete substitution
   coverage and actual tokenizer files must be supplied, not fabricated.
2. Close concrete D/probe binding and the minimal runtime request expansion.
   A missing experiment definition is not waived by deferring the C11 guard.
3. Native-environment CPU-only objective/gradient validation; then real offline
   tokenizer qualification and a measured excluded-root zero-fit path when
   the world/runtime are defined. No inference was launched in this step.
4. Keep matched parenting and parent-removal tests separate: PCFL substrate
   progress alone does not establish parenting/internalization/H1/H2.

## Additive diagnostic, separate from PCFL

The archived read-only drift audit finds first logged loss divergence at step
10 for all seeds. Exact input IDs/masks/order, nominal config, recorded versions,
initialized LoRA and optimizer defaults match. Actual RNG/backend/checkpoint
execution parity is not established; there is no confirmed cause.
Audit SHA256: 88f49a658d2997b53231ff70f66e968c98e8395843fe63754fab26dac475dab4.

A bounded seed0 diagnostic is being implemented, not launched: first native
forward/backward under each frozen OLD/NEW MEMORY_ONLY path, no optimizer step,
no adapter save or readout. Record naturally seeded RNG, initial tensors,
losses, gradients and backend/checkpoint settings. Never force states equal to
hide a mismatch. If a frozen path cannot be intercepted faithfully, report
that gap. This does not repeat completed scientific fits or start a sweep.
