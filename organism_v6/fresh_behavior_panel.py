"""CPU preparation/reduction of the fixed SEQ-073 adapter reread; never fit or launch."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, is_dataclass
import hashlib
import importlib
from importlib.metadata import version
import inspect
import itertools
import json
from pathlib import Path
import statistics

from . import batch_loop, mini_sudoku_behavior_analysis as analysis
from . import mini_sudoku_behavior_material as material
from . import neutral_pair_custody as custody
from . import reasoning_gym_gym as native
from .reasoning_neutral_probe import file_hashes
from .run_reasoning_neutral import read_spec
from .preschool_reasoning import facts_from_act, outcome_block


BASE = Path("/localhome/local-rohing/astra_diagnostics")
ROOTS = (BASE / "astra_mini_sudoku_useful_corrupt_20260912_attempt3",
         BASE / "astra_mini_sudoku_seed1_20260912_attempt1",
         BASE / "astra_mini_sudoku_seed2_20260912_attempt1")
MODEL = "/localhome/local-rohing/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct/snapshots/a09a35458c702b33eeacc393d103063234e8bc28"
CANDIDATES = tuple(f"rg/mini_sudoku/{seed}" for seed in range(1900070, 1900100))
GENERATOR_SHA256 = "20b77f97b1f5a9aa364940311d6647c4fa3e2b69834995371e0b20dd9f818c0c"
MATERIAL_PINS = {
    "useful.json": "c6954d48246a37cdd1ac06309d819664e37a2119d92cbf6d2eceeb945caf5db4",
    "corrupt.json": "e670bb9ddb8bfddea8774e435fec5054b5ab0cf4dca5a07a1ba7f433c95b2127",
    "oracle_sources.json": "e86d480dbcc723115aaf4789e477efd23f69302e9cf4109243dc64ed3ba90785",
    "ids.json": "6468cb882e64145c0529b7765df2956c3e04426060f4243d447f4d5abf3b76a2",
    "local_pins.json": "84f9a010ce2f0367f0456ccc25da4149a9fb833322414a0c897248cb1c2f43fb",
}
WEIGHT_PINS = (
    ("42096acafe563db0e614ce7cd42e874159545822066cdfeb47b6501eee0fd14c",
     "9cb1a01d93222131587f1cd4f550844007c681f32eb13788b4fabda9aace4689"),
    ("91d29c8ec9ff80a6708c03d4fe7bcd9a9a7975a206af398a6b036b24dc7473f3",
     "88d322b9f5d3370a6612bc23534a3b3da06090464d833bec5f1e30722a83510e"),
    ("8f5d08e15b93b7f3184fc3f255c44bff4c2a05d03c3a5dde34ec9b81739af3e0",
     "5c1e1ce199c00c6a8003db8cc97948c765fb170700eabbb12087298058cc081e"),
)
SETTINGS = dict(gen_seed=0, seed_salt=15420, budget_ticks=1, wake_max_tokens=400,
                scratchpad_max_tokens=100, total_token_budget=38400, max_episodes=16,
                max_model_len=4096, worker_timeout_seconds=900, order=["off", "on"])
LIMITATIONS = [
    "Exploratory, potentially overtuned follow-up to a known weak development-panel effect; not confirmation.",
    "Optimizer seeds 0/1/2 share identical training data; not independent-data replications.",
    "One shared 16-item panel; repeated conditions are not independent puzzles or significance evidence.",
    "Exact labeled solution-grid nonoverlap only, not nonisomorphism or absence from model pretraining.",
    "External-oracle material, not parenting, general G2, H1/H2 qualification, or clean lineage.",
    "Configured source/model hashes do not authenticate official origin or loaded runtime.",
    "Fixed useful-then-corrupt ordering retains time/device effects; OFF is paired per adapter.",
    "Missing/invalid/unmeasured first ACT is zero; missing artifacts or failed processes are not zero observations.",
]


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _encoded(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _write(path, value):
    with Path(path).open("xb") as target:
        target.write(_encoded(value))


def _key(board):
    return tuple(tuple(row) for row in board)


def _solutions():
    rows = tuple(itertools.permutations((1, 2, 3, 4)))
    return tuple(board for board in itertools.product(rows, repeat=4)
                 if all(len({board[row][column] for row in range(4)}) == 4 for column in range(4))
                 and all(len({board[row][column] for row in range(top, top + 2)
                              for column in range(left, left + 2)}) == 4
                         for top in (0, 2) for left in (0, 2)))


def _entry(gym, episode_id, solutions):
    family, seed = native.parse_id(episode_id)
    dataset, entry = gym._item(family, seed)
    puzzle = material.board_from_text(entry["question"], question=True)
    solution = material.board_from_text(entry["answer"])
    metadata = entry["metadata"]
    _require(metadata["puzzle"] == puzzle and metadata["solution"] == solution,
             "entry/metadata board mismatch")
    _require(all(type(cell) is int and 0 <= cell <= 4 for row in metadata["puzzle"] for cell in row)
             and all(type(cell) is int and 1 <= cell <= 4 for row in metadata["solution"] for cell in row),
             "invalid board cell")
    _require(metadata["num_empty"] == sum(cell == 0 for row in puzzle for cell in row), "blank count mismatch")
    material.validate_solution(puzzle, solution)
    matches = [board for board in solutions if all(not puzzle[row][column]
               or puzzle[row][column] == board[row][column] for row in range(4) for column in range(4))]
    _require(matches == [_key(solution)], "not uniquely solvable")
    answer = "\n".join(" ".join(map(str, row)) for row in solution)
    _require(entry["answer"] == answer, "noncanonical native answer")
    for text in (answer, native.decode_answer(answer.replace("\n", " ; "))):
        score = dataset.score_answer(answer=text, entry=entry)
        _require(type(score) in (int, float) and score == 1, "native verifier rejects reference")
    config = getattr(dataset, "config", None)
    return dict(episode_id=episode_id, entry=entry, puzzle=puzzle, solution=solution,
                entry_sha256=_sha(_encoded(entry)), board_sha256=_sha(_encoded(puzzle)),
                solution_sha256=_sha(_encoded(solution)),
                dataset_config=asdict(config) if is_dataclass(config) else None)


def select_panel(gym, historical, excluded_ids=()):
    """Deterministic CPU-only selection; malformed candidates abort, overlaps skip."""
    solutions = _solutions()
    _require(len(solutions) == 288, "independent completion enumeration failed")
    expected = set(material.TRAIN_IDS + material.EVAL_IDS)
    _require(len(historical) == 48 and {row["episode_id"] for row in historical} == expected,
             "historical 32+16 IDs mismatch")
    for old in historical:
        actual = _entry(gym, old["episode_id"], solutions)
        _require(all(actual[name] == old[name] for name in ("entry", "puzzle", "solution")),
                 "historical generator drift")
    forbidden_solutions = {_key(row["solution"]) for row in historical}
    forbidden_puzzles = {_key(row["puzzle"]) for row in historical}
    selected_solutions, selected_puzzles, selected, audit = set(), set(), [], []
    for episode_id in CANDIDATES:
        if episode_id in excluded_ids:
            audit.append(dict(episode_id=episode_id, decision="prior_exposure"))
            continue
        _require(gym.split_of(episode_id) == "canary", "candidate outside frozen canary range")
        record = _entry(gym, episode_id, solutions)
        solution, puzzle = _key(record["solution"]), _key(record["puzzle"])
        reason = ("historical_solution" if solution in forbidden_solutions else
                  "selected_solution" if solution in selected_solutions else
                  "historical_puzzle" if puzzle in forbidden_puzzles else
                  "selected_puzzle" if puzzle in selected_puzzles else "accepted")
        audit.append(dict(record, decision=reason))
        if reason == "accepted":
            selected.append(record)
            selected_solutions.add(solution)
            selected_puzzles.add(puzzle)
            if len(selected) == 16:
                break
    return selected, audit


def _runtime():
    _require(native.installed_version() == "0.1.25", "reasoning_gym version mismatch")
    generator = importlib.import_module("reasoning_gym.games.mini_sudoku")
    path = Path(inspect.getfile(generator)).resolve()
    _require(custody._digest(path) == GENERATOR_SHA256, "generator digest mismatch")
    modules = [generator, importlib.import_module("reasoning_gym.factory"),
               importlib.import_module("reasoning_gym.dataset")]
    files = {str(Path(inspect.getfile(module)).resolve()): custody._digest(inspect.getfile(module))
             for module in modules}
    packages = {name: version(name) for name in ("reasoning_gym", "vllm", "transformers", "tokenizers", "torch")}
    _require(packages["vllm"] == "0.27.1", "historical vllm version mismatch")
    return dict(files=files, packages=packages,
                scope="Generator historical pin; dependency hashes observed now, not historical runtime authentication")


def _historical(roots, snapshot, inputs):
    specs, reference, model_hashes = {}, None, None
    for seed, root in enumerate(roots):
        directory = root / "material"
        manifest = inputs.read(directory / "manifest.json")
        _require(manifest.get("status") == "PREPARED", "historical material incomplete")
        artifacts = {}
        for name, digest in manifest["files"].items():
            path = custody._file(directory, name)
            artifacts[name] = inputs.read(path)
            _require(inputs.hashes[str(path)] == digest, "material manifest mismatch")
        for name, digest in MATERIAL_PINS.items():
            _require(manifest["files"].get(name) == digest, "historical material pin mismatch")
        if reference is None:
            reference = artifacts
        _require(all(artifacts[name] == reference[name] for name in MATERIAL_PINS), "cross-seed material mismatch")
        for arm_index, arm in enumerate(("useful", "corrupt")):
            spec = inputs.read(root / f"logs/{arm}/probe_spec.json")
            adapter = root / f"training/{arm}_seed{seed}"
            _require(spec["adapter_path"] == str(adapter) and spec["model_path"] == MODEL, "actual input path mismatch")
            _require(spec["expected_adapter_hashes"].get("adapter_model.safetensors") == WEIGHT_PINS[seed][arm_index],
                     "actual adapter weight pin mismatch")
            _require(all(spec[name] == value for name, value in SETTINGS.items()), "historical generation settings mismatch")
            done = inputs.read(root / f"probes/{arm}/PAIR_DONE.json")
            _require(done["spec_sha256"] == inputs.hashes[str(root / f"logs/{arm}/probe_spec.json")],
                     "historical spec binding mismatch")
            _require(done["source_snapshot"]["sha256"] == snapshot["sha256"], "historical probe source drift")
            _require(spec["families_sha256"] == custody._digest(Path(snapshot["source_root"]) / "organism_v6/reasoning_gym_families.json"),
                     "families digest mismatch")
            _require(file_hashes(adapter) == spec["expected_adapter_hashes"], "adapter inventory mismatch")
            if model_hashes is None:
                model_hashes = file_hashes(MODEL)
            _require(model_hashes == spec["expected_model_hashes"] == artifacts["local_pins.json"]["files"],
                     "model/tokenizer inventory mismatch")
            specs[f"seed{seed}_{arm}"] = spec
    return specs, reference


def _prompt_record(gym, tokenizer, record):
    prompt = material.one_tick_prompt(gym, record["episode_id"])
    _require(record["entry"]["question"].strip() in prompt, "native prompt lost question")
    rendered = tokenizer.apply_chat_template([dict(role="user", content=prompt)],
                                             tokenize=False, add_generation_prompt=True)
    tokens = tokenizer.encode(rendered, add_special_tokens=False)
    _require(getattr(tokenizer, "eos_token_id", None) is not None, "tokenizer EOS missing")
    _require(len(tokens) + 400 + 512 + 100 <= 4096, "prompt/context allowance exceeds 4096")
    action = record["entry"]["answer"].replace("\n", " ; ")
    facts = facts_from_act(dict(kind="act", episode_id=record["episode_id"], execution_id="cpu-reference/1", tick=1,
                                action=action, outcome="attempt 1: verifier score 1.00 (accepted)",
                                score=1.0, occurrence_id="cpu-reference"))
    scratchpad = prompt.rstrip("\n") + "\n\n" + outcome_block(facts, "Scratchpad")
    scratchpad_rendered = tokenizer.apply_chat_template([dict(role="user", content=scratchpad)],
                                                        tokenize=False, add_generation_prompt=True)
    scratchpad_tokens = tokenizer.encode(scratchpad_rendered, add_special_tokens=False)
    _require(len(scratchpad_tokens) + 400 + 100 <= 4096, "native scratchpad context exceeds 4096")
    return dict(record, q=prompt, q_sha256=_sha(prompt.encode()), rendered_q_sha256=_sha(rendered.encode()),
                prompt_tokens=len(tokens), prompt_token_ids_sha256=_sha(_encoded(tokens)),
                canonical_scratchpad_prompt_sha256=_sha(scratchpad.encode()),
                canonical_scratchpad_tokens=len(scratchpad_tokens),
                scratchpad_allowance_tokens=512,
                context_check="Wake 400 + conservative post-outcome wrapper/action allowance 512 + scratchpad 100; actual prompts audited after probe")


def prepare(out_new, *, roots=ROOTS, source_root=None, prior_exposure=()):
    """Native CPU preparation; caller has selected scope. No approval machinery."""
    output = Path(out_new).absolute()
    roots = tuple(Path(root).resolve(strict=True) for root in roots)
    _require(len(roots) == 3, "three historical roots required")
    _require(not output.exists() and not output.is_symlink(), "output already exists")
    source = Path(source_root or Path(__file__).resolve().parents[1]).resolve(strict=True)
    _require(source == Path(__file__).resolve().parents[1], "run helper from declared source")
    _require(all(isinstance(value, str) for value in prior_exposure), "invalid prior exposure IDs")
    protected = (*roots, Path(MODEL).resolve(), source)
    _require(not any(output.resolve() == path or output.resolve() in path.parents or path in output.resolve().parents
                     for path in protected), "output overlaps protected inputs")
    output.mkdir(parents=True)
    inputs = analysis._Inputs()
    try:
        runtime = _runtime()
        snapshot = custody.source_snapshot()
        specs, artifacts = _historical(roots, snapshot, inputs)
        families = source / "organism_v6/reasoning_gym_families.json"
        gym = native.ReasoningGymGym(families_path=str(families), require_package=True, strict_verifier=True)
        excluded = sorted(set(material.TRAIN_IDS + material.EVAL_IDS)
                          | set(artifacts["ids.json"]["declared_prior_cpu_examined_ids"])
                          | set(gym.cfg["canary_set"]) | set(prior_exposure))
        selected, audit = select_panel(gym, artifacts["oracle_sources.json"]["records"], excluded)
        _write(output / "candidate_audit.json", dict(candidates=list(CANDIDATES), records=audit))
        _require(len(selected) == 16, "PANEL_INSUFFICIENT: fewer than 16 eligible candidates")
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(MODEL, local_files_only=True)
        selected = [_prompt_record(gym, tokenizer, record) for record in selected]
        panel_ids = [record["episode_id"] for record in selected]
        _write(output / "panel.json", dict(episode_ids=panel_ids, records=selected, excluded_ids=excluded,
               historical_records=artifacts["oracle_sources.json"]["records"], limitations=LIMITATIONS))
        (output / "specs").mkdir()
        (output / "probes").mkdir()
        for cell, original in specs.items():
            spec = dict(original, episode_ids=panel_ids, families_path=str(families),
                        probe_root=str(output / "probes"), output_dir=str(output / "probes" / cell),
                        training_life_roots=[str(root) for root in roots],
                        lineage_roots=[str(root / "training") for root in roots],
                        panel_role="exploratory", selection_used_episode_ids=excluded)
            path = output / "specs" / (cell + ".json")
            _write(path, spec)
            digest = custody._digest(path)
            read_spec(path, digest)
            with path.with_suffix(".json.sha256").open("x") as target:
                target.write(digest + "\n")
        inputs.verify()
        _require(_runtime() == runtime, "runtime changed during preparation")
        custody.verify_source_snapshot(snapshot)
        _write(output / "preflight.json", dict(status="PREPARED", model_calls=0, fits=0,
               runtime=runtime, source_snapshot=snapshot, helper_sha256=custody._digest(__file__),
               historical_input_sha256=inputs.hashes, tokenizer_class=type(tokenizer).__name__,
               gym_configuration=gym.cfg,
               generation_settings=SETTINGS, execution_order="Within each seed useful then corrupt; seeds may use separate reserved devices"))
        inventory = {str(path.relative_to(output)): custody._digest(path)
                     for path in output.rglob("*") if path.is_file()}
        _write(output / "manifest.json", dict(status="PREPARED", sha256=inventory))
        for path in output.rglob("*"):
            if path.is_file():
                path.chmod(0o444)
        return dict(status="PREPARED", episode_ids=panel_ids, manifest_sha256=custody._digest(output / "manifest.json"))
    except Exception as error:
        _write(output / "failure.json", dict(status="PREPARATION_FAILED", error=str(error), fits=0, model_calls=0))
        raise


def _load_prepared(root, inputs):
    _require(not (root / "failure.json").exists(), "preparation failed")
    manifest = inputs.read(root / "manifest.json")
    _require(manifest.get("status") == "PREPARED", "preparation not complete")
    required = {"panel.json", "candidate_audit.json", "preflight.json"}
    required.update(f"specs/seed{seed}_{arm}.json" for seed in range(3) for arm in ("useful", "corrupt"))
    _require(required <= manifest["sha256"].keys(), "preparation manifest missing inputs")
    for name, digest in manifest["sha256"].items():
        relative = Path(name)
        _require(not relative.is_absolute() and ".." not in relative.parts, "unsafe manifest path")
        path = root / relative
        _require(path.is_file() and not path.is_symlink() and root in path.resolve().parents, "unsafe prepared file")
        _require(custody._digest(path) == digest, "prepared file digest mismatch")
        inputs.hashes[str(path)] = digest
    panel = inputs.read(root / "panel.json")
    ids = panel["episode_ids"]
    _require(len(ids) == len(set(ids)) == 16 and set(ids) <= set(CANDIDATES), "invalid fresh panel IDs")
    _require([record["episode_id"] for record in panel["records"]] == ids, "panel record order mismatch")
    _require(not set(ids) & set(panel["excluded_ids"]), "panel contains prior exposure")
    historical = panel["historical_records"]
    _require(len(historical) == 48 and {row["episode_id"] for row in historical} == set(material.TRAIN_IDS + material.EVAL_IDS),
             "historical exclusions incomplete")
    solutions = {_key(row["solution"]) for row in panel["records"]}
    _require(len(solutions) == 16 and not solutions & {_key(row["solution"]) for row in historical}, "solution overlap")
    return panel, inputs.read(root / "preflight.json")


def _condition(root, condition, spec, panel, preflight, inputs):
    directory = root / condition
    config = inputs.read(directory / "configuration.json")
    results = inputs.read(directory / "results.json")
    _require(config["episode_ids"] == panel["episode_ids"], "condition panel mismatch")
    for name in ("gen_seed", "seed_salt", "budget_ticks", "wake_max_tokens", "scratchpad_max_tokens",
                 "total_token_budget", "max_episodes"):
        _require(config[name] == spec[name] == SETTINGS[name], "generation setting mismatch")
    expected = {"model": spec["expected_model_hashes"]}
    if condition == "on":
        expected["adapter"] = spec["expected_adapter_hashes"]
    _require(config["hashes_before"] == expected, "condition input hashes mismatch")
    _require(config["sources"]["model"] == spec["model_path"]
             and config["source_identity"]["adapter_input"] == (spec["adapter_path"] if condition == "on" else None),
             "condition source path mismatch")
    _require(config["reasoning_gym_version"] == "0.1.25"
             and config["source_identity"]["default_temperature"] == 0.7, "generation contract mismatch")
    _require(config["gym_configuration"] == preflight["gym_configuration"], "gym configuration mismatch")
    snapshot = preflight["source_snapshot"]
    _require(_sha(config["birth_prompt"].encode()) == snapshot["sha256"]["organism_v6/bootstrap_reasoning_gym.txt"],
             "bootstrap mismatch")
    required_code = {str(Path(snapshot["source_root"]) / f"organism_v6/{module}.py")
                     for module in custody._PROBE_MODULES}
    _require(required_code <= config["code_hashes_before"].keys(), "missing probe source inventory")
    for name, digest in config["code_hashes_before"].items():
        relative = str(Path(name).relative_to(snapshot["source_root"]))
        _require(snapshot["sha256"].get(relative) == digest, "probe source mismatch")
    requests = inputs.read(directory / "generations.jsonl", jsonl=True)
    for request in requests:
        if request.get("kind") == "generation_request":
            _require(request.get("source_identity") == config["source_identity"], "request backend identity mismatch")
            _require(request.get("max_tokens") in (400, 100) and request.get("temperature") == 0.7,
                     "request generation contract mismatch")
    wake = [row for row in requests if row.get("kind") == "generation_request" and row.get("max_tokens") == 400]
    _require(len(wake) == 16, "wrong wake request count")
    for record, request in zip(panel["records"], wake):
        _require(request["prompts"] == [record["q"]] and request["temperature"] == 0.7
                 and request["seeds"] == [batch_loop._seed_for(record["episode_id"], 1, 0)], "first prompt/seed mismatch")
    entries = results["episodes"]
    _require(len(entries) == 16 and {entry["episode_id"] for entry in entries} == set(panel["episode_ids"]),
             "missing or duplicate result entries")
    _require(len({entry["ledger"] for entry in entries}) == 16, "reused ledger")
    by_id = {entry["episode_id"]: entry for entry in entries}
    episodes = [analysis._episode(by_id[episode_id], directory, inputs) for episode_id in panel["episode_ids"]]
    return dict(episodes=episodes, summary=analysis._totals(episodes),
                first_act_status_counts=dict(Counter(row["first_act"]["status"] for row in episodes)))


def reduce(prepared_root, output_new):
    """Read all twelve completed conditions; preserve paired OFF and first-ACT semantics."""
    root, output = Path(prepared_root).resolve(strict=True), Path(output_new).absolute()
    _require(not output.exists() and not output.is_symlink(), "output already exists")
    _require(not (root / "probes") in output.resolve().parents and not (root / "specs") in output.resolve().parents,
             "report overlaps protected evidence")
    inputs = analysis._Inputs()
    panel, preflight = _load_prepared(root, inputs)
    for name, digest in preflight["runtime"]["files"].items():
        _require(custody._digest(name) == digest, "generator/dependency drift since preparation")
    seeds, off_vectors = [], []
    for seed in range(3):
        pairs = {}
        for arm in ("useful", "corrupt"):
            cell = f"seed{seed}_{arm}"
            path = root / "specs" / (cell + ".json")
            spec = inputs.read(path)
            pair_root = root / "probes" / cell
            _require(spec["output_dir"] == str(pair_root), "pair output binding mismatch")
            _require(spec["episode_ids"] == panel["episode_ids"] and spec["panel_role"] == "exploratory"
                     and spec["order"] == ["off", "on"], "prospective spec mismatch")
            binding = analysis._pair_custody(pair_root, inputs)
            _require(binding["status"] == "ARTIFACT_CUSTODY_VALIDATED", "pair incomplete; not a zero observation")
            _require(binding["spec_sha256"] == inputs.hashes[str(path)]
                     and binding["source_snapshot"] == preflight["source_snapshot"], "pair/preparation binding mismatch")
            for condition in ("off", "on"):
                cleanup = inputs.read(pair_root / (condition + ".cleanup.json"))
                _require(cleanup.get("owned_group_empty") is True and cleanup.get("gpu_processes_absent") is True,
                         "worker cleanup unverified")
            pair = {condition: _condition(pair_root, condition, spec, panel, preflight, inputs)
                    for condition in ("off", "on")}
            pair["custody"] = binding
            pair["on_minus_off"] = analysis._difference(pair["on"], pair["off"])
            pairs[arm] = pair
            off_vectors.append([(row["first_act"].get("action"), row["metrics"]["first_act_native_score_zero_filled"])
                                for row in pair["off"]["episodes"]])
        seeds.append(dict(optimizer_seed=seed, pairs=pairs, useful_minus_corrupt={
            name: analysis._difference(pairs["useful"][name], pairs["corrupt"][name])
            for name in ("off", "on", "on_minus_off")}))
    gains = [row["useful_minus_corrupt"]["on_minus_off"]["summary"]["first_act_solved_count"] for row in seeds]
    inputs.verify()
    report = dict(evidence_label="EXPLORATORY_ORACLE_DIAGNOSTIC", episode_ids=panel["episode_ids"], seeds=seeds,
                  solved_count_gain=dict(values=gains, mean=statistics.mean(gains), median=statistics.median(gains),
                                         range=[min(gains), max(gains)], all_three_positive=all(value > 0 for value in gains)),
                  all_off_action_score_vectors_equal=all(vector == off_vectors[0] for vector in off_vectors),
                  limitations=LIMITATIONS, input_sha256=inputs.hashes, reducer_sha256=custody._digest(__file__))
    _write(output, report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("--out-new", required=True)
    prep.add_argument("--source-root")
    for seed, root in enumerate(ROOTS):
        prep.add_argument(f"--seed{seed}-root", default=str(root))
    prep.add_argument("--prior-exposure-json", help="Optional frozen JSON list of additional previously examined IDs")
    reduction = commands.add_parser("reduce")
    reduction.add_argument("--prepared-root", required=True)
    reduction.add_argument("--output-new", required=True)
    args = parser.parse_args(argv)
    if args.command == "prepare":
        prior = json.loads(Path(args.prior_exposure_json).read_text()) if args.prior_exposure_json else []
        _require(isinstance(prior, list), "prior exposure must be a JSON list")
        result = prepare(args.out_new, roots=[getattr(args, f"seed{seed}_root") for seed in range(3)],
                         source_root=args.source_root, prior_exposure=prior)
        print(json.dumps(result, sort_keys=True))
    else:
        reduce(args.prepared_root, args.output_new)
        print("FRESH_BEHAVIOR_REPORT_WRITTEN " + args.output_new)


if __name__ == "__main__":
    main()
