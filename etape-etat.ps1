# Usage : .\etape-etat.ps1 projet 01 appel-simple      (consigne : journal\prompts-etat\NN-slug.md)
# La même chose que etape-etat.sh, pour Windows PowerShell 5.1 et PowerShell 7 : une session neuve d'OpenCode par étape,
# OpenCode réduit à ses propres outils, sa sortie complète gardée, une copie d'ETAT.md après chaque étape.
# Variables : $env:OPENCODE (le binaire, défaut : opencode) ; $env:OPENCODE_HOME (si définie, sert de dossier personnel
# à OpenCode : aucune configuration, aucun plugin ni skill du poste n'est lu).
# La consigne passe par l'entrée standard, pas en argument : Windows PowerShell 5.1 abîme les guillemets d'un argument.
# Écrit par Claude (outillage), pas par OpenCode.
param(
    [Parameter(Mandatory = $true)][ValidateSet('projet', 'maquette')][string]$Dossier,
    [Parameter(Mandatory = $true)][string]$N,
    [Parameter(Mandatory = $true)][string]$Slug
)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$consigne = Join-Path (Join-Path 'journal' 'prompts-etat') "$N-$Slug.md"
if (-not (Test-Path $consigne)) { throw "consigne absente : $consigne" }
$oc = if ($env:OPENCODE) { $env:OPENCODE } else { 'opencode' }

# UTF-8 dans les deux sens : sans cela, Windows PowerShell 5.1 envoie la consigne dans un autre encodage (accents abîmés).
$utf8 = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = $utf8
[Console]::OutputEncoding = $utf8

# Couper tout ce qui ne vient pas d'OpenCode (noms de la 2.x, puis ceux de la 1.x).
foreach ($v in 'OPENCODE_DISABLE_CLAUDE_CODE', 'OPENCODE_DISABLE_CLAUDE_CODE_PROMPT', 'OPENCODE_DISABLE_CLAUDE_CODE_SKILLS',
               'OPENCODE_DISABLE_EXTERNAL_SKILLS', 'OPENCODE_DISABLE_AUTOUPDATE', 'OPENCODE_DISABLE_FREE_MODELS') {
    Set-Item -Path "env:$v" -Value '1'
}
$avant = @{ HOME = $env:HOME; USERPROFILE = $env:USERPROFILE }
if ($env:OPENCODE_HOME) { $env:HOME = $env:OPENCODE_HOME; $env:USERPROFILE = $env:OPENCODE_HOME }

# --pure n'existe qu'en 1.x : la 2.x le refuse et affiche son aide.
$version = (& $oc --version 2>&1 | Out-String)
$arguments = @('run')
if ($version -match '(^|\s)v?1\.') { $arguments += '--pure' }
$arguments += @('--auto', '--format', 'json', '--title', "etat-$Dossier-$N-$Slug")

$journal = Join-Path (Join-Path $PSScriptRoot 'journal') "etat-$Dossier"
$fichierEtape = Join-Path (Join-Path $PSScriptRoot 'journal') 'ETAPE'
New-Item -ItemType Directory -Force -Path $journal | Out-Null
[IO.File]::WriteAllText($fichierEtape, "etat-$Dossier-$N-$Slug", $utf8)
[IO.File]::WriteAllText((Join-Path $journal "$N-$Slug.debut"), (Get-Date -Format s), $utf8)

$texte = [IO.File]::ReadAllText((Resolve-Path $consigne).Path, [Text.Encoding]::UTF8)
$lignes = New-Object System.Collections.Generic.List[string]
Push-Location $Dossier
$ErrorActionPreference = 'Continue'   # les messages d'OpenCode sur stderr ne doivent pas arrêter le script
try {
    $texte | & $oc @arguments 2>&1 | ForEach-Object { $l = "$_"; $l; $lignes.Add($l) }
} finally {
    Pop-Location
    $env:HOME = $avant.HOME; $env:USERPROFILE = $avant.USERPROFILE
}
$sortie = Join-Path $journal "$N-$Slug.opencode.jsonl"
[IO.File]::WriteAllLines($sortie, $lignes, $utf8)
[IO.File]::WriteAllText((Join-Path $journal "$N-$Slug.fin"), (Get-Date -Format s), $utf8)
[IO.File]::WriteAllText($fichierEtape, '', $utf8)
$etat = Join-Path $Dossier 'ETAT.md'
if (Test-Path $etat) {
    Copy-Item $etat (Join-Path $journal "ETAT-$N.md")
    Write-Host "état gardé : $(Join-Path $journal "ETAT-$N.md")"
}
Write-Host "sortie complète : $sortie"
