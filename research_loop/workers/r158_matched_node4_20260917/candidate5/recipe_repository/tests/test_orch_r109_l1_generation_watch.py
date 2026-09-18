import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from gpu import orch_r109_l1_generation_watch as watcher


class GenerationWatchTests(unittest.TestCase):
    def response(self,node,**changes):
        report=dict(node=node,raw_output=False,hard_deadline_unix=watcher.END,lanes=[])
        report.update(changes)
        return SimpleNamespace(stdout=json.dumps(report))

    def test_two_nodes_no_deadline_extension(self):
        with patch.object(watcher.subprocess,'run',side_effect=[self.response('node1'),self.response('node2')]):
            result=watcher.snapshot()
        self.assertEqual(result['errors'],[])
        self.assertEqual(set(result['nodes']),{'node1','node2'})
        self.assertEqual(result['hard_deadline_unix'],1789491360)

    def test_raw_or_wrong_node_rejected(self):
        with patch.object(watcher.subprocess,'run',side_effect=[self.response('node1',raw_output=True),self.response('node1')]):
            result=watcher.snapshot()
        self.assertEqual(len(result['errors']),2)
        self.assertEqual(result['nodes'],{})

    def test_failure_is_not_normal_reload(self):
        lane=dict(index=4,launch={},alive=False,failure=dict(error_type='RuntimeError'))
        with patch.object(watcher.subprocess,'run',side_effect=[self.response('node1'),self.response('node2',lanes=[lane])]):
            result=watcher.snapshot()
        self.assertEqual(result['errors'][0]['index'],4)


if __name__ == '__main__':unittest.main()
