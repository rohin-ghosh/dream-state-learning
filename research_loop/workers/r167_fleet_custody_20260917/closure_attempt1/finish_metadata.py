import ast


def finish(life, previous):
    reader = Reader()
    reader.metadata_bytes = previous['reads']['metadata_bytes']
    output = dict(life_id=life['life_id'], status='SOURCE_CLOSURE_PENDING')
    try:
        before, argv = identity(life['inventory_identity']['pid'])
        require(before['start_ticks'] == life['inventory_identity']['start_ticks'], 'same_native_start_ticks')
        config_path = Path(argv[argv.index('--config') + 1])
        config, config_ref = reader.document(config_path)
        plan, plan_ref = reader.document(config['plan_path'])
        require(plan_ref['sha256'] == config['plan_sha256'], 'current_native_plan_pin')
        root = Path(plan['source_root'])
        pins = config['source_pins']
        pending = ['gpu/orch_r125_continual_guard.py']
        checked = {}
        while pending:
            relative = pending.pop()
            if relative in checked:
                continue
            require(len(checked) < 256, 'static_runtime_source_count_cap')
            require(relative in pins and '..' not in Path(relative).parts and not Path(relative).is_absolute(),
                    'declared_relative_python_source')
            raw = reader.raw(root / relative)
            actual = hashlib.sha256(raw).hexdigest()
            checked[relative] = dict(sha256=actual, expected_sha256=pins[relative],
                                     matches=actual == pins[relative], bytes=len(raw))
            tree = ast.parse(raw, filename=relative)
            modules = []
            package = relative[:-3].replace('/', '.').split('.')[:-1]
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    modules.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    base = node.module or ''
                    if node.level:
                        prefix = package[:len(package) - node.level + 1]
                        base = '.'.join(prefix + ([base] if base else []))
                    if base:
                        modules.append(base)
                        modules.extend(base + '.' + alias.name for alias in node.names if alias.name != '*')
            for module in modules:
                components = module.split('.')
                candidates = [module.replace('.', '/') + '.py', module.replace('.', '/') + '/__init__.py']
                candidates.extend('/'.join(components[:index]) + '/__init__.py'
                                  for index in range(1, len(components)))
                pending.extend(candidate for candidate in candidates if candidate in pins and candidate not in checked)
        after, unused = identity(before['pid'])
        require(all(before[key] == after[key] for key in ['pid', 'start_ticks', 'boot_id', 'argv_sha256', 'cwd']),
                'same_native_after_runtime_source')
        output.update(status='DECLARED_STATIC_RUNTIME_IMPORT_PINS_CHECKED',
            native_identity={key: after[key] for key in ['pid', 'start_ticks', 'boot_id']},
            source_root=str(root), config=config_ref, plan=plan_ref, source_files=checked,
            all_checked_pins_match=bool(checked) and all(item['matches'] for item in checked.values()),
            source_scope='STATIC_IMPORT_CLOSURE_FROM_NATIVE_GUARD_NOT_TEST_INVENTORY',
            dynamic_imports_and_in_memory_source_not_attested=True, observed_unix=time.time())
    except Exception as error:
        output['error'] = dict(type=type(error).__name__, reason=str(error))
    output['cumulative_metadata_bytes'] = reader.metadata_bytes
    if life['life_id'] == 'repo_reader':
        life['prior_metadata_bytes'] = reader.metadata_bytes
        life['prior_journal_bytes'] = previous['reads']['journal_bytes']
        life['prior_record_count'] = previous['reads']['record_count']
        output['alias_custody'] = observe_life(life)
    return output


request = json.loads(sys.argv[1])
require([life['life_id'] for life in request['lives']] ==
    ['C1', 'C2', 'C3', 'C4', 'continual_run1', 'pilot', 'repo_reader'], 'exact_seven_node5_scope')
for life in request['lives']:
    print(json.dumps(finish(life, request['previous'][life['life_id']]), sort_keys=True), flush=True)
