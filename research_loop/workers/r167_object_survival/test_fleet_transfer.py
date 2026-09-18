import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest


SPEC = importlib.util.spec_from_file_location('fleet_transfer', Path(__file__).with_name('fleet_transfer.py'))
transfer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(transfer)
protocol = transfer.protocol


class TransferTests(unittest.TestCase):
    def archive(self, checksum=None, extra=False, link=False):
        raw=b'{"status":"IMMUTABLE_ADAPTER_BIRTH_CUSTODY"}\n'
        name='lives/life/captures/000000/COMPLETE.json'
        digest=hashlib.sha256(raw).hexdigest()
        header=dict(schema=transfer.SCHEMA,life_id='life',sleep=0,context_visibility='PRIVATE_EVALUATOR_ONLY',
            capture=dict(path=str(transfer.ROOT/name),sha256=digest),source_plan_sha256='source',
            files=[dict(name=name,bytes=len(raw),sha256=checksum or digest)])
        stream=io.BytesIO()
        with tarfile.open(fileobj=stream,mode='w') as archive:
            for filename,value in [('TRANSFER_HEADER.json',protocol.canonical(header)),(name,raw)]:
                info=tarfile.TarInfo(filename);info.size=len(value)
                if link and filename==name:
                    info.type=tarfile.SYMTYPE;info.linkname='/etc/passwd';info.size=0
                archive.addfile(info,io.BytesIO(value))
            if extra:
                info=tarfile.TarInfo('optimizer_rng.pt');info.size=0;archive.addfile(info,io.BytesIO())
        stream.seek(0)
        return stream

    def test_exact_receive_once_and_no_model_calls(self):
        with tempfile.TemporaryDirectory() as temporary:
            result=transfer.receive(self.archive(),Path(temporary))
            self.assertEqual(result['status'],'EXACT_RECEIVING_COPY_VERIFIED')
            self.assertEqual(result['model_calls'],0)
            with self.assertRaises(FileExistsError):transfer.receive(self.archive(),Path(temporary))

    def test_wrong_hash_preserves_failure_no_completion(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            with self.assertRaisesRegex(ValueError,'copied_bytes_sha256'):
                transfer.receive(self.archive(checksum='0'*64),root)
            self.assertTrue((root/'receiving_transfers/life_000000/ONCE.json').exists())
            self.assertFalse((root/'receiving_transfers/life_000000/COMPLETE.json').exists())

    def test_unlisted_payload_and_link_refuse(self):
        for options in (dict(extra=True),dict(link=True)):
            with tempfile.TemporaryDirectory() as temporary,self.subTest(options=options):
                with self.assertRaisesRegex(ValueError,'only_regular_expected_unique_files'):
                    transfer.receive(self.archive(**options),Path(temporary))

    def test_wrong_life_or_optimizer_or_traversal_refused(self):
        for name in ('../other','/absolute','lives/other/captures/000000/COMMIT.original.json',
                'lives/life/captures/000000/adapter/optimizer_rng.pt'):
            with self.subTest(name=name),self.assertRaises(ValueError):transfer.safe_member(name,'life',0)


if __name__=='__main__':unittest.main()
