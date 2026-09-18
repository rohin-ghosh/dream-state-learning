"""One source-bound transient-provider retry; never retry a publication."""

from pathlib import Path
import time

from console_baseline import read, ref, require, sha, write


MODEL = 'openai/openai/gpt-6-astra'


def consumed_request(seed, attempts, state):
    return any(entry.get('source', {}).get('request_count') == state['request_count']
               for entry in [*seed['attempts'], *attempts])


def candidate(directory, state):
    if directory.name.endswith('_prepub_retry1'):
        return False
    if not (directory / 'RESULT.json').exists() or (directory / 'PUBLISH_INTENT.json').exists():
        return False
    result = read(directory / 'RESULT.json')
    if result.get('status') != 'PROVIDER_FAILED' or 'publication' in result:
        return False
    if result.get('error_type') != 'HTTPError' or not any(code in result.get('error','') for code in ('404','503')):
        return False
    source = read(directory / 'SOURCE.json')
    require(result['source_sha256'] == sha(directory / 'SOURCE.json'), 'failed_source_pin')
    if source['request_count'] != state['request_count'] or source['response_count'] != state['response_count']:
        return False
    require(read(directory / 'API_REQUEST.json')['model'] == MODEL, 'same_known_working_request_model')
    return True


def retry_once(policy, source_root, config, output, seed, state):
    failures = [directory for directory in sorted(output.glob('parent_*')) if directory.is_dir() and candidate(directory,state)]
    if not failures:
        return None
    original = failures[-1]
    directory = output / (original.name + '_prepub_retry1')
    if directory.exists():
        return None
    memory = policy.memory(seed, policy.local_attempts(output), state)
    if memory['awaiting_render']:
        return None
    prompt = read(original / 'PROMPT.json')
    source = read(original / 'SOURCE.json')
    directory.mkdir(mode=0o700)
    write(directory / 'SOURCE.json', source)
    write(directory / 'PROMPT.json', prompt)
    write(directory / 'DISPATCH_INTENT.json', dict(original=ref(original / 'RESULT.json'),
        original_request=ref(original / 'API_REQUEST.json'), original_prompt=ref(original / 'PROMPT.json'),
        reason='Main authorized one bounded pre-publication transient404/503 retry',
        maximum_additional_calls=1, cursor_reset=False, baseline_republished=False))
    result = dict(status='PROVIDER_FAILED', source_sha256=sha(directory/'SOURCE.json'))
    try:
        response, model, usage = policy.parent.strong(prompt['payload'], directory, config['hard_end_unix'],
            prompt['instruction'], reasoning_effort=config.get('parent_reasoning_effort','low'))
        result.update(model=model,usage=usage,status='VALIDATION_FAILED')
        details = policy.decision(response,source,memory)
        if details is None:
            result['status']='SILENT'
        else:
            lesson=config['community_learner'] and not memory['grammar_delivered']
            message=response['message'] + ('\n\n'+policy.GRAMMAR if lesson else '')
            require(len(message.split())<=config['r175_word_limit'] and len(message.encode())<=4096
                    and time.time()<config['hard_end_unix'], 'unchanged_strict_arm_publication_cap')
            result.update(details,message=message,grammar_lesson=lesson,status='PUBLICATION_UNKNOWN',
                relapse_audit_sha256=[audit['authority_sha256'] for audit in memory['relapses']
                    if audit['credit_id']==details['relapse_credit_id']])
            write(directory/'PUBLISH_INTENT.json',dict(message=message,speaker='Astra'))
            result['publication']=policy.parent.publish(source_root,config,message)
            result['status']='PUBLISHED'
    except Exception as error:
        result.update(error_type=type(error).__name__,error=str(error)[:500])
    write(directory/'RESULT.json',result)
    return dict(status=result['status'],one_prepublication_retry=True,result=ref(directory/'RESULT.json'))
