# 22 — Verified Submission Deadlines (as of Aug 11, 2026)

Scope: venues for the Dream-State paper(s) — LLM-agent memory / continual learning / benchmarks.
Assumptions for "realistic?": **benchmark paper ready in ~4-8 weeks** (mid-Sept to early Oct 2026); **method paper needs GPU experiments, ~2-4 months** (mid-Oct to mid-Dec 2026).

All dates AoE unless noted. ✅ = verified directly on official page; ⚠️ = not directly verifiable (estimate/third-party).

## Master table (sorted by deadline from Aug 11, 2026)

| # | Venue | Deadline (abstract / full) | Notification | Conference date & place | Verified on | Realistic for us? |
|---|-------|---------------------------|--------------|------------------------|-------------|-------------------|
| 1 | ✅ AAAI-27 Special Track on AI Alignment | Abs **Aug 14, 2026** / Full **Aug 21, 2026** | Nov 30, 2026 | Feb 16-23, 2027, Montréal | https://aaai.org/conference/aaai/aaai-27/aia-call/ | **No** — 3 days out, and scope (alignment) is a poor fit. Note: AAAI-27 **main track already closed** (abs Jul 21 / full Jul 28, 2026; verified at https://aaai.org/conference/aaai/aaai-27/main-technical-track-call/). |
| 2 | ✅ **PALM @ NeurIPS 2026** — "Personalized, Aligned, Long-Term Memory for AI Systems" workshop (Paris) | **Aug 24, 2026** (regular); Oct 1, 2026 fast-track for NeurIPS-reviewed papers | Sep 29, 2026 | Dec 12 or 13, 2026, Paris | https://palm-neurips-2026.github.io/ (submit: OpenReview NeurIPS.cc/2026/Workshop/PALM) | **Stretch but high-value** — 13 days. Perfect topical fit (the MemAgents-successor slot). Non-archival; accepts 4-page short papers → submit benchmark design + preliminary results as short paper. |
| 3 | ✅ **CL4FMAgents @ NeurIPS 2026** — "Continual Learning in the Era of Foundation Models and Embodied Agents" | **Aug 29, 2026** | Sep 29, 2026 | Dec 11-12, 2026, Sydney | https://neurips26-cl4fmagents.github.io/ | **Stretch** — 18 days; workshop-length WIP version feasible. Strong fit for the continual-learning framing. |
| 4 | ✅ **TTCL @ NeurIPS 2026** — "Towards Test-Time Continual Learning Agents" | **Aug 29, 2026** | Sep 25, 2026 | Dec 12 or 13, 2026, Atlanta | https://ttcl-agents.github.io/ | **Stretch** — same as above; very strong fit for wake/sleep test-time learning angle. |
| 5 | ⚠️ Other NeurIPS 2026 agent workshops: SLM-Agents (Aug 23), Interpreting Agent Behavior (Aug 29), Meta Agents (Aug 30), Who Verifies the Agents? (Aug 30) | Aug 23-30, 2026 | ≤ Sep 29, 2026 (NeurIPS-mandated) | Dec 11-13, 2026 (Sydney/Paris/Atlanta) | Tracker only: https://aiworkshoptracker.com/conference/neurips/ — individual sites not checked | Backup options; weaker fit than #2-4. NeurIPS rule (verified at https://neurips.cc/Conferences/2026/WorkshopsGuidance): suggested deadline Aug 29, **hard notification deadline Sep 29, 2026**. |
| 6 | ✅ **ICLR 2027** (main conference) | Abs **Sep 18, 2026** / Full **Sep 25, 2026** | Reviews Nov 5; discussion to Nov 18; **final decisions Dec 16, 2026** | Main conf Apr 26-28, workshops Apr 28-30, 2027; location TBA on official page | https://iclr.cc/Conferences/2027/Dates | **Yes for benchmark paper** (5.5 weeks — at the fast end of 4-8 wk estimate; commit now). **Method paper: very tight/no** unless GPU experiments are already substantially underway. THE target venue. |
| 7 | ⚠️ **AISTATS 2027** | Expected **~early Oct 2026** (pattern: Oct 2 '24, Oct 10 '23, Oct 16 '22; third-party lists Oct 8, 2026) | ~Jan 2027 (unannounced) | ~Apr-May 2027, location conflicting across trackers (Paris per one) | **NOT VERIFIED** — aistats.org has no 2027 CFP yet; third-party only (getpaperpilot.com) | Timing fits benchmark paper as ICLR backup, but topical fit is mediocre (stats-flavored venue). Re-check aistats.org in Sept. |
| 8 | ✅ **ARR October 2026 cycle** (→ NAACL 2027 / COLING 2027) | **Oct 12, 2026** | Reviews before commitment **Dec 20, 2026** | NAACL/COLING 2027 (dates per those venues) | https://aclrollingreview.org/dates | **Yes for benchmark paper** — 9 weeks, comfortable. Good fit if framed as an NLP-flavored agent-memory benchmark. |
| 9 | ✅ **ACL 2027 via ARR January 2027 cycle** | **~Jan 2027** ARR submission (exact date TBA on ARR page); note Aug 2026 cycle (Aug 3) already closed, fed EACL 2027 | commitment ~Mar 2027 | ACL 2027, summer 2027 | https://aclrollingreview.org/dates | **Yes for method paper** — Jan cycle gives ~5 months of GPU time. |
| 10 | ⚠️ **ICML 2027** | Expected **~late Jan 2027** (ICML 2026 full deadline was Jan 28, 2026); nothing official | ~May 2027 | Location "South America" per official Future Meetings page; dates TBA | Partially verified: https://icml.cc/Conferences/FutureMeetings (location only); https://icml.cc/Conferences/2027/Dates is 404. A search snippet claiming "Sep 15, 2026" deadline / "Seoul May 2027" is wrong (confusion with ICML 2026). | **Yes — primary target for the method paper** (~5.5 months of runway). Verify exact date when CFP posts (~Oct-Nov 2026). |
| 11 | ⚠️ **ICLR 2027 workshops** (incl. possible MemAgents 2027) | Proposals expected ~Oct 2026 (ICLR 2026 pattern: Oct 10, 2025); papers expected **~early Feb 2027** | ~Mar 2027 | Workshops Apr 28-30, 2027 (verified on ICLR dates page) | **NOT VERIFIED** — no 2027 workshop CFP yet; pattern from https://iclr.cc/Conferences/2026/CallForWorkshops. MemAgents ran at ICLR 2026 (https://sites.google.com/view/memagent-iclr26/); 2027 recurrence unknown. | **Yes** — natural landing spot for method-paper WIP or benchmark spin-off in Feb 2027. |
| 12 | ⚠️ **CoLM 2027** | Expected **~late Mar 2027** (CoLM 2026: abs Mar 26 / paper Mar 31, 2026) | ~Jul 2027 (2026 pattern: Jul 8) | Oct 2027 (2026 edition: Oct 6-9, San Francisco) | **NOT VERIFIED** — colmweb.org/dates.html still shows only 2026; pattern-based | **Yes for method paper** — latest safe harbor; ~7.5 months runway. |

## Recommended plan

- **Now → Aug 24-29:** short-paper (4 pg) version of the benchmark to **PALM** (Aug 24) and/or **TTCL / CL4FMAgents** (Aug 29). Non-archival, so it does not burn the ICLR submission; buys visibility + feedback in exactly our niche.
- **Now → Sep 18/25:** full benchmark paper to **ICLR 2027** (abstract Sep 18, paper Sep 25). This is the main shot; 5.5 weeks is inside the 4-8 wk estimate only at the fast end — decide by ~Aug 18.
- **Fallback for benchmark:** ARR Oct 12 cycle (→ NAACL 2027) or AISTATS (~Oct 8, pending CFP).
- **Method paper:** target **ICML 2027 (~late Jan)**, with ARR Jan 2027 cycle (→ ACL 2027) and CoLM 2027 (~Mar) as alternates; ICLR 2027 workshops (~Feb) for the WIP version.

## Verification caveats

- Rows 7, 10 (deadline), 11, 12 are **pattern-based estimates**, not official — re-check in Sept/Oct 2026.
- Row 5 workshop deadlines come from aiworkshoptracker.com, not the workshops' own pages.
- Tracker/aggregator sites disagreed in several places (e.g., PALM listed Aug 24 vs. site-confirmed Aug 24 regular + Oct 1 fast-track; CL4FMAgents tracker said Aug 30 vs. official site Aug 29; a search result gave a bogus ICML 2027 "Sep 15/Seoul" answer). Official sites were preferred everywhere they existed.
- ICLR 2027 location: official Dates page still says TBA (ignore third-party "Sydney" claims).
