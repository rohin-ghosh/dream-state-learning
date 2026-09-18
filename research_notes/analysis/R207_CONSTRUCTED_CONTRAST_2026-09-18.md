# R207: constructed-contrast results

Owner: Main. Actual inference: node4 physical0, existing selected scalar adapters, no weight updates.
20 fitting-held DEVELOPMENT contests, five top published-ranked captions per contest, six contrast types; 600 scored pairs per judge. The two judges received exactly the same cases. No skips. This reuses development contests, not a fresh confirmatory test; locked validation and FINAL were untouched.

| Contrast | Widegap wins/ties/losses | Accuracy (ties ½) | BT8k wins/ties/losses | Accuracy (ties ½) |
| --- | --- | ---: | --- | ---: |
| word_shuffled | 100/0/0 | 100.0% | 100/0/0 | 100.0% |
| other_contest | 51/0/49 | 51.0% | 45/2/53 | 46.0% |
| scene_description | 100/0/0 | 100.0% | 100/0/0 | 100.0% |
| truncated | 94/0/6 | 94.0% | 47/3/50 | 48.5% |
| nonsense | 99/0/1 | 99.0% | 67/1/32 | 67.5% |
| mid_tier | 74/0/26 | 74.0% | 55/3/42 | 56.5% |

**Readout:** widegap improves over BT8k on truncated, nonsense, and real mid-tier contrasts. **Both fail to reliably distinguish good captions for this image from good captions for another image.** Widegap51% / BT8k46% on mismatches is not evidence of scene grounding. Shuffling/nonsense discrimination does not establish human humor judgment. Relative-rank game acceptance remains explicitly provisional; pixel novelty is separate from scene relevance and humor.

The 30% positive-vote-mass condition is removed by Rohin207. It is not a promotion gate. Scalar values are not vote probabilities. Mid-tier means the center of the real published-rank ordering; other-contest pairs use a different scene group. Ties and losses remain in the report.

## Actual receipts

- widegap: completed 2026-09-18T04:29:12.803821+00:00; load+prepare+score 20.44s; selected config SHA256 `5c3fb5fd35a26fb0585c09ee91ebc457c31871f591aabfb7a9f53fb05dbc86a8`.
- bt8k: completed 2026-09-18T04:30:15.491053+00:00; load+prepare+score 20.77s; selected config SHA256 `90bcfe8ddfb99ab88221220f58f5c8e39ca4bf756c498d63b517cb339ae0d0bc`.
- Common case-ID digest: `6763a62cf349e969c1dd7ecad0637c8718fef45572eced5a07a50406e3de66ba`.
- Remote root: `/localhome/local-rohing/orch_r207_caption_contrast_20260918`.
- Two input-preparation failures (unready scene selection; old BT8k metadata missing ranks) were preserved and repaired before those cases were scored. Both scored jobs use the same rank-bearing development suite.
- Per-pair pseudonymous scores and skipped-case counts: `WIDEGAP_REPORT.json`, `BT8K_REPORT.json` under `research_loop/workers/rohin207_contrast_20260918/`. Private captions remain evaluator-only on node4.

## Per-contest accuracy

Each cell is **widegap / BT8k**, wins plus half ties out of5 opportunities. IDs are pseudonyms.

| Contest | Shuffled | Other contest | Scene | Truncated | Nonsense | Mid-tier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 05385edcbc473664 | 100% / 100% | 20% / 60% | 100% / 100% | 100% / 60% | 100% / 60% | 80% / 80% |
| 08862f73d891e85b | 100% / 100% | 40% / 20% | 100% / 100% | 80% / 60% | 100% / 60% | 60% / 60% |
| 1b5f5c857a8daed1 | 100% / 100% | 40% / 40% | 100% / 100% | 100% / 40% | 100% / 60% | 100% / 40% |
| 373039a14221a990 | 100% / 100% | 60% / 80% | 100% / 100% | 80% / 40% | 80% / 40% | 40% / 40% |
| 3be7664fe9d9ee95 | 100% / 100% | 40% / 60% | 100% / 100% | 100% / 60% | 100% / 80% | 80% / 60% |
| 3bfe603efd9dfc15 | 100% / 100% | 80% / 40% | 100% / 100% | 100% / 80% | 100% / 80% | 60% / 60% |
| 4574860dc9071e70 | 100% / 100% | 80% / 40% | 100% / 100% | 100% / 50% | 100% / 60% | 80% / 40% |
| 50292d32c65d20a5 | 100% / 100% | 80% / 40% | 100% / 100% | 100% / 50% | 100% / 80% | 100% / 80% |
| 5ab48ddd96dfaa1a | 100% / 100% | 0% / 20% | 100% / 100% | 80% / 20% | 100% / 20% | 40% / 20% |
| 62c07d8864b93953 | 100% / 100% | 60% / 60% | 100% / 100% | 100% / 50% | 100% / 40% | 80% / 60% |
| 7de07b1561ec065a | 100% / 100% | 100% / 20% | 100% / 100% | 100% / 20% | 100% / 100% | 100% / 20% |
| 9013973b161b7157 | 100% / 100% | 0% / 30% | 100% / 100% | 100% / 40% | 100% / 40% | 80% / 70% |
| a4519317aac2a88c | 100% / 100% | 40% / 20% | 100% / 100% | 100% / 20% | 100% / 40% | 40% / 60% |
| a4a150ff72efcbfd | 100% / 100% | 60% / 60% | 100% / 100% | 100% / 40% | 100% / 80% | 80% / 50% |
| c2d290ecef00aa96 | 100% / 100% | 40% / 40% | 100% / 100% | 80% / 100% | 100% / 90% | 100% / 100% |
| c3f84dfad639df9f | 100% / 100% | 20% / 60% | 100% / 100% | 80% / 40% | 100% / 100% | 60% / 90% |
| d3f5921da38cda1f | 100% / 100% | 80% / 50% | 100% / 100% | 100% / 60% | 100% / 80% | 60% / 20% |
| db287a3949ad6402 | 100% / 100% | 80% / 80% | 100% / 100% | 100% / 80% | 100% / 100% | 80% / 60% |
| ec5925cc6f1ac490 | 100% / 100% | 60% / 40% | 100% / 100% | 80% / 40% | 100% / 60% | 80% / 80% |
| f3c0c075cbf656c3 | 100% / 100% | 40% / 60% | 100% / 100% | 100% / 20% | 100% / 80% | 80% / 40% |
