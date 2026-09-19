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

## 4. What a fresh Codex checkout still needs before it can operate

Status from a fresh checkout at `/Users/rohinghosh/Documents/New project/dream-state-learning`, checked 2026-09-19 PDT: the repository contains the operating procedure and wrapper scripts, but not the private local state required to reach the VM, GPU nodes, or Colossus. This is intentional. Do not put the missing host map, keys, tokens, or lease secrets in git.

### Required private host map

Create or copy `gpu/hosts.env`. It is gitignored by `.gitignore` and is absent in a clean clone. Without it, the first real control command fails immediately:

```bash
bash gpu/talk_astra.sh --watch 5
# gpu/hosts.env missing (see hosts.env.example)
```

The file should contain shell assignments for every active wrapper that may be used. Use `user@host` or the SSH alias that already works from the machine; do not include passwords, tokens, lease secrets, or comments containing internal IPs that will be copied into reports.

Minimum current variable set:

```bash
NVL_HOST="user@helper-vm"      # always-on VM that hosts Astra's tmux session
A100_NODE="user@node-1"        # a100_ssh.sh
OVX_NODE="user@node-2"         # ovx_ssh.sh
OVX2_NODE="user@node-3"        # ovx2_ssh.sh
OVX3_NODE="user@node-5"        # ovx3_ssh.sh; C2 / community lives
OVX4_NODE="user@ovx4"          # ovx4_ssh.sh; curriculum learner/frozen sibling
OVX5_NODE="user@ovx5"          # ovx5_ssh.sh, if still leased
A40_NODE="user@old-a40"        # a40_ssh.sh, legacy wrapper
A40R_NODE="user@node-4"        # a40r_ssh.sh; P3/P7 fleet
GH200_NODE="user@gh200"        # gh200_ssh.sh, if active
V2_NODE="user@v2-node"         # v2node_ssh.sh, if active
```

The committed `gpu/hosts.env.example` is only a stub. It does not list all wrappers now used by the watcher flow. If a wrapper is not active, either leave its variable unset and avoid that wrapper, or set it to a valid SSH alias for the active replacement.

### Required SSH access

The machine needs a private key or agent configuration that can reach:

- `NVL_HOST`, where Astra runs in tmux session `astra2`.
- Every active GPU node named in `gpu/hosts.env`.
- GitHub, preferably over SSH, if this machine must push commits.

Smoke tests after `gpu/hosts.env` is present:

```bash
bash gpu/nvl_ssh.sh 'tmux ls'
bash gpu/talk_astra.sh --watch 20
bash gpu/talk.sh --list
perl -e 'alarm 100; exec @ARGV' bash gpu/ovx3_ssh.sh 'hostname; nvidia-smi -L | head'
perl -e 'alarm 100; exec @ARGV' bash gpu/a40r_ssh.sh 'hostname; nvidia-smi -L | head'
perl -e 'alarm 100; exec @ARGV' bash gpu/ovx2_ssh.sh 'hostname; nvidia-smi -L | head'
perl -e 'alarm 100; exec @ARGV' bash gpu/ovx4_ssh.sh 'hostname; nvidia-smi -L | head'
```

Expected meaning:

- `tmux ls` must show `astra2`.
- `talk_astra.sh --watch` must print Astra's pane, with hostnames and IPs redacted by the wrapper.
- `talk.sh --list` is local and only proves aliases exist; it does not prove node reachability.
- Each bounded node SSH call must return promptly. If it hangs or asks an interactive question, fix SSH known-hosts/key access before starting watcher work.

### Required Colossus access

This checkout does not by itself provide the Colossus CLI or login. The handoff expects:

```bash
~/.venvs/colossus-cli/bin/colossus
```

If absent, install the same package used on the original machine, then perform the Colossus login flow. After login, verify leases without printing secrets:

```bash
~/.venvs/colossus-cli/bin/colossus bm lease list --status ACTIVE --json \
  | python3 -c 'import json,sys; [print(l["lease_details"].get("lease_id"), l["lease_details"].get("end_time")) for l in json.load(sys.stdin)]'
```

Never print or paste `lease_secrets`. Extend leases only with explicit intent. The historical note says 3-day extensions have worked, while 5- and 8-day extensions were refused; re-check current quota before assuming that still holds.

For inventory search without the CLI, `gpu/scout.py` can query Colossus when `COLOSSUS_TOKEN` is supplied in the environment. That token is short-lived and must remain env-only:

```bash
COLOSSUS_TOKEN=... python3 gpu/scout.py
COLOSSUS_TOKEN=... python3 gpu/scout.py --any
```

### Required watcher state

To run the Fable/watcher loop faithfully, the machine needs:

- A current repo checkout on `main`.
- The private `gpu/hosts.env`.
- Claude Code or Codex environment capable of running the loop.
- The watcher memory directory copied to the path pattern described above, if reproducing Fable's exact standing memory matters.
- The committed prompt in `tools/watcher/CHECK_PROMPT.md`.

First watcher action after setup should be a liveness scan, not a launch. The watcher role is relay/diagnosis. It should not start new lives by itself. If it finds a stall, it should identify the exit reason and relay the concrete restart order to Astra.

### Operational readiness checklist for Codex

Before saying "I can do shit" from a new machine, require all of the following to pass:

```bash
test -f gpu/hosts.env
bash gpu/talk_astra.sh --watch 20
bash gpu/talk.sh --list
bash gpu/nvl_ssh.sh 'tmux capture-pane -p -t astra2 | tail -n 20'
bash gpu/nvl_ssh.sh 'pgrep -fc "[a]stra_watch.sh"'
test -x ~/.venvs/colossus-cli/bin/colossus
~/.venvs/colossus-cli/bin/colossus bm lease list --status ACTIVE --json >/tmp/colossus_active_leases.json
git status --short --branch
git ls-remote --heads origin main >/dev/null
```

Then run the bounded fleet checks from `tools/watcher/CHECK_PROMPT.md` over the kept roots. Record only high-level movement/stall facts in reports; do not paste internal hostnames, IPs, tokens, keys, or lease secrets.

### If something is missing

- Missing `gpu/hosts.env`: copy it from the working laptop or reconstruct it from known SSH aliases. Do not commit it.
- Missing SSH key access: add the new public key to the VM and active nodes from a machine that still has access, or use the existing key/agent.
- Missing Colossus CLI: install the CLI in `~/.venvs/colossus-cli`, log in, and verify active leases.
- Missing Astra tmux session: use the VM reboot recipe in section 2. Do not restart Astra if `astra2` already exists.
- Missing GitHub push auth: use SSH remote or the GitHub connector if it has write permission; otherwise edits can be local but not published.
- Missing watcher memory: the scripts still work, but the watcher may lose Rohin's pinned report style and standing rules. Re-copy memory before unattended looping.

## 5. Repo mailbox fallback when this computer cannot reach the VM

Decision, 2026-09-19 PDT: if the current computer cannot SSH to the helper VM, use a Git-backed mailbox rather than exposing tmux on a public host. This makes the conversation email-style: slower, but durable, auditable, and safer than a public terminal.

The implementation lives in `tools/repo_mailbox/`:

- `tools/repo_mailbox/send_message.sh` creates `mailbox/to_vm/<id>.md` messages.
- `tools/repo_mailbox/vm_poll.sh` runs on the VM, pulls messages, talks to Astra's tmux session, writes `mailbox/from_vm/<id>.reply.md`, commits, and pushes.
- `tools/repo_mailbox/README.md` documents setup, supported actions, and safety boundaries.

Supported mailbox actions are intentionally narrow:

- `send`: paste a Rohin message into Astra and wait for a reply/pane tail.
- `watch`: capture Astra's redacted pane tail without interrupting it.
- `resume`: send `/goal resume` only if Astra is idle and paused.
- `status`: report basic tmux/watchdog/git status.

There is no arbitrary shell action. If the mailbox repo is public, every message and reply is public; use a private repo or private branch for real conversations if possible. Do not put keys, tokens, lease secrets, internal hostnames, or private IPs in mailbox messages.

Bootstrap still requires the VM to start the poller once. If direct SSH from this computer is impossible, commit/push these scripts and use whatever path still reaches the VM or the running VM-side agent to run:

```bash
cd ~/dream-state
git pull --rebase --autostash
nohup bash tools/repo_mailbox/vm_poll.sh > ~/repo_mailbox_vm.out 2>&1 < /dev/null &
```

After that, from this computer:

```bash
bash tools/repo_mailbox/send_message.sh --commit --push "What changed since the last watcher check?"
git pull --rebase --autostash
ls -lt mailbox/from_vm | head
```

For continuous conversation, send one mailbox message per turn and pull replies. Longer instructions and longer replies are fine; this path is optimized for reliability, not immediacy.
