import hashlib
from pathlib import Path
import tempfile
import unittest
from astra_qwen_public_binding_20260913 import check_files, REPOSITORY, REVISION


class PublicBindingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.data = b'fixture bytes\n'
        (self.root/'fixture').write_bytes(self.data)
        self.entry = dict(rfilename='fixture',size=len(self.data),blobId=hashlib.sha1(
            ('blob '+str(len(self.data))+'\0').encode()+self.data).hexdigest())
        self.metadata = dict(id=REPOSITORY,sha=REVISION,siblings=[self.entry])

    def test_plain_blob(self):
        self.assertEqual(check_files(self.root,self.metadata)['fixture']['public_match'],'GIT_BLOB_SHA1')

    def test_lfs_blob(self):
        self.entry['lfs'] = dict(size=len(self.data),sha256=hashlib.sha256(self.data).hexdigest())
        self.assertEqual(check_files(self.root,self.metadata)['fixture']['public_match'],'LFS_SHA256')

    def test_wrong_identity(self):
        self.metadata['sha'] = 'wrong'
        with self.assertRaises(ValueError): check_files(self.root,self.metadata)

    def test_changed_content(self):
        (self.root/'fixture').write_bytes(b'changed bytes\n')
        with self.assertRaises(ValueError): check_files(self.root,self.metadata)

    def test_wrong_size(self):
        self.entry['size'] += 1
        with self.assertRaises(ValueError): check_files(self.root,self.metadata)

    def test_unsafe_duplicate(self):
        self.metadata['siblings'].append(dict(self.entry))
        with self.assertRaises(ValueError): check_files(self.root,self.metadata)
        self.metadata['siblings'] = [dict(self.entry,rfilename='../outside')]
        with self.assertRaises(ValueError): check_files(self.root,self.metadata)


if __name__ == '__main__':
    unittest.main()
