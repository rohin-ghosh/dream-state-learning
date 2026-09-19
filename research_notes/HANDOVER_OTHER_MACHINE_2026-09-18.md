# Handing control of Astra, the fleet and Colossus to another computer (Fable for Rohin, 2026-09-18 evening)

Nothing that matters runs on the laptop. Astra is a Codex thread on the always-on VM; the children run on the GPU nodes; the leases live in Colossus. The laptop holds only three things: ssh access, the repo checkout with its gitignored `gpu/hosts.env`, and the Colossus CLI. The watcher (Fable) is a Claude Code session whose standing rules live in a memory directory. Move those and the other machine has everything.

## 1. What is where

| Thing | Where it lives | What the other machine needs |
|---|---|---|
| Astra (orchestrator) | Codex thread `01a0a2f4-1c22-7e03-bac2-bb3231b4e5cf` on the VM, tmux session `astra2`, cwd `/data/home/rohing/dream-state-orch`; launched by `~/.local/bin/codex-astra --sandbox workspace-write resume <id>` (wrapper sources `~/.codex/nvidia.env`; Codex auth in `~/.codex/auth.json`) | ssh to the VM. Nothing else: the keys and Codex login are on the VM. |
| Children, judges, probes | GPU nodes (node 1 a100, node 2 ovx, node 3 ovx2, node 4 a40r, node 5 ovx3, ovx4, ovx5) under `/localhome/local-rohing/` | ssh to each node (same key as the VM if you used one key). |
| Repo | `github` origin `main`; laptop checkout `~/dream-state`; VM clone `dream-state-orch` (Astra pushes from it) | `git clone` + `gpu/hosts.env` copied by hand (gitignored; internal hostnames only, no secrets; see `gpu/hosts.env.example`). |
| Colossus leases | Colossus service; CLI on the laptop at `~/.venvs/colossus-cli/bin/colossus` | Install the CLI in a venv on the other machine and log in the same way you did here (`colossus --help` shows the auth command); leases are account-bound, not machine-bound. |
| Watcher (Fable) | Claude Code session in `~/dream-state`; memory at `~/.claude/projects/-Users-rohing/memory/` (pinned rules: report style, approve-and-interrupt, continuous work, thesis, numbers-are-guesses) | Claude Code installed; copy the memory directory to the same path pattern on the other machine (`~/.claude/projects/<escaped-cwd>/memory/`); the check prompt is in `tools/watcher/CHECK_PROMPT.md`. |
| Watcher scripts | `tools/watcher/` (committed tonight): `clone_scan.py`, `recent_turns.py`, `c2_post_sleep.py`, `p7_watch.py`, `astra_watch.sh`; talk commands `gpu/talk.sh` (children) and `gpu/talk_astra.sh` (Astra) | via git. |

## 2. Steps on the other machine

1. **ssh.** Put your private key(s) there (or generate a new key and add its public half to `~/.ssh/authorized_keys` on the VM and every node from this laptop while it still works). Test: `ssh <vm> 'tmux ls'` must list `astra2`.
2. **Repo.** `git clone <origin> ~/dream-state && cd ~/dream-state`. Copy `gpu/hosts.env` from this laptop (`scp` or paste; it is gitignored). Test: `bash gpu/talk_astra.sh --watch 20` prints Astra's pane; `bash gpu/talk.sh --list` prints the children.
3. **Astra.** You do not restart anything. To talk: `bash gpu/talk_astra.sh "…"`. To look: `--watch 60` or `--attach` (read-only tmux; Ctrl-b then d to leave). If the VM ever reboots again: `ssh <vm>`, then `tmux new -d -s astra2 -c /data/home/rohing/dream-state-orch "~/.local/bin/codex-astra --sandbox workspace-write resume 01a0a2f4-1c22-7e03-bac2-bb3231b4e5cf"` — run it as the tmux command, not inside a login shell (your `~/.bashrc` on the VM auto-starts a Claude Code session in interactive shells). Then relaunch the approval watch: `nohup bash tools/watcher/astra_watch.sh >> /tmp/astra_watch.log &` on the VM (copy the script there first).
4. **Colossus.** `python3 -m venv ~/.venvs/colossus-cli && ~/.venvs/colossus-cli/bin/pip install <colossus cli package>` (same package you installed here), then the login step, then check: `~/.venvs/colossus-cli/bin/colossus bm lease list --status ACTIVE --json | python3 -c 'import json,sys; [print(l["lease_details"].get("lease_id"), l["lease_details"].get("end_time")) for l in json.load(sys.stdin)]'`. Extend with `bm lease extend --lease-id <id> --duration 3d` (quota is a rolling 30-day window; 3-day extensions have been accepted, 5- and 8-day ones refused). Never print `lease_secrets`.
5. **Watcher.** Install Claude Code, copy the memory directory, open Claude Code in `~/dream-state`, and start the loop with the prompt in `tools/watcher/CHECK_PROMPT.md` (`/loop 30m <prompt>`). The first thing it should do is a liveness scan; the rules it must follow are in the pinned memories and `CLAUDE.md`.
6. **Retire this laptop cleanly.** Stop its Claude Code session so two watchers do not both press Enter on Astra's approval prompts. The node-side daemons (C2 and P7 watchers, approval watch) run on the nodes and the VM and keep going.

## 3. Lease and bound dates to carry over (as of 2026-09-18)

Leases: node 5 (ipp2-ovx-p1-10) to 09-21 21:04 PDT; node 2 (ipp2-ovx-p2-08) to 09-21; node 3 (ipp2-ovx-p6-09) to 09-25; node 1 (a4u8g-0147) to 09-26; a4u8g-0105 to 09-28; ovx5 (ipp2-ovx-p6-07) to 09-29; ovx4 (ipp2-ovx-p3-02) to 10-01. The kept lives' resident wall bounds were set today to lease end minus a margin (node 3 to 09-24 18:00Z, C0/Astra7/C2 to 09-20 18:00Z, P3/P7 to 09-25, learner/sibling/base to 09-30). Node 5 and node 2 need extending before 09-21 or C2 and C0 stop with them.
