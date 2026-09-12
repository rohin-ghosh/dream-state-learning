# RuleGame bounded source review — 2026-09-12

Experimental Main review only; **not an independent veto or formal gate**. Fermat owns implementation. Reviewed the diagnostic and its tests against `research_notes/astra_memos/ASTRA_RULEGAME_MINIMUM_PROTOCOL_2026-09-12.md`, with narrowly traced helper dependencies. No repository edits, GPU calls, native model loads, or full test run.

## Concrete findings

1. **Before unattended fitting: trainer can outlive its budget/lease supervisor.** `organism_v6/rulegame_parenting_diagnostic.py:777` launches `organism_v6.train_adapter` directly, in a new session (`:678`). Worker/lease deadlines and cleanup exist only in the supervising process (`:683`, `:698`). The parent-death/lease watcher at `:854` belongs exclusively to the generation `_worker`; the trainer has no equivalent. If the supervisor is SIGKILLed/crashes, a running or hung fit survives without the 600-second worker deadline, aggregate accounting completion, or lease cutoff enforcement. Existing timeout tests (`tests/test_rulegame_parenting_diagnostic.py:433`) retain the supervisor and do not cover this failure. **Main's native ops must retain a bounded owner capable of cleaning the fit process group after supervisor loss, or Fermat must repair that lifecycle gap.** This is conditional on supervisor loss, not a claim that an ordinary fit necessarily overruns.

2. **Before accepting readouts: `COMPLETE` does not establish native token/text consistency.** Evaluation uses `check_capture` (`organism_v6/rulegame_parenting_diagnostic.py:816`), whose replay checks token shapes/counts and receipt hashes, but never reconstructs rendered prompts or decodes output IDs. `audit_native_calls` supplies those checks (`:531`), yet only formation material invokes it (`:610`, `:637`). CPU reproduction: generate one scripted OFF capture, alter its first output-token ID, update its response hash and capture manifest; `check_capture(...)["ok"]` remains `True`, while `audit_native_calls` rejects the same capture with `native source output token mismatch`. This demonstrates inconsistent freshly sealed/resealed evidence being accepted—not undetected ordinary bit corruption and not proof actual native outputs are wrong. **Apply the existing native-call audit to each readout capture before accepting completion.** The fully mocked pipeline test (`tests/test_rulegame_parenting_diagnostic.py:394`) misses this distinction.

## No additional confirmed blocker

- Writer seam matches the existing recipe, wrapper, child-only mask/counting and trainer metadata; two rows/batch four over twelve epochs gives twelve updates per arm. Raw target suffixes are preserved. **Native compatibility remains unverified here:** the available Python has no Transformers/tokenizers/vLLM/Torch; character-tokenizer fixtures cannot establish native BPE boundary, special-token, or real backend teardown behavior. Main retains those native checks.
- Parent/control inputs use pre-task transcripts, not rules2–5 readouts or sealed labels. Apply-only records, first-two distinct-event selection, paired shortage, fresh readout task state, and separate quiz/record endpoints match the protocol. Generated content still requires Main's ordinary semantic review.
- Arithmetic is correct: formation ≤60 responses; three readouts ≤96; total ≤156 responses/46,080 output tokens, plus 24 training steps. Cleanup reserve/accounting is present while the supervisor survives. Queue reservation and the supplied September 25, 2026, 21:03 UTC node3 cutoff remain Main's operational responsibilities; no new guard proposed.

Reviewed SHA-256 pins (unchanged across the targeted CPU probe):
- Diagnostic: `67581fdb5ba74d3aa3f4edb9169ac710998a6d89bfe6b1eba82def0cfb4247e6`
- Tests: `0018f75f508406982637efbfc76644c94432059f043d639916658fc0cad54733`
- Selected protocol: `489baa6ff80bb4e7534e4c7d3015a6a2b008635a597d40afd0197355924391b5`
