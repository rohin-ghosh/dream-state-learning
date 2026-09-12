import datetime
import hashlib
import json
from pathlib import Path
import sys


source = Path.home() / 'astra_sources/5f6e1f1d217dcdb15176dc84b9ac34ec960c48de'
sys.path.insert(0, str(source))
from organism_v6 import conditional_behavior_corpus as corpus
assert Path(corpus.__file__).resolve().parent.parent == source
root = Path.home() / 'astra_diagnostics/astra_conditional_behavior_20260912_attempt2/material'
root.mkdir(parents=True, exist_ok=False)


def write(name, value):
    with (root / name).open('x') as output:
        json.dump(value, output, indent=2, sort_keys=True, allow_nan=False)


candidate = corpus.build_candidate(root=0, action_labels=("dax", "wug"), outcome_labels=("fep", "nup"))
write('candidate.json', candidate)
write('recipe.json', corpus.training_recipe(learning_rate=1e-4, seed=0))
try:
    parent = json.loads((Path.home() / 'astra_diagnostics/astra_fundamental_teaching_20260912_attempt1/plan.json').read_text())
    names = {'config.json', 'tokenizer.json', 'tokenizer_config.json', 'vocab.json', 'merges.txt',
        'special_tokens_map.json', 'added_tokens.json', 'chat_template.jinja', 'chat_template.json'}
    hashes = {name: digest for name, digest in parent['model_files'].items() if name in names}
    native = corpus.audit_native(candidate, parent['model'], hashes)
    write('native_audit.json', native)
    for arm in corpus.ARMS:
        write(arm + '.json', {'corpus': native['corpora'][arm]})
    write('teacher_forcing_interface.json', corpus.teacher_forcing_interface(candidate))
    summary = dict(status='NATIVE_PREPARED_NO_FIT_NO_LAUNCH', source=str(source), root=str(root),
        observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        input_tokens_per_epoch=native['input_tokens_per_epoch'],
        target_tokens_per_epoch=native['target_tokens_per_epoch'],
        origin='UNRESOLVED_LOCAL_HASHES_ONLY',
        source_sha256=native['source_sha256'],
        files={path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(root.iterdir())})
    write('manifest.json', summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
except BaseException as error:
    write('failure.json', dict(type=type(error).__name__, message=str(error),
        observed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), source=str(source),
        status='NATIVE_AUDIT_FAILED_NO_FIT_NO_LAUNCH'))
    raise
