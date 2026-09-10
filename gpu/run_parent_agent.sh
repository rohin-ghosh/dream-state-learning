#!/bin/bash
# Smoke-run the AGENTIC PARENT room against one life directory, ON a node.
#
# The provider configuration comes ONLY from the caller's environment. Export
# it in your ssh session; never put a key in a file, a script, an argument or
# the shell history of a shared account:
#
#   set +o history                       # (bash) keep the key out of history
#   export PARENT_A_PROVIDER=anthropic PARENT_A_MODEL=claude-fable-5-1
#   export PARENT_A_BASE_URL=https://<inference-hub>/v1 PARENT_A_API_KEY=...
#   export PARENT_B_PROVIDER=openai_compat PARENT_B_MODEL=<astra-model>
#   export PARENT_B_BASE_URL=https://<inference-hub>/v1 PARENT_B_API_KEY=...
#   export PARENT_REASONING=high PARENT_MAX_TOOL_CALLS=8
#   bash gpu/run_parent_agent.sh ~/v6_out/RP_B_seed400            # smoke
#   bash gpu/run_parent_agent.sh ~/v6_out/RP_B_seed400 --mock     # no network
#
# Optional knobs (defaults in parentheses; see the agentic_parent docstring):
#   PARENT_MAX_TOKENS        output cap per call, thinking included (16000 for
#                            anthropic and for openai_compat with reasoning;
#                            4000 openai_compat without; 2000 local). A reply
#                            cut at the cap is retried once with a doubled cap.
#   PARENT_MAX_TOKENS_FIELD  max_completion_tokens (openai_compat default; the
#                            inference hub's reasoning models require it) or
#                            max_tokens (local vLLM default). A 400 naming the
#                            field swaps it once automatically.
#   PARENT_TIMEOUT_S         per request (240)
#   PARENT_ROOM_TIMEOUT_S    wall clock for the whole room per sleep (900);
#                            past it late phases are skipped and the best
#                            validated proposal (or the fallback) is delivered
#   PARENT_ROOM_MIN_PHASE_S  time a critique/merge phase needs to start (60)
#   PARENT_CRITIQUE_CONTEXT_CHARS  replay budget of a parent's own tool
#                            results into its critique/merge turns (40000)
#
# Single parent: export PARENT_PROVIDER/PARENT_MODEL/PARENT_BASE_URL/
# PARENT_API_KEY instead. Local fallback: PARENT_PROVIDER=local (vLLM at
# http://127.0.0.1:8011/v1, see gpu/launch_parent_server.sh), no key.
# A key with a plaintext http:// base URL is refused unless the host is
# loopback; HTTP redirects are never followed and *_proxy variables are
# ignored, so the key reaches the configured host only.
#
# The smoke run writes to <life>/parent_smoke_<ts>/ (not a sleep_* dir: the
# child never reads it; the child's parent ledger and the society ledger are
# untouched). Pass --commit to write into the latest sleep dir for real.
# agentic_parent removes PARENT_*_API_KEY from its own environment at import
# and masks the key in every file it writes; this script never echoes it.
#
# The life itself switches parents with:  run_life_v2 ... --parent-mode agentic
set -u
LIFE="${1:?usage: run_parent_agent.sh <life_dir> [--mock] [--commit] [--sleep-dir D]}"; shift
cd ~/dream-state
export HF_HUB_OFFLINE=1 PATH=$HOME/v2/venv/bin:$PATH
P=~/v2/venv/bin/python
[ -x "$P" ] || P=python3

MOCK=0; for a in "$@"; do [ "$a" = "--mock" ] && MOCK=1; done
if [ "$MOCK" = 0 ] && [ -z "${PARENT_PROVIDER:-}${PARENT_A_PROVIDER:-}${PARENT_B_PROVIDER:-}" ]; then
  echo "no PARENT_PROVIDER / PARENT_A_PROVIDER / PARENT_B_PROVIDER in the environment (or use --mock)"; exit 2
fi
# report configuration WITHOUT values: only which variables are set
echo "parent env set: $(env | grep -o '^PARENT_[A-Z_]*=' | tr -d '=' | sort | tr '\n' ' ')"
for v in PARENT_API_KEY PARENT_A_API_KEY PARENT_B_API_KEY; do
  [ -n "${!v:-}" ] && echo "$v: present (value not shown)"
done
[ -d "$LIFE" ] || { echo "no such life dir: $LIFE"; exit 2; }
[ -f "$LIFE/ledger.jsonl" ] || { echo "no ledger.jsonl in $LIFE"; exit 2; }

$P -m organism_v6.agentic_parent --life-dir "$LIFE" "$@" 2>&1 | sed -E 's/(sk-[A-Za-z0-9_-]{6})[A-Za-z0-9_-]+/\1***/g'
echo "RUN_PARENT_AGENT_EXIT=${PIPESTATUS[0]}"
