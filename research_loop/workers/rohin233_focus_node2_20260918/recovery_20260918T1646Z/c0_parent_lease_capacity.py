"""Continue the same CPU-only curriculum through its existing lease deadline."""

from c0_parent_clock_repair import transfer
from recover import HERE


if __name__ == '__main__':
    transfer(HERE / 'C0_CURRICULUM_CYCLE_RECONCILED', HERE / 'C0_CURRICULUM_LEASE_CAPACITY',
        lease_capacity=True)
