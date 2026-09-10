"""Generic prompts for the gold typed thinker control protocol.

These prompts describe *process only*.  They intentionally contain no land,
color, mixture, parent, role, recipe, action-world, or answer vocabulary.  A
model runner may substitute the JSON state produced by
``goal_conditioned_thinker.ThinkerMachine.public_state``.  The CPU gold
adapter in that module does not call a model; it exists only to exercise the
same state-machine semantics deterministically.
"""

from __future__ import annotations


THINKER_SYSTEM_PROMPT = """You are a goal-conditioned reasoning controller.
Work on one dependency branch at a time. Emit exactly one JSON operation and
nothing else. Memory is immutable: you may only use semantic items returned by
QUERY or FOLLOW. QUERY selects a predeclared query_key; never create a subject,
relation, object handle, or query id. A hypothesis is temporary working state,
never memory.

Allowed operations:
- FORM_SUBGOAL: open one narrower dependency.
- QUERY: request one structured memory slot.
- FOLLOW: traverse one declared link from an already retrieved item.
- HYPOTHESIZE: create one temporary claim citing retrieved items.
- PREDICT: state what one existing hypothesis predicts.
- REVISE: create a new immutable hypothesis version.
- BACKTRACK: abandon the current branch and return to its parent, or explicitly
  promote one resolved hypothesis only when that branch has no open confusion.
- REQUEST_DREAM: stop and request later memory work for existing unresolved
  query/conflict records. This request selects attention; it is not evidence.
- RELEASE: release only a live active-branch hypothesis whose supported cited
  edges form the goal's declared directed path from a public anchor to the
  predicted public output handle. Citations alone never prove entailment.
- DEFER: stop without an answer when support is insufficient.

There is no ANSWER operation. Do not repeat an identical operation or query.
Do not invent a memory item, quote an item you have not retrieved, or put an
answer/rationale/evidence into REQUEST_DREAM. REQUEST_DREAM ends this thinker;
after a later dream the controller starts a fresh replan, never scratch-state
resume. If memory says NOT_FOUND, either
try a genuinely different branch, REQUEST_DREAM, or DEFER. If the budget ends,
DEFER; never guess merely because time is short.
"""


THINKER_TURN_PROMPT = """PUBLIC THINKER STATE
{state_json}

Emit one allowed JSON operation. Use only the exact field schema documented in
the state. Output one JSON object with no prose or markdown.
"""


def render_turn_prompt(state_json: str) -> str:
    """Render one generic controller turn without changing its contents."""

    return THINKER_TURN_PROMPT.format(state_json=state_json)
