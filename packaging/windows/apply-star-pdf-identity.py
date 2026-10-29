"""One-off STAR PDF Windows branding migration; no install or default-app override."""
from pathlib import Path
import os, json, urllib.request, hashlib, tomllib, re, struct, base64, subprocess
import cairosvg
from PIL import Image
root = Path('.')
changes = {}
def save(path, data):
    (root/path).write_bytes(data if isinstance(data, bytes) else data.encode())
    changes[path] = True
path = 'packaging/windows/pdfcraft.wxs'
s = (root/path).read_text()
for old,new in [('Name="FriendlyAppName" Value="PdfCraft"','Name="FriendlyAppName" Value="STAR PDF"'),('Name="ApplicationName" Value="PdfCraft"','Name="ApplicationName" Value="STAR PDF"'),('Title="PdfCraft"','Title="STAR PDF"')]:
    if s.count(old) != 1: raise RuntimeError('Unexpected source; refusing unsafe replacement: '+old)
    s = s.replace(old,new)
save(path,s)
path = 'assets/app-icon/pdfcraft-document.svg'
s = (root/path).read_text()
for old,new in [('#efe9dc','#ffffff'),('#c8ece4','#ffd9df'),('#12a58a','#f04b64'),('#087f6b','#dc3452'),('#0b0b0c','#183e42')]: s=s.replace(old,new)
save(path,s)
blobs=[cairosvg.svg2png(bytestring=s.encode(),output_width=n,output_height=n) for n in [16,20,24,32,40,48,64,128,256]]
entries=b''; offset=6+16*len(blobs)
for blob in blobs:
    w,h=struct.unpack('>II',blob[16:24])
    entries+=struct.pack('<BBBBHHII',w%256,h%256,0,0,1,32,len(blob),offset); offset+=len(blob)
save('assets/app-icon/pdfcraft-document.ico',struct.pack('<HHH',0,1,len(blobs))+entries+b''.join(blobs))
manifest=(root/'ATTRIBUTION.toml').read_text(); before=tomllib.loads(manifest)
for path in ['assets/app-icon/pdfcraft-document.svg','assets/app-icon/pdfcraft-document.ico']:
    blocks=manifest.split('[[asset]]'); hits=0
    for i,block in enumerate(blocks):
        if block.lstrip().startswith('path = "'+path+'"'):
            block=re.sub(r'sha256 = "[^"]+"','sha256 = "'+hashlib.sha256((root/path).read_bytes()).hexdigest()+'"',block)
            block=block.replace('PdfCraft PDF document icon','STAR PDF document icon').replace('PdfCraft contributors (PDF badge, lettering and composition)','PdfCraft contributors (PDF badge, lettering and composition); STAR7 contributors (coral palette)')
            blocks[i]=block; hits+=1
    if hits!=1: raise RuntimeError('Asset entry missing')
    manifest='[[asset]]'.join(blocks)
save('ATTRIBUTION.toml',manifest)
after=tomllib.loads(manifest)
def row(a):
    esc=lambda t:t.replace('|','\\|')
    return '| `'+a['path']+'` | '+' | '.join([esc(a['title']),esc(a['author']),a['licence'],esc(a['source']),esc(a['usage'])])+' |'
md=(root/'ATTRIBUTION.md').read_text()
for a,b in zip(before['asset'],after['asset']):
    if a!=b:
        if row(a) not in md: raise RuntimeError('Attribution row missing')
        md=md.replace(row(a),row(b))
save('ATTRIBUTION.md',md)
path='assets/app-icon/LICENSE-document.txt'
save(path,(root/path).read_text()+'\nSTAR7 coral palette adaptation: Copyright (c) 2026 STAR7 contributors.\nLicensed under MIT OR Apache-2.0; original Lucide and PdfCraft notices above remain in force.\n')
path='assets/app-icon/README.md'
save(path,(root/path).read_text().replace('green badge and outlined PDF lettering','coral badge and outlined PDF lettering')+'\nSTAR PDF Windows document icon: original Lucide/PdfCraft composition with a STAR7 coral palette, not Adobe artwork. Resource ID 2 and the existing ProgID are preserved.\n')
test = '''from pathlib import Path
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
'''
save('packaging/windows/test_star_pdf_associations.py',test)
ps = r"""param([Parameter(Mandatory)][string] $MsiPath)
$ErrorActionPreference = 'Stop'
$installer = New-Object -ComObject WindowsInstaller.Installer
$db = $installer.OpenDatabase((Resolve-Path -LiteralPath $MsiPath).Path, 0)
function Assert-Registry([string] $Key, [string] $Name, [string] $Expected) {
  $filter = if ($Name) { ('`Name` = ''' + $Name + '''') } else { '`Name` IS NULL' }
  $v = $db.OpenView('SELECT `Value`, `Root` FROM `Registry` WHERE `Key` = ''' + $Key + ''' AND ' + $filter)
  try {
    [void]$v.Execute(); $r = $v.Fetch()
    if (-not $r -or $r.StringData(1) -cne $Expected -or $r.StringData(2) -ne '-1') { throw "STAR PDF registration mismatch: $Key / $Name" }
  } finally { [void]$v.Close() }
}
Assert-Registry 'Software\Classes\Applications\pdfcraft.exe' 'FriendlyAppName' 'STAR PDF'
Assert-Registry 'Software\PdfCraft\Capabilities' 'ApplicationName' 'STAR PDF'
Assert-Registry 'Software\RegisteredApplications' 'STAR PDF' 'Software\PdfCraft\Capabilities'
Assert-Registry 'Software\Classes\.pdf\OpenWithProgids' 'PdfCraft.Document' ''
Assert-Registry 'Software\Classes\PdfCraft.Document\DefaultIcon' '' '"[#PdfcraftExe]",-2'
Assert-Registry 'Software\Classes\PdfCraft.Document\shell\open\command' '' '"[#PdfcraftExe]" "%1"'
$v=$db.OpenView('SELECT `Key`, `Name` FROM `Registry`')
try {
 [void]$v.Execute()
 while ($r=$v.Fetch()) {
  $key=$r.StringData(1); $name=$r.StringData(2)
  if ($key -match 'UserChoice' -or ($key -eq 'Software\Classes\.pdf' -and -not $name)) { throw 'Installer must not override the user-selected PDF default.' }
 }
} finally { [void]$v.Close() }
Write-Output 'PASS STAR PDF compiled association identity and default-app consent.'
"""
save('packaging/windows/test-star-pdf-associations.ps1',ps)
path='packaging/windows/package.ps1'; s=(root/path).read_text()
anchor='Write-Output "STAR PDF installer built successfully: $Msi"'
if s.count(anchor)!=1: raise RuntimeError('Package script changed')
s=s.replace(anchor,"& (Get-Process -Id $PID).Path -NoProfile -File (Join-Path $PSScriptRoot 'test-star-pdf-associations.ps1') -MsiPath $Msi\nif ($LASTEXITCODE -ne 0) { throw 'STAR PDF compiled association checks failed.' }\n"+anchor)
save(path,s)
subprocess.run(['python3','packaging/windows/test_star_pdf_associations.py'],check=True)
if set(Image.open(root/'assets/app-icon/pdfcraft-document.ico').ico.sizes())!={(s,s) for s in [16,20,24,32,40,48,64,128,256]}: raise RuntimeError('Invalid ICO frames')
repo=os.environ['GITHUB_REPOSITORY']; token=os.environ['GH_TOKEN']
def api(path,body=None,method=None):
 req=urllib.request.Request('https://api.github.com/repos/'+repo+'/'+path,data=json.dumps(body).encode() if body is not None else None,method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=60) as r:
  raw=r.read();return json.loads(raw) if raw else None
head=api('git/ref/heads/main')['object']['sha']
if head!=os.environ['GITHUB_SHA']: raise RuntimeError('Branch changed; rerun against latest main')
base=api('git/commits/'+head)['tree']['sha']; entries=[]
for path in changes:
 blob=api('git/blobs',{'content':base64.b64encode((root/path).read_bytes()).decode(),'encoding':'base64'})
 entries.append({'path':path,'mode':'100644','type':'blob','sha':blob['sha']})
tree=api('git/trees',{'base_tree':base,'tree':entries})
commit=api('git/commits',{'message':'Fix STAR PDF Open with name and coral document icon; preserve user consent','tree':tree['sha'],'parents':[head]})
api('git/refs/heads/main',{'sha':commit['sha'],'force':False},'PATCH')
print('Committed',commit['sha'])
api('actions/workflows/release.yml/dispatches',{'ref':'main'})
print('Release compilation requested; public download assets are unchanged.')
