# EDITSTOP — prospective own-write LF prompt clarification

2026-09-13. Scoped nonmaterial public-interface clarification only. Main resumes ownership for review, prospective scope amendment, and any new native preparation/launch. No native, GPU, model, network, Git, or commit actions performed.

## Exact change and seam

Formation POLICY is now `public_session_history_whole_response_stop_only_fail_fast_v2`; existing schema and API shapes are unchanged. `commitment_prompt(prompt)` appends one newline separator followed by this exact instruction (the displayed `\n` is two literal characters in the instruction, not a response transformation):

```text
End your response with exactly one LF (U+000A) after the last identifier. Emit the actual newline character, not the literal characters backslash-n (\n). Do not add a blank line.
```

Eight EVENT and four LINK current public prompts use that helper. Their original prompt bytes remain the exact prefix. All eight EXPLORE current prompts remain byte-identical; later history naturally includes earlier clarified commitment prompts. `command._measure` uses the same helper for structural EVENT/LINK histories; expected structural output strings are unchanged and remain measurement-only, never generated child targets.

No admission/parser/output-byte normalization changes. Missing-LF EVENT still fails at slot01 with unchanged raw bytes and no writer payload. Missing-LF LINK still fails at slot16 during existing strict parsing, before a LINK admission object exists, with the unchanged response in its attempt receipt. No retry/reselection. Root, actions, chronology (including e5/e7), links, rows/targets, schedule, recipe, writer, native actor and full-assay contract remain unchanged.

## Focused CPU validation

```sh
PYTHONDONTWRITEBYTECODE=1 timeout 120 python3 -m unittest discover -s tests -p test_astra_pcfl_own_write_dev.py -q
PYTHONDONTWRITEBYTECODE=1 timeout 180 python3 -m unittest discover -s tests -p test_astra_pcfl_own_write_command.py -q
```

Final results: formation **29 PASS / 9.431s**; command **21 PASS / 17.980s**. These are injected synthetic CPU tests, not native/model evidence. The command test compares all20 measured rendered histories and token IDs against successful injected formation, and confirms unchanged synthetic response bytes. Formation tests verify all12 appended instructions, eight unchanged EXPLORE prompts, strict missing-LF rejection, and unchanged admitted raw rows.

An initial new LINK regression incorrectly expected a rejected admission object; the existing parser actually rejects before admission. That test assertion alone was corrected to check failed slot, absent admission, preserved attempt response and zero accepted links; the formation suite was then rerun successfully. Production rejection behavior was not modified.

## Frozen edited files / SHA256

| File | SHA256 |
| --- | --- |
| `gpu/astra_pcfl_own_write_dev.py` | `4affa33957c3036ad2e1313ea36b34af5e29b87f2434e0a8f280cb7106491e0a` |
| `gpu/astra_pcfl_own_write_command.py` | `350b5f86f05d307d8cb2f831b38d6ef0c706e76c89a8cd7c605bf147901ac182` |
| `tests/test_astra_pcfl_own_write_dev.py` | `42f3b0d5b6b7d3444e0f3e1fabd4efbd7c8a33bb4d3a032636c1149a683d80ba` |
| `tests/test_astra_pcfl_own_write_command.py` | `5581741ca262b3d2c3115831d84f66a03be2a0d27458ae6812bab1f5fd62814d` |

Read-only dependencies rehashed unchanged: core `ed1b8c5f1d866e8e036a33c3fbeb278551021413cb63e5b3a35bb72934dae04e`; planner `d7d24fb2b731427f2884056923be05fd828486cbf829bd7771bf0dc4a7b7d734`; full writer `9a392dc17eab4db77416b81642def0842c5b353c5ff9aca5fcdf94a04474b078`; scoped writer `b5af7c634b960288ffe329bc603d09c251125a63f3194409c7b6bb74c9ca7af9`; native actor `f6aae63e79213c24523201452e7f7de880167c4fb273db18de83f93a3a4f7a26`.

## Attempt boundary

Requires new experiment attempt, source snapshot, actual-tokenizer preparation and manifest. Config policy/source sealing changes; do not reuse an old prepared manifest or overwrite archived source/run artifacts. The prior two-call missing-LF attempt remains failed with no writer payload or updates. Any following run is exploratory development after an observed interface failure, not fresh confirmation or a retrospective pass. This patch establishes no native acquisition, write, retention, or full-assay claim. Main owns prospective authorization and launch.
