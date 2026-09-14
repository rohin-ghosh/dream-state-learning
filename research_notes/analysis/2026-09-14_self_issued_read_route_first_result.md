# Self-issued READ/ROUTE: first retained DEV result

## Scope and conclusion

Read-only terminal-artifact audit on 2026-09-14. Run completion marker:
**2026-09-14 08:34:31 UTC**. Source commit:
`a450f5283d6f834b5cfca85143582fb3b5f57d14`.

The four previously exposed tasks produced **BASE 2/4, FITTED 3/4,
FITTED_READER_OFF 3/4**. Every episode immediately committed ROUTE;
**all arms made zero memory reads**. The reader-disable control was therefore
**unexercised**, not a successful ablation. These traces do not show that memory
is unavailable, that a reader would fail, or that contextual memory is unnecessary.
They show no self-issued READ in these twelve initial decisions under this prompt.

No callback/infrastructure exceptions were found in the retained traces. All
twelve calls have matching call/episode evidence, terminal EOT flags, and actual
post-commit outcomes. This is a same-bank, zero-new-fit diagnostic, not a transfer,
generalization, autonomous-parenting, or scientific-promotion result.

## Preserved evidence

- Remote: `node2:/tmp/astra_event_read_route_20260914_attempt1`.
- Local root: `gpu_artifacts_local/astra_event_read_route_20260914_attempt1`.
- Exact source files: `evidence/`, with `evidence/SOURCE_MANIFEST.json` listing
  every original relative path, byte size, and SHA256.
- Compressed snapshot: `evidence.tar.gz`.
- Machine-readable independent joins and per-task raw/token/outcome records:
  `AUDIT.json` in the local root.

Copied **43 original files, 92,404 bytes**. No weights, checkpoint tensors, or
external model directory were copied. The bounded copy rejected symlinks and
non-terminal runs, capped files at 128, each file at 2 MiB and total source bytes
at 8 MiB, and allowed only the observed JSON/text/script/log/hash extensions.
Remote contents were reread for equality before archive emission. All 43 local
files were subsequently checked against their captured sizes and SHA256 values.
No remote files were written.

| Evidence | SHA256 |
| --- | --- |
| Archive | `aa7854ff728e25f01e54abf003b53513e471df48697c7667c073bc8e2a7fb27e` |
| Source manifest | `9455ef6c81d6a0c9a572359d69d385d4dc2b2d17e408fd308891915e18c4ceb1` |
| Independent AUDIT.json | `db0ecccfe7ae98a604edcc2105835c16a8d6f3d8561a14475b08a5a853d783c7` |
| BASE RESULT | `49765fa51c9ad4e3cc900e0c9fa12f1bdfadd0b7f6943afb27dc76ea4fe86a69` |
| FITTED RESULT | `c69e8b3a45f3223576dfbb5aae76f023ff1153701d5391b71199ff901e7ff919` |
| FITTED_READER_OFF RESULT | `4d7b793d8fda0971e6d9aa10696dd5e5a34efa549c062eea849538084b4a8730` |

## Exception and evidence audit

The audit inspected all twelve `CALL_*.json`, all twelve `EPISODE_*.json`,
the three `EPISODES.json` aggregates, three terminal `RESULT.json` reports,
source hashes and `run.log`. Checks passed:

- Each individual episode equals its aggregate entry. Every actor trace response
  equals the corresponding native call generation, including messages, raw
  string, token IDs, prompt-token count and flags.
- Exactly one actor and one committed transition trace occur per episode. No
  memory trace or callback-error trace occurs. No populated error/exception
  fields or `FAILED.json` artifacts are present.
- All twelve generations have `terminal=true`, `truncated=false`; their final
  token ID is `151645`, matching the retained tokenizer's `<|im_end|>` ID.
  Every raw command has **zero trailing LF characters**, accepted by the declared
  final-LF-only command parser. No other whitespace or identifier was repaired.
- Parsed port, committed port, transition port and chosen port agree. Actual
  outcome agrees with the recorded transition and the deterministic source-bank
  mapping. Success equals actual outcome == public GOAL, not an inferred target.
- Every terminal reason is either `reached_goal` or `wrong_outcome`.
  The two BASE misses and one miss in each fitted arm are wrong outcomes,
  not parse failures, truncations, budget failures or recorded infrastructure errors.
- `run.log` contains model-load progress, `torch_dtype` deprecation warnings and
  generation-flag warnings about temperature/top_p/top_k, but no traceback or
  recorded CUDA/OOM/timeout error.

The wrapper's previously identified risk remains a property of its source:
generation exceptions can be converted to episode failures, and unsuccessful
generation attempts are not appended to its capture counter. **No manifestation
was found in this run's retained evidence**: all callback-attempt counts join
one-to-one to successful native captures and all episodes end in a real transition.
This does not claim to detect activity absent from every retained artifact.

## Accounting

| Arm | Reached goal | Actor calls | Reader calls | Episodes with reads | Total model calls | New fits |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| BASE | 2/4 | 4 | 0 | 0 | 4 | 0 |
| FITTED | 3/4 | 4 | 0 | 0 | 4 | 0 |
| FITTED_READER_OFF | 3/4 | 4 | 0 | 0 | 4 | 0 |
| Total | 8/12 descriptive only | 12 | 0 | 0 | 12 | 0 |

Each episode uses one of at most three actor calls and none of two available
reads. Each arm uses 4/20 allowed calls; the three executions use **12/60**.
There is no evidence of a retry or omitted failed attempt in these joins.
The pooled success count is accounting, not an independent twelve-task estimate.

## Goal-swap tasks and exact raw outputs

Within each pair, only the public GOAL changes. System instruction, node,
displayed port list and displayed event list are identical. Matching tasks have
identical input messages across all three arms. Initial prompt-token counts
for tasks 1–4 are respectively **169, 168, 168, 171** in every arm.

**Pair A, tasks 1–2**

- Node: `N_FEKWBHXIER`.
- Ports, in displayed order: `P_GBV7TYNMYX,P_LRZJ7WQPLZ`.
- Events, in displayed order: `E_CHYIWYDY6Y,E_W76IFWI75T`.
- Goals: task 1 `N_PZO6QGCFYQ`; task 2 `N_XKJMA6ROET`.

**Pair B, tasks 3–4**

- Node: `N_KGA6B2GC43`.
- Ports, in displayed order: `P_IW6NBDXQPN,P_STMW7CXQGK`.
- Events, in displayed order: `E_QAQ5WQZQRH,E_X3YBAILZSM`.
- Goals: task 3 `N_CMZXILYYFI`; task 4 `N_FHOFB66WSI`.

All raw strings below are complete: no trailing LF, commentary or memory result.
FITTED and OFF are combined in this table because their corresponding call JSON
objects are equal and individual episode files are byte-identical for all four
tasks, not merely because aggregate scores agree.

| Task | BASE raw | BASE actual outcome | Hit | FITTED = OFF raw | FITTED = OFF actual outcome | Hit |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `ROUTE P_GBV7TYNMYX` | `N_PZO6QGCFYQ` | Yes | `ROUTE P_GBV7TYNMYX` | `N_PZO6QGCFYQ` | Yes |
| 2 | `ROUTE P_GBV7TYNMYX` | `N_PZO6QGCFYQ` | No | `ROUTE P_LRZJ7WQPLZ` | `N_XKJMA6ROET` | Yes |
| 3 | `ROUTE P_STMW7CXQGK` | `N_CMZXILYYFI` | Yes | `ROUTE P_IW6NBDXQPN` | `N_FHOFB66WSI` | No |
| 4 | `ROUTE P_STMW7CXQGK` | `N_CMZXILYYFI` | No | `ROUTE P_IW6NBDXQPN` | `N_FHOFB66WSI` | Yes |

BASE does not change its port under either goal swap: 1/2 in each pair.
FITTED/OFF change port appropriately on Pair A (2/2), but use the same port for
both goals on Pair B (1/2). Relative to BASE, fitted behavior gains tasks 2 and 4,
loses task 3 and retains task 1: **net +1/4**, not uniform improvement.
Only one of the two fitted goal-swap pairs shows the appropriate route switch.

## Provenance and limits

All arms identify the same earlier collection and adapter-training receipt:

- Collection: `/tmp/astra_microloop_20260914_attempt2/collection`.
- Collection RESULT SHA256:
  `9a17d0ae568972523366060933e6c82cb9fce422298bafe97fef46be42d5461d`.
- Training RESULT SHA256:
  `c42010e12efed8a06c1e98901f09d576cf0c568175e837fa66255138e3c8a40f`.
- Selected adapter file hash pinned by the runner:
  `8597605e7e07b882f613e359decee0193275d4bd16eacac8cd5c45db75f25788`.
- Historical compilation mode: `FINAL_LF_ONLY`; the original collection had
  zero strictly accepted events before that separately labeled compilation.
  That training provenance is not hidden or relabeled as strict success.
- Native wrapper SHA256:
  `21c8e824b1523e822167b1b756e148d89923cb9fa389677735960bcd7c0d999d`.
- Pure controller SHA256:
  `b6ca95525ddd5af5f8c775bf3287693865d01d7e1ba8d1c5f9b0ffbcee022aaa`.

The audit checked the retained source-module hashes against the local modules
used for the pure deterministic bank/command checks. No model, tokenizer,
training, CUDA operation or native generation was invoked. Native reports claim
unchanged frozen base and saved adapter; this audit did not independently load
or hash remote weights. EOT/token claims were checked against retained token IDs
and tokenizer signature, not by a new tokenizer decode.

Because no READ occurs, no memory response exists to assess for factual accuracy,
raw repair or contextual use. Reader-only disabling never activates; the OFF
arm is operationally another fitted-actor execution for these trajectories.
Identical FITTED/OFF traces are therefore unsurprising and **cannot establish
reader irrelevance**. Zero voluntary reads also cannot establish that learned
memory is unavailable. Four exposed tasks and two paired goals support only
this local descriptive result; no new scientific promotion is inferred.
