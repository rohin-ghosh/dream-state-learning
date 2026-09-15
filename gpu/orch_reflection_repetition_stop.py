"""Conservative exact-paragraph stopping, without torch/transformers imports.

Create a fresh ``ExactParagraphRepetitionStop(tokenizer, prompt_length=...)``
for each single-sequence, non-beam generation. The callable accepts HF-style
``input_ids, scores`` and returns a scalar bool; an integrating adapter may
wrap it in the framework's stopping-criteria container. Do not share an
instance between sequences or use it to stop an entire multi-sequence batch.

Only generated tokens count toward the minimum. At least three complete,
consecutive copies of a sufficiently long paragraph/block must be present.
An unfinished next copy does not hide them. Internal whitespace, case and
punctuation are exact, not normalized; short list entries cannot trigger it.
Default inspection cadence is 16 tokens after the 512-token minimum. Blocks
may contain up to four paragraphs. At least one must contain 160 non-padding
characters; a multi-paragraph block must total at least 320 such characters.
This admits long/short-formula/long loops without admitting all-short lists.

Call ``finalize(actual_input_ids, max_new_tokens=actual_cap)`` after generation.
It preserves the decoded raw prefix, reports actual EOS/cap/repetition endings
separately, and does not retroactively claim an early stop from a final scan.
Early-stopped reflections are NOT EOS-complete or automatically fit-eligible.
Character duplication is a lexical proxy only; semantic yield stays UNKNOWN.
No runtime integration, mutation of input IDs, retries, or budget changes occur
in this module. Prose before a protocol action is not evaluated for correctness.
"""

from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import re


_BOUNDARY = re.compile(r'\r?\n[ \t]*\r?\n(?:[ \t]*\r?\n)*')
STOP_REASON = 'EXACT_REPEATED_PARAGRAPH'


def _integer(name, value, minimum):
    if type(value) is not int or value < minimum:
        raise ValueError(f'{name} must be an integer >= {minimum}')
    return value


@dataclass(frozen=True)
class RepeatPolicy:
    min_generated_tokens: int = 512
    min_paragraph_chars: int = 160
    min_block_chars: int = 320
    min_repeats: int = 3
    max_block_paragraphs: int = 4
    check_every_tokens: int = 16

    def __post_init__(self):
        for name in ('min_generated_tokens', 'min_paragraph_chars', 'min_block_chars',
                     'max_block_paragraphs', 'check_every_tokens'):
            _integer(name, getattr(self, name), 1)
        _integer('min_repeats', self.min_repeats, 3)


def _block_suffix(paragraphs, block_size, policy):
    if len(paragraphs) < block_size * policy.min_repeats:
        return None
    block = paragraphs[-block_size:]
    lengths = [len(paragraph.strip()) for paragraph in block]
    required_chars = policy.min_paragraph_chars if block_size == 1 else policy.min_block_chars
    if max(lengths) < policy.min_paragraph_chars or sum(lengths) < required_chars:
        return None
    copies = 1
    remaining = len(paragraphs) - block_size
    while remaining >= block_size and paragraphs[remaining - block_size:remaining] == block:
        copies += 1
        remaining -= block_size
    if copies < policy.min_repeats:
        return None
    return block, copies


def repeated_paragraph_tail(text, policy=None):
    """Return an exact terminal repeat witness, or None; never alter text.

Three occurrences are three complete copies (two redundant copies), not two
copies plus a partial third. Blocks can repeat with an unfinished fourth copy.
Only a currently repeating suffix qualifies; a varied recovery paragraph does
not trigger based on an old repeat elsewhere in the output.
"""
    policy = policy or RepeatPolicy()
    if not isinstance(text, str):
        raise TypeError('text must be str')
    paragraphs = _BOUNDARY.split(text)
    witnesses = []

    def record(block, copies, tail_chars, partial_final):
        block_chars = sum(map(len, block))
        witnesses.append(dict(block_paragraphs=len(block), complete_copies=copies,
            block_content_characters=block_chars,
            long_paragraphs=sum(len(paragraph.strip()) >= policy.min_paragraph_chars for paragraph in block),
            repeated_content_characters=(copies - 1) * block_chars + tail_chars,
            matched_next_copy_characters=tail_chars,
            partial_final_paragraph=partial_final,
            block_sha256=hashlib.sha256(json.dumps(block, ensure_ascii=False).encode()).hexdigest()))

    for block_size in range(1, policy.max_block_paragraphs + 1):
        matched = _block_suffix(paragraphs, block_size, policy)
        if matched:
            record(*matched, 0, False)
        closed, tail = paragraphs[:-1], paragraphs[-1]
        for completed_next in range(block_size):
            prefix = closed[:-completed_next] if completed_next else closed
            matched = _block_suffix(prefix, block_size, policy)
            if matched is None:
                continue
            block, copies = matched
            if completed_next and closed[-completed_next:] != block[:completed_next]:
                continue
            expected = block[completed_next]
            if not expected.startswith(tail):
                continue
            tail_chars = sum(map(len, block[:completed_next])) + len(tail)
            record(block, copies, tail_chars, bool(tail) and len(tail) < len(expected))
    if not witnesses:
        return None
    return max(witnesses, key=lambda item: (item['repeated_content_characters'],
                                           item['complete_copies'], -item['block_paragraphs']))


def _token_row(input_ids):
    if hasattr(input_ids, 'tolist'):
        input_ids = input_ids.tolist()
    if not isinstance(input_ids, (list, tuple)):
        raise TypeError('input_ids must be a token sequence or a single-row token batch')
    if input_ids and isinstance(input_ids[0], (list, tuple)):
        if len(input_ids) != 1:
            raise ValueError('one independent sequence only; batching/beams require separate criteria')
        input_ids = input_ids[0]
    if any(type(token) is not int for token in input_ids):
        raise TypeError('token IDs must be integers')
    return tuple(input_ids)


class ExactParagraphRepetitionStop:
    """Stateful single-sequence callable; ``finalize`` reports observed endings."""

    def __init__(self, tokenizer, *, prompt_length, policy=None, eos_token_ids=None):
        self.tokenizer = tokenizer
        self.prompt_length = _integer('prompt_length', prompt_length, 0)
        self.policy = policy or RepeatPolicy()
        eos = getattr(tokenizer, 'eos_token_id', None) if eos_token_ids is None else eos_token_ids
        if eos is None:
            eos = ()
        elif type(eos) is int:
            eos = (eos,)
        if not isinstance(eos, (list, tuple, set, frozenset)) or any(type(token) is not int for token in eos):
            raise TypeError('eos_token_ids must be an integer or a collection of integers')
        self.eos_token_ids = frozenset(eos)
        self._last_input_ids = None
        self._last_check_tokens = None
        self._trigger_ids = None
        self._trigger_witness = None

    def _observe(self, input_ids):
        tokens = _token_row(input_ids)
        if len(tokens) < self.prompt_length:
            raise ValueError('input is shorter than the declared prompt')
        if self._last_input_ids is not None and tokens[:len(self._last_input_ids)] != self._last_input_ids:
            raise ValueError('sequence changed or shrank; use a fresh criterion for each generation')
        self._last_input_ids = tokens
        return tokens[self.prompt_length:]

    def _decode(self, tokens):
        return self.tokenizer.decode(list(tokens), skip_special_tokens=False,
                                     clean_up_tokenization_spaces=False)

    def __call__(self, input_ids, scores=None, **kwargs):
        del scores, kwargs
        generated = self._observe(input_ids)
        if self._trigger_ids is not None:
            return True
        if not generated or generated[-1] in self.eos_token_ids:
            return False
        if len(generated) < self.policy.min_generated_tokens:
            return False
        if self._last_check_tokens is not None and len(generated) - self._last_check_tokens < self.policy.check_every_tokens:
            return False
        self._last_check_tokens = len(generated)
        witness = repeated_paragraph_tail(self._decode(generated), self.policy)
        if witness is None:
            return False
        self._trigger_ids = generated
        self._trigger_witness = witness
        return True

    def finalize(self, input_ids, *, max_new_tokens):
        """Return full decoded output plus conservative, explicitly nonsemantic metadata.

An EOS or cap reached without a prior callback trigger is never labelled an
early stop. If generation continued after a trigger, the stop was not honored:
        report the actual later ending and preserve both the original trigger and all
        emitted text. ``truncated`` is reserved for cap exhaustion, not repeat stopping.
        A trigger coinciding with the cap gets no credit as an early termination.
"""
        _integer('max_new_tokens', max_new_tokens, 1)
        generated = self._observe(input_ids)
        eos_reached = bool(generated) and generated[-1] in self.eos_token_ids
        cap_reached = len(generated) >= max_new_tokens
        trigger_at_final_prefix = self._trigger_ids is not None and generated == self._trigger_ids
        honored = trigger_at_final_prefix and not cap_reached and not eos_reached
        reason = STOP_REASON if honored else 'EOS' if eos_reached else 'MAX_NEW_TOKENS' if cap_reached else 'EXTERNAL_STOP'
        raw_prefix = self._decode(generated)
        content = self._decode(generated[:-1]) if eos_reached else raw_prefix
        paragraphs = _BOUNDARY.split(content)
        eligible = [paragraph for paragraph in paragraphs if len(paragraph.strip()) >= self.policy.min_paragraph_chars]
        counts = Counter(eligible)
        repeated_chars = sum((count - 1) * len(paragraph) for paragraph, count in counts.items())
        total_chars = sum(map(len, eligible))
        witness = repeated_paragraph_tail(content, self.policy)
        return dict(schema='EXACT_PARAGRAPH_STOP_V1', raw_prefix=raw_prefix,
            raw_prefix_sha256=hashlib.sha256(raw_prefix.encode()).hexdigest(),
            policy=asdict(self.policy), stop_reason=reason, early_stopped=honored,
            eos_reached=eos_reached, terminal=eos_reached and not honored,
            length_cap_reached=cap_reached, truncated=reason == 'MAX_NEW_TOKENS',
            repetition_stop_requested=self._trigger_ids is not None,
            repetition_stop_honored=honored,
            repetition_stop_at_final_prefix=trigger_at_final_prefix,
            repetition_stop_coincides_with_cap=trigger_at_final_prefix and cap_reached,
            stop_requested_at_generated_tokens=len(self._trigger_ids) if self._trigger_ids is not None else None,
            trigger_witness=self._trigger_witness, final_repeat_witness=witness,
            generated_tokens_including_special=len(generated),
            generated_tokens_excluding_terminal_eos=len(generated) - int(eos_reached),
            repeated_content_characters=witness['repeated_content_characters'] if witness else 0,
            repeated_content_tokens=None,
            repeated_content_tokens_status='NOT_MEASURED_CHARACTER_COUNTS_ARE_NOT_TOKEN_COUNTS',
            lexical_novelty_proxy=dict(unit='characters_in_eligible_paragraph_segments',
                eligible_segments=len(eligible), eligible_content_characters=total_chars,
                exact_duplicate_segments=sum(count - 1 for count in counts.values()),
                exact_duplicate_content_characters=repeated_chars,
                unique_content_fraction=(total_chars - repeated_chars) / total_chars if total_chars else None,
                scope='THIS_OUTPUT_ONLY_EXACT_DUPLICATION_NOT_SEMANTIC_YIELD',
                final_segment_may_be_incomplete=True),
            semantic_novelty_yield='UNKNOWN', semantic_review_status='PENDING_AUTHOR_REVIEW',
            fit_eligibility='NOT_DECIDED_BY_THIS_SAFEGUARD')
