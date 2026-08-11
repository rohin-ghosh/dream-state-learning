"""FeltCraft — persistent-world crafting game with ground-truth fact labels,
procedural deep hierarchies, and an exact oracle value. The LLM-tier environment."""
from .dag import CraftDAG, gen_dag, oracle_value, td_salience, requirements
from .engine import World, FeltCraft, Fact, scripted_optimal_play, scripted_noisy_play
from .generator import make_worlds, curriculum_goals, generate_dataset
