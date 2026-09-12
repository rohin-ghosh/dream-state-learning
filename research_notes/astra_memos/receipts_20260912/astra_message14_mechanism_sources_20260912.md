# Message 14: experience → update, not a sleep-interval diagnosis
2026-09-12 UTC · bounded primary-source decision memo for Rohin · recommendations only.

## Scope and answer
- Identity leads: `research_notes/WHAT_TO_PARENT_FROM_THE_LITERATURE_2026-09-12.md:13`–17 and `research_notes/related_work/tmem_positioning_2026-09-10.md:3`; question: raw Message 14 and `research_loop/COORDINATION.md:4610`. Those notes identify papers, not evidence for their mechanisms.
- TMEM compiles experience into supervised QA examples; SEAL learns to generate useful training data/configurations; OEL converts experience into privileged teacher context; SDFT converts demonstrations into privileged teacher context. The latter two train on student-generated continuations, not simply on the extracted lesson/demonstration text.
- These are different data interfaces and objectives, not interchangeable ways to repeat a transcript. None establishes an optimal sleep interval for our organism. TMEM's context-budget trigger is a scheduling precedent, not evidence that our sleeps should move closer together.
- Our unresolved question is whether grounded supervision plus a different update objective yields acquisition **and** selective use/retention. Neither a prettier corpus nor lower spill alone establishes that conjunction.

## TMEM — grounded QA → cumulative fast-weight SFT
**Verified identity:** Tao Ren et al., *Scaling Self-Evolving Agents via Parametric Memory*, arXiv:2606.04536v1, June 3, 2026. TMEM is the method name; the title does not start with “TMEM:”.
**Primary source:** https://arxiv.org/html/2606.04536v1 — §3/Figure 1; §3.1 equations 5–6; §3.2; §4; §5.1 “Online TTT configuration”; §5.4.
- Interface: current interaction context → extraction prompt → grounded JSON instruction–answer pairs → online SFT of LoRA; clear working context, retain adapter state. Each trigger continues the current adapter, rather than refitting from base.
- Concrete recipe: rank 6, last four layers' FFN projections; SVD-initialized A frozen, B trained; SGD, learning rate 5e-4, five epochs, batch 16. Context-token budgets trigger writes. The separate outer RL phase rewards final task success and trains extraction/action tokens without differentiating through the inner optimizer; its base is fixed within a rollout, not across outer RL.
- **Unestablished here:** benefit of grounded QA versus whole-text training, SVD/frozen-A subspace, cumulative adapter updates, or their interaction with dose and interference. Within-episode results do not establish our lifelong procedural retention.
- **One decision:** use QA→adapter as the precise TMEM compiler reference, not “shorter sleep” or an automatically transferable hyperparameter prescription.

## SEAL — generated self-edit → SFT → adaptation-utility reward
**Verified identity:** Adam Zweiger, Jyothish Pari, Han Guo, Ekin Akyürek, Yoon Kim, Pulkit Agrawal, *Self-Adapting Language Models*, arXiv:2506.10943v2, September 18, 2025.
**Primary source:** https://arxiv.org/html/2506.10943v2 — §§3.1–3.2, §5/Figure 6, Appendix A.2 and B.3.
**Author corroboration:** https://jyopari.github.io/posts/seal — “What is SEAL?” and knowledge-incorporation/few-shot examples.
- Interface: passage → generated implications → training documents → SFT; alternatively, few-shot examples → augmentation/tool/configuration choices → SFT. Downstream performance after adaptation rewards the self-edit generator via ReST-EM filtered imitation. This is not an intrinsic reward for fluent reflections.
- B.3 splits single-passage generations by newline but uses full generations for multi-passage training; the multi-passage setting aggregates five edits per passage. A.2 exposes augmentation, learning rate, epochs and all-token/output-token loss choices.
- **Unestablished here:** whether diversity, document segmentation, output-only masking or adaptation-utility selection improves our writer at matched dose. §5 explicitly does **not** optimize retention; penalizing regressions on earlier tasks is proposed future work, not a demonstrated SEAL retention mechanism.
- **One decision:** judge a compiled self-edit by its downstream update utility, while keeping retention a separate criterion; do not import SEAL as proof of stable successive writes.

## OEL — trajectory → accumulated lessons → contextual distillation
**Verified identity:** Tianzhu Ye, Li Dong, Qingxiu Dong, Xun Wu, Shaohan Huang, Furu Wei, *Online Experiential Learning for Language Models*, arXiv:2603.16856v2, June 29, 2026.
**Primary source:** https://arxiv.org/html/2603.16856v2 — §§3.1–3.3, §§4.4/4.6, Appendices A and C.2–C.4.
- Interface: actions + textual environmental feedback → sequentially accumulated transferable knowledge e. Collect response-position trajectory prefixes x; student samples y from x alone; frozen pre-consolidation teacher scores those same prefixes/tokens with e added. Minimize token-level reverse KL, D_KL(student || teacher). Redeploy and repeat; this does not require server-side environment access or scalar rewards.
- C.2 permits structured **or unstructured** lessons; C.3 uses multiple accumulation seeds and bounded lengths. C.4 uses 20/100 update steps, temperature 0.7 and a top-256-student-token KL approximation. These are dose/support choices, not a universal “perfect corpus”.
- **Unestablished here:** on-policy rollout support, useful lesson-conditioned teacher advantage, KL direction/truncation, accumulation length/diversity and update budget. Its OOD preservation comparison does not establish retention of our learned old skills through repeated adapter writes.
- **One decision:** treat OEL as a genuinely different teacher/student interface, not another CE fit on lesson text; our frozen-OFF anchor has not tested it.

## SDFT — demonstration → contextual teacher → on-policy distillation
**Verified identity:** Idan Shenfeld, Mehul Damani, Jonas Hübotter, Pulkit Agrawal, *Self-Distillation Enables Continual Learning*, arXiv:2601.19897v2, August 7, 2026.
**Primary source:** https://arxiv.org/html/2601.19897v2 — §3 “Practical Implementation”, §§4.3/4.6, §5, Appendices A.3/B.1 and Algorithm 1.
**Official-code clarification:** https://raw.githubusercontent.com/idanshen/Self-Distillation/main/README.md — “Updates”; linked from https://self-distillation.github.io/SDFT.html .
- Interface: query x + demonstration c → demonstration-aware teacher distribution; student generates y from x without c; teacher evaluates the same student prefixes with c. Normally the teacher follows an EMA of the student; training updates student parameters.
- **Important correction:** reverse-KL theory/equations are not the experimental recipe. §3's practical paragraph and the official README explicitly say the results used per-token **forward KL**, D_KL(teacher || student), with **on-policy student sampling**. Direction and sampling policy are separate knobs.
- **Unestablished here:** that conditioned teacher, fresh rollout distribution, EMA timescale, forward-KL objective, or matched repeated-training dose in frozen-base LoRA. B.1 reports full-parameter tuning; §4.3's sequential three-skill result is not our reproduction or a universal no-forgetting guarantee.
- **One decision:** specify forward-KL/on-policy/EMA SDFT separately from reverse-KL/frozen-teacher OEL; do not label either “our KL anchor”.

## Minimal local evidence boundary — not a duplicate diagnostic report
- `organism_v6/memory_preservation.py:1` and `:38`: our diagnostic is whole-text CE plus fixed-prefix frozen-OFF forward KL; explicitly no trajectories, demonstrations, EMA or full fine-tuning. Sharing the word “KL” does not reproduce SDFT.
- `research_notes/astra_memos/ASTRA_PRESERVATION_TERMINAL_2026-09-12.md:1`: coefficient 0→0.1 reduced spill 0.416→0.0367 but acquisition I_d 1.921→0.152; both gates failed in one learner-seed comparison. This does not rule out other objectives or establish the optimal preservation weight.
- `research_loop/COORDINATION.md:4174` and `:4316`: SEQ-092 compares A2=Fit(base, OLD+NEW) with AN=Fit(base, NEW), not NEW learning applied to OLD adapter weights. It is reconstruction/coexistence evidence. Do not infer catastrophic forgetting, elapsed-time decay or a causal sleep-interval effect from its OLD-frame difference.
- Unresolved jointly: supervision representation/masking, diversity versus repeated exposure at matched gradient dose, on-policy versus fixed-prefix support, teacher information/refresh, parameter subspace, and actual successive-update retention. These are open distinctions, not recommendations to launch a sweep.

## Verification limits and provenance
- Web-tool attempts returned no usable text. Allowed `python3 tools/webtext.py` fetched the four versioned primary HTML papers and author pages; only consequential method/configuration/retention sections were inspected. No curl/wget, model downloads, GPU use, experiments or repo edits.
- Abstract/API requests for TMEM, SEAL and OEL returned HTTP 429; their versioned HTML headers independently verified identifier/title/authors/date. SDFT's abstract endpoint succeeded. Pinned versions above are verified, not claimed to be the newest available.
- GitHub metadata returned HTTP 403 rate limiting; the public SDFT main-branch README succeeded. Main script and part of trainer were fetched, but no complete loss-code/commit audit was performed. The forward-KL correction is directly author-stated, not inferred from those partial files. TMEM/OEL/SEAL executable implementations were not audited.
- Figure-rendered prompt bodies were not independently transcribed; exact prompt bytes, TMEM loss masks and end-to-end reproduction are not certified. No inaccessible detail is filled from Fable's synthesis.
- Fetch evidence is preserved in `/tmp/astra_message14_primary_webtext_20260912.txt`, `/tmp/astra_message14_identity_webtext_20260912.txt` and `/tmp/astra_message14_sdft_*_20260912.txt`. This memo changes no architecture, invariant, scientific claim or launch authorization.
