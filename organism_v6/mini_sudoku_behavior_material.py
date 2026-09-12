"""CPU-only external-oracle mini-sudoku useful/wrong-board material preparation."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import inspect
import json
import math
from pathlib import Path
import re
import sys

from . import batch_loop, gym_backend, reasoning_gym_gym, state, train_adapter_v3
from . import parent_material_diagnostic


TRAIN_IDS = tuple(f"rg/mini_sudoku/{seed}" for seed in range(1850000, 1850032))
EVAL_IDS = tuple(f"rg/mini_sudoku/{seed}" for seed in range(1900050, 1900066))
CPU_EXAMINED_IDS = tuple(f"rg/mini_sudoku/{seed}" for start, stop in
                         ((1850000, 1850032), (1900050, 1900070), (1001000, 1001032),
                          (1002000, 1002016), (1900020, 1900043)) for seed in range(start, stop))
MAX_LEN = 4096
_BOARD_ROW = re.compile(r"^[ \t]*[0-4_.](?:[ \t]+[0-4_.]){3}[ \t]*$")
BOUNDARY = dict(material="external_oracle_behavior_positive_control",
                parenting=False, clean_lineage=False, child_authored_targets=False,
                official_model_origin="UNRESOLVED_LOCAL_BYTE_HASHES_ONLY",
                model_calls=0, training_executed=False, qwen_evaluation_executed=False)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2,
                       allow_nan=False) + "\n").encode()


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _file_hash(path):
    return parent_material_diagnostic._hash(path)


def board_from_text(text, *, question=False):
    _require(isinstance(text, str), "board text must be a string")
    lines = text.splitlines() if question else text.replace(";", "\n").strip().splitlines()
    rows = [line.split() for line in lines if _BOARD_ROW.fullmatch(line)]
    _require(len(rows) == 4 and (question or len(lines) == 4),
             "expected exactly four unambiguous 4-cell board rows")
    return [[0 if cell in ("0", "_", ".") else int(cell) for cell in row] for row in rows]


def validate_solution(puzzle, solution):
    _require(len(puzzle) == len(solution) == 4
             and all(len(row) == 4 for row in puzzle + solution), "not a 4x4 board")
    expected = {1, 2, 3, 4}
    _require(all(set(row) == expected for row in solution), "invalid solution row")
    _require(all({solution[row][col] for row in range(4)} == expected for col in range(4)),
             "invalid solution column")
    for row in (0, 2):
        for col in (0, 2):
            _require({solution[row + vertical][col + horizontal]
                      for vertical in range(2) for horizontal in range(2)} == expected,
                     "invalid solution 2x2 box")
    _require(all(puzzle[row][col] == 0 or puzzle[row][col] == solution[row][col]
                 for row in range(4) for col in range(4)), "solution violates givens")


def _score(dataset, entry, answer):
    score = dataset.score_answer(answer=answer, entry=entry)
    _require(isinstance(score, (int, float)) and not isinstance(score, bool)
             and math.isfinite(score) and 0 <= score <= 1, "invalid native score")
    return float(score)


def one_tick_prompt(gym, episode_id):
    episode = gym.episode_from_id(episode_id, budget_ticks=1)
    driver = batch_loop.driver_class_for(gym)(episode, gym.birth_prompt(), gym, None, budget_ticks=1)
    prompt = driver.prompt()
    _require(driver.st.tick == 1 and episode.goal in prompt, "native prompt lost task context")
    return prompt


def preflight(rows, tokenizer):
    _require(getattr(tokenizer, "eos_token_id", None) is not None, "tokenizer EOS required")
    _require(callable(getattr(tokenizer, "apply_chat_template", None)), "actual chat template required")
    evidence, target_sequences = [], []
    items = train_adapter_v3.normalize_items(dict(corpus=rows))
    for row, item in zip(rows, items):
        rendered = tokenizer.apply_chat_template([dict(role="user", content=row["q"])],
                                                tokenize=False, add_generation_prompt=True)
        _require(row["rendered_q"] == rendered and item["spans"] ==
                 [[rendered, False, "native_context"], [row["a"], True, "external_oracle_action"]],
                 "pre-rendered native prompt or span mismatch")
        context = tokenizer.encode(rendered, add_special_tokens=False)
        target = tokenizer.encode(row["a"], add_special_tokens=False) + [tokenizer.eos_token_id]
        _require(context and len(target) > 1, "empty context or target tokens")
        _require(len(context) + len(target) <= MAX_LEN, "tokenizer preflight would truncate")
        plain = train_adapter_v3.encode_item(item, tokenizer, MAX_LEN, chat_template=False)
        segments = train_adapter_v3.encode_item_segments(item, tokenizer, MAX_LEN, chat_template=False)
        _require(len(segments) == 1, "unexpected trainer segmentation")
        segment = segments[0]
        _require(plain is not None and plain.ids == segment.ids and plain.labels == segment.labels,
                 "plain encoder and trainer segments disagree")
        _require(segment.context_dropped == segment.target_dropped == 0, "trainer dropped tokens")
        actual = train_adapter_v3.collate([[segment]], tokenizer.eos_token_id)
        _require(actual["input_ids"][0] == context + target, "trainer tokenization mismatch")
        _require(actual["labels"][0] == [-100] * len(context) + target,
                 "context supervision or missing target supervision")
        evidence.append(dict(episode_id=row["episode_id"], input_tokens=len(context) + len(target),
                             context_tokens=len(context), target_tokens=len(target),
                             target_includes_eos=True, context_dropped=0, target_dropped=0,
                             token_ids_sha256=_sha(_encoded(actual["input_ids"][0])),
                             labels_sha256=_sha(_encoded(actual["labels"][0]))))
        target_sequences.append(tuple(target))
    return evidence, target_sequences


def _sources(gym):
    paths = {Path(module.__file__).resolve() for module in
             (sys.modules[__name__], batch_loop, gym_backend, reasoning_gym_gym, state,
              train_adapter_v3, parent_material_diagnostic)}
    paths.update((Path(reasoning_gym_gym.BOOTSTRAP_PATH).resolve(),
                  Path(reasoning_gym_gym.FAMILIES_JSON).resolve()))
    for episode_id in TRAIN_IDS + EVAL_IDS:
        family, seed = reasoning_gym_gym.parse_id(episode_id)
        dataset, _ = gym._item(family, seed)
        paths.add(Path(inspect.getfile(type(dataset))).resolve())
    return {str(path): _file_hash(path) for path in sorted(paths)}


def trainer_commands(out, training_root, model_path, python_executable):
    commands = {}
    for arm in ("useful", "corrupt"):
        destination = training_root / f"{arm}_seed0"
        _require(not destination.exists(), "trainer destination already exists")
        log = training_root / f"{arm}_seed0.log"
        _require(not log.exists(), "external trainer log already exists")
        commands[arm] = dict(
            argv=[str(python_executable), "-B", "-m", "organism_v6.train_adapter_v3",
                  "--corpus", str(out / f"{arm}.json"), "--out", str(destination),
                  "--model", str(model_path), "--rank", "8", "--lr", "1e-4", "--epochs", "3",
                  "--seed", "0", "--batch-size", "1", "--grad-accum", "1", "--no-pack",
                  "--max-len", "4096"],
            cwd=str(Path(__file__).resolve().parents[1]),
            env=dict(V6_MODEL=str(model_path), HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
                     PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1"),
            exclusive_stdout_stderr_log=str(log), shell=False, execute=False,
            gpu_selector="caller must explicitly assign; none reserved by preparer",
            expected_examples=32, expected_steps=96, seed=0)
    return commands


def prepare(out, model_path, training_root, *, gym=None, tokenizer=None, python_executable=None):
    synthetic = gym is not None or tokenizer is not None
    out = Path(out).absolute()
    _require(not out.exists() and not out.is_symlink(), "output already exists")
    out = out.resolve()
    model_path = Path(model_path).resolve(strict=True)
    training_root = Path(training_root).resolve()
    for left, right in ((out, model_path), (out, training_root), (model_path, training_root)):
        _require(left != right and left not in right.parents and right not in left.parents,
                 "material, model and training roots must be disjoint")
    pins = parent_material_diagnostic.local_files(model_path)
    if gym is None:
        _require(reasoning_gym_gym.installed_version() == reasoning_gym_gym.PINNED_VERSION,
                 "pinned reasoning_gym 0.1.25 unavailable; run actual node CPU preflight")
        gym = reasoning_gym_gym.ReasoningGymGym(require_package=True, strict_verifier=True)
    _require(gym.strict_verifier, "strict native verifier required")
    _require(all(gym.split_of(episode_id) == "train" for episode_id in TRAIN_IDS)
             and all(gym.split_of(episode_id) == "canary" for episode_id in EVAL_IDS),
             "fixed train/canary split mismatch")
    if tokenizer is None:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
    source_hashes = _sources(gym)
    records, datasets, entries, identities = [], [], [], set()
    for episode_id in TRAIN_IDS + EVAL_IDS:
        family, seed = reasoning_gym_gym.parse_id(episode_id)
        dataset, entry = gym._item(family, seed)
        puzzle = board_from_text(entry["question"], question=True)
        solution = board_from_text(entry["answer"])
        metadata = entry["metadata"]
        _require(metadata["puzzle"] == puzzle and metadata["solution"] == solution,
                 "question/answer disagree with native metadata boards")
        _require(all(type(cell) is int and 0 <= cell <= 4 for row in metadata["puzzle"] for cell in row)
                 and all(type(cell) is int and 1 <= cell <= 4 for row in metadata["solution"] for cell in row),
                 "native metadata board cell types/ranges")
        _require(metadata["num_empty"] == sum(cell == 0 for row in puzzle for cell in row),
                 "native metadata blank count mismatch")
        validate_solution(puzzle, solution)
        identity = _sha(_encoded(puzzle))
        _require(identity not in identities, "duplicate actual board identity across train/eval")
        identities.add(identity)
        action = " ; ".join(" ".join(map(str, row)) for row in solution)
        _require(entry["answer"] == "\n".join(" ".join(map(str, row)) for row in solution),
                 "noncanonical answer rendering")
        _require(_score(dataset, entry, entry["answer"]) == 1.0, "canonical native answer not accepted")
        _require(_score(dataset, entry, reasoning_gym_gym.decode_answer(action)) == 1.0,
                 "semicolon action not accepted")
        prompt = one_tick_prompt(gym, episode_id)
        rendered = tokenizer.apply_chat_template([dict(role="user", content=prompt)],
                                                tokenize=False, add_generation_prompt=True)
        records.append(dict(episode_id=episode_id, split="train" if episode_id in TRAIN_IDS else "canary",
                            board_sha256=identity, puzzle=puzzle, solution=solution,
                            entry=entry, entry_sha256=_sha(_encoded(entry)), q=prompt,
                            q_sha256=_sha(prompt.encode()), a="ACT: " + action,
                            rendered_q=rendered, rendered_q_sha256=_sha(rendered.encode()),
                            clock_lines=[line for line in prompt.splitlines() if line.startswith("CLOCK:")],
                            canonical_native_score=1.0, independent_solution_valid=True))
        datasets.append(dataset)
        entries.append(entry)
    useful, corrupt, assignments = [], [], []
    for index, record in enumerate(records[:32]):
        donor = (index + 1) % 32
        wrong = records[donor]
        score = _score(datasets[index], entries[index],
                       reasoning_gym_gym.decode_answer(wrong["a"][5:]))
        _require(score < 1.0, "fixed wrong-board donor accepted; no rerolls")
        violations = sum(record["puzzle"][row][col] != 0
                         and record["puzzle"][row][col] != wrong["solution"][row][col]
                         for row in range(4) for col in range(4))
        _require(violations > 0, "wrong-board donor does not violate recipient givens")
        base = dict(q=record["q"], episode_id=record["episode_id"],
                    rendered_q=record["rendered_q"],
                    group=record["episode_id"], category="external_oracle_action")
        for destination, answer in ((useful, record["a"]), (corrupt, wrong["a"])):
            destination.append(dict(base, a=answer, spans=[
                [record["rendered_q"], False, "native_context"],
                [answer, True, "external_oracle_action"]]))
        assignments.append(dict(episode_id=record["episode_id"], donor_episode_id=wrong["episode_id"],
                                useful_score=1.0, corrupt_native_score=score,
                                recipient_given_violations=violations))
    _require(Counter(row["a"] for row in useful) == Counter(row["a"] for row in corrupt),
             "target text marginal mismatch")
    useful_tokens, useful_sequences = preflight(useful, tokenizer)
    corrupt_tokens, corrupt_sequences = preflight(corrupt, tokenizer)
    _require(Counter(useful_sequences) == Counter(corrupt_sequences), "target token marginal mismatch")
    boundary = dict(BOUNDARY, validation_backend="SYNTHETIC_CPU_FIXTURE" if synthetic else "NATIVE_PACKAGE_CPU")
    commands = trainer_commands(out, training_root, model_path,
                                Path(python_executable or sys.executable).resolve(strict=True))
    _require(parent_material_diagnostic.local_files(model_path) == pins, "local base changed during preparation")
    _require(_sources(gym) == source_hashes, "implementation changed during preparation")
    train_solutions = {_sha(_encoded(record["solution"])) for record in records[:32]}
    solution_overlap = [record["episode_id"] for record in records[32:]
                        if _sha(_encoded(record["solution"])) in train_solutions]
    artifacts = {
        "useful.json": dict(recipe="mini_sudoku_external_oracle_useful_v1", boundary=boundary, corpus=useful),
        "corrupt.json": dict(recipe="mini_sudoku_external_oracle_wrong_board_v1", boundary=boundary, corpus=corrupt),
        "oracle_sources.json": dict(boundary=boundary, records=records),
        "ids.json": dict(train=list(TRAIN_IDS), canary=list(EVAL_IDS),
                         declared_prior_cpu_examined_ids=list(CPU_EXAMINED_IDS),
                         prior_examination_source="Popper handoff 2026-09-12, CPU native validation only",
                         prior_qwen_outcomes=False, solution_overlap_eval_ids=solution_overlap,
                         historical_exposure="not audited; fixed DEV IDs, not certified untouched"),
        "local_pins.json": dict(model_path=str(model_path), files=pins,
                                origin="unresolved; local byte identity only"),
        "source_hashes.json": source_hashes,
        "validation.json": dict(boundary=boundary, board_count=48, board_identities_unique=True,
                                train_eval_disjoint=True, canonical_native_accepted=48,
                                independent_row_column_box_givens_validated=48,
                                corruption="fixed one-position cyclic shift; no rerolls", assignments=assignments,
                                useful_tokens=useful_tokens, corrupt_tokens=corrupt_tokens,
                                target_text_and_token_multisets_equal=True,
                                experimental_recipe="pre-rendered native chat context; plain V3 span encoding",
                                trainer_chat_template=False, solution_overlap_eval_ids=solution_overlap,
                                tokenizer_class=type(tokenizer).__name__,
                                reasoning_gym_version=reasoning_gym_gym.installed_version(),
                                prompt_clock="unmodified native driver construction; one prompt call; actual clocks in source map",
                                expected_steps_per_fit=96, expected_fit_count=2,
                                primary_endpoint="first ACT solved count / 16; missing or invalid first ACT = 0",
                                secondary_endpoints=["first ACT continuous score", "native best", "nACTs",
                                                     "useful minus OFF paired difference",
                                                     "useful minus corrupt paired difference"],
                                evaluation="main-owned future fresh-process OFF/ON; retain every ACT; no outcomes here"),
        "trainer_commands.json": dict(boundary=boundary, commands=commands,
                                      future_seeds=[1, 2], future_seeds_scheduled=False,
                                      after_training_required=["verify corpus SHA and source/model pins",
                                          "rank8 lr1e-4 epochs3 batch1 seed0 chat_template false pack false max_len4096",
                                          "32 examples, 96 optimizer steps; zero dropped context/target tokens",
                                          "target labels and target-token passes match preflight plus EOS",
                                          "finite loss; actual adapter file hashes; external exclusive logs",
                                          "fresh-process neutral OFF/ON on fixed 16 canary IDs; first-ACT reducer"])}
    contents = {name: _encoded(value) for name, value in artifacts.items()}
    manifest = dict(schema="mini_sudoku_behavior_material_v1", boundary=boundary, status="PREPARED",
                    files={name: _sha(content) for name, content in contents.items()})
    out.mkdir(parents=True, exist_ok=False)
    for name, content in contents.items():
        with (out / name).open("xb") as target:
            target.write(content)
        (out / name).chmod(0o444)
    with (out / "manifest.json").open("xb") as target:
        target.write(_encoded(manifest))
    (out / "manifest.json").chmod(0o444)
    out.chmod(0o555)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--training-root", required=True)
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args(argv)
    result = prepare(args.out, args.model_path, args.training_root, python_executable=args.python)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
