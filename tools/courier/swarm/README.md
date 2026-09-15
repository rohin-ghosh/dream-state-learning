# Fable parent swarm (PARENTING_BATTLE_PLAN_v4 §6)

- `prompts/F1..F4.md` — the fixed parent prompt (extracted from the plan's `> You are the parent…` block) with
  [GAME]/[STYLE]/[NUDGING]/[FOCUS] filled; `F<n>.fields.json` (schema ORCH_R114_HEAD_FIELDS_V1) carries the fields incl.
  REFLECTION{mode,max_new_tokens} and the .md sha256. Consumed by Astra's `gpu/orch_r110_claude_broker.py`
  (`--prompt-root`), re-read on every parent call. Regenerate with `python3 tools/courier/swarm/make_prompts.py`.
- `head_parent.md` + `head_parent.sh` — the head parent (one `claude -p --effort max` call per new Fable sleep,
  cron `10,40 * * * *` on the VM (the reader runs at :05 and :35, so those minutes always skipped)); edits STYLE/FOCUS/REFLECTION only; appends to research_loop/PARENTING_EXCHANGE.md.
- VM runtime: `~/courier/swarm/{prompts/,branches.json,head_state.json,cycles/,head_parent.log}`; `branches.json` maps
  F<n> → {"node": "ovx3", "root": "/localhome/…"} and is written once Astra posts the branch roots.
No hostnames, keys or raw transcripts live here.
