$ErrorActionPreference = 'Stop'

$Serwer = if ($env:BACKUP_SERWER) { $env:BACKUP_SERWER } else { 'root@46.62.151.181' }
$ZdalnyKatalog = if ($env:BACKUP_ZDALNY_KATALOG) { $env:BACKUP_ZDALNY_KATALOG } else { '/opt/backup/rag' }

$KatalogSkryptu = Split-Path -Parent $MyInvocation.MyCommand.Path
$KatalogLokalny = Join-Path (Split-Path -Parent $KatalogSkryptu) 'backup'

if (-not (Test-Path $KatalogLokalny)) {
    New-Item -ItemType Directory -Path $KatalogLokalny | Out-Null
}

$zdalne = @(& ssh $Serwer "ls -1 $ZdalnyKatalog/rag-*.tar.gz 2>/dev/null")
if ($LASTEXITCODE -ne 0 -and $zdalne.Count -eq 0) {
    Write-Output "brak archiwow na serwerze $Serwer w $ZdalnyKatalog"
    exit 0
}

$pobrane = 0
$pominiete = 0

foreach ($wpis in $zdalne) {
    $sciezka = $wpis.Trim()
    if (-not $sciezka) { continue }

    $nazwa = Split-Path -Leaf $sciezka
    $cel = Join-Path $KatalogLokalny $nazwa

    if (Test-Path $cel) {
        $pominiete++
        continue
    }

    & scp "${Serwer}:$sciezka" $cel
    if ($LASTEXITCODE -ne 0) {
        throw "nie udalo sie pobrac $nazwa"
    }
    $pobrane++
}

$lokalne = @(Get-ChildItem -Path $KatalogLokalny -Filter 'rag-*.tar.gz' | Sort-Object Name)

Write-Output "pobrano nowych: $pobrane"
Write-Output "pominieto juz posiadanych: $pominiete"
Write-Output "archiwow lokalnie: $($lokalne.Count)"
if ($lokalne.Count -gt 0) {
    Write-Output "najnowsze: $($lokalne[-1].Name)"
}
