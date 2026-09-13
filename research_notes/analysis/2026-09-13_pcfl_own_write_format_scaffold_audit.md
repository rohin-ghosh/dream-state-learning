# Independent audit: PCFL own-write format scaffold and public-pair curriculum

Date: 2026-09-13  
Scope: read-only review of builder commits `69b760cd`, `cf572c73`,
`25c427c0`, `68c59c62`, `e37af6fb`, the frozen reducer, and the committed
SEQ-171/172 receipts. No runtime, test, model, tokenizer, fit, readout, or GPU
operation was performed.

## Verdict

**CONDITIONAL GO for the already narrow storage diagnostic.** The regex
constraint is scientifically acceptable as a disclosed external action-format
scaffold. It is not acceptable evidence that the child learned serialization
or formed connected memories autonomously. The public-pair and generic LINK
instructions make the later LINK rows a **controlled curriculum**, not free
connection discovery. The current reducer mostly says this correctly.

At the audit cut, no terminal v5 formation result, fit, or AUTH/C0 readout was
committed. SEQ-171 and SEQ-172 remain formation failures. Therefore this memo
audits the design and its permitted interpretation, not an acquisition result.

## 1. What the format scaffold actually does

`gpu/astra_pcfl_lf_actor.py` applies vLLM structured decoding with regex
`[^\r\n]+\n` to exactly 12 commitment calls: eight EVENT and four LINK calls.
It does not constrain the eight EXPLORE calls or either cold readout arm. The
regex contains no task identifier, expected row, receipt, port, node, answer,
or graph fact. The original grammar/provenance judges still reject a one-line
response with wrong semantic contents. Sampling policy and regex are pinned in
formation config/report and raw/render receipts.

That makes this a legitimate **format-assisted formation** diagnostic. It is
not ordinary unconstrained child generation: the constraint renormalizes
decoding over allowed continuations and externally guarantees a one-line LF
shape. The resulting LF is a joint model/decoder artifact even though it
appears in the model output token stream and the harness does not append it.
Claims must therefore say `external constrained-decoding assistance`, not
`the child learned/emitted the required format unaided`.

The scaffold does **not** cross the thinker/compiler boundary in the dangerous
post-hoc sense. The compiler still receives the exact admitted generation;
it does not append, normalize, repair, or synthesize a target, and prompt text
is not copied directly into the loss target. But the child-side behavior that
authors the target is externally scaffolded. Thus provenance is clean while
behavioral attribution is narrow.

## 2. Public pair and LINK-semantics instructions

Commit `cf572c73` publicly names the two already admitted EVENT handles that
the child must link. This does not disclose the expected LINK row, shared node,
receipts, later goal, or hidden outcome. It does, however, disclose a
substantive structural choice: which two experiences belong in the requested
connection. The pair was preselected because the two events form a valid
chain. It is therefore inaccurate to imply that the child selected or
discovered the connection.

Commit `68c59c62` additionally teaches the generic record algorithm: VIA is
first.GOT = second.AT, and EVIDENCE is the two receipts in order. That is a
reasonable schema/interface lesson after SEQ-172's failure, and it supplies
no instantiated answer. It further narrows the evidence, however: a successful
LINK is the child's exact, world-verified realization of an externally assigned
pair under a supplied schema—not autonomous induction of how experiences
connect.

This still does not mechanically cross the thinker/compiler line. The lesson
is visible during the child's wake/recording task, the child must produce a
valid row, the world admits it, and only that exact child continuation becomes
a target. Nothing is silently written by the compiler. It is closer to a
teacher-assigned exercise than to unparented self-reflection.

The four committed development outcomes must remain visible:

- SEQ-169/170: semantically correct EVENT payload, missing terminal LF.
- SEQ-171: eight EVENTs accepted; the first LINK was a different valid chain
  and failed the hidden preselected-pair contract.
- SEQ-172: eight EVENTs and two LINKs accepted; the third LINK used the wrong
  VIA field under the now-public pair curriculum.

These are development history, not matched controls and not evidence that the
new scaffold caused any later acquisition result.

## 3. AUTH_WRITE versus NO_WRITE_C0 symmetry

There is no unfair **readout-interface** asymmetry in the committed design.
Both arms use the same LoRA-enabled engine, base checkpoint, source-withdrawn
MEMORY_SYSTEM, roster, W0-W8 prompts, seeds, token limits, unconstrained
sampling, scorer, and 153-call schedule. AUTH_WRITE alone mounts the saved
adapter; that is the intended treatment difference.

There are nevertheless two interpretation limits:

1. NO_WRITE_C0 is not compute-matched. AUTH received 800 presentations over
   160 encodings and C0 received none. A difference establishes only the
   effect of this complete SFT write, not a unique effect of experiential
   content versus generic format/instruction tuning.
2. W8 holds out only wrapper wording. All 17 addresses and their exact target
   blocks trained through W0-W7. The endpoint is address-to-block acquisition
   under a paraphrased request, not new-fact or new-address generalization.

The strict primary can also mix two effects: learning opaque address/content
mappings and learning exact LF/record formatting. Exact opaque target IDs make
a large 17-address strict advantage impossible to explain by format alone,
but mandatory semantic reporting is needed to show whether any difference is
driven by the final newline rather than the stored payload.

## 4. Required report and secondary metrics

Keep the prospectively frozen W8 `strict_stop` endpoint unchanged:
exact service 17/17, AUTH >=15/17, C0 <=2/17, and paired difference >=13/17.
Do not promote a secondary metric after seeing results. Every report must also
show:

1. Ordered W8 `semantic_stop` vectors and totals for both arms beside the
   strict vectors. The existing semantic scorer covers exact payload without
   the final LF (and fenced renderings), so it exposes LF-only strict misses.
2. A raw descriptive split of strict misses into terminal-LF-only, other
   formatting, refusal, truncation, usable false row, and wrong content.
3. W8 results by query kind: EVENT 8, EVENTS_AT 6, LINKS_FROM 3. LINK results
   are especially important because those rows received the strongest
   curriculum scaffolding.
4. All per-address paired vectors and raw strings. Never treat 153 wrapper
   calls as independent experimental units.
5. W0-W7 strict and semantic results labeled repeated trained-surface
   diagnostics, not held-out tests.
6. Exact-child-service 17/17 as a target-integrity ceiling, never a model arm.
7. Actual loss/update trace and the fixed accounting: 12 child rows, 17
   address blocks, 20 scheduled blocks, 160 unique encodings, 800
   presentations, 200 updates, one life/root/fit/initialization.
8. The formation format policy, pair policy, generic LINK-semantics lesson,
   and every prior failed attempt in the provenance narrative.

The frozen reducer already records nearly all of this. Its result label
`FORMAT_SCAFFOLDED_DESCRIPTIVE_ONLY`, W8 query-kind splits, semantic vectors,
raw pairs, and explicit non-compute-matched/no-causal limits are appropriate.
The prose report should explicitly add that generic LINK field semantics were
supplied, because `link_pair_policy` alone does not fully communicate v5.

## 5. Exact claim wording

If the endpoint passes, the strongest defensible sentence is:

> In one development root, after external one-line constrained decoding and
> an externally assigned LINK-pair/schema curriculum, a rank-8 LoRA trained
> on 12 world-admitted child-emitted records reproduced X/17 exact stored
> blocks under an untrained request wrapper, versus Y/17 for the identical
> frozen base without the write. All 17 addresses and facts were present in
> training; this is a scoped cold acquisition diagnostic.

It must be followed immediately by:

> This does not test autonomous exploration or link discovery, learned
> serialization, address selectivity, unseen-fact generalization, graph
> traversal, action improvement, retention across later writes, compression,
> parenting, or the full Dream–LoRA–Think flywheel.

If formation succeeds but readout does not pass, say only that the fixed 7B
child completed the controlled record curriculum under the disclosed
scaffolds. Do not call formation a storage result.

## 6. Regex versus EOS-payload/exogenous framing

The EOS-payload design is scientifically cleaner for future paper-grade work.
The unconstrained child already produced the correct 90-byte semantic EVENT
payload twice; treating EOS as the child evidence boundary and adding a
separately receipted `HARNESS_RECORD_DELIMITER` preserves natural generation
and cleanly separates cognition from storage serialization. The regex instead
intervenes during every token decision and folds externally forced formatting
into the learned target.

That superiority does not invalidate this disposable diagnostic. The current
regex route is acceptable because it is target-free, fully receipted, applied
only during formation, and explicitly excluded from learned-format and
autonomy claims. It should not become the default final architecture merely
because it unblocks this one storage check. For any paper claim about the
child authoring its own experience, prefer exact EOS-terminated semantic
payload plus exogenous, separately hashed record framing.

## Bottom line

Proceeding with v5 can answer one small question: can a LOW/r8 LoRA cold-read
exact mappings compiled from world-admitted child records when the recording
interface and pair exercise are externally scaffolded? It cannot answer
whether the agent independently chose, connected, compressed, traversed, or
used its experiences. The design is fair at readout and does not silently
cross the compiler boundary, but its claim must remain exactly this narrow.
