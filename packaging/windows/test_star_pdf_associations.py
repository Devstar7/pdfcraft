from pathlib import Path
import unittest, xml.etree.ElementTree as ET, tomllib, hashlib
ROOT=Path(__file__).resolve().parents[2]
class Associations(unittest.TestCase):
 def setUp(self):
  self.rows=ET.parse(ROOT/'packaging/windows/pdfcraft.wxs').findall('.//{http://wixtoolset.org/schemas/v4/wxs}RegistryValue')
 def test_visible_name(self):
  for name in ['FriendlyAppName','ApplicationName']:
   rows=[r for r in self.rows if r.get('Name')==name]
   self.assertEqual(len(rows),1);self.assertEqual(rows[0].get('Value'),'STAR PDF')
 def test_default_app_consent(self):
  self.assertFalse(any('UserChoice' in r.get('Key','') for r in self.rows))
  self.assertFalse(any(r.get('Key')=='Software/Classes/.pdf'.replace('/',chr(92)) and not r.get('Name') for r in self.rows))
 def test_stable_open_command(self):
  rows=[r for r in self.rows if r.get('Key')=='Software/Classes/PdfCraft.Document/shell/open/command'.replace('/',chr(92))]
  self.assertEqual(len(rows),1);self.assertEqual(rows[0].get('Value'),'"[#PdfcraftExe]" "%1"')
 def test_document_resource_id(self):
  rows=[r for r in self.rows if r.get('Key')=='Software/Classes/PdfCraft.Document/DefaultIcon'.replace('/',chr(92))]
  self.assertEqual(len(rows),1);self.assertEqual(rows[0].get('Value'),'"[#PdfcraftExe]",-2')
 def test_asset_hashes(self):
  assets=tomllib.loads((ROOT/'ATTRIBUTION.toml').read_text())['asset']
  for path in ['assets/app-icon/pdfcraft-document.svg','assets/app-icon/pdfcraft-document.ico']:
   a=next(a for a in assets if a['path']==path)
   self.assertEqual(a['sha256'],hashlib.sha256((ROOT/path).read_bytes()).hexdigest())
if __name__=='__main__':unittest.main()
