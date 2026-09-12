import hashlib
import json
from pathlib import Path

from organism_v6 import batch_loop
from organism_v6 import parent_correction_diagnostic as correction
from organism_v6 import reasoning_gym_gym as native
from organism_v6.mini_sudoku_behavior_material import board_from_text, validate_solution
from organism_v6.parent_material_write import _load_tokenizer

home = Path.home()
original = home / "astra_diagnostics/astra_P1_fresh_correction_20260912_attempt1/sham"
prepared = home / "astra_diagnostics/astra_P1_fresh_correction_preparation_20260912_attempt1"
out = Path("/tmp/astra_correction_utility_panel_20260912.json")
prior = correction.read("/tmp/astra_parent_correction_prior_ids_20260912.json")
prior_questions = correction.read("/tmp/astra_parent_correction_prior_questions_20260912.json")["questions"]
prior_questions += correction.read(prepared / "questions.json")["questions"]
prior_hashes = {row["question_sha256"] for row in prior_questions}
ids = [f"rg/mini_sudoku/{seed}" for seed in range(1900000, 1900100)
       if f"rg/mini_sudoku/{seed}" not in set(prior["episode_ids"])][:32]
expected_suffixes = [0, 1, *range(3, 20), *range(43, 50), *range(70, 76)]
assert ids == [f"rg/mini_sudoku/{1900000 + suffix}" for suffix in expected_suffixes]
correction.verify_inventory(original)
capture = next(row for row in correction.read(original / "captures.json")
               if row["episode_id"] == "rg/mini_sudoku/1850124")
source_bytes = capture["wakes"][1]["generation"]["text"].encode()
own_act = source_bytes[:42].decode()
assert source_bytes[42:43] in (b"", b"\n")
assert hashlib.sha256(own_act.encode()).hexdigest() == "74887f842a07dd4e8e0992ecdc50d903859be33e5684c4709bdf5ceb4c084575"
board = board_from_text(own_act.removeprefix("ACT: "))
validate_solution(board_from_text(capture["question"], question=True), board)
config = correction.read(prepared / "config.json")
tokenizer = _load_tokenizer(config["model_path"])
gym = native.ReasoningGymGym(require_package=True, strict_verifier=True)
rows = []
for episode in ids:
    assert gym.split_of(episode) == "canary"
    question = gym.question(episode)
    question_hash = hashlib.sha256(question.encode()).hexdigest()
    assert question_hash not in prior_hashes
    puzzle = board_from_text(question, question=True)
    conflicts = [dict(row=row + 1, column=column + 1, given=puzzle[row][column],
                      learned_board_cell=board[row][column])
                 for row in range(4) for column in range(4)
                 if puzzle[row][column] and puzzle[row][column] != board[row][column]]
    driver = batch_loop.driver_class_for(gym)(gym.episode_from_id(episode, 1), gym.birth_prompt(), gym, None, 1)
    prompt = driver.prompt()
    rendered = tokenizer.apply_chat_template([dict(role="user", content=prompt)],
        tokenize=False, add_generation_prompt=True)
    tokens = len(tokenizer.encode(rendered, add_special_tokens=False))
    assert tokens + 400 <= 4096
    rows.append(dict(episode_id=episode, question=question, question_sha256=question_hash,
        puzzle=puzzle, learned_board_compatible=not conflicts, learned_board_conflicts=conflicts,
        initial_prompt=prompt, initial_prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
        rendered_prompt=rendered, prompt_tokens=tokens))
assert len(rows) == len({row["question_sha256"] for row in rows}) == 32
result = dict(status="NATIVE_PANEL_PREPARED_NO_INFERENCE", episode_ids=ids,
    selection="first32 numeric existing canary IDs absent recovered133 prior IDs; no outcome selection",
    prior_exact_question_hashes=len(prior_hashes), questions=rows,
    source_act_sha256=hashlib.sha256(own_act.encode()).hexdigest(),
    learned_board_compatible_count=sum(row["learned_board_compatible"] for row in rows),
    references_consulted=False, global_historical_freshness=False,
    native_version=native.installed_version(), model_path=config["model_path"],
    families_sha256=correction.formation._hash(Path(native.FAMILIES_JSON)),
    evaluator="existing run_reasoning_neutral; first-ACT primary, post-ACT Scratchpad100tokens measured separately",
    prospective_probe=dict(gen_seed=0, seed_salt=15420, budget_ticks=1, wake_max_tokens=400,
        scratchpad_max_tokens=100, total_token_budget=48000, max_episodes=32, max_model_len=4096))
with out.open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(json.dumps({key:value for key,value in result.items() if key != "questions"}, sort_keys=True))
