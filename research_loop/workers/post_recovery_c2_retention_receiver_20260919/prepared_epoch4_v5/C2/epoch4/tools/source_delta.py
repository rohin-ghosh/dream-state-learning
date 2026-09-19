from pathlib import Path
import hashlib
NATIVE = "gpu/orch_r125_continual_native.py"
RUNTIME = "gpu/c2_retention_runtime.py"
READER = "gpu/checkpoint_tail_runtime.py"
PROOF = "gpu/immutable_prefix_proof.py"
AUTHORITY = "gpu/c2_prefix_authority.py"
GUARD = "gpu/orch_r125_continual_guard.py"
EXPECTED = {'gpu/orch_r125_continual_native.py': {'before': '1bf18d5f34d2f027be1c79120ec654afe9869e647150245a29c8a19ebda81ff6', 'after': '004042397f5bdec18bdd5cb26b30ed102ee94d70db1e4cea7ee85ff1936b2ebb'}, 'gpu/c2_retention_runtime.py': {'before': None, 'after': '8106e997354d333f64057eaf1484de4c2f105908ae347192b036b4b167b336b7'}, 'gpu/checkpoint_tail_runtime.py': {'before': '972456b7d6cb026cc922e067114701d4f157fa6ed775e4406ecb52c86eef7d3e', 'after': '4e7746a8da7f99cb0354beb8d489a92e8fcb387e1409256901d1a9b0a033803c'}, 'gpu/immutable_prefix_proof.py': {'before': None, 'after': 'ce5542e08f463cac4d795100bdc409480b4aef162632dc2aa6642bed9d08960b'}, 'gpu/c2_prefix_authority.py': {'before': None, 'after': '8ef2d9e7e61afad19919c614393a36e998c12187b375825b2686a5ca039f3c5c'}, 'gpu/orch_r125_continual_guard.py': {'before': '1b12ff40ae7d88c06b956cf8c624aa8b010781f66a4eb0f630455f1be5e9dab6', 'after': '2afd2c89bbb92f1533f68cfef0b0eb43c1bd2029e8993f5dafca2b1278c98e13'}}
def changes_for(source):
    for name, entry in EXPECTED.items():
        path = Path(source) / name
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
        if actual != entry["before"]:
            raise ValueError("exact_original_C2_preimage:" + name)
    return {name: dict(entry) for name, entry in EXPECTED.items()}
