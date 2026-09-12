# dream-state — standing rules for Claude Code agents and subagents

## Web access: never call the WebFetch tool
The org-managed Claude Code policy puts `WebFetch` in the permissions *ask* list. A managed ask rule overrides every user/project allow rule, so each WebFetch call pops a permission prompt on Rohin's terminal (a survey run produced ~100 prompts). `WebSearch` and Bash are unrestricted.

- To read a page, README, arXiv abstract or JSON API from the shell:
  `python3 tools/webtext.py URL [URL ...] --max 30000` (GitHub repo URL → metadata + README; arXiv abs/pdf URL → title, authors, abstract, dates; anything else → HTML stripped to text; batch several URLs per call; `--out FILE` to save).
- Plain `curl` in Bash is also fine. Do not call WebFetch, and forbid it explicitly in every subagent or workflow prompt you write.

## Secrets and hosts
API keys are passed environment-only at launch and never written to files, logs or ledgers. Internal hostnames/IPs live only in the gitignored `gpu/hosts.env`.

## Parent servers on the nodes: when is one idle?
A vLLM parent server (Qwen2.5-14B on port 8011) is used by parented lives (RP) AND by R4 lives (gate + panel + parent brief) — but only at sleep time, every 32 episodes. A momentary "zero established connections" therefore proves nothing. Before stopping a parent server: list every running life on that node (`pgrep -f run_life_v2`), and for each check whether its sleep dirs contain `parent_brief.json` and whether it still has sleeps to run (sleep dirs < 32, no LIFE_DONE). Stop the server only if no such life exists. Incident: 2026-09-12 00:25 UTC, R4_B_seed605 crashed at its final sleep after the server was stopped at 23:10 (COORDINATION.md).
