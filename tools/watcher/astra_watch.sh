#!/bin/bash
# 2-hour watch on the orchestrator pane: approve prompts, flush queued inputs when idle, resume a paused goal when idle.
END=$(( $(date +%s) + 7200 )); T=0
while [ $(date +%s) -lt $END ]; do
  T=$((T+1)); TS=$(date -u +%H:%M:%SZ)
  P=$(tmux capture-pane -p -t astra2 2>/dev/null)
  if echo "$P" | grep -q 'Press enter to confirm\|Yes, proceed\|Allow command\|Approve'; then
    CMD=$(echo "$P" | grep -i -m1 -A2 'confirm\|proceed\|Allow' | tr '\n' ' ' | cut -c1-200 | sed -E 's/sk-[A-Za-z0-9_-]+/[key]/g')
    if echo "$CMD" | grep -qi 'ssh/config\|id_rsa\|\.token\|api_key\|OPENAI_API_KEY'; then echo "$TS DECLINED (credential exposure): $CMD"; else tmux send-keys -t astra2 Enter; echo "$TS APPROVED: $CMD"; fi
  fi
  BUSY=$(echo "$P" | grep -c 'esc to interrupt')
  if [ "$BUSY" = "0" ] && echo "$P" | grep -q 'Queued follow-up'; then tmux send-keys -t astra2 S-Left; sleep 2; tmux send-keys -t astra2 Enter; echo "$TS flushed queued input"; fi
  if [ "$BUSY" = "0" ] && echo "$P" | grep -q 'Goal paused'; then sleep 20; P2=$(tmux capture-pane -p -t astra2); if ! echo "$P2" | grep -q 'esc to interrupt'; then tmux send-keys -t astra2 -l '/goal resume'; sleep 1; tmux send-keys -t astra2 Enter; echo "$TS sent /goal resume (idle + paused)"; fi; fi
  echo "$TS tick $T: busy=$BUSY $(echo "$P" | grep -o 'Goal paused' | head -1)"
  sleep 900
done
