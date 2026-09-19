from unittest.mock import patch
import unittest

from gpu import orch_math_feedback_uptake_r118_preinfer_broker as wrapper


class BrokerBindingTests(unittest.TestCase):
    def test_changes_only_service_namespace(self):
        original = dict(wrapper.broker.life.client.BRANCHES)
        with patch.object(wrapper.broker.life, 'SERVICES'):
            wrapper.configure()
            self.assertEqual(wrapper.broker.life.service_for('A2'), wrapper.SERVICES/'lane5')
            self.assertEqual(wrapper.broker.life.client.BRANCHES, original)

    def test_delegates_original_config_claims_and_parent_budget(self):
        with patch.object(wrapper.broker.life, 'SERVICES'), patch.object(wrapper.broker, 'main') as delegate:
            wrapper.main()
            delegate.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
