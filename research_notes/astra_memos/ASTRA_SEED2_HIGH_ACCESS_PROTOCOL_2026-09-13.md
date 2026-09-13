# Seed2-high checkpoint acquisition/access diagnostic

Frozen September13 08:38UTC before native forward passes. Exploratory,
checkpoint-specific diagnostic motivated by preserved seed2/high-LR fit2's
lower aggregate training loss, not a selected confirmatory result or new fit.

Reuse SEQ136's exact measurement algorithms on this DIFFERENT completed
checkpoint. OFF, fit1 and fit2_PROMOTE each cold-load the frozen base and,
where appropriate, the pinned saved LoRA. Each scores16exact TRAIN prefixes
and16READOUT prefixes against both original legal actions:64teacher-forced
candidate forwards/state,192total, zero updates. Retain target masks/EOS,
unequal12/14-token lengths, first-divergent-token and full-string likelihood
metrics, exact ties, and old/new splits. HF forced-candidate choices are NOT
vLLM greedy successes; historical greedy reports remain separate. This test
does not fill the missing exact-TRAIN native greedy endpoint.

Question: does the lower fit loss correspond to stronger keyed candidate
discrimination on exact TRAIN, and does it transfer to READOUT wording?
Compare each fitted state with OFF on the identical cases. Strong TRAIN but
weak READOUT motivates prompt-access diagnosis; weak first-decision margins
despite low suffix loss motivates association-acquisition diagnosis. Neither
pattern alone identifies capacity or proves a general learning failure. No
posthoc tie threshold, replacement target, answer edit or checkpoint selection.
Report all states/metrics, including failures; no automatic scientific pass.

Original plan74569b1e8c3e0330e0c4f387120fedd4d9f71406366d8b5459088a35ab1a3593;
fit2candidate8e79df460e52e94b342de285bcc85ef69cc5fb468a8904d443c665af37bc8ff4.
New probe d319c53aeeaf45743d77e87af30eafe1ae8e2f111d35e440c8c0b1402b4b2525
changes only bindings, seed2/LR checks and explicit seed forwarding to the
original full training-encoding replay. Algorithms remain AST-identical.
Main40CPU tests PASS4.956s; native CPU tokenizer replay passes32cases,
caseSHA4644578efc36a24f181a1adffd31fabdcac07e936723b435c72b532c87eeea21,
lengths12/14, zero forwards/updates. Prior diagnostic is not rerun unchanged.

New node3GPU3 root l2_access_high_seed2_20260913_attempt1,1200scontroller cap
including cleanup/reduction, about5–8minutes expected from prior264.7s;
0.334GPU-hour maximum. Require currentboot247596ab-08fe-436a-abbd-b8494c19e5d7,
explicit leaseend1790391780 (September26 03:03UTC / September25 20:03Pacific),
freshqueue/reservation/all-process XML vacancy. Initial VM20s read-only probe
transport timed out; original probe absent afterward, later targeted identity,
all-process XML, queue and reservations all passed. No infrastructure repair,
foreign kill or reboot is licensed. Perworker checks/owned cleanup remain.

Retain original captures and new outputs separately. Main alone launches and
inspects; no new fit, parenting, H1/H2, clean ancestry or mechanism promotion.
