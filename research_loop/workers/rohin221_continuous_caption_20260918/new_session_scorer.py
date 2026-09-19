"""Additional fixed-6250 scorer identity; existing service and games stay untouched."""

from gpu import ny_caption_data as data
from research_loop.workers.rohin221_continuous_caption_20260918 import shared_scorer
from research_loop.workers.rohin221_continuous_caption_20260918.native_proxy import require_future_origin


class FutureOnlyHub(shared_scorer.Hub):
    def __init__(self,root,registry,game_factory,scenes,rule):
        data.require(len(registry['rows']) == 1, 'one_explicit_new_identity')
        config = registry['rows'][0]
        data.require(config['session_id'] == 'r229_extra_unparented_node2_gpu2'
            and config['host_alias'] == 'ovx'
            and type(config.get('minimum_origin_record_index')) is int,
            'exact_new_session_future_epoch')
        super().__init__(root,registry,game_factory,scenes,rule)

    def native(self,envelope):
        if type(envelope) is dict and envelope.get('session_id') in self.registry:
            require_future_origin(self.registry[envelope['session_id']],envelope['request'])
        return super().native(envelope)


if __name__ == '__main__':
    shared_scorer.Hub = FutureOnlyHub
    shared_scorer.main()
