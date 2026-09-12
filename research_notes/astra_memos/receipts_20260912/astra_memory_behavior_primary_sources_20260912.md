# Behavior, fact memory, and replay: bounded primary-source check

September 12, 2026. Scope: Rohin's message19 question and Fable's 18:39 analogy, not a diagnosis of Astra's failure or an architecture proposal. Web tool only for retrieval; no curl/wget, repository/Git/GPU activity. Only this memo was written.

## What the sources support

**[1] CLS1995: differentiated acquisition and integration, not a universal identity.** The original account connects hippocampal amnesia, including temporally graded loss, to rapid encoding of arbitrary conjunctions and slower integration into overlapping neocortical representations through interleaved reinstatement. Crucially, pp.426–427 distinguish observed hippocampal reactivation from the then-limited direct evidence for hippocampally driven cortical reinstatement. Page427 explicitly acknowledges unproven assumptions; this is a computational/theoretical synthesis, not a direct demonstration of every consolidation step. It includes other brain systems in its discussion of spared skills. [1, pp.419, 425–428]

**[2] Direct synaptic/skill evidence: acquisition and stabilization have different time courses.** Xu et al. report motor-learning-associated spine formation in mouse motor cortex within an hour. Their original supplement §5/Fig.S3 reports day-one new-spine survival to day5 of **39.7±1.9% in trained animals versus 26.4±3.5% in controls** (four mice each). Activity controls and learning-phase comparisons distinguish skill acquisition from movement repetition alone; long-term activity-control sampling is explicitly limited. Supplement §6 also warns that imaging provides limited information about synaptic strength. Thus “skills are slow from the start” is too categorical: rapid structural changes and subsequent stabilization can coexist. This experiment does not compare fact learning with motor learning. [2, abstract; supplementary §§4–6, Fig.S3, Table S1]

**[3] Direct replay observation, not proof of cortical transfer.** Wilson and McNaughton's original abstract describes recordings in three rats: place cells coactive during behavior became more coactive during subsequent slow-wave sleep than before that behavior. Inactive or spatially nonoverlapping cells did not show the increase. This supports experience-specific reactivation, not a demonstrated transfer of a particular fact into cortex, causal necessity of replay, or a training-dose prescription. [3, abstract only]

## What does not follow — reviewer inference

- **“Behavior versus memory” is not a clean biological opposition.** Learned skills themselves have memory. CLS's rapid/gradual division is not simply “facts versus behaviors,” and shared synaptic plasticity does not imply identical representations, circuits, or retrieval requirements. [1–2]
- **No demonstrated biological equivalence to LoRA.** These papers do not map a text record to a hippocampus, a compiler to biological replay, or a low-rank parameter update to the relevant synaptic mechanisms. Those are engineering analogies, not verified homologies. [1–3]
- **Neither adapter separation nor mandatory sharing is established.** Distinct biological systems do not prescribe two software adapters; involvement of cortex in multiple forms of learning does not require one undifferentiated parameter store. [1–2]
- **No causal diagnosis of our failed recall.** The sources do not identify dose, relative loss share, interference, optimization, readout, or capacity as our cause. They cannot guarantee success from more copies or exclude alternative explanations. [1–3]

Suggested bounded wording: **“Biology motivates distinguishing acquisition, stabilization, and replay regimes. It does not establish equivalence of our behavior and fact-learning mechanisms, determine adapter organization, or explain this failure.”** This is an inference boundary, not a new experimental finding. [1–3]

## Three precise references and access scope

1. **McClelland, J. L., McNaughton, B. L., & O'Reilly, R. C. (1995).** *Why There Are Complementary Learning Systems in the Hippocampus and Neocortex: Insights From the Successes and Failures of Connectionist Models of Learning and Memory.* **Psychological Review, 102(3), 419–457.** DOI: `10.1037/0033-295X.102.3.419`. Inspected the original Stanford author-hosted PDF, especially pp.419 and 425–428.
2. **Xu, T., Yu, X., Perlik, A. J., Tobin, W. F., Zweig, J. A., Tennant, K., Jones, T., & Zuo, Y. (2009).** *Rapid formation and selective stabilization of synapses for enduring motor memories.* **Nature, 462, 915–919.** DOI: `10.1038/nature08389`. Read the publisher's original abstract and original 12-page supplementary PDF, especially §§4–6, Fig.S3 and Table S1. The paywalled main article/PMC full-text route was not successfully retrieved; full-main-text verification is not claimed.
3. **Wilson, M. A., & McNaughton, B. L. (1994).** *Reactivation of hippocampal ensemble memories during sleep.* **Science, 265(5172), 676–679.** DOI: `10.1126/science.8036517`; PMID `8036517`. Checked the authors' original abstract indexed by PubMed, not the full experimental text; claims above stay within that abstract.

Access limits are explicit: this is a primary-text check using an original paper, original supplementary results, and authors' abstracts—not a claim to have read all three main articles in full. No secondary summary supplies the biological conclusions. No claim of cause identification or new architecture follows.
