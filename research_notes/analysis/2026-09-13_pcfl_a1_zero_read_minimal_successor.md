# PCFL A1 zero-READ result: minimal development successor

**Date:** 2026-09-13  
**Observed result:** the completed exploratory A1 stage made 64 native calls,
served zero READs, and produced zero successful routes. All 64 first responses
began with `ROUTE`; 48 were invalid complete guesses and 16 exhausted the
256-token response cap. The run itself completed/replayed/released cleanly and
performed zero fits/updates.

## Interpretation

This is not evidence that the memory service failed: it was never invoked. It
shows that merely documenting the three READ commands does not cause this
Qwen2.5-7B child to choose memory before guessing. The mismatch is also visible
in the specification: A1's acceptance requires a READ, but the public prompt
says only that READ is available and capped; it never requires one.

## Smallest successor

Use a newly named exposed-root development prompt that adds exactly one
answer-free behavioral requirement:

```text
Before any ROUTE, you must issue at least one READ. Use only the public START
and exact identifiers returned by memory; never invent a READ address.
```

Do not say which READ form to use, reveal a registered address, return a row in
advance, name a route, or correct a failed choice. The obvious legal first move
remains child-selected: `READ EVENTS_AT <public START>`. All READ/ROUTE parsers,
service bytes, tasks, roots, seeds, caps, raw capture, and same-task reducer stay
unchanged.

First run an eight-task smoke balanced across the four exposed roots and both
goals (maximum 104 calls). Continue once to the frozen 64-task development
panel only if at least 7/8 tasks issue a legal registered non-MISS READ with no
invalid turn. The 64-task gate remains 60/64. Both stages are optimization data,
not confirmation and never training material.

If the smoke still produces zero/near-zero legal reads, stop prompt prose
iterations. The next comparison should be a symmetric typed-tool/structured
action interface for every arm, explicitly labeled external action-format
scaffolding; do not keep adding examples or useful addresses to A1.

Route success after the first READ remains diagnostic. A handshake pass only
establishes that the child can call and consume the service when instructed;
connected traversal still requires the full active-memory ceiling and unseen
confirmation.
