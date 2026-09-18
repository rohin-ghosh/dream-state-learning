"""32MiB individual records; unchanged 64MiB total, chain and hash checks."""

from research_loop.workers.rohin221_continuous_caption_20260918 import journal_bundle, journal_transport


def configure():
    journal_bundle.MAX_BYTES = 33554432
    journal_transport.MAX_BYTES = 33554432
    assert journal_transport.MAX_TOTAL_BYTES == 67108864
    assert journal_transport.MAX_ENVELOPE_BYTES == 100663296


if __name__ == '__main__':
    configure()
    journal_transport.main()
