# Independent audit: PCFL EVENT-prefix import and EVENT-only write localizer

**Date:** 2026-09-13 PT  
**Verdict:** **REWORK before fit/readout; conditional GO for one bounded
development localizer after the gates below pass; NO-GO for any connected-
knowledge or whole-system claim.**  
**Evidence cut:** helper-VM commit `7a8f327b`, its two EVENT-only scope memos,
the fixed SEQ-171 archive, the exact-v3 replay receipt, and the current
uncommitted prefix-import/writer/tests. No model, tokenizer, fit, adapter,
readout, or GPU operation was performed by this audit.

## Executive finding

The first sixteen SEQ-171 calls are a scientifically usable **candidate
prefix**. They are eight chronological EXPLORE/EVENT pairs; all eight EVENTs
were accepted against real public world receipts before the first LINK call
failed. A later LINK failure does not invalidate an earlier causal prefix.
Selecting the first complete EVENT prefix from the first format-scaffolded
attempt, rather than the best later attempt, is a defensible retrospective
component decomposition.

It is not yet a qualified fit input. The new importer deliberately returns
`native_custody_verified=false`; the actual-tokenizer receipt has not been
produced; the importer, scoped writer, and tests are still uncommitted; and the
importer checks the archived identity file's bytes but does not yet validate
the substantive native-actor/model identity needed for an “own child record”
claim. No fit may start until those joins close.

After that repair, one predeclared LOW/r8 fit plus symmetric W0/W8 AUTH-versus-
C0 readout answers a useful but small question:

> Can a rank-8 adapter cold-reproduce compiled address-to-row-block mappings
> derived from eight world-admitted, externally format-assisted child EVENT
> records, after the source transcript is withdrawn?

It cannot answer whether the child formed connections, traversed a graph,
expanded knowledge under a goal, retained knowledge across later sleeps,
improved actions over a lifetime, compressed experience, or beat an evolving
text-memory system.

## 1. Independent archive findings

The following fixed evidence was inspected directly on the helper VM:

- archive
  `gpu_artifacts_local/pcfl_own_write_format_20260913_attempt1/evidence.tar`,
  SHA-256
  `bd6829dfa4e6c0a63f48cf184e28091e12cf9de9a231e0f6cda6672d5133c869`;
- source tar SHA-256
  `698ad6278f69131fdc7721d173753732631b7485b2d420ac293a2ef0e4e50280`;
- original report: `FORMATION_FAILED`, `17` attempted calls, `8` accepted
  EVENTs, `0` accepted LINKs, `0` fits, `0` updates, `writer_payload=null`;
- original failure: slot `old/formation/16`, `child LINK differs from
  pre-output choice`;
- outer record: `FAILED`, no generation retry, worker return code `1`, no
  signal;
- first sixteen slots: eight exact EXPLORE outputs alternating with eight
  exact accepted EVENT outputs. Every EVENT carries the source, port,
  destination, and receipt from its immediately preceding executed action;
- the commitment decoder was the disclosed target-free regex
  `[^\r\n]+\n`. It forced one physical LF-terminated line but supplied no
  identifier, row field, route fact, or answer;
- the failed LINK at call 16 remains in the archive and is not imported or
  trained;
- the exact-v3 replay receipt records the original report as failed and
  locally replay-valid, with `native_custody_verified=false` and zero new
  calls/fits/updates.

These facts support importing the prefix without calling the original full
formation successful. They also require the label **format-assisted
controlled EVENT curriculum**. The child produced the semantic row contents,
but the external decoder guaranteed their line shape. The eight actions were
part of a fixed development curriculum, not evidence of autonomous
exploration policy learning.

Materializing only those eight EVENT rows yields fourteen deterministic
addresses:

- `8` `READ EVENT` blocks;
- `6` `READ EVENTS_AT` blocks;
- `0` `READ LINKS_FROM` blocks;
- `12` singleton targets and `2` two-EVENT targets.

The query-map hash recorded in both the scope and current importer is
`39e2d8d430e54ff3818967790cbe38eb15f41c014010f6647562b4c68ce02f8c`.
The two-EVENT `EVENTS_AT` blocks are compiler aggregation of separately
witnessed rows; they are not child-authored LINKs and must not be described as
connected memory.

## 2. What is already sound in the proposed import

The current `astra_pcfl_event_prefix_import.py` takes several important
precautions:

1. It accepts only the one fixed archive and original source tar hashes.
2. It requires every source member to match the original absolute-path pin.
3. It requires the original failed report, rc1, failed LINK slot, zero fit,
   and release observations to remain unchanged.
4. It imports exactly calls `0..15` and EVENT slots `1,3,...,15`; no missing
   row, alternate attempt, or later “better” prefix can be substituted.
5. It reconstructs the public chronological history and replays every action
   and EVENT admission against the pinned core.
6. It carries the exact raw EVENT bytes and source hashes into lineage; no
   parent/checker text, expected-bank row, rejected LINK, normalizer, or
   fabricated completion enters the targets.
7. It preserves the legacy rows' `native_generation_verified=false` rather
   than rewriting history. A later independent custody receipt is the right
   place to qualify them.

The proposed `14+6` schedule is also coherent in the current tests: fourteen
original address blocks plus six deterministic authentic replays produce
twenty slots; every underlying EVENT has support count three; each of five
epochs contains all twenty slots under all eight W0--W7 wrappers; four
support-disjoint examples make each update; total accounting is `800`
presentations and `200` updates. W8 never trains.

## 3. Blocking rework before any fit

### A. Close native child custody, not merely archive byte custody

The importer currently fixes and joins `formation/actor/identity.json`, but it
does not inspect the identity's substantive fields. Before the prefix can be
called child-native, the import receipt must validate at least:

- repository `Qwen/Qwen2.5-7B-Instruct` and revision
  `a09a35458c702b33eeacc393d103063234e8bc28`;
- mount `C0`, `lora_request=null`, and the expected model-binding hash;
- actor config, engine policy, model/tokenizer file hashes, environment, and
  source pins against the archived manifest/config;
- all sixteen request/render/raw/response joins, stop reasons, token counts,
  monotone timing, and the exact raw output-token decode;
- no later LINK prompt, private expected bank, teacher text, or checker repair
  in any imported request history.

The exact original-source replay receipt is useful but explicitly says
`native_custody_verified=false`; it does not close this gate by itself. The
legacy per-row flag should remain unchanged, while a new sealed prefix-custody
receipt records the completed external validation.

### B. Perform and bind the actual tokenizer check

The committed archive includes tokenizer measurements, and the new code has a
reasonable actual-tokenizer verifier. The current unit test uses an explicitly
simulated archived token table. Before fitting, the actual pinned tokenizer
must reproduce all sixteen chat renders and output-token decodes, including
the terminal LF, and its sealed receipt must be an input to the fit command.

### C. Commit and execute the scoped CPU gates

At the audit cut, the importer, writer, replay receipt, and their tests are
uncommitted, and no completed test receipt exists. Commit/pin them without
mixing the unrelated in-progress interface branch; run the archive/import,
schedule, mask/EOS, source-drift, and numerical-dispatch suites; preserve the
exact schedule object before model output exists. A failed import stops; it
must not silently generate a new prefix or select SEQ-172/173.

### D. Freeze a content endpoint separately from the known LF interface

The current proposed primary is W8 `strict_stop`: AUTH `>=13/14`, C0 `<=1/14`,
paired gain `>=12/14`. `strict_stop` requires byte identity including the
terminal LF. The same child repeatedly produced semantically exact rows ending
at EOS without that LF in SEQ-169/170. Consequently this endpoint conflates
opaque mapping acquisition with the already demonstrated serialization
interface.

No readout exists yet, so the non-post-hoc repair is to freeze two nested
endpoints now:

1. **Content-acquisition primary:** W8 `semantic_stop`, with the same
   `13/14`, `1/14`, and `12/14` thresholds. This scorer still requires the
   exact ordered opaque EVENT rows and permits only the registered final-LF
   omission/fence variants; it does not accept wrong identifiers or prose.
2. **Exact-byte interface endpoint:** W8 `strict_stop` under the existing
   thresholds. Only this endpoint licenses “exact stored block” wording.

If the builder elects to keep strict-only primary, the experiment remains
valid, but its question must be narrowed to *exact byte-interface acquisition*
rather than storage/extractability generally. In either case, both vectors and
all raw responses must be reported prospectively.

### E. Finish the one-shot command/reducer/release path

The proposed source presently has no committed EVENT-specific analyzer,
command, outer lifecycle, or terminal receipt. Before launch require:

- one fresh C0 base fit with the exact r8/alpha16/dropout `.05`, LR `3e-5`,
  `200`-update recipe and actual initial tensor hash;
- separate fresh AUTH and C0 processes using the identical LoRA-enabled
  engine, W0/W8 roster, seeds, prompts, token caps, scorer, and order; only the
  adapter mount differs;
- all `56` planned model calls or an explicit invalid assay—never fill missing
  outputs with zeros;
- exact adapter/source/fit/readout joins, no retry/checkpoint selection, and
  verified engine/process/GPU release.

## 4. Useful bounded inference and exact claim ladder

### If semantic and strict endpoints both pass

The strongest defensible sentence is:

> In one disposable development root, a rank-8 LoRA trained for 200 updates
> on compiler-rendered address blocks derived from eight world-admitted,
> externally format-assisted child EVENT records reproduced X/14 exact W8
> blocks after source withdrawal, versus Y/14 for the same frozen base without
> the write. All addresses and facts trained under W0--W7; W8 held out wrapper
> wording only.

### If semantic passes but strict fails

Use only:

> The adapter reproduced X/14 semantically exact ordered opaque EVENT blocks
> under W8, while exact-byte interface compliance remained unresolved.

This is positive content-carriage evidence and negative interface evidence;
it is not an exact-block acquisition pass.

### If W0 passes but W8 fails

The fit stored or memorized trained-surface mappings but did not make them
extractable through the held request wrapper. Do not call the writer acquired.

### If C0 exceeds its frozen ceiling

Mark `NO_MEASURABLE_ACQUISITION_HEADROOM`; do not infer a write benefit from a
high AUTH score alone.

### If AUTH fails

This one dose/root/interface did not establish cold acquisition. It does not
prove that LoRA cannot store experiential records generally.

In every case the experimental unit is one source life/root/fit containing
eight EVENTs. The `56` readout calls and fourteen addresses are paired
diagnostic observations, not independent lives or a powered sample.

## 5. Controls present and absent

Present and adequate for the narrow question:

- fresh `AUTH_WRITE` versus fresh `NO_WRITE_C0` with symmetric readout;
- W0 trained-wrapper diagnostic versus W8 held-wrapper endpoint;
- exact deterministic service target as an integrity check, not a model arm;
- strict, semantic, raw termination/error, query-kind, and paired-address
  reporting;
- fixed clean initialization, schedule, dose, and no result-driven retry.

Absent, and therefore unavailable as claims:

- compute-matched LR0 or format-only adapter;
- wrong-lineage, shuffled-content, absent-address, or fresh-root controls;
- later-sleep retention, generic no-harm, task-action use, and connected LINK
  cuts;
- raw-chronology LoRA, evolving external memory, final-batch LEAFE-like write,
  or lifetime comparisons.

Those omissions do not block this one storage localizer. They do block claims
that correct semantic content uniquely caused a behavioral gain, that the
write is selective or safe, or that it improves over post-training or memory
baselines.

## 6. Scope-collapse firewall

The scope documents themselves are appropriately explicit, but the practical
risk is high because EVENT-only is easier than the paper's missing construct.
Apply these stop rules:

1. Spend at most one fixed import, one fixed LOW200 fit, and the predeclared
   W0/W8 readout. Do not tune rank, LR, replay choice, wrapper, or select a
   later prefix from this result.
2. Preserve SEQ-171 as `FORMATION_FAILED`; never relabel the prefix import as
   a successful full formation.
3. Never call compiler-built two-EVENT `EVENTS_AT` blocks LINKs, connections,
   compositions, or graph traversal.
4. Whether positive or negative, return immediately to the missing bridge:
   admit every publicly valid LINK pair in any child-chosen order, bind the
   actual child bank, and feed that authentic bank into the two-root vertical.
5. Keep corrected supplied-memory C0 running as the independent “can the actor
   use connected knowledge?” branch. EVENT-only cannot substitute for it.
6. The paper objective remains authentic EVENT/LINK formation -> compiled
   parametric carriage -> causal connected use -> useful goal-conditioned
   expansion -> OLD/NEW retention -> increasing-lifetime comparison against
   evolving text and terminal-batch controls.

## Final decision

**REWORK/HOLD now.** The archive supports a valid fixed EVENT-prefix candidate,
but native model custody, actual tokenizer qualification, committed/tested
import and schedule, construct-aligned endpoint semantics, and the complete
one-shot reducer/lifecycle must close before a fit.

**CONDITIONAL GO afterward** for exactly one format-assisted, one-life atomic
storage localizer. **NO-GO** for using it as evidence of connected memory,
Dream compilation advantage, autonomous learning, lifetime improvement, or
the full Dream--LoRA--Think claim.
