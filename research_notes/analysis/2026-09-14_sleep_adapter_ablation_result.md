# Sleep-note adapter ablation: fixed prompts, no admitted material

2026-09-14 UTC. Independent bounded read-only audit through
`bash gpu/ovx_ssh.sh`. Only this memo is written. No model/tokenizer loads,
generation, GPU experiment, fit, rerun, remote mutation, or additional custody
collection was performed. Other live jobs were left untouched.

Evidence root **R** is
`/tmp/astra_adult_cycle2_20260914_attempt1/CUE_REPLAY`.
The completed OFF diagnostic is `R/recollect_base_diagnostic`; archived ON
comparators are `R/recollect_rehearsal` and `R/recollect_revision`. Prior context
is recorded in the two-recipe and parent-feedback-revision result memos.

## Strongest supported conclusion

**Disabling the adapter changes the outputs on these two exact posed prompts,
but does not provide a clean successful-contract control. Neither OFF output
is admitted training material. The result cannot establish an adapter-specific
cause of the original whole-note failures.**

OFF rehearsal supplies four exact W-labelled EVENT records and four exact
W-labelled EXPLORE actions. It removes the ON answer's ambiguous interepisode
travel bridges and trailing NONE, but retains uncited factual prose outside
those labelled records. OFF revision outputs exactly `NONE`: syntactically a
standalone abstention, not evidence that supported observations are absent.
All four public observations exist, and repetition is explicitly allowed.

The adapter-disabled base **did not collect these experiences**. Its first-person
wording is a response to the inherited prompt, not a provenance fact. Both OFF
outputs are explicitly `EXCLUDED_FROM_TRAINING`, with
`own_experience_actor=false`. They are not child targets, an alternate clean
lineage, evidence of useful extraction, or a parenting/learning success.

## Per-prompt comparison and visibility

| Condition | Archived ON | Diagnostic OFF |
|---|---|---|
| Rehearsal: calls / input / emitted IDs | 1 /1735 /171 | 1 /1735 /373 |
| Rehearsal: output | Four cited transition descriptions, uncited opening, ambiguous travel bridges, trailing NONE | Four W-labelled EXPLORE actions and four W-labelled exact EVENTs; uncited prose; no trailing NONE |
| Rehearsal: parent visibility | Absent | Absent |
| Exact revision: calls / input / emitted IDs | 1 /1996 /208 | 1 /1996 /2 |
| Exact revision: output | Four exact EVENT lines without W citations, followed by NONE | Literal `NONE`, no final LF |
| Revision: parent visibility | Present | Present |

All four archived/diagnostic generations are terminal and untruncated. The two
OFF outputs contain112 and1 whitespace-delimited words, below the250-word
instruction. OFF total is **2 calls,3731 input tokens,375 emitted token IDs,
0 fits**. Emitted-ID counts include the terminal token. Native generation is
greedy, one beam, at most768 emitted tokens, with full inputs bounded at2048;
the captured token counts and prefix checks show no truncation. No tokenization
was rerun in this audit.

Rehearsal has roles `system,user`. Revision has roles
`system,user,assistant,user`: the same rehearsal context, the entire unrepaired
**archived ON rehearsal answer**, then the exact predeclared parent feedback.
It is not conditioned on the newer failed ON revision or on OFF rehearsal.
The system/user context exposes the four public wake transcripts, including
researcher-authored task/formation instructions and child-written EVENTs.
The revision additionally exposes the rejection and parent feedback. Parent
visibility must not be collapsed into a parent-free label for that condition.

## Exact matching and public-only grounding

For each condition, OFF saved PROMPT bytes are identical to archived ON PROMPT
bytes, and both NOTE `messages` equal that prompt. Tokenizer signatures and
declared base identities also match the archived ON receipts. The two prompt
SHA-256 values are:

- Rehearsal: `1552e07f97763f22847ddd47ab4cdec2a0851020e7e5fc50d08206a03a3ee7b5`.
- Revision: `c5d03c9425e4c7624b71666d9a95c429da035ed4dbef451460c8bcaac76ddc44`.

I reconstructed the labelled W1–W4 transcript payload directly from each
collection episode's four captured public messages plus raw child EVENT. It
exactly equals the prompt payload. No hidden bank outcome, acceptance flag,
sealed result, or evaluator feedback was needed for grounding. For each episode,
the public RECEIPT supplies source/port/destination/receipt, the offered EVENT
address supplies its identifier, and the captured EXPLORE matches that tuple.
The OFF EVENT and EXPLORE lines match these public bytes, in order:

```text
- W1: EVENT E_43DKZR6D3S AT N_NQ7SZP2WK3 DID P_MLFJXQ3WZH GOT N_WBXQVETNWG EVIDENCE R_V75J4A4RYG
- W2: EVENT E_VEEAOY3IIH AT N_NQ7SZP2WK3 DID P_X3KIPDIW4F GOT N_6AUMRWYCVK EVIDENCE R_YJNOWTRK53
- W3: EVENT E_QQ43NOEYBQ AT N_IRD6ZSHY2B DID P_ONQCERJ5LE GOT N_ZXFXLP2ESD EVIDENCE R_6MJCDE77X2
- W4: EVENT E_DEX6OHDHJP AT N_IRD6ZSHY2B DID P_FWMNJO5UYN GOT N_DH2AYPUMUT EVIDENCE R_3KI5HYYQOV
```

These exact subrecords do not make the whole rehearsal candidate compliant.
Its uncited prose is retained, including:

> I explored four different source and port combinations in the deterministic public route system. Here are the events I observed:

> Each exploration resulted in a receipt, which I used to commit an event:

> These events confirm the successful exploration and routing through the system.

The instruction requires W citations for **every factual statement**, not just
the bullets. The final broad statement is not separately cited; personal
experience attribution is also invalid for this base diagnostic. Do not attach
citations, strip prose, or salvage the four EVENTs into training targets.

Revision's whole raw output is `NONE`. This fixes the ON revision's mixed
EVENT-plus-NONE syntax, but no warranted absence of supported observations
follows. In particular, the rehearsal system's fallback says “If no supported
observation can be stated, output NONE”; the four grounded public observations
demonstrate that this absence condition is not established. The parent feedback
permits the standalone form, but syntax alone is not substantive extraction or
evidence-calibrated abstention. There is no factual payload to admit, and the
diagnostic exclusion applies regardless.

## OFF context, restoration, and unchanged-state evidence

Audited frozen source commit:
`4b9984a2945c6b4066e4637c172db1a70aa9a2be`.
The runner blob SHA matches REQUEST/RESULT:
`42c7cdbd44aae7fe79b7843f029c8614f4efb400a85d9a2d8663e29bc9eaea91`.

The native function enumerates every module with both `lora_A` and `lora_B`,
requires all initially enabled and the model in evaluation mode, then encloses
both generations in one `disable_adapter()` context. It asserts **all enumerated
layers disabled at context entry**. The inspected generation function does not
toggle adapters. A `finally` block records flags and parameter hashes and
requires restoration and unchanged evaluation mode.

`SLEEP_BASE_RESTORATION.json` contains **196 original and196 restored layer
flags**, with identical layer keys and all values `false` (not disabled).
`adapter_restored=true`; pre/post adapter parameter hashes match each other,
the loaded-state receipt, the collecting actor, and both archived ON receipts:

`07ecf4c5d965db5ea2765482439db3de5e230d90e0d86a99876a9c4ce6109300`.

The loaded adapter is the collecting **A1** actor's train adapter, not the later
cycle2 fitted state. Initial adapter-file SHA:
`7e6fe380553b20e23b63f5934199fb04a44388079ce3fcc68b0ccbb9e9602f26`.
Initial training RESULT binding:
`3eaad009cc1546fa62209a1871b0b129140db485afc4676f057a93333faf8046`.
Declared frozen base state:
`a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`.

The completed native path checks the base parameter hash after generation,
checks adapter parameters unchanged, and rechecks the initial adapter-file and
training-receipt hashes before writing `RECOLLECTION_CAPTURED_NO_FIT` with
`frozen_base_unchanged=true`. REQUEST fields match RESULT; no FAILED file exists.
Both panel receipts explicitly report adapter OFF, one call, zero fits,
non-collecting actor, and exclusion from training.

Scope of verification: these are inspected source assertions and captured
native attestations, not fresh tensor measurements by this auditor. OFF flags
are asserted at context entry; a separate per-call OFF bitmap is not serialized.
The restoration file independently preserves the full initial/restored maps.

## Retention, timing, and limits

All prior source-file hashes recorded in `SLEEP_BASE_SOURCE.json` match the
archived rehearsal/revision files. Referenced collection and collection RESULT
hashes match actual bytes. Feedback matches the archived revision prompt,
recorded feedback SHA, and frozen source literal. No new prompt variant or
generation was used to repair a candidate.

Native diagnostic timing: **11:13:04.543700–11:14:09.633308 UTC**, September14,
2026; **65.089608s** elapsed including setup. Per-call elapsed times and dollar
cost are not separately recorded. Relevant diagnostic SHA-256 anchors:

| File under `R/recollect_base_diagnostic` | SHA-256 |
|---|---|
| `RESULT.json` | `2b0d9af3ff9d6a30925ef8233ac07c81ab643ca24837e25af3c967ca87879670` |
| `REQUEST.json` | `3010993d48984896c1e988fbfc7d8858b67e8686c86ca4c7d8fb497ddf5499a3` |
| `SLEEP_BASE_SOURCE.json` | `922b6ca223d0bc161b161af2ca36f41adaef1f7945aff9725517193ffdd69399` |
| `SLEEP_BASE_REHEARSAL.json` | `a42c90a4d6b31876d135a39f041f7ec064ff1a22f26b5156c84122c187c81186` |
| `SLEEP_BASE_REVISION.json` | `61e58c0f0afc18e48c28c3f70441b771fbd758354fe4946cdca3f6cf5c5bd681` |
| `SLEEP_BASE_RESTORATION.json` | `04639c2eb248562bdbf4d7b214255904a86f3e58ad368032cf38061b32ef9c89` |

All raw outputs and original ON failures remain untouched at their archived
paths. The read-only assertion check passed prompt joins, hashes, public-only
grounding, counts, visibility, restoration maps, and recorded state equality.
No new tests or code were added.

Limits: two fixed prompt conditions, not independent samples; archived ON
rather than contemporaneous paired reruns; source/receipt verification rather
than model re-execution; no successful whole-note material control; no admission,
fit, downstream utility, transfer, or H1/H2 evidence. The comparison shows
different observable failure forms with adapter OFF, not that the adapter alone
caused the posed-task failures or that the base genuinely lacks supported facts.

**Released to Main. No fit, repair, new probe, or commit authorized/performed.**
