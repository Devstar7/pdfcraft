param([Parameter(Mandatory)][string] $MsiPath)
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
