"""Offline descriptive no-teacher anchor reduction; stdlib only, no inference."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import zlib


IDS = [f"rg/mini_sudoku/{seed}" for seed in range(1850000, 1850016)]
TEACHER = "=== A NOTE FROM YOUR TEACHER ==="
MARK = re.compile(r"^(PREDICT|ACT|NOTE|RECALL|DONE)\s*:?\s*(.*)$", re.MULTILINE)
BOARD_ROW = re.compile(r"^[ \t]*[0-4_.](?:[ \t]+[0-4_.]){3}[ \t]*$")
STATIC = Path("/tmp/astra_static_competency_terminal_20260912")
METRICS = ("solves", "available", "format_valid", "score_mean",
           "raw_native_first_score_mean", "native_best_mean", "total_actions",
           "output_tokens", "outputs_at_retokenized_cap")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def inventory(root, hashes):
    require(root.is_dir() and not root.is_symlink(), f"missing/unsafe directory: {root}")
    path = root / "artifact_hashes.json"
    files = read(path)["files"]
    require(set(item.name for item in root.iterdir()) == set(files) | {path.name},
            f"inventory file set: {root}")
    for name, expected in files.items():
        require(Path(name).name == name and name not in (".", "..", path.name), "unsafe inventory name")
        item = root / name
        require(item.is_file() and not item.is_symlink(), f"missing/unsafe file: {item}")
        actual = digest(item.read_bytes())
        require(actual == expected, f"inventory hash: {item}")
        hashes[str(item)] = actual
    hashes[str(path)] = digest(path.read_bytes())
    return hashes[str(path)]


def groups(board):
    return (list(board) + [tuple(board[row][column] for row in range(4)) for column in range(4)]
            + [tuple(board[row][column] for row in range(top, top + 2)
                     for column in range(left, left + 2)) for top in (0, 2) for left in (0, 2)])


def grid_universe():
    permutations = list(itertools.permutations(range(1, 5)))
    return [board for board in itertools.product(permutations, repeat=4)
            if all(len(set(group)) == 4 for group in groups(board))]


def parse_board(text, question=False):
    lines = text.splitlines() if question else text.replace(";", "\n").strip().splitlines()
    rows = [line.split() for line in lines if BOARD_ROW.fullmatch(line)]
    require(len(rows) == 4 and (question or len(lines) == 4), "invalid board form")
    return tuple(tuple(0 if cell in ("0", "_", ".") else int(cell) for cell in row) for row in rows)


def constraints(action, givens, solution):
    lines = action.replace(";", "\n").strip().splitlines()
    grid_lines = [line for line in lines if BOARD_ROW.fullmatch(line)]
    board = parse_board("\n".join(grid_lines)) if len(grid_lines) == 4 else None
    extras = [line for line in lines if not BOARD_ROW.fullmatch(line)]
    violations = []
    duplicates = {}
    if board:
        violations = [dict(row=row + 1, column=column + 1, given=givens[row][column],
                           returned=board[row][column]) for row in range(4) for column in range(4)
                      if givens[row][column] and givens[row][column] != board[row][column]]
        for offset, name in ((0, "rows"), (4, "columns"), (8, "boxes")):
            duplicates[name] = [index + 1 for index, group in enumerate(groups(board)[offset:offset + 4])
                                if len([cell for cell in group if cell]) != len(set(cell for cell in group if cell))]
    return dict(candidate_rows=board, extra_segments=extras, given_violations=violations,
                duplicate_groups=duplicates, blank_count=sum(cell == 0 for row in board for cell in row) if board else None,
                unchanged_givens_echo=board == givens, candidate_matches_solution=board == solution,
                classification_only_no_output_repair=True)


def endpoint(ledger):
    acts = [row for row in ledger if row["kind"] == "act"]
    for row in acts:
        score = row["score"]
        require(isinstance(score, (int, float)) and not isinstance(score, bool)
                and math.isfinite(score) and 0 <= score <= 1, "invalid native score")
    first = acts[0] if acts else None
    valid = False
    if first:
        try:
            board = parse_board(first["action"])
            valid = all(cell in (1, 2, 3, 4) for row in board for cell in row)
        except ValueError:
            pass
    score = first["score"] if first and valid else 0.0
    return dict(first_action=first, first_action_available=first is not None,
                first_action_format_valid=valid, first_action_score=score,
                first_action_solved=int(score == 1), native_best=max((row["score"] for row in acts), default=0.0),
                n_actions=len(acts), actions=acts)


def aggregate(rows):
    return dict(solves=sum(row["first_action_solved"] for row in rows),
                available=sum(row["first_action_available"] for row in rows),
                format_valid=sum(row["first_action_format_valid"] for row in rows),
                score_mean=sum(row["first_action_score"] for row in rows) / 16,
                raw_native_first_score_mean=sum(row["first_action"]["score"] if row["first_action"] else 0 for row in rows) / 16,
                native_best_mean=sum(row["native_best"] for row in rows) / 16,
                total_actions=sum(row["n_actions"] for row in rows),
                output_tokens=sum(row["output_tokens"] for row in rows),
                outputs_at_retokenized_cap=sum(row["output_tokens"] == 400 for row in rows))


def without_teacher(prompt, package):
    separator = "\n=== STATE ===\n"
    require(prompt.count(separator) == 1, "ambiguous STATE boundary")
    head, state = prompt.split(separator, 1)
    block = "\n\n" + package
    require(head.endswith(block) and head.count(block) == 1, "ambiguous teacher separator")
    return head[:-len(block)].rstrip() + separator + state


def load_run(root, preparation, modes, hashes, universe):
    prepared_hash = inventory(preparation, hashes)
    config = read(preparation / "config.json")
    preflight = read(preparation / "preflight.json")
    questions = read(preparation / "questions.json")
    require(config["episode_ids"] == IDS == [row["episode_id"] for row in questions], "fixed16 episode mismatch")
    protocol = config["protocol"]
    for key, expected in dict(episodes=16, budget_ticks=1, batch_size=8, generation_seed=7101,
                              wake_max_tokens=400, temperature=.7, note_calls=0,
                              max_model_len=4096, backend_max_model_len=16384).items():
        require(protocol[key] == expected, f"protocol mismatch: {key}")
    absent = modes == ["no_teacher"]
    require(config.get("teacher_absent", False) == absent, "teacher_absent mode mismatch")
    require(set(config["packages"]) == set(modes) == set(preflight["rows"]), "condition set mismatch")
    require(preflight["status"] == "READY" and preflight["context_fits"], "preflight not ready")
    require(preflight["exact_token_match"] == (not absent), "unmatched input label mismatch")
    if absent:
        require(config["packages"] == {"no_teacher": ""}, "nonempty absent package")
        require(preflight["posthoc_descriptive_anchor"] is True, "posthoc preflight label")
        require(config["boundary"]["teacher_present"] is False
                and config["boundary"]["posthoc_descriptive_anchor"] is True
                and config["boundary"]["input_token_matched"] is False, "anchor boundary mismatch")
    require(config["boundary"]["training"] is False and config["boundary"]["adapter"] is None,
            "not no-write/no-adapter")
    started, completed = read(root / "STARTED.json"), read(root / "COMPLETED.json")
    require(not (root / "FAILED.json").exists(), "FAILED run")
    require(started["preparation_sha256"] == prepared_hash and started["order"] == modes, "STARTED binding")
    require(set(completed["arms"]) == set(modes), "COMPLETED arm mismatch")
    puzzles = {}
    for question in questions:
        require(digest(question["question"].encode()) == question["question_sha256"], "question hash")
        givens = parse_board(question["question"], question=True)
        matches = [grid for grid in universe if all(not givens[row][column] or grid[row][column] == givens[row][column]
                                                  for row in range(4) for column in range(4))]
        require(len(matches) == 1, "nonunique public puzzle")
        puzzles[question["episode_id"]] = (givens, matches[0])
    arms, requests = {}, {}
    for mode in modes:
        folder = root / mode
        seal_hash = inventory(folder, hashes)
        report, arm_config = read(folder / "results.json"), read(folder / "config.json")
        require(all(arm_config.get(key) == value for key, value in config.items()), "arm config differs from preparation")
        require(arm_config["mode"] == mode and arm_config["preparation_sha256"] == prepared_hash, "arm config binding")
        require(completed["arms"][mode] == report and report["status"] == "COMPLETE"
                and report["execution_backend"] == "LOCAL_GPU_BACKEND" and report["mode"] == mode, "terminal report binding")
        presentations, package_tokens = (0, 0) if absent else (16, 97)
        require(report["denominator"] == len(report["episodes"]) == 16
                and report["presentations"] == presentations
                and report["package_tokens_per_presentation"] == package_tokens
                and report["cumulative_package_tokens"] == 16 * package_tokens
                and report["reserved_output_tokens"] == 6400, "report dose mismatch")
        if absent:
            require(report["episode_opportunities"] == 16 and report["boundary"] == config["boundary"], "anchor report boundary")
        process, cleanup = read(root / f"{mode}.process.json"), read(root / f"{mode}.cleanup.json")
        require(process["pid"] == cleanup["pid"] and process["device"] == cleanup["device"] == started["device"], "cleanup ownership")
        require(all(cleanup[key] is True for key in ("owned_group_empty", "gpu_processes_absent", "reservation_release_verified"))
                and cleanup["cleanup_error"] is None, "cleanup incomplete")
        require(len(preflight["rows"][mode]) == 16, "preflight row count")
        package = config["packages"][mode]
        require(preflight["package_tokens"][mode] == package_tokens
                and preflight["packages"][mode] == dict(text=package, sha256=digest(package.encode())), "package preflight")
        rows, requests[mode] = [], []
        for index, question in enumerate(questions):
            episode = question["episode_id"]
            request, output = read(folder / f"request_{index:02d}.json"), read(folder / f"output_{index:02d}.json")
            ledger = [json.loads(line) for line in (folder / f"episode_{index:02d}.jsonl").read_text().splitlines() if line.strip()]
            require(all(request.get(key) == value for key, value in preflight["rows"][mode][index].items()), "request/preflight mismatch")
            require(request["episode_id"] == output["episode_id"] == episode
                    and request["request_index"] == output["request_index"] == index
                    and all(row["episode_id"] == episode for row in ledger), "episode/request mismatch")
            require(request["mode"] == mode and request["package_presentations"] == (0 if absent else 1)
                    and request["package_tokens"] == package_tokens and request["package_sha256"] == digest(package.encode()), "request package dose")
            require(request["max_tokens"] == 400 and request["temperature"] == .7
                    and request["seed"] == ((zlib.crc32(f"{episode}/1".encode()) ^ 7101) & 0x7fffffff), "request generation settings")
            require(isinstance(output["output_tokens"], int) and 0 <= output["output_tokens"] <= 400, "output token count")
            require(request["prompt_tokens"] + 400 <= 4096, "context budget")
            require(request["prompt"].count(question["question"]) == 1, "question delivery")
            require(TEACHER not in request["prompt"] if absent else request["prompt"].count(package) == 1, "teacher delivery")
            for text_key, hash_key in (("prompt", "prompt_sha256"), ("rendered_prompt", "rendered_sha256")):
                require(digest(request[text_key].encode()) == request[hash_key], f"{text_key} hash")
            rendered = ("<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>\n"
                        "<|im_start|>user\n" + request["prompt"] + "<|im_end|>\n<|im_start|>assistant\n")
            require(request["rendered_prompt"] == rendered, "native chat wrapper")
            identity = request["source_identity"]
            require(identity["adapter_input"] is None and identity["adapter_files"] == {}
                    and identity["model_input"] == config["model_path"] and identity["backend"] == "vllm", "loader identity")
            require(digest(output["text"].encode()) == output["output_sha256"], "raw output hash")
            thoughts = [row for row in ledger if row["kind"] == "thought"]
            require(len(thoughts) == 1 and thoughts[0]["note"] == output["text"]
                    and thoughts[0]["prompt"] == request["prompt"], "raw output/thought binding")
            measured = endpoint(ledger)
            raw_acts = [match.group(2).strip() for match in MARK.finditer(output["text"]) if match.group(1) == "ACT"]
            require(raw_acts == [row["action"] for row in measured["actions"]], "raw ACT ordering")
            native_row = dict(episode_id=episode, request_index=index, **measured)
            require(report["episodes"][index] == native_row, "native endpoint row mismatch")
            givens, solution = puzzles[episode]
            action = measured["first_action"]["action"] if measured["first_action"] else ""
            diagnosis = constraints(action, givens, solution)
            require(measured["first_action_solved"] == int(measured["first_action_format_valid"]
                    and diagnosis["candidate_matches_solution"]), "native solved/independent Sudoku mismatch")
            rows.append(dict(native_row, output_tokens=output["output_tokens"], output_sha256=output["output_sha256"],
                             prompt_sha256=request["prompt_sha256"], prompt_tokens=request["prompt_tokens"],
                             public_constraint_diagnosis=diagnosis))
            requests[mode].append(request)
        totals = aggregate(rows)
        require(report["first_action_solves"] == totals["solves"], "report solve total")
        arms[mode] = dict(totals, episodes=rows, artifact_hash=seal_hash, cleanup=cleanup,
                          package_presentations=presentations, package_tokens=package_tokens,
                          input_token_counts=[request["prompt_tokens"] for request in requests[mode]])
    for path in root.iterdir():
        if path.is_file():
            hashes[str(path)] = digest(path.read_bytes())
    return dict(config=config, questions=questions, arms=arms, requests=requests,
                completed_utc=completed["completed_utc"], preparation_sha256=prepared_hash)


def analyze(root, preparation, static_root, static_preparation, static_analysis):
    hashes = {}
    universe = grid_universe()
    require(len(universe) == 288, "independent grid enumeration")
    previous = load_run(static_root, static_preparation, ["process", "sham"], hashes, universe)
    anchor = load_run(root, preparation, ["no_teacher"], hashes, universe)
    frozen = read(static_analysis)
    hashes[str(static_analysis)] = digest(static_analysis.read_bytes())
    require(frozen["valid"] is True, "previous analysis not valid")
    require(previous["questions"] == anchor["questions"], "different question bytes or IDs")
    require(previous["config"]["expected_files"] == anchor["config"]["expected_files"]
            and previous["config"]["model_path"] == anchor["config"]["model_path"], "different base pins")
    joined, paired = [], []
    for mode in ("process", "sham"):
        arm = previous["arms"][mode]
        for key in METRICS:
            if key != "native_best_mean":
                require(arm[key] == frozen["arms"][mode][key], f"frozen {mode} aggregate changed: {key}")
        require(len(frozen["arms"][mode]["episodes"]) == 16, "frozen row count")
        for index, old in enumerate(frozen["arms"][mode]["episodes"]):
            require(all(arm["episodes"][index].get(key) == value for key, value in old.items()), "frozen per-episode row changed")
    for index, episode in enumerate(IDS):
        request = anchor["requests"]["no_teacher"][index]
        for mode in ("process", "sham"):
            prior = previous["requests"][mode][index]
            block = "\n\n" + previous["config"]["packages"][mode]
            require(prior["prompt"].count(block) == 1, "ambiguous teacher separator")
            expected_prompt = without_teacher(prior["prompt"], previous["config"]["packages"][mode])
            require(request["prompt"] == expected_prompt
                    and request["rendered_prompt"] == prior["rendered_prompt"].replace(prior["prompt"], expected_prompt, 1),
                    "teacher block/separator not entirely removed")
            require(request["prompt_tokens"] < prior["prompt_tokens"], "anchor input not shorter")
            require(all(request[key] == prior[key] for key in ("seed", "max_tokens", "temperature", "source_identity")), "paired request setting mismatch")
            joined.append(dict(episode_id=episode, prior_mode=mode, exact_removal_match=True,
                               input_token_difference=request["prompt_tokens"] - prior["prompt_tokens"]))
        cells = {mode: run["arms"][mode]["episodes"][index] for mode, run in
                 (("process", previous), ("sham", previous), ("no_teacher", anchor))}
        paired.append(dict(episode_id=episode, cells={mode: {key: row[key] for key in
                           ("first_action_solved", "first_action_format_valid", "first_action_score", "native_best", "n_actions")}
                           for mode, row in cells.items()},
                           process_minus_no_teacher={key: cells["process"][key] - cells["no_teacher"][key]
                                                     for key in ("first_action_solved", "first_action_format_valid", "first_action_score")},
                           sham_minus_no_teacher={key: cells["sham"][key] - cells["no_teacher"][key]
                                                  for key in ("first_action_solved", "first_action_format_valid", "first_action_score")}))
    arms = dict(previous["arms"], **anchor["arms"])
    source_pins = {label: run["config"]["sources"] for label, run in (("static", previous), ("anchor", anchor))}
    return dict(valid=True, label="POSTHOC_DESCRIPTIVE_NO_TEACHER_ANCHOR", original_primary_unchanged=True,
                arms=arms, paired_rows=paired, exact_prompt_joins=joined, source_pins=source_pins,
                source_model_pins=anchor["config"]["expected_files"], input_sha256=hashes,
                completed_utc=dict(static=previous["completed_utc"], no_teacher=anchor["completed_utc"]),
                differences={f"{mode}_minus_no_teacher": {key: arms[mode][key] - arms["no_teacher"][key] for key in METRICS}
                             for mode in ("process", "sham")},
                independent_grid_universe=288, unique_public_question_completions=16,
                prompt_join_rule="Remove appended two-newline teacher block, then strip bootstrap trailing whitespace at STATE boundary as state.render_context does; compare all remaining bytes exactly.",
                limitations=["Post-hoc descriptive anchor; shorter unmatched input, not a matched causal comparison.",
                             "Original fixed process/sham primary is unchanged; no posthoc rescue, internalization, P1 or H1 claim.",
                             "One seed7101, existing training questions, separate later execution; no significance claim.",
                             "Native partial scores preserved from ledgers, not rerun through reasoning_gym; strict solved grids independently checked.",
                             "Counts are captured tokenizer measurements, not local retokenization; below cap is not a finish reason.",
                             "Loader/source pins are captured provenance, not official origin authentication or fresh weight/source-payload rehash.",
                             "Cleanup receipts validated offline; controller absence not independently polled.",
                             "Candidate grid extraction is classification only; missing/invalid first ACT stays zero; later ACT/native best stays separate."])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--static-root", type=Path, default=STATIC / "astra_P1_static_competency_20260912_attempt1")
    parser.add_argument("--static-preparation", type=Path, default=STATIC / "astra_P1_static_competency_preparation_20260912_attempt1")
    parser.add_argument("--static-analysis", type=Path, default=Path("/tmp/astra_static_competency_terminal_analysis_20260912.json"))
    parser.add_argument("--output-new", type=Path, required=True)
    args = parser.parse_args()
    require(not args.output_new.exists() and not args.output_new.is_symlink(), "output already exists")
    for source in (args.root, args.preparation, args.static_root, args.static_preparation):
        require(args.output_new.resolve() != source.resolve() and source.resolve() not in args.output_new.resolve().parents,
                "output overlaps captured input")
    result = analyze(args.root, args.preparation, args.static_root, args.static_preparation, args.static_analysis)
    with args.output_new.open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(valid=True, output=str(args.output_new), sha256=digest(args.output_new.read_bytes()),
                          cells={mode: {key: arm[key] for key in METRICS} for mode, arm in result["arms"].items()})))


if __name__ == "__main__":
    main()
