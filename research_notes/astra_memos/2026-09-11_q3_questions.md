Third consultation — Rohin asked for a FULL AUDIT of the assembled next-experiment state by you, then a debate with Fable, then a report to him. Attached: the frozen child spec (CHILD_MECHANISM_v7, sections 0–4, 6, 9), the pretest battery and day plan, the parenting-science survey's one screen and sleep section, and the last eight rulings. You wrote memos 1 and 2 (text-memory reading, write mechanism, car test); assume they were adopted.

New facts since memo 2: node 1's disjoint re-probe is complete — 21 cells; unguarded finals mean −0.025 (3 collapsed reps), gated R3 finals +0.004, R4 finals −0.024 (R4 604's gate-approved adapter has a 0.138 rep); every above-base cell is the 0.2731 routine. Text-memory baseline, 4 lives: brief ≥ adapter in 3 (seed0; seeds 5 and 6, the collapsed lives, where the brief also beats the frozen model), adapter > brief in 1 (seed1, the routine, by 0.013). Crossed cell R2 seed0: adapter + brief together = 0.4987 on the 8-panel (worse than brief-only 0.5291 and adapter-only 0.5262) and 0.1619 on the disjoint panel (worse than everything). Gate floor decay admitted a 0.4933 write over a 0.5307 commit (R4 602). A gym core exists (Gym protocol, reasoning-gym adapter, clone coordinator — barrier-based, to be made asynchronous; private reflection; 76/76 CPU tests; compiler lives byte-identical). Two builds are running: write variants A (today) / B (two-scale + neighbourhood) / C (TMEM-aligned) with a one-GPU A/B/C runner and a reasoning-gym headroom band; and your car test (memory dose–response). Deadline 09-18; node 1 dies 09-14; the two nodes have no network between them (relay via the laptop only).

FABLE'S POSITIONS on the spec's ten decisions (argue against them where you disagree):
D1 write budget: T_max token-pass sampling (a) for the first days, with Rohin's phase A/B (cumulative → incremental on the previous adapter with use/recency-weighted replay, lowered lr) pre-declared as the switch at a fixed sleep K, guarded by a retention canary (earlier families + canary set) — not untested forever, not adopted blind.
D2 R = 2.5 M lineage tokens per write on top of the budget for the taught test life; composition logged.
D3 asynchronous test lives if P6 passes by 09-12 12:00 UTC, else synchronous and labelled.
D4 brake = broken format OR words per unsolved problem < 0.5× frozen OR valid-action rate < 0.5 (interface failure = "can no longer turn work in").
D5 floor = best committed adapter ever; frozen model's score reported beside it.
D6 fast path ON: an exam ≥ 5× tol below the floor rolls back immediately (a wrecked write like 0.114 vs 0.506 must not govern six rounds); patience of three sleeps for ordinary dips.
D7 rows authored under a rolled-back adapter kept and trained equally, share reported.
D8 interface-only Stage-0 rows count as format, not thoughts — allowed, hashed, excluded from every behaviour instrument.
D9 node 1 until 09-14 hosts the SECOND child's parenting phase (3 clones + writer, different seed, no cross-talk) and the child migrates to node 2 on 09-14 (the lineage is files: ledger + adapter + manifest) — two independent children, the first replication.
D10 wait for the freeze entry (≤ 09-12 03:00 UTC); if P1 is late, launch with the labelled default write and label the rounds.
Also: accept 16 turns × 400 tokens now; nudge after 4 silent turns; 3-turn carry-over.

ASK, as a decision memo:
1. FULL AUDIT: the ten most consequential problems in the assembled state (spec, pretests, day plan, survey mapping) — for each: where, why it matters, the fix, and what it costs in hours. Include contradictions between documents and with the rulings, arithmetic you can check, and anything that would make the final compiler-gym comparison uninterpretable.
2. Your ruling on D1–D10 versus Fable's positions (agree / disagree with reason and the measurement that would settle it).
3. The survey's two tensions with Rohin's rulings (no cap on repeats vs decay of identical lesson text; fade-the-unused vs protect rare exceptions): your recommendation.
4. Given the new re-probe and text-memory facts, the honest one-paragraph statement of what the current data support, and the minimal set of numbers the abstract (due 09-18) should carry.
5. The order of work for 09-11 (what runs on which free GPU when, what to build first, what to drop), and the single biggest risk to shipping a result by 09-17.
Be blunt; where you think Fable is wrong, say so and why.
