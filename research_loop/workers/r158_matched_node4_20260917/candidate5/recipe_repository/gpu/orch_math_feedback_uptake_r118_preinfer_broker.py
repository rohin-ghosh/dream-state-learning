"""A2-only fresh-service binding over the unchanged legacy HTTP broker."""

from pathlib import Path

from gpu import orch_math_feedback_uptake_r118_parallel_broker as broker


SERVICES = Path('/localhome/local-rohing/orch_math_feedback_uptake_r118_preinfer_20260915_attempt4')


def configure():
    broker.life.SERVICES = SERVICES
    broker.require(broker.life.service_for('A2') == SERVICES/'lane5', 'exact_A2_preinference_service')


def main():
    configure()
    broker.main()


if __name__ == '__main__':
    main()
