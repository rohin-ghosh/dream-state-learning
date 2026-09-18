"""Nonblocking GRID parent mailbox, applied only to subsequent TRAIN calls."""

from copy import deepcopy
import json
import time


def life_class(grid, era, first_parent=41):
    class AsyncLife(grid.Life):
        def poll(self):
            pending, available = [], []
            reserved = {row['number']: row.get('reserved_unix') for row in
                [json.loads(line) for line in (self.root / 'LEDGER.jsonl').read_text().splitlines() if line]
                if row['kind'] == 'PARENT'}
            for path in sorted((self.root / 'parent_queue').glob('P*.request.json')):
                number = int(path.name[1:].split('.')[0])
                if number < first_parent:
                    continue
                identifier = f'P{number:04d}'
                request = grid.read(path)
                received = self.root / 'parent_received' / (identifier + '.json')
                response_path = self.root / 'parent_queue' / (identifier + '.response.json')
                if not received.exists():
                    response = grid.read(response_path) if response_path.exists() else None
                    if response is None and time.time() < min(request['lane_deadline_unix'], grid.END - 5):
                        pending.append(identifier)
                        continue
                    disposition = grid.policy.previous.parent_disposition(
                        request, response, time.time(), self.config['parent_model'])
                    settings = grid.reflection_settings(response, request, grid.read(self.root / 'BROKER_CONFIG.json'))
                    grid.write(received, dict(request=grid.ref(path),
                        response=grid.ref(response_path) if response_path.exists() else None,
                        disposition=disposition, reflection_settings=settings, observed_unix=time.time(),
                        nonblocking=True, request_to_observed_seconds=(time.time()-reserved[number]
                            if reserved.get(number) is not None else None),
                        request_to_reply_seconds=(response.get('finished_unix', time.time())-reserved[number]
                            if response is not None and reserved.get(number) is not None else None)))
                document = grid.read(received)
                applied = self.root / era / 'parent_applied' / (identifier + '.json')
                if not applied.exists():
                    available.append((identifier, document, applied))
            return pending, available

        def ask(self, task, episode, phase):
            grid.require(task['split'] == 'TRAIN' and time.time() < grid.TRAIN_END, 'TRAIN_parent_only')
            pending, available = self.poll()
            request_ref = None
            if not pending:
                number = grid.reserve(self.root, 'PARENT', dict(cycle=self.cycle, task_id=task['id'], phase=phase))
                identifier = f'P{number:04d}'
                request = grid.policy.queue_request(identifier, self.config['life_id'], self.cycle, episode,
                    phase, task, self.events, self.config['cohort_sha256'], time.time())
                request['lane_deadline_unix'] = min(time.time() + 600, grid.END - 5)
                path = self.root / 'parent_queue' / (identifier + '.request.json')
                grid.write(path, request)
                request_ref = grid.ref(path)
            return dict(request=request_ref, response=None,
                disposition=dict(status='PENDING', guidance=None, continue_life=True),
                nonblocking=True, wait_seconds=0, backlog_backpressure=bool(pending),
                delivery_policy='next_TRAIN_generation_boundary', observed_unix=time.time())

        def calls(self, tasks, purpose, messages, cap, *, attached_readout=False):
            grid.require(not attached_readout and all(task['split'] == 'TRAIN' for task in tasks),
                         'async_mailbox_never_DEV_FINAL')
            pending, available = self.poll()
            prompts = deepcopy(messages)
            for identifier, document, applied in available:
                settings = document['reflection_settings']
                if settings['status'] == 'BOUND_FOR_LANE_DECODER':
                    self.settings = settings
                guidance = document['disposition'].get('guidance')
                if guidance:
                    message = json.dumps(dict(parent_request=identifier,
                        guidance_about_preceding_TRAIN=guidance, application='next_turn_boundary'), sort_keys=True)
                    for prompt in prompts:
                        prompt.append(dict(role='user', content=message))
                    self.event('parent', guidance, document['response']['sha256'])
            if purpose == 'reflection':
                cap = self.settings['effective_max_new_tokens']
            results = super().calls(tasks, purpose, prompts, cap, attached_readout=False)
            for identifier, document, applied in available:
                grid.write(applied, dict(parent_request=identifier, parent_received=document['request'],
                    disposition=document['disposition']['status'], applied_to=[item['reference'] for item in results],
                    no_retroactive_replay=True, observed_unix=time.time()))
            return results

    return AsyncLife
