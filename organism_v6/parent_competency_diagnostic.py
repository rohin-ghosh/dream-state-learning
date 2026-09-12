"""Static process/sham teaching scout: inference only, no training or NOTE gate."""
from __future__ import annotations

import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys

from . import batch_loop, model_backend, parent_material_diagnostic as formation
from . import preschool_reasoning as policy, run_reasoning_neutral as supervisor
from .mini_sudoku_behavior_material import TRAIN_IDS, EVAL_IDS, board_from_text
from .parent_material_write import _load_tokenizer
from .reasoning_gym_gym import ReasoningGymGym, FAMILIES_JSON, BOOTSTRAP_PATH
from .reasoning_neutral_probe import _ProbeLedger


PACKAGES = {
    "process": "=== A NOTE FROM YOUR TEACHER ===\n"
    "First, check the requested answer form before submitting any candidate. Identify the required structure "
    "and compare your candidate with that structure. Reject a candidate that does not fit the requested form.\n"
    "Next, keep a ledger of the stated constraints while considering your candidate. Check each constraint "
    "against the candidate before submitting it. Revise a candidate that conflicts with any stated constraint. "
    "Use only the visible question and public feedback; do not assume an undisplayed result.",
    "sham": "=== A NOTE FROM YOUR TEACHER ===\n"
    "First, notice the presented workshop setting while considering the current question. Notice the "
    "arrangement and the description of that setting. The workshop presents a question within "
    "the current setting.\n"
    "Next, notice the sequence of workshop occasions while considering the moment. Each occasion "
    "has a place within the workshop sequence. The current occasion follows an earlier occasion and precedes "
    "a later occasion. Use only the visible question and public feedback; do not assume an undisplayed result.",
}
MODES = ("process", "sham")
BOUNDARY = dict(label="EXPLORATORY_STATIC_COMPETENCY_PACKAGE", inference_only=True,
                training=False, clean_lineage=False, adapter=None, H1_claim=False,
                origin="UNRESOLVED_LOCAL_BASE_HASHES_ONLY", adaptive_parenting=False,
                interpretation="joint FORM_CHECK then CONSTRAINT_LEDGER package, not separation of competencies",
                endpoint="first native ACT; missing or invalid first action scores zero",
                panel="existing training questions, not held-out generalization")
PROTOCOL = dict(episodes=16, budget_ticks=1, batch_size=8, generation_seed=7101,
                wake_max_tokens=400, temperature=0.7, max_model_len=4096,
                backend_max_model_len=16384,
                presentations_per_arm=16, reserved_output_tokens_per_arm=6400,
                note_calls=0, worker_timeout_seconds=900)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_bytes())


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def seal(root):
    formation._write(root / "artifact_hashes.json", dict(files={path.name: formation._hash(path)
                     for path in root.iterdir() if path.is_file()}))
    for path in root.iterdir():
        path.chmod(0o444)
    root.chmod(0o555)


def verify_inventory(root):
    files = read(root / "artifact_hashes.json")["files"]
    require({path.name for path in root.iterdir()} == set(files) | {"artifact_hashes.json"}, "artifact inventory mismatch")
    for name, expected in files.items():
        require(Path(name).name == name and name not in (".", "..", "artifact_hashes.json"), "unsafe artifact path")
        require(not (root / name).is_symlink() and formation._hash(root / name) == expected, "artifact hash mismatch")
    return formation._hash(root / "artifact_hashes.json")


def selected_ids(ids, gym):
    require(isinstance(ids, list) and len(ids) == len(set(ids)) == 16 and set(ids) <= set(TRAIN_IDS),
            "choose exactly 16 unique IDs from existing mini_sudoku_behavior_material.TRAIN_IDS")
    held = set(EVAL_IDS)
    for split in ("canary", "gate", "exam"):
        held.update(gym.benchmarks(split))
    require(not set(ids) & held and all(gym.split_of(episode) == "train" for episode in ids),
            "training selection overlaps held-out panel")


def fresh_output(path, protected):
    root = Path(path).absolute()
    require(not root.exists() and not root.is_symlink() and root == root.resolve(), "fresh canonical output required")
    for value in protected:
        other = Path(value).resolve()
        require(not (root == other or root in other.parents or other in root.parents), "output overlaps protected inputs")
    return root


def condition_packages(teacher_absent=False):
    return {"no_teacher": ""} if teacher_absent else PACKAGES


def bootstrap_for(gym, mode):
    return gym.birth_prompt() if mode == "no_teacher" else gym.birth_prompt() + "\n\n" + PACKAGES[mode]


def prompts_for(gym, ids, mode):
    bootstrap = bootstrap_for(gym, mode)
    drivers = [formation.DiagnosticDriver(gym.episode_from_id(episode, 1), bootstrap, gym, None, 1) for episode in ids]
    return [driver.prompt() for driver in drivers]


def preflight(gym, ids, tokenizer, *, teacher_absent=False):
    selected = condition_packages(teacher_absent)
    packages = {mode: dict(text=text, sha256=policy._sha(text.encode())) for mode, text in selected.items()}
    prompts = {mode: prompts_for(gym, ids, mode) for mode in selected}
    for mode in selected:
        for prompt in prompts[mode]:
            if teacher_absent:
                require("=== A NOTE FROM YOUR TEACHER ===" not in prompt, "teacher present in absent anchor")
            else:
                require(prompt.count(PACKAGES[mode]) == 1 and PACKAGES[MODES[1 - MODES.index(mode)]] not in prompt,
                        "package not presented exactly once")
    if tokenizer is None:
        return dict(status="PREFLIGHT_PENDING_TOKENIZER", packages=packages, prompts=prompts,
                    reason="actual local tokenizer unavailable; no token estimates or padding")
    tokens = {mode: len(tokenizer.encode(text, add_special_tokens=False)) for mode, text in selected.items()}
    rows = {}
    for mode in selected:
        rows[mode] = []
        for episode, prompt in zip(ids, prompts[mode]):
            rendered = tokenizer.apply_chat_template([dict(role="user", content=prompt)], tokenize=False, add_generation_prompt=True)
            count = len(tokenizer.encode(rendered, add_special_tokens=False))
            rows[mode].append(dict(episode_id=episode, prompt=prompt, rendered_prompt=rendered,
                                  prompt_sha256=policy._sha(prompt.encode()), rendered_sha256=policy._sha(rendered.encode()),
                                  prompt_tokens=count, seed=batch_loop._seed_for(episode, 1, PROTOCOL["generation_seed"])))
    matched = not teacher_absent and tokens["process"] == tokens["sham"] and all(left["prompt_tokens"] == right["prompt_tokens"]
                    for left, right in zip(rows["process"], rows["sham"]))
    fits = all(row["prompt_tokens"] + 400 <= PROTOCOL["max_model_len"] for arm in rows.values() for row in arm)
    return dict(status="READY" if (matched or teacher_absent) and fits else "PREFLIGHT_PENDING_PACKAGE_OR_CONTEXT_BUDGET",
                packages=packages, package_tokens=tokens, rows=rows, exact_token_match=matched, context_fits=fits,
                posthoc_descriptive_anchor=teacher_absent,
                reason="fixed complete packages; no padding, retries, or generated rewrite")


def prepare(out, model_path, expected_files, ids, *, gym=None, tokenizer=None, teacher_absent=False):
    model = Path(model_path).resolve(strict=True)
    root = fresh_output(out, [model, Path(__file__).resolve().parents[1]])
    require(formation.local_files(model) == expected_files, "local base pins mismatch")
    gym = gym if gym is not None else ReasoningGymGym(require_package=True, strict_verifier=True)
    require(isinstance(gym, ReasoningGymGym) and gym.strict_verifier, "native strict public verifier required")
    selected_ids(ids, gym)
    injected = tokenizer is not None
    if tokenizer is None:
        try:
            tokenizer = _load_tokenizer(str(model))
        except (ImportError, OSError):
            tokenizer = None
    check = preflight(gym, ids, tokenizer, teacher_absent=teacher_absent)
    if injected:
        check["status"] = "SYNTHETIC_CPU_ONLY" if check["status"] == "READY" else check["status"]
    questions = [dict(episode_id=episode, question=gym.question(episode), question_sha256=policy._sha(gym.question(episode).encode())) for episode in ids]
    sources = {str(Path(module.__file__).resolve()): formation._hash(module.__file__) for module in
               (sys.modules[__name__], formation, batch_loop, model_backend, sys.modules[ReasoningGymGym.__module__])}
    sources[str(Path(FAMILIES_JSON).resolve())] = formation._hash(FAMILIES_JSON)
    sources[str(Path(BOOTSTRAP_PATH).resolve())] = formation._hash(BOOTSTRAP_PATH)
    boundary = dict(BOUNDARY, teacher_present=not teacher_absent, posthoc_descriptive_anchor=teacher_absent,
                    input_token_matched=bool(check.get("exact_token_match", False)))
    if teacher_absent:
        boundary["interpretation"] = "post-hoc no-teacher descriptive anchor, shorter unmatched input"
    config = dict(boundary=boundary, protocol=PROTOCOL, model_path=str(model), expected_files=expected_files,
                  teacher_absent=teacher_absent, episode_ids=ids, packages=condition_packages(teacher_absent),
                  tokenizer="synthetic CPU injection" if injected else "actual local tokenizer",
                  sources=sources, prepared_utc=utc())
    require(formation.local_files(model) == expected_files, "model changed during preparation")
    root.mkdir(parents=True)
    for name, value in (("config.json", config), ("preflight.json", check), ("questions.json", questions)):
        formation._write(root / name, value)
    seal(root)
    return dict(status=check["status"], preparation=str(root), boundary=boundary)


def action_summary(rows):
    acts = [row for row in rows if row["kind"] == "act"]
    first = acts[0] if acts else None
    valid = False
    if first:
        try:
            board = board_from_text(first["action"])
            valid = all(1 <= cell <= 4 for row in board for cell in row)
        except ValueError:
            pass
    score = first["score"] if first and valid else 0.0
    return dict(first_action=first, first_action_available=first is not None, first_action_format_valid=valid,
                first_action_score=score, first_action_solved=int(score == 1),
                native_best=max((row["score"] for row in acts), default=0.0), n_actions=len(acts), actions=acts)


def run_arm(preparation, out, mode, *, gym, backend_factory, allow_synthetic=False):
    prep = Path(preparation).resolve(strict=True)
    prep_hash = verify_inventory(prep)
    config, check = read(prep / "config.json"), read(prep / "preflight.json")
    teacher_absent = config.get("teacher_absent", False)
    require(mode in condition_packages(teacher_absent), "unknown condition")
    require(config["protocol"] == PROTOCOL and config["packages"] == condition_packages(teacher_absent), "protocol/package changed")
    require(check["status"] == "READY" or (allow_synthetic and check["status"] == "SYNTHETIC_CPU_ONLY"), "native token preflight pending")
    require(not allow_synthetic or config["tokenizer"] == "synthetic CPU injection", "synthetic mode mismatch")
    require(formation.local_files(config["model_path"]) == config["expected_files"], "model changed")
    require(isinstance(gym, ReasoningGymGym) and gym.strict_verifier, "strict verifier required")
    selected_ids(config["episode_ids"], gym)
    require([gym.question(episode) for episode in config["episode_ids"]] == [row["question"] for row in read(prep / "questions.json")], "questions changed")
    root = fresh_output(out, [prep, config["model_path"], Path(__file__).resolve().parents[1]])
    root.mkdir(parents=True)
    formation._write(root / "config.json", dict(config, mode=mode, preparation_sha256=prep_hash, started_utc=utc()))
    results = []
    try:
        with backend_factory(config["model_path"]) as backend:
            identity = model_backend.configured_generation_identity(config["model_path"], None)
            require(backend.generation_identity() == identity, "clean local base/no-adapter identity required")
            current = preflight(gym, config["episode_ids"], backend.tok, teacher_absent=teacher_absent)
            require(current["status"] == "READY" and current["rows"] == check["rows"]
                    and current["package_tokens"] == check["package_tokens"], "runtime tokenizer preflight differs")
            for start in range(0, 16, 8):
                batch = check["rows"][mode][start:start + 8]
                for offset, row in enumerate(batch, start):
                    formation._write(root / f"request_{offset:02d}.json", dict(row, request_index=offset, mode=mode,
                        package_sha256=check["packages"][mode]["sha256"], package_tokens=check["package_tokens"][mode],
                        package_presentations=0 if teacher_absent else 1, source_identity=identity, max_tokens=400, temperature=.7))
                outputs = backend.batch([row["prompt"] for row in batch], max_tokens=400, temperature=.7,
                                        seeds=[row["seed"] for row in batch])
                require(isinstance(outputs, (list, tuple)) and len(outputs) == len(batch) and all(isinstance(text, str) for text in outputs), "incomplete generation batch")
                for index, (row, text) in enumerate(zip(batch, outputs), start):
                    output_tokens = len(backend.tok.encode(text, add_special_tokens=False))
                    formation._write(root / f"output_{index:02d}.json", dict(request_index=index, episode_id=row["episode_id"],
                        text=text, output_sha256=policy._sha(text.encode()), output_tokens=output_tokens))
                require(all(len(backend.tok.encode(text, add_special_tokens=False)) <= 400 for text in outputs),
                        "returned generation exceeds output budget")
                for index, (row, text) in enumerate(zip(batch, outputs), start):
                    ledger = _ProbeLedger(str(root / f"episode_{index:02d}.jsonl"))
                    Path(ledger.path).touch(exist_ok=False)
                    driver = formation.DiagnosticDriver(gym.episode_from_id(row["episode_id"], 1), bootstrap_for(gym, mode), gym, ledger, 1)
                    require(driver.prompt() == row["prompt"], "runtime prompt mismatch")
                    driver.consume(text)
                    results.append(dict(episode_id=row["episode_id"], request_index=index, **action_summary(ledger.rows())))
                require(backend.generation_identity() == identity, "backend identity changed")
        require(verify_inventory(prep) == prep_hash and formation.local_files(config["model_path"]) == config["expected_files"], "inputs changed")
        result = dict(boundary=config["boundary"], mode=mode, completed_utc=utc(), status="COMPLETE", episodes=results,
                      execution_backend="SYNTHETIC_CPU_FIXTURE" if allow_synthetic else "LOCAL_GPU_BACKEND",
                      first_action_solves=sum(row["first_action_solved"] for row in results), denominator=16,
                      presentations=0 if teacher_absent else 16, episode_opportunities=16,
                      package_tokens_per_presentation=check["package_tokens"][mode],
                      cumulative_package_tokens=16 * check["package_tokens"][mode], reserved_output_tokens=6400)
        formation._write(root / "results.json", result)
        return result
    except BaseException as error:
        formation._write(root / "failure.json", dict(error=repr(error), failed_utc=utc(), completed_episodes=len(results)))
        raise
    finally:
        seal(root)


def execute_pair(preparation, out, *, allow_gpu=False):
    require(allow_gpu, "explicit --allow-gpu required")
    device = supervisor.selected_device()
    prep = Path(preparation).resolve(strict=True)
    digest = verify_inventory(prep)
    config = read(prep / "config.json")
    teacher_absent = config.get("teacher_absent", False)
    modes = tuple(condition_packages(teacher_absent))
    require(read(prep / "preflight.json")["status"] == "READY", "preflight pending")
    require(os.environ.get("V6_MODEL") == config["model_path"], "set V6_MODEL before Python starts")
    root = fresh_output(out, [prep, config["model_path"], Path(__file__).resolve().parents[1]])
    root.mkdir(parents=True)
    formation._write(root / "STARTED.json", dict(preparation_sha256=digest, device=device, started_utc=utc(), order=list(modes)))
    try:
        results = {}
        for mode in modes:
            command = [sys.executable, "-B", "-m", "organism_v6.parent_competency_diagnostic", "--preparation", str(prep),
                       "--out", str(root / mode), "--condition", mode, "--allow-gpu"]
            supervisor.run_worker(command, log_path=root / f"{mode}.log", timeout=900, device=device)
            verify_inventory(root / mode)
            require(not (root / mode / "failure.json").exists(), "worker failed")
            results[mode] = read(root / mode / "results.json")
            require(results[mode]["status"] == "COMPLETE" and results[mode]["presentations"] == (0 if teacher_absent else 16)
                    and results[mode]["mode"] == mode and results[mode]["execution_backend"] == "LOCAL_GPU_BACKEND"
                    and [row["episode_id"] for row in results[mode]["episodes"]] == config["episode_ids"],
                    "incomplete fixed delivery")
        if not teacher_absent:
            require(results["process"]["cumulative_package_tokens"] == results["sham"]["cumulative_package_tokens"],
                    "unequal package dose")
        formation._write(root / "COMPLETED.json", dict(boundary=config["boundary"], completed_utc=utc(), arms=results,
                           interpretation="post-hoc no-teacher descriptive anchor, shorter unmatched input" if teacher_absent else
                           "static joint process package versus sham; no persistence or learning claim"))
    except BaseException as error:
        formation._write(root / "FAILED.json", dict(error=repr(error), failed_utc=utc()))
        raise


def launch_pair(preparation, out, device):
    from gpu.astra_mini_sudoku_diagnostic import check_free
    require(device == "3", "only the prospectively selected GPU3")
    prep = Path(preparation).resolve(strict=True)
    prep_hash = verify_inventory(prep)
    config = read(prep / "config.json")
    require(config["protocol"] == PROTOCOL and config["packages"] == condition_packages(config.get("teacher_absent", False)),
            "changed protocol/packages")
    require(read(prep / "preflight.json")["status"] == "READY", "native preparation pending")
    require(formation.local_files(config["model_path"]) == config["expected_files"], "base pins changed")
    source = Path(__file__).resolve().parents[1]
    root = fresh_output(out, [prep, config["model_path"], source])
    logs = fresh_output(str(root) + "_logs", [root, prep, config["model_path"], source])
    metadata, xml = check_free(device)
    logs.mkdir()
    environment = {key: os.environ[key] for key in ("HOME", "USER", "LOGNAME", "PATH", "LD_LIBRARY_PATH", "TMPDIR")
                   if key in os.environ}
    environment.update(CUDA_VISIBLE_DEVICES=device, V6_MODEL=config["model_path"], PYTHONPATH=str(source),
                       PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", HF_HUB_OFFLINE="1",
                       TRANSFORMERS_OFFLINE="1", VLLM_WORKER_MULTIPROC_METHOD="spawn",
                       CUDA_HOME="/usr/local/cuda-13.0", OMP_NUM_THREADS="1", TOKENIZERS_PARALLELISM="false")
    environment["PATH"] = "/usr/local/cuda-13.0/bin:" + environment.get("PATH", "")
    command = [sys.executable, "-B", "-m", "organism_v6.parent_competency_diagnostic",
               "--preparation", str(prep), "--out", str(root), "--allow-gpu"]
    with (logs / "gpu_before.xml").open("x") as stream:
        stream.write(xml)
    with (logs / "controller.log").open("xb") as output:
        process = subprocess.Popen(command, cwd=source, env=environment, stdin=subprocess.DEVNULL,
                                   stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    receipt = dict(status="LAUNCHED_NOT_COMPLETED", pid=process.pid, device=device, node=3,
                   started_utc=utc(), source=str(source), command=command, preparation_sha256=prep_hash,
                   script_sha256=formation._hash(__file__), gpu=metadata, continuous_reservation=True,
                   root=str(root), logs=str(logs), arm_timeout_seconds=900)
    formation._write(logs / "launch.json", receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--model-path")
    parser.add_argument("--pins", help="JSON {model_path, files} of caller-provided local base hashes")
    parser.add_argument("--ids", help="JSON list of 16 selected existing training IDs")
    parser.add_argument("--preparation")
    parser.add_argument("--condition", choices=(*MODES, "no_teacher"))
    parser.add_argument("--no-teacher", action="store_true")
    parser.add_argument("--allow-gpu", action="store_true")
    parser.add_argument("--launch", action="store_true")
    parser.add_argument("--device", choices=("3",))
    args = parser.parse_args(argv)
    if args.preparation:
        require(args.allow_gpu and not any((args.ids, args.pins, args.model_path, args.no_teacher)), "explicit GPU opt-in and prepared inputs required")
        if args.launch:
            require(args.device is not None and not args.condition, "launch requires device and both conditions")
            result = launch_pair(args.preparation, args.out, args.device)
        elif args.condition:
            supervisor.selected_device()
            result = run_arm(args.preparation, args.out, args.condition,
                             gym=ReasoningGymGym(require_package=True, strict_verifier=True), backend_factory=formation.local_backend)
        else:
            result = execute_pair(args.preparation, args.out, allow_gpu=True)
    else:
        require(args.ids and args.pins and args.model_path and not args.allow_gpu and not args.condition
                and not args.launch and args.device is None, "CPU preparation requires model-path, pins and ids")
        pins = read(args.pins)
        require(pins["model_path"] == str(Path(args.model_path).resolve(strict=True)), "pin model path mismatch")
        result = prepare(args.out, args.model_path, pins["files"], read(args.ids), teacher_absent=args.no_teacher)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
