import unittest, tempfile, sys, zipfile, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import packages
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE = json.loads((PROJECT_ROOT/'dataset'/'acceptance.json').read_text(encoding='utf-8'))
class PackagesTest(unittest.TestCase):
    def test_versions_backup_and_tampering(self):
        root=packages.ROOT;data=packages.DATA
        source=root/ACCEPTANCE['sources']['plain']
        with tempfile.TemporaryDirectory() as tmp:
            packages.ROOT=Path(tmp);packages.DATA=Path(tmp)/'workspace-data'
            try:
                a=packages.import_file(source);b=packages.import_file(source)
                self.assertEqual(a['count'],ACCEPTANCE['expected']['recordCount']);self.assertEqual(b['id'],'v0002')
                packages.set_current('v0001');self.assertEqual(packages.manifest()['current'],'v0001')
                self.assertEqual(len(packages.manifest()['versions']),2)
                backup=packages.backup();packages.restore(backup);packages.verify(packages.DATA)
                original=packages.manifest()
                with zipfile.ZipFile(backup) as z: contents={n:z.read(n) for n in z.namelist()}
                contents['v0001/records/0.json']=b'[]'
                bad=Path(tmp)/'bad.zip'
                with zipfile.ZipFile(bad,'w') as z:
                    for n,b in contents.items():z.writestr(n,b)
                with self.assertRaises(ValueError):packages.restore(bad)
                self.assertEqual(packages.manifest(),original)
            finally:packages.ROOT=root;packages.DATA=data
if __name__=='__main__':unittest.main()
