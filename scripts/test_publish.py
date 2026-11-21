import tempfile
import unittest
from pathlib import Path
from publish import metadata, check_forward, read_metadata

class PublicationTests(unittest.TestCase):
    def test_names_and_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            apk = Path(directory) / 'Example-1.apk'
            apk.write_bytes(b'fixture')
            data = metadata('example', '1.0.0', 1, [apk])
            self.assertEqual(64, len(data['sha256'][apk.name]))
            for name in ['../other', 'example/stable', 'Example']:
                with self.assertRaises(ValueError): metadata(name, '1.0.0', 1, [apk])
            with self.assertRaises(ValueError): metadata('example', '1.0.0', 1, [apk, apk])
    def test_app_isolation_rollback_and_reused_code(self):
        old = dict(app='simple', version='1.0.0', code=1, sha256={'x.apk':'a'})
        check_forward(old, old)
        check_forward(old, dict(old, version='1.0.1', code=2))
        for new in [dict(old, app='other'), dict(old, code=0), dict(old, sha256={'x.apk':'b'}), dict(old, version='1.0.1')]:
            with self.assertRaises(ValueError): check_forward(old, new)
    def test_unrecognized_existing_channel_fails_closed(self):
        with self.assertRaises(ValueError): read_metadata('Unrelated release')

if __name__ == '__main__': unittest.main()
