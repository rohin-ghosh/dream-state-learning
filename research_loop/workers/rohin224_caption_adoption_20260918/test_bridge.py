import io
import os
from pathlib import Path
import socket
import tempfile
import threading
import time
import unittest

from bridge import LIMIT, forward, read_line


class BridgeTests(unittest.TestCase):
    def test_protocol_line_is_bounded(self):
        self.assertEqual(read_line(io.BytesIO(b'{}\n')), b'{}\n')
        for raw in (b'{}', b'word' * LIMIT + b'\n'):
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                read_line(io.BytesIO(raw))

    def test_waits_for_new_listener_and_forwards_exactly_once(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'new.sock'
            observed = []

            def replacement():
                time.sleep(.1)
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
                    listener.bind(str(target))
                    listener.listen(1)
                    connection, address = listener.accept()
                    with connection, connection.makefile('rb') as stream:
                        observed.append(read_line(stream))
                        connection.sendall(b'{"scored":true}\n')

            worker = threading.Thread(target=replacement, daemon=True)
            worker.start()
            result = forward(b'{"origin":"actual"}\n', target, deadline=time.monotonic() + 2)
            worker.join(2)
            self.assertFalse(worker.is_alive())
            self.assertEqual(observed, [b'{"origin":"actual"}\n'])
            self.assertEqual(result, b'{"scored":true}\n')

    def test_missing_replacement_times_out_without_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(TimeoutError):
                forward(b'{}\n', Path(directory) / 'absent.sock', deadline=time.monotonic() + .05)

    def test_socket_alias_remains_connectable_after_atomic_route_switch(self):
        with tempfile.TemporaryDirectory() as directory:
            endpoint = Path(directory) / 'original.sock'
            legacy = Path(directory) / 'legacy.sock'
            pending = Path(directory) / 'pending'
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
                listener.bind(str(endpoint))
                listener.listen(1)
                os.link(endpoint, legacy)
                pending.symlink_to(Path(directory) / 'future.sock')
                os.replace(pending, endpoint)
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                    client.connect(str(legacy))
                    accepted, address = listener.accept()
                    with accepted:
                        client.sendall(b'actual')
                        self.assertEqual(accepted.recv(6), b'actual')


if __name__ == '__main__':
    unittest.main()
