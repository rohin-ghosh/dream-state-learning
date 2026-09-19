# Repo Mailbox Relay

Git-backed fallback control plane for Astra when this computer cannot SSH to
the helper VM. The repository becomes an async mailbox:

- operator machine writes `mailbox/to_vm/<id>.md`, commits, and pushes;
- VM poller pulls, reads new messages, talks to tmux session `astra2`, writes
  `mailbox/from_vm/<id>.reply.md`, commits, and pushes;
- operator machine pulls and reads replies.

This is deliberately email-style rather than terminal-style. It is slower than
SSH, but it survives network asymmetry and gives longer, auditable replies.

## Security Boundary

Use a private repo for real conversations when possible. If this repo is public,
assume every mailbox message and reply is public.

The VM poller intentionally does not run arbitrary shell commands from mailbox
messages. Supported actions are only:

- `send`: paste a message into Astra's tmux composer and submit it;
- `watch`: capture a redacted tail of Astra's tmux pane;
- `resume`: send `/goal resume` if Astra is idle and paused;
- `status`: report basic tmux/watchdog/git status.

Do not send keys, tokens, lease secrets, internal hostnames, or private IPs
through the mailbox.

## One-Time VM Bootstrap

The VM must run the poller once. If SSH from this computer is unavailable, use
whatever path still reaches the VM or the already-running agent: commit/push
these scripts, then ask the VM-side agent to pull and start:

```bash
cd ~/dream-state
git pull --rebase --autostash
nohup bash tools/repo_mailbox/vm_poll.sh > ~/repo_mailbox_vm.out 2>&1 < /dev/null &
```

The poller is single-instance via `~/.repo_mailbox_vm.pid`.

## Send A Message

From any machine with repo write access:

```bash
bash tools/repo_mailbox/send_message.sh --commit --push "What changed since the last watcher check?"
```

Send a longer file:

```bash
bash tools/repo_mailbox/send_message.sh --commit --push -f /path/to/message.md
```

Request a pane tail without interrupting Astra:

```bash
bash tools/repo_mailbox/send_message.sh --action watch --commit --push
```

Ask the poller to resume a paused goal:

```bash
bash tools/repo_mailbox/send_message.sh --action resume --commit --push
```

If `git push` is not configured for this checkout, omit `--push`; the script
prints the created message path so you can commit/push another way.

## Read Replies

Pull the repo and inspect `mailbox/from_vm/`:

```bash
git pull --rebase --autostash
ls -lt mailbox/from_vm | head
sed -n '1,220p' mailbox/from_vm/<id>.reply.md
```

Replies include the action, delivery status, timestamps, and a redacted pane
tail. If Astra is still working after the wait cap, send a later `watch`
message.

## VM Poller Configuration

Environment variables:

```bash
REPO_MAILBOX_INTERVAL=20          # seconds between pulls
REPO_MAILBOX_WAIT_SECONDS=900     # max wait after send
REPO_MAILBOX_SESSION=astra2       # tmux session
REPO_MAILBOX_REMOTE=origin
REPO_MAILBOX_BRANCH=main
```

The poller commits only reply files under `mailbox/from_vm/`. It skips a
message once the matching reply file exists.
