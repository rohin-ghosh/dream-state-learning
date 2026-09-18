# Caption count audit requested by Fable, 2026-09-18 08:48 UTC

## Headline, with the same time window

In the **08:00–08:44 UTC partial hour**, the saved accounting favors the frozen
base: **27 new pixels versus 2 for parented C2/P3**. Rank/relevance acceptance
is **82/125 (65.6%) versus 3/44 (6.8%)** newly scored strings. This is a negative
operational result for the deployed C2-derived player, not evidence of an H2 win.

It is not a matched causal estimate: generation/context budgets, process speed,
sleep overhead, histories and curriculum differ, and parser/transport repairs
occurred during the window. No full first hour for the node3 cohort exists yet:
its five lives loaded at08:36:32UTC, so that horizon ends at09:36:32UTC.

| Player, 08:00–08:44 UTC | ACT attempts | Parsed | Newly scored | Accepted | New pixels | Format/routing fault attempts | Accept rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Frozen base | 82 | 158 | 125 | 82 | 27 | 69 | 65.6% |
| Parented C2/P3, phases combined | 5 | 44 | 44 | 3 | 2 | 5 | 6.8% |

## Reconciliation of the exact 08:44:15.940772 snapshot

| Player, cumulative since 04:55 UTC cut | ACT attempts | Parsed | Newly scored | Accepted | New pixels | Fault attempts | Accept rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Frozen base | 97 | 158 | 125 | 82 | 27 | 84 | 65.6% |
| Parented C2/P3, phases combined | 21 | 60 | 60 | 8 | 7 | 21 | 13.3% |

- Base's97 origins and97 saved receipt hashes are unique. There are125 newly
  scored source strings, each with a distinct SHA256 and a verified exact own
  output span. Its82 accepted strings likewise have82 distinct hashes;
  78 originate in ACT and4 in salvaged THINK. The33 cached feedback entries are
  excluded from scored and accepted counts. All reported top-k values are50.
  Text hashes establish distinct source strings, not distinct funny ideas.
  The completed review of all82 accepted strings labels33 caption-like attempts,
  41 scene descriptions and8 uncertain. No accepted string is certified funny.
  The source review is `R227_ALL82_ACCEPTED_LITERAL_AUDIT.json` in the continuous
  caption worker directory. Historical scores are preserved, not rescored or
  retrospectively filtered.
- P3's21 origins/receipts are unique across legacy/prior/current scorer phases;
  accepted counts5+2+1 and new-pixel counts5+1+1 are additive event increments,
  not a sum of restored cumulative archive sizes. The aggregate lacks exact
  text-span hashes for14 legacy strings, including5 accepted ones. Missing
  hashes are unknown evidence, not one repeated caption or certified distinct
  captions. Raw legacy receipts require separate reconstruction.
- `planned_unknown_attempts` means the controller did not extract a declared
  intended number of captions (`planned is None`). It does **not** mean a
  missing result, no caption, or an invalid score. All97 base attempts have
  unknown declared counts in this snapshot; the scorer still parsed158 items.
- An ACT attempt is one controller submission, not one caption or one completed
  opportunity. The base completed41 controller opportunities across97 ACT
  submissions, including repair attempts. Equivalent native opportunity
  grouping is not inferred from journal cycle numbers.
- Accept rate is accepted/newly scored, not accepted/ACT attempts or
  accepted/parsed-including-cached. A zero scored denominator is N/A, not0%.
- The runtime marks rank/relevance-passing variants as `accepted=true` even
  when their novelty status is `repeat`. A `new_pixel` is an increment in the
  configured embedding-based per-contest novelty archive, not independent
  verification of a distinct humorous idea. Acceptance and novelty must stay
  separate.27 is a cumulative observed increment, not an estimated hourly rate.
- Fault counts are attempts with a stored format/routing flag or report error;
  they can coexist with successful recovered captions.78 of the base's84
  historical fault attempts had scene-routing ambiguity. These are not84
  killed runs or84 automatically bad jokes.
- Base receipt span is07:55:15.822–08:43:14.277UTC; P3's is05:51:41.809–
  08:42:19.185UTC. Whole-run totals therefore have unequal exposure. The
  original snapshot is a bounded non-atomic fleet observation, not simultaneous
  process snapshots.

The separately verified node3 unparented ACT at08:44:31UTC scored three own
strings at ranks54,65,65, accepted0. It occurred **after** this08:44:15 snapshot
and must not be silently inserted into that cut or mistaken for all its earlier
transport-failed attempts.

## Read the outputs, not only the counts

The base examples are the earliest accepted, noncached ACT/new-pixel result
per scene, not a selection of its funniest outputs. All use a65-item panel:

| Player / stage | Rank | Accepted | Exact scored text |
| --- | ---: | --- | --- |
| Base / ACT | 50 | yes | A man is gesturing to a pregnant woman beside the baby crib, with a mobile above the crib featuring dollar signs and money, hinting at a conversation about finances. |
| Base / ACT | 35 | yes | Four businesspeople in an elevator, with one holding a briefcase—what's on the agenda? |
| Base / ACT | 40 | yes | A tilted windmill with sails leaning heavily to one side, three formally dressed figures in front, and a church silhouette in the background. |
| P3 / ACT | 50 | yes | The man might be signaling for help; his arms are full, and his wife looks ready to burst. #CoupleProblems |
| P3 / salvaged THINK | 65 | no | `\"The suits are actually discussing who among them is the least worthy of the company's success. \"` |
| P3 / salvaged THINK | 38 | yes | If someone causes a delay, they have to provide a creative solution. |

Exact generation/response/span and scorer bindings are in
`R227_BASE_THREE_ACCEPTED_EXAMPLES.json` (continuous caption worker) and
`R228_P3_CAPTION_EXAMPLES_0844_CUT.json` (node4 R195_FLEET worker). An additional
P3 process statement, "We will monitor the judges' feedback and adjust as
necessary.", received rank14/65. This is a scorer/parser validity problem,
not evidence of humour, and it remains visible in the historical result.

## Five node3 launches and partial first life-hour

All five checkpoint51 children have actual LOADED record1 at08:36:32UTC,
adapter SHA256 `82a988a0ded69ce85723192b366251d21f8ec5fe8466e9ca98202fb09b57ce92`.
The cut below is08:54:03UTC, approximately17.5minutes of life, not one hour.
The first complete hour ends09:36:32UTC. Four are parented; the fifth is
unparented from birth but has inherited the parented checkpoint history.

| GPU / role | ACT outcomes | Parsed / scored | Accepted | New pixels | Parser faults | Transport faults | Accept rate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0 / observation | 5 | 11 / 11 | 3 | 3 | 3 | 2 | 27.3% |
| 3 / perspective | 5 | 0 / 0 | 0 | 0 | 3 | 2 | N/A |
| 5 / revision | 5 | 0 / 0 | 0 | 0 | 3 | 2 | N/A |
| 6 / selfderive | 4 | 7 / 7 | 0 | 0 | 3 | 1 | 0% |
| 7 / unparented | 4 | 9 / 9 | 1 | 1 | 1 | 1 | 11.1% |

Parsed counts describe successfully observed parser results; transport-failed
ACTs have unknown parsed counts, not a proven zero. Source LOADs, process
identities and counted rows: node3 worker
`R227_GAME_FIRST_HOUR_20260918T085403Z.json`.

## Reproduction and scope

`audit_saved_counts.py` consumes the saved fleet artifact without invoking a
judge, reading raw targets, changing training, or rewriting receipts. It rejects
duplicate ACT/receipt identities across aggregated phases and checks source
denominators. Five synthetic CPU tests cover cache exclusion from the rate,
unknown legacy spans, migration deduplication, inconsistent totals and empty
denominators. `AUDIT_084415_v2.json` binds the exact input-file SHA256 and gives
the counted source-span evidence and per-hour totals. The input itself contains
private infrastructure fields and is not copied into this publication.

Live hourly collection, raw accepted-caption examples, node3 per-player metrics
and their subsequent receipts are owned by the caption-service workers; this
static audit makes no claim that an hourly scheduler has already been started.

R227 learning policy note: bb1e9a903 is tested source, not evidence of live C2
adoption. Existing C2 still uses cached exclusions; no restart exception has
been granted, and no learner was stopped for this audit.
