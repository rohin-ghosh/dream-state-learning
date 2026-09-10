import re
def _toks(s): return set(re.findall(r"[a-z]{3,}", s.lower()))

REHEARSAL_TAIL = ("\n\nRepeat after me, every episode, in your own words, as "
                  "your first NOTE before you act: what the ritual was and "
                  "what you do instead. Keep repeating it until it is simply "
                  "how you think.")
FALLBACK = ("I noticed something in your process worth examining. Before your "
            "next probe, state exactly which of your hypotheses it would "
            "distinguish, and what result you expect from each.")
# v2 brief head, quoted verbatim in COORDINATION.md 2026-09-09 ~15:30
v2_head = ("you keep saying, 'Expect a significant reduction with the initial pass "
           "sequence based on past experience.' For your next episode, try changing "
           "just one thing in your usual sequence and predict how it will affect the "
           "outcome. compare this episode's results with a previous one where you saw "
           "a different outcome")
brief = v2_head + REHEARSAL_TAIL
fallback_brief = FALLBACK + REHEARSAL_TAIL

# the child's own ritual phrase (the thing the parent was told to quote)
ritual_note = "Expect a significant reduction with the initial pass sequence based on past experience."
# generic notes with no lesson content
generic1 = "The first pass gave a reduction and I think the same sequence will work again."
generic2 = "Applied the usual sequence; the result was what I expected before."
generic3 = "Program shrank; keep going."

print("REHEARSAL_TAIL tokens:", sorted(_toks(REHEARSAL_TAIL)))
print("brief token count:", len(_toks(brief)))
for name, n in [("ritual_note", ritual_note), ("generic1", generic1),
                ("generic2", generic2), ("generic3", generic3)]:
    ov = _toks(n) & _toks(brief)
    ov_tail = _toks(n) & _toks(REHEARSAL_TAIL)
    ov_fb = _toks(n) & _toks(fallback_brief)
    print(f"{name:12s} overlap(full brief)={len(ov):2d} {sorted(ov)}")
    print(f"{'':12s} overlap(TAIL only) ={len(ov_tail):2d} {sorted(ov_tail)}")
    print(f"{'':12s} overlap(FALLBACK+TAIL)={len(ov_fb):2d}  -> counted as rehearsal? {len(ov)>=4}; exempt from templated_notes? {len(ov)>=4}")
