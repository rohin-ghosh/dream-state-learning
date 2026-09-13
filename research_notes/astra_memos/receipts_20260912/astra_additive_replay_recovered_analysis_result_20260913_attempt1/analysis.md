# Additive replay — collection-only recovery

| Seed | Arm | Exact eligible | Paraphrase content | Held | Canary | Screen |
|---|---|---:|---:|---:|---:|---|
| 0 | ADDITIVE | 14/14 | 10/14 | 47/48 | 12/12 | True |
| 0 | MEMORY_ONLY | 10/14 | 10/14 | 47/48 | 12/12 | True |
Seed 0: original controller/collector/holder rc0/1/1; recovery recorded rc0, collection attempt2, scientific retries0. Original error: {"error": "'dict' object has no attribute 'score_row'", "error_type": "AttributeError", "retry": false, "time": 1789300235.5144627}. Launcher error (separate): null.
| 1 | ADDITIVE | 7/8 | 7/8 | 48/48 | 12/12 | True |
| 1 | MEMORY_ONLY | 8/8 | 8/8 | 46/48 | 12/12 | False |
Seed 1: original controller/collector/holder rc0/1/1; recovery recorded rc0, collection attempt2, scientific retries0. Original error: {"error": "'dict' object has no attribute 'score_row'", "error_type": "AttributeError", "retry": false, "time": 1789300156.5445015}. Launcher error (separate): {"error": "BrokenPipeError(32, 'Broken pipe')", "holder_may_be_running": true}.
| 2 | ADDITIVE | 8/8 | 4/8 | 39/48 | 12/12 | False |
| 2 | MEMORY_ONLY | 3/8 | 2/8 | 47/48 | 12/12 | False |
Seed 2: original controller/collector/holder rc0/1/1; recovery recorded rc0, collection attempt2, scientific retries0. Original error: {"error": "'dict' object has no attribute 'score_row'", "error_type": "AttributeError", "retry": false, "time": 1789300208.4660075}. Launcher error (separate): null.

6 fits,1632 updates,480 cold calls unchanged; recovery adds zero fits/updates/generation. No automatic promotion.
Exact original errors/byte pins, component costs and per-item contrasts remain in analysis.json; all archived evidence remains untouched.
