# First matched frozen base / C2 caption datum

Actual game receipts: September 18, 2026, 05:43:48 UTC (base) and
05:44:03 UTC (C2); September 17, 22:43–22:44 PDT. Watcher header times
are not used as execution timestamps.

Both players received the same three scene descriptions, explicit humour
objective, initial context, greedy decoder and THINK384 / ACT768 budgets.
The base is plain Qwen2.5-7B-Instruct, with zero LoRA parameters. C2 uses
the verified frozen snapshot51 rank8 adapter. Neither player trained here.
Initial-message SHA256:
`bdea6ff9cc149820c225ef5d525c17db069a4c541cb3c7eb828c14ea098b9e03`.

Acceptance is provisional rank <=50 against 64 fixed human references from
the chosen contest, plus the same weak relevance gate and separate pixel
novelty archives. Both choose their own scene; they did not choose the same
one, so these ranks are within different contest panels, not direct rankings
against each other. Every raw score, rank and original attempt is preserved.

| Player | Chosen scene | Rank /65 | Score | Relevance | Outcome |
|---|---:|---:|---:|---:|---|
| Plain base | 1, crib | 60 | -6.53125 | 0.402766 | Rejected |
| Plain base | 1, crib | 56 | -6.25000 | 0.523369 | Rejected |
| C2 snapshot51 | 3, windmill | 25 | -5.62500 | 0.309364 | Accepted, new pixel |
| C2 snapshot51 | 3, windmill | 60 | -6.31250 | 0.277558 | Rejected |

**Counts in this one opportunity: base 0 accepted ideas; C2 1.**
The accepted literal C2 caption is “Even the windmill knows this meeting's
ridiculous.” Its second is “Formal wear isn't optional in a tilted windmill
meeting.” Trailing whitespace remains unchanged in the scored artifacts.

The base captions are descriptive financial similes: the man's hand like a
flag / the mobile like a cash tornado, then the mobile like a roulette wheel.
Their full literal strings remain in source-bound proposal artifacts.

## Format repair, not a replacement generation

C2 originally declared two captions but omitted the `Caption:` prefix on the
second line. The strict parser failed. Both players' original ACTs were
reprocessed with a tolerant extractor; no new sample, editorial repair or
THINK-only caption was submitted. C2 has one unprefixed-line format fault;
base has none. The original failed artifact is retained. Format metrics are
separate from humour/relevance/novelty outcomes and may inform parenting.

This is a first development search datum, not a multi-seed comparison,
long-horizon coverage result, learning result, retention result, or validation
of scene fit. The interim relevance gate remains weak. No tau gate or
fabricated probability is used, and no sealed/final pool was read.

Public receipts:
`research_loop/workers/rohin209_first_game_20260918/receipts/r212/`.
Raw generations, original failure, exact inputs and recovery outputs:
`research_loop/workers/rohin209_first_game_20260918/private/matched/`.

## Scene description requested earlier

The scene for “Discussing finances for the new arrival” was supplied by the
vision model as a man and a pregnant woman beside a crib, with the man
gesturing, the woman appearing concerned, and a mobile of money/dollar signs.
This is model-generated scene text, not independently verified image ground
truth. The earlier caption ranked55/65 and remains rejected at the new bar.
