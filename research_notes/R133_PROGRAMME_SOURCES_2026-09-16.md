# R133 — parent-only public-source programmes

**Retrieved and prepared 2026-09-16 UTC.** Usable source set: **six verified public-source question forms with separately labeled LM adaptations, plus four primary-source brain-lecture cards**. No held data, GPU runs, parent delivery, or commits. This is a parent teaching/dialogue programme, not a scored diagnostic or clinical intervention.

## Ready artifacts

- `research_notes/r133_programmes/parent_question_set.json`: six exact short source excerpts, private-detail-free source locators, explicitly non-quotation adaptations, attribution, and parent framing.
- `research_notes/r133_programmes/brain_lecture_cards.json`: four source-backed explanations, population/species, limitations, and separately labeled LoRA analogies.
- `research_notes/r133_programmes/source_manifest.json`: exact requested/final URLs, HTTP status/date, full response SHA-256, authors/title/year/DOI, source/member provenance, and exclusions.
- `research_notes/r133_programmes/validation.json`: verified counts and artifact-hash checks.

**Parent use:** choose the explicitly marked adaptation, not the surrounding human biography. The topics are observed interaction, action/outcome, reasons and uncertainty, judgment basis, information sufficiency, and alternative explanations. Reports concern available records; “unknown” or “not observable” is acceptable. Do not demand hidden internal narratives, presume feelings/distress, or imply that therapy treats a language model. No therapeutic efficacy, consciousness, or validated metacognition claim follows from these questions.

Only **23 words of verbatim dataset text in total** are copied, once, into the question artifact. They are exact retrieved utterances, not invented quotations. Adapted questions are original R133 wording and explicitly labeled as such. No situations, conversational context, names, speaker IDs, or human life events are copied; source locators permit verification without storing those details in the repo. Full raw data stays under `/tmp/r133-programme-sources-20260916/`.

## Selected conversation source and license

**Hannah Rashkin, Eric Michael Smith, Margaret Li, Y-Lan Boureau (2019), _Towards Empathetic Open-domain Conversation Models: A New Benchmark and Dataset_.** [Primary paper](https://aclanthology.org/P19-1534/), DOI `10.18653/v1/P19-1534`. Dataset: **EmpatheticDialogues**, [official Facebook Research repository](https://github.com/facebookresearch/EmpatheticDialogues). This is empathetic conversation research, not a validated psychotherapy protocol.

The official repository's [LICENSE](https://raw.githubusercontent.com/facebookresearch/EmpatheticDialogues/9649114c71e1af32189a3973b3598dc311297560/LICENSE) explicitly states **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**. Attribution and adaptation disclosure are included. Retrieval does **not** establish permission for commercial use; respect the stated noncommercial condition and check the intended deployment before using these adaptations beyond this research preparation.

Repository commit, resolved using `git ls-remote`: `9649114c71e1af32189a3973b3598dc311297560`. The [pinned README](https://raw.githubusercontent.com/facebookresearch/EmpatheticDialogues/9649114c71e1af32189a3973b3598dc311297560/README.md) supplies the [official data archive URL](https://dl.fbaipublicfiles.com/parlai/empatheticdialogues/empatheticdialogues.tar.gz). **The archive is independently hash-pinned; the Git commit is not claimed to version the archive bytes.** Questions were selected from its public training split, not any project's held evaluation set.

| Retrieved artifact | HTTP / UTC date-time | SHA-256 |
| --- | --- | --- |
| Pinned README | 200 / September 16, 2026 09:51:35 | `bdb4ad826512bccc956f65d3c0e7df19b7c597aa552f2cbb608cba8e69906c1b` |
| Pinned LICENSE | 200 / September 16, 2026 09:51:35 | `82656a050544ab820c9aa7b61433f5181f8e80cacd042377140962a3e3eb5721` |
| Official archive | 200 / September 16, 2026 09:52:16 | `56f234d77b7dd1f005fd365bb17769cfe346c3c84295b69bc069c8ccb83be03d` |
| Extracted `empatheticdialogues/train.csv` | Derived member, not another HTTP retrieval | `35053a4e1ef39f6766e7706c9a3c97b8fa090cfb28d32087a8316a606ab1a7dd` |

ESConv was also retrieved but **not selected**: its CC BY-NC 4.0 license accompanies an additional academic-research-only README statement. No ESConv quotations or conversation content enter this programme.

## Primary brain-lecture references

The cards paraphrase these papers; no paper passages are copied. Sources N2–N4 concern **humans**; N1 is an explicitly labeled **rat comparison**. Exact neuroscience retrieval URLs and byte hashes are in the manifest, including successful Europe PMC records where direct publisher/PubMed access was unavailable.

| ID / primary reference | Safe factual teaching point and boundary |
| --- | --- |
| **N1. M. A. Wilson, B. L. McNaughton (1994), _Reactivation of hippocampal ensemble memories during sleep_.** DOI `10.1126/science.8036517`; [retrieved author abstract/metadata](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID%3A8036517%20AND%20SRC%3AMED&format=json&resultType=core). | Place-cell coactivity during spatial behavior recurred more strongly in subsequent slow-wave sleep in three rats. This is physiological reactivation evidence, not proof of subjective replay, dreams, or memory improvement in every instance. Author abstract inspected; full paper not retrieved. |
| **N2. B. Rasch, C. Büchel, S. Gais, J. Born (2007), _Odor cues during slow-wave sleep prompt declarative memory consolidation_.** DOI `10.1126/science.1138581`; [retrieved author abstract/metadata](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=EXT_ID%3A17347444%20AND%20SRC%3AMED&format=json&resultType=core). | Learning-associated odor cues during human slow-wave sleep improved retention in the tested declarative task, not the procedural task. Timing and prior association mattered; do not generalize to all memories or all sleep. Author abstract inspected; full paper not retrieved. |
| **N3. Marcus E. Raichle, Ann Mary MacLeod, Abraham Z. Snyder, William J. Powers, Debra A. Gusnard, Gordon L. Shulman (2001), _A default mode of brain function_.** DOI `10.1073/pnas.98.2.676`; [primary full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC14647/). | Human resting metabolism provides an organized baseline; some regions decrease relative to it during goal-directed activity. Rest is not shutdown, and this does not identify every resting thought or make default-mode activity synonymous with self-awareness. |
| **N4. Stephen M. Fleming, Rimona S. Weil, Zoltan Nagy, Raymond J. Dolan, Geraint Rees (2010), _Relating introspective accuracy to individual differences in brain structure_.** DOI `10.1126/science.1191883`; [primary full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC3173849/). | Confidence–correctness discrimination varied beyond perceptual performance and correlated with anterior prefrontal structure. Correlation does not establish causation or make confidence a direct readout of subjective experience. |

**Lecture boundary:** behavioral retention, neural activity, and confidence accuracy are distinct measurements. The studies do not imply one universal memory mechanism. LoRA optimization, replayed training examples, context windows, and idle generation are engineered operations—not biological sleep stages, hippocampi, or a default-mode network. Any comparison in the cards is explicitly an analogy, not a finding of these papers or evidence of model feelings/consciousness.

## Retrieval and validation qualifications

All **eight accepted HTTP receipts** were checked against saved response bytes and actual content. Direct PubMed pages for N1/N2 returned HTTP 203 without usable article abstracts; they were rejected. A university-hosted Rasch PDF failed TLS validation and is not claimed retrieved. Scoville/Milner metadata was fetched, but the scanned paper was not read; no substantive lecture claim relies on it. Empty search results were not treated as evidence.

Validation confirms six exact source matches, six clearly labeled adaptations, zero exported biographical-context fields, **23 quoted dataset words**, and four primary neuroscience references. These checks establish attribution and bounded content handling, not efficacy. Parent-only denotes the programme's workflow audience; these files are not cryptographically access-controlled.

Artifact SHA-256:

- Questions: `2098e26e540ee152ea6ba6a9b52c13a8c95c86d608b01733e798215f2f9210bb`
- Lecture cards: `4a645e43a889c791cf23a433ffd710380cb2b053a383b453de39cb25a88dac36`
- Source manifest: `e46c8b8baf5383c7e3a0d444b12ac55e40399a6beee758c504fb4bb7bba8f77d`

Only this note and new `research_notes/r133_programmes/` artifacts are written in the repo. No programme was sent to any parent or child.
