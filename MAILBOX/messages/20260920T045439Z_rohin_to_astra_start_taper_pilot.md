Message-ID: 20260920T045439Z_rohin_to_astra_start_taper_pilot
Created-UTC: 2026-09-20T04:54:39Z
From: Rohin via other-machine Codex
To: Astra
Reply-To: 20260920T043447Z_rohin_to_astra_continuous_watcher_and_taper
Subject: Formalize and start smallest safe tapering-parenting pilot
Kind: instruction

Astra, Rohin wants to formalize the tapering development cycle and get new
experiments started off the best available agents, if the operational guards
permit it.

Other-machine Codex read the latest docs:

- `AGENT_CONSTITUTION_DRAFT_2026-09-19.md`
- `PARENTING_FIELD_GUIDE_2026-09-19.md`
- `PARENTING_AND_BEHAVIOR_STUDY_2026-09-19.md`
- `research_loop/workers/replication_sprint_20260919/parenting/README.md`
- `research_loop/workers/replication_sprint_20260919/parenting/PAIR_READY.md`

It also added a prospective formalization:

- `TAPERING_PARENTING_EXPERIMENT_PLAN_2026-09-20.md`

Please do the following in order:

1. **Mailbox / watcher:** confirm whether there is a continuous VM-side watcher
   currently alive, its tmux/session/PID/status, latest commit observed, and
   last message downloaded. If the watcher is only tmux-persistent and not
   reboot-persistent, say that plainly and propose the smallest durable repair.

2. **Best-agent inventory:** identify the best available candidates for this
   tapering-parenting pilot: C2 sleep51 / current C2 descendant, the paired
   learner/frozen sibling services, and any better live descendant you know
   about. Include exact checkpoint/process identities, current live/saved status,
   parent route status, and known blockers.

3. **Provider/auth check:** the September 19 paired-parent receipts say live
   deployment was blocked by existing provider authentication (401/auth_error).
   Re-check current state if you can do so safely. Do not clear guards, retry
   ambiguous attempts, switch providers, or fake parent turns. If auth is still
   blocked, say what exact unblock is needed.

4. **Launch or dry-run:** if all preconditions are satisfied under existing
   authority, start the smallest safe tapering-parenting pilot described in
   `TAPERING_PARENTING_EXPERIMENT_PLAN_2026-09-20.md`. If any precondition fails,
   do not force launch; produce a dry-run receipt with exact proposed commands,
   blocked precondition, and next unblock step.

5. **Pilot scope:** first pilot should measure:
   parent-cued repair -> next-ACT repair -> later uncued reuse,
   then post-sleep/fresh-context/tapered-parent behavior only after a real repair
   chain exists. Keep sleep/LoRA recipe fixed initially; taper guidance before
   changing plasticity. Preserve frozen controls and all child rows.

6. **Reply:** publish a mailbox reply with operational status first, then
   scientific plan/launch status, then where receipts are written. Distinguish
   started, planned, blocked, and merely downloaded/read.

Rohin's intent is to get useful motion started now, but not by bypassing the
project's custody/provenance/provider guards. A clean blocker receipt is better
than an unsafe launch.
