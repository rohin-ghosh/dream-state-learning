import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import time

import reasoning_gym


assert version('reasoning-gym') == '0.1.25'
families = ('countdown', 'knights_knaves', 'mini_sudoku')
results = []
for index in range(24):
    family = families[index % len(families)]
    dataset = reasoning_gym.create_dataset(family, seed=1500000 + index, size=1)
    entry = dataset[0]
    correct = dataset.score_answer(answer=str(entry['answer']), entry=entry)
    invalid = dataset.score_answer(answer='__NOT_AN_ANSWER__', entry=entry)
    assert type(correct) in (int, float) and math.isfinite(correct) and correct == 1
    assert type(invalid) in (int, float) and math.isfinite(invalid) and 0 <= invalid < 1
    results.append(dict(task_index=index, family=family, seed=1500000 + index,
                        reference_check_passed=True, invalid_not_accepted=True))
package = Path(reasoning_gym.__file__).resolve().parent
inventory = {str(path.relative_to(package)): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in sorted(package.rglob('*.py'))}
print(json.dumps(dict(schema='R158_INSTALLED_GYM_CPU_SMOKE_V1', observed_unix=time.time(),
                      package_version=version('reasoning-gym'), tasks=results,
                      package_source_sha256=hashlib.sha256(json.dumps(inventory, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
                      status='PASS', gpu_used=False, child_evaluation=False,
                      answers_published=False), sort_keys=True))
