"""Pure memory-row serialization of four captured transfer-world child EVENTs.

Connected sources are validated by full two-hop replay, never the disconnected
micro-bank validator. The caller authenticates the source collection and actor;
this helper neither selects a latest artifact nor generates material or fits.
"""

from hashlib import sha256

from organism_v6 import experienced_event_two_hop as hop


ROW_COUNT = 32
SERIALIZATION = 'FINAL_LF_ONLY'
require = hop.require


def compile_rows(collection):
    """Return eight wrapper-major views of four actual receipt-grounded EVENTs.

    The prior memory layout is retained, with world set to the transfer master
    and source_collection_sha256 binding every row to the full captured source.
    Only final LF count changes; no EVENT fields or query answers are invented.
    """
    verified = hop.replay_collection(collection)
    require(verified['master'] == hop.TRANSFER_MASTER, 'fresh_transfer_collection_required')
    store = hop.exact_text_store(verified)
    rows = []
    for wrapper_index, wrapper in enumerate(hop.micro.WRAPPERS[:8]):
        for record in verified['records']:
            event = record['edge']['event']
            raw = store[event]
            target = hop.micro.canonical_event(raw)
            rows.append(dict(world=verified['master'], event=event, wrapper=f'W{wrapper_index}',
                messages=[dict(role='system', content=hop.micro.MEMORY_SYSTEM),
                          dict(role='user', content=wrapper.format(REQUEST='READ EVENT ' + event)),
                          dict(role='assistant', content=target)],
                source_raw_sha256=sha256(raw.encode('utf-8')).hexdigest(),
                target_sha256=sha256(target.encode('utf-8')).hexdigest(),
                serialization=SERIALIZATION, source_collection_sha256=verified['collection_sha256']))
    require(len(rows) == ROW_COUNT, 'four_facts_times_eight_views_required')
    return rows


def replay_rows(rows, collection):
    """Rebuild and verify all 32 rows against actual source calls and receipts."""
    require(type(rows) is list and len(rows) == ROW_COUNT, 'complete_transfer_memory_rows_required')
    verified = compile_rows(collection)
    require(hop.document_sha256(rows) == hop.document_sha256(verified), 'transfer_memory_row_drift')
    return verified
