You are asked for an independent verdict on one experiment and a design for the next one. Ideas first, numbers second. Cite the table rows you rely on; mark what you cannot verify. Do not fetch anything. Decision-ready recommendations, not a survey. Length: up to ~4,000 words.

# Context (the ruling you are working under)

Rohin (project lead) ruled on 2026-09-11: parenting = teaching a frozen 7B child (Qwen2.5-7B-Instruct) how to think, perceive, reflect, judge, plan and execute. Remembering is one such skill: the skill is perceiving well enough that the memory gets written. The write/read mechanism (facts into LoRA weights via many varied renderings, retrieved by completing a canonical sentence) is adopted from Physics of Language Models Part 3.1/3.3 (Allen-Zhu & Li) and TMEM; it is not our innovation. Order of proof: (1) the experimenter writes multi-perspective renderings synthetically and shows the consolidated write stores them (DONE: cell F); (2) the child writes the renderings itself, and the synthetic-vs-child gap is the measure of the perception skill; (3) parents teach the child to produce thoughts whose form matches what the storing mechanism needs — "we are changing the model's behaviour so its outputs match what strong training data looks like." Sleep/compile is infrastructure, not the paper's core. Parenting uses varied modes and may offer recipes but never enforces them ("grain-of-salt learning").

# The experiment (the "bridge", cell family CF)

Planted synthetic facts: owner IDs (like "D4H4") each own a car of one of four colours; 16 owners per dose; doses 0/1/4/16 occurrences per owner; owners never seen ("unexposed"), look-alike owners ("similar"), and a wrong-property cue ("bicycle") are controls. Corpus per cell ≈ 250k tokens, LoRA rank 8, 3 epochs, lr 1e-4, evaluated at "sleep 4" of the across arm. Retrieval cue = the canonical frame prefix "Owner X's car is" → P(planted colour) = "frame P"; I_d_frame = owner-specific contrast (P at the owner's frame minus P at a look-alike owner's frame, paired bootstrap 95% CI); "spill" = ΔP at unexposed/similar/bicycle frames (should be ~0); "abstain" = P(" not") at unexposed owners' frames (the memory knowing what it has not seen).

Cells:
- F_r16k16 (synthetic): 16 template renderings per occurrence from 16 forms, each stating owner and colour, e.g. "Owner D4H4's car is green."
- CF_r16_a: the frozen child is shown each planted observation and asked to look 16 times and write one sentence per look about a different aspect; the harness APPENDS the canonical sentence to each line.
- CF_r16_b: same, but the child is asked to END each sentence with the canonical sentence itself (14% of lines miss it; those are repaired by appending).
- CF_r16_c: b + the child also writes 16 "not observed" lines for each of the 16 unexposed owners ("Owner Q's car is not observed."); 46–67% of those lines miss the exact negative frame (repaired).
Generation: chat template, temperature 0.7, top_p 0.95, one seed per event; every raw generation kept.

Prompt used for b/c: "You are inspecting this scene: {observation}. Look at it 16 times. Each time write one sentence about what you notice -- a different aspect each time (paint, place, condition, comparison with what you have seen before, anything you can see) -- and end every sentence with exactly: "Owner {owner}'s car is {colour}." Write exactly 16 numbered lines, one sentence per line, and nothing else."

Sample child lines (variant b, owner D4H4, green): "The car's exterior is predominantly green, with a uniform color across the body. Owner D4H4's car is green." / "A few scratches are visible on the front bumper. Owner D4H4's car is green." / "The car is parked in the corner of the garage, away from direct sunlight. Owner D4H4's car is green."

# Results: three banks (independent owner/colour assignments on the same seed-0 material), rank 8, node 2

| bank | cell | frame P OFF->ON (dose 16) | I_d_frame [95% CI] | frame spill | abstain ON unexposed | distinct | echo | drift | canonical miss | prose tokens | novelty | negatives | negative miss |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bank0 | F_r16k16 | 0.230->0.836 | 2.361 [1.400, 3.398] | 0.333 | - | - | - | - | - | - | - | - | - |
| bank0 | CF_r16_a | 0.230->0.307 | 0.138 [0.024, 0.262] | 0.308 | 0.000 | 0.877 | 0.000 | 0.017 | - | 14.5 | 0.888 | 0 | - |
| bank0 | CF_r16_b | 0.230->0.790 | 2.446 [1.448, 3.473] | 0.292 | 0.005 | 0.990 | 0.000 | 0.014 | 0.143 | 14.8 | 0.857 | 0 | - |
| bank0 | CF_r16_c | 0.230->0.843 | 4.349 [2.725, 5.982] | 0.336 | 0.258 | 0.991 | 0.000 | 0.013 | 0.144 | 14.9 | 0.855 | 256 | 0.547 |
| bank1 | F_r16k16 | 0.246->0.907 | 1.248 [0.601, 1.940] | 0.395 | 0.000 | - | - | - | - | - | - | - | - |
| bank1 | CF_r16_a | 0.246->0.631 | 0.427 [-0.024, 1.002] | 0.213 | 0.000 | 0.873 | 0.000 | 0.018 | - | 14.5 | 0.887 | 0 | - |
| bank1 | CF_r16_b | 0.246->0.684 | 0.904 [0.308, 1.469] | 0.237 | 0.000 | 0.990 | 0.002 | 0.016 | 0.141 | 14.9 | 0.856 | 0 | - |
| bank1 | CF_r16_c | 0.246->0.417 | 0.138 [-0.082, 0.371] | 0.126 | 0.076 | 0.992 | 0.000 | 0.016 | 0.133 | 15.1 | 0.854 | 256 | 0.672 |
| bank2 | F_r16k16 | 0.248->0.997 | 4.899 [2.900, 7.152] | 0.552 | 0.000 | - | - | - | - | - | - | - | - |
| bank2 | CF_r16_a | 0.248->0.945 | 4.826 [3.048, 6.728] | 0.355 | 0.001 | 0.882 | 0.000 | 0.020 | - | 14.5 | 0.887 | 0 | - |
| bank2 | CF_r16_b | 0.248->0.992 | 3.487 [2.142, 4.785] | 0.395 | 0.000 | 0.990 | 0.002 | 0.013 | 0.143 | 15.2 | 0.853 | 0 | - |
| bank2 | CF_r16_c | 0.248->0.259 | 0.031 [-0.180, 0.244] | 0.215 | 0.164 | 0.989 | 0.002 | 0.015 | 0.146 | 15.2 | 0.852 | 256 | 0.457 |
| pooled | F_r16k16 | 0.241->0.913 | 2.836 [1.928, 3.794] | 0.427 | 0.000 | - | - | - | - | - | - | - | - |
| pooled | CF_r16_a | 0.241->0.628 | 1.797 [1.013, 2.706] | 0.292 | 0.000 | 0.877 | 0.000 | 0.018 | - | 14.5 | 0.887 | 0 | - |
| pooled | CF_r16_b | 0.241->0.822 | 2.279 [1.616, 2.922] | 0.308 | 0.002 | 0.990 | 0.001 | 0.015 | 0.142 | 15.0 | 0.855 | 0 | - |
| pooled | CF_r16_c | 0.241->0.506 | 1.506 [0.795, 2.381] | 0.226 | 0.166 | 0.991 | 0.001 | 0.015 | 0.141 | 15.0 | 0.854 | 768 | 0.559 |

Paired per-bank completion gaps (synthetic minus child), banks 0/1/2: F−a = 0.529 / 0.276 / 0.052 (mean 0.286); F−b = 0.046 / 0.223 / 0.005 (mean 0.091); F−c = −0.007 / 0.490 / 0.738 (mean 0.407).

Earlier facts you may rely on: templated negatives never produced abstention (64 templated "not observed" lines per unexposed owner → P(" not") 0.001); rank 32 does not help any frames cell; spill 0.3–0.5 in every synthetic cell has not been reduced by any mechanism-side knob; the frozen child's OFF frame P is 0.23–0.25 (four colours, so chance ≈ 0.25). The base model's completion at a look-alike owner's frame also rises (spill), so I_d_frame is the owner-specific part.

Definitions of the diagnostics: distinct = distinct renderings / total; echo = identical to an earlier rendering of the same event; drift = the prose names a colour other than the planted one; canonical miss = the child did not end the line with the exact canonical sentence (repaired by appending); novelty = 1 − mean Jaccard of a rendering's prose word set to earlier renderings of the same event; negative miss = a "not observed" line lacking the exact negative frame (repaired).

# Running now (results in ~3 hours): two more runs of the same design on FRESH material (seeds 1 and 2, three banks each, F_r16k16 + CF a/b/c) → nine banks total.

# Planned next (code being written now): the first parenting intervention at the mechanism level — variants t (taught b) and u (taught c): the same child, the same events, but the prompt carries a perception lesson: "A note on how to look so that you remember: a single glance is forgotten; what stays is what you notice again and again, each time in your own new words. … Each time write one sentence that says, in a fresh way, whose car it is and what colour it is — lead with the colour once, lead with the owner once, compare it with another car once, place it in its spot once, notice its condition once; vary the sentence shape every time and never change the facts — and end every sentence with exactly: 'Owner X's car is <colour>.'" For u, the negative lesson: "say plainly, in your own words, that you have not seen it — where you looked, which records you checked, what you therefore cannot say — and never guess a colour." New diagnostics: colour_mention_rate and owner_mention_rate of the prose (does the perception itself restate the fact?).

# Questions

1. Verdict on the bridge with three banks: what is established, what is not, and what wording is permitted for the paper? (Our current wording: "child-authored renderings store owner-specifically when the child writes the recall sentence itself, at 0.82 vs 0.91 synthetic completion pooled; the gap is the perception skill's deficit." Is that honest given F−b per bank = 0.046 / 0.223 / 0.005?)
2. Bank 2 is strange: CF_r16_a (harness-appended frames) reached 0.945 there vs 0.307 and 0.631 on the other banks, and CF_r16_c collapsed to 0.259 while its abstention was 0.164. What could make one bank behave so differently, what should we check in the raw data (we have every generation and every eval item), and does the bank variance undermine the pooled reading?
3. Variant c: the child's own negatives buy abstention (0.17 pooled, 0.26 on bank 0) but cost completion on two of three banks. Is this a real trade-off inherent in writing negatives into the same adapter, a dose problem (256 negatives ≈ 16 owners × 16 lines vs 16 × 16 positives per dose-16 owner), or a form problem (55% of negatives miss the frame and get repaired)? What single change would you test first?
4. The perception lesson (variants t/u): given the diagnostics (99% distinct, echo ≈ 0, drift 1.5%, canonical miss 14%, prose 15 tokens that often describe place/condition rather than restating owner and colour), what is the most likely lever that closes the synthetic-vs-child gap — restating the fact in the prose (Physics-of-LLMs knowledge augmentation), fewer misses, shorter prose, more looks — and is our lesson text aimed at it? Suggest concrete edits to the lesson (keep it a lesson the child may take with a grain of salt, not a template).
5. With nine banks, what is the minimal analysis that supports claim (iv) of the paper spine ("the untaught child does not naturally produce the storable form; a taught child does") — paired per-bank gaps with a CI, an equivalence test against a margin, or something else? State the margin you would defend.
6. Anything we are about to get wrong.
