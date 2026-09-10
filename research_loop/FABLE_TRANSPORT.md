# Fable reviewer transport — LIVE (2026-08-30)

Mailbox (as suggested in notes/40):
  .research_loop/handoffs/inbox/<request_id>.request.json
  .research_loop/handoffs/outbox/<request_id>.response.json

How the Fable side serves it:
1. A background poller in the interactive Fable session detects new
   inbox requests and wakes the session.
2. The session runs `python3 research_loop/fable_transport.py validate
   <request>` — required fields, prompt/schema existence, SHA-256 checks
   on every context file. Any problem -> response verdict "escalate"
   (never guessed content).
3. INDEPENDENCE (handoff clause 5, disclosed here and in every
   response summary): the interactive session is NOT fresh. Each review
   is therefore produced by a FRESHLY SPAWNED subagent that receives
   ONLY the request's prompt + context files, read-only, with no access
   to the session's history or the implementer's reasoning trace.
4. The subagent's schema-shaped verdict is written via
   `fable_transport.py respond` — minimal-schema validated, atomic
   (tmp+rename), never overwrites an existing response.
5. This path never launches GPU work, edits evaluated experiments,
   pushes, contacts anyone, or touches leases.

Request fields expected: request_id, run_id, node_id, prompt_path,
response_schema_path, context_files [{path, sha256}], autonomy_boundary.
