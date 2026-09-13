# PCFL A3 terminal result: repair the generation frame before judging THINK

**Date:** 2026-09-13 PT  
**Role:** independent read-only result adjudication and prospective DEV repair  
**Scope:** exposed-root interface development only; no source, model, tokenizer,
fit, adapter, benchmark-root, or GPU mutation

## Decision

`A3_THINK` is a **typed-turn framing failure**, not evidence that Qwen cannot
think over the supplied graph. The next smallest experiment is
`A3B_NEWLINE_FRAMED`: preserve the same public task, graph, grammar, sampling,
limits, and exact parsers, but terminate each physical generation at the first
LF before dispatch. Feed an accepted `THINK` line back into the conversation,
append the frozen information-free `CONTINUE` message, and request the next
physical turn.

This is not last-line extraction and does not rescue the rejected A3 bytes.
It changes future generation framing so the already-declared one-line action
protocol is physically realizable. Apply the same framing to every eventual
arm using typed THINK/READ/ROUTE/PROBE turns.

Run an eight-task exposed-root smoke first. Expand to the existing 64-task DEV
panel only if at least 7/8 tasks produce an exact THINK on the first turn, no
mixed accepted turn, and an exact terminal ROUTE within the existing cumulative
budget. If A3B clears the thought-interface gate but not route correctness,
run the already-predeclared generic `A4_SCAFFOLD` under the identical newline
frame. If A3B still cannot sustain typed turns, stop prompt iteration and test
a symmetric structured action channel rather than weakening the parser.

## What actually happened

Authoritative root:

```text
/localhome/local-rohing/astra_diagnostics/
  pcfl_interface_a3_20260913_attempt1
```

The outer worker terminated itself cleanly after the bound controller PID
disappeared. Its terminal report is `COMPLETE`, contains 64 tasks, zero fits,
zero updates, and 13,642 generated actor tokens. The released post-GPU receipt
reports no compute process.

The official reducer is correctly all-zero:

| endpoint | result |
|---|---:|
| exact accepted THINK tasks | 0/64 |
| graph-successful ROUTE tasks | 0/64 |
| stage gate | fail |

But the raw-response shape localizes why:

| raw-response property | count |
|---|---:|
| begins with `THINK ` | 64/64 |
| contains at least one LF | 64/64 |
| contains a later line beginning `ROUTE ` | 54/64 |

For example, the first raw response is one generation containing both:

```text
THINK N_S6JZXHYXBT has a path to N_HJZRZAYWOT through ...
ROUTE N_S6JZXHYXBT N_HJZRZAYWOT : ...
```

The frozen dispatcher requires one complete typed physical line and forbids a
THINK plus an action in one response, so rejection is correct. The model did
what ordinary autoregressive decoding naturally does: after producing a
newline, it kept generating. The prompt's verbal instruction cannot itself
create a transport boundary.

By contrast, A2 supplied the identical complete graph with no THINK channel.
It produced 54/64 exact-syntax ROUTE lines and 10/64 invalid turns, but 0/64
graph successes. A2 therefore shows that terse answer-only generation does not
compose the five-hop route. A3 shows that the model attempts multi-step
reasoning when invited, but its reasoning and action were never separated into
the recurrent turns the assay claims to provide. Neither result yet tests a
working recurrent THINK interface.

## Exact prospective framing rule

For typed-turn actor calls only:

1. Generate unconstrained tokens with the already-frozen temperature, seed,
   per-turn cap, and cumulative cap.
2. Configure LF (`"\n"`) as a stop string and exclude the stop string from the
   returned response bytes.
3. Preserve the exact returned pre-LF bytes. Do not strip spaces, extract a
   line from a longer generation, repair a prefix, or continue after a malformed
   response.
4. Fullmatch those bytes against exactly one permitted family.
5. An exact THINK is appended verbatim to history and receives only the frozen
   `CONTINUE` text. Exact READs receive only the deterministic registered
   service result. ROUTE/PROBE are terminal.
6. EOS before LF is allowed only if the complete returned bytes already
   fullmatch one family. A per-turn token-cap stop without a fullmatch fails.
7. Log the configured stop string, include/exclude setting, finish reason,
   raw token IDs, returned bytes, and conversation-prefix hash for every turn.

LF stopping constrains only **where one tool turn ends**, not which semantic
action is selected. It must be common to clean base, supplied memory, learned
LoRA, and active-text baselines. It cannot be introduced after looking at a
confirmation root.

## Minimal next ladder

### A3B smoke

- Same exposed roots and exact graph rows as A3.
- Eight balanced tasks: one fixed task from each current root/goal pairing.
- At most 7 calls/task (`6 THINK + 1 ROUTE`), 56 calls maximum.
- Existing 256-token physical and 2,048-token cumulative actor caps.
- Pass interface: first response exact THINK on >=7/8; zero malformed accepted
  turns; terminal exact ROUTE on >=7/8.
- Report graph success, but do not tune on individual routes.

### A3B development panel

Only after the smoke passes, run the existing 64 A3 tasks once. Preserve the
predeclared A3 gate: >=60/64 tasks with an accepted THINK and >=60/64 exact
graph success, with zero mixed accepted turns.

### A4 conditional

If A3B has a valid recurrent channel but route success remains below 60/64,
add only the already-written generic traversal algorithm and optional neutral
two-edge example. Keep newline framing, graph, roots, budgets, parser, and
sampling fixed. A4 passing would establish execution of a supplied generic
algorithm, not spontaneous discovery of a traversal policy.

### Separate local-read handshake

A1 remains unresolved because it issued 0/64 READs. Its answer-free successor
should require one READ before ROUTE and use the same newline frame. Run the
previously designed eight-task handshake smoke; require >=7/8 legal served
reads before a 64-task panel. Do not infer local-read usability from A2/A3B/A4,
which receive the complete graph directly.

## Claim boundary

All roots in this ladder are exposed optimization data. A pass licenses only a
candidate interface for the supplied-memory ceiling and later common use. It
does not establish storage, LoRA transport, connected experiential formation,
novel expansion, retention, lifetime improvement, compression, or superiority
to text memory. Paper evidence still requires a fully repaired interface,
frozen bytes, and untouched confirmation roots.

