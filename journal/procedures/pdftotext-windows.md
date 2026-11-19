# Installer pdftotext sous Windows (pour l'étape 06)

L'étape 06 extrait le texte des PDF avec `pdftotext -layout`. Sous Windows, l'outil n'est pas installé. Si OpenCode propose de le télécharger et de l'installer lui-même, l'arrêter : c'est à l'utilisateur de choisir ce qui s'installe sur son poste. La procédure ci-dessous se fait dans le dossier de l'utilisateur, sans droits d'administrateur, avec les outils officiels de Xpdf.

## 1. Arrêter OpenCode

Échap, ou lui dire : « N'installe rien, je m'occupe de pdftotext. »

## 2. Télécharger et vérifier

```powershell
$d = "$env:USERPROFILE\outils"
New-Item -ItemType Directory -Force $d | Out-Null
Invoke-WebRequest -UseBasicParsing -Uri https://dl.xpdfreader.com/xpdf-tools-win-4.06.zip -OutFile "$d\xpdf-tools-win-4.06.zip"
(Get-FileHash "$d\xpdf-tools-win-4.06.zip" -Algorithm SHA256).Hash
```

L'empreinte doit être exactement `2B6CA45DA794E7854A6468FD6C8063FDE62701F001CE03FA4F603EAB7E15A0B6` (Xpdf 4.06, version courante au 19 novembre 2026, archive téléchargée depuis `xpdfreader.com`). Si elle diffère, s'arrêter. Le site publie aussi une signature (`xpdf-tools-win-4.06.zip.sig`).

## 3. Décompresser et ajouter au PATH

```powershell
Expand-Archive "$d\xpdf-tools-win-4.06.zip" -DestinationPath $d -Force
$env:PATH = "$d\xpdf-tools-win-4.06\bin64;$env:PATH"
pdftotext -v
```

Ce `PATH` ne vaut que pour la fenêtre PowerShell ouverte : relancer OpenCode depuis cette fenêtre pour qu'il trouve l'outil. Pour le garder dans le compte de l'utilisateur (il faut ensuite ouvrir une nouvelle fenêtre) :

```powershell
[Environment]::SetEnvironmentVariable('PATH', "$d\xpdf-tools-win-4.06\bin64;" + [Environment]::GetEnvironmentVariable('PATH','User'), 'User')
```

Si Windows bloque `pdftotext.exe` parce qu'il vient d'Internet :

```powershell
Get-ChildItem -Recurse "$d\xpdf-tools-win-4.06" | Unblock-File
```

## 4. Le piège de l'encodage

Le `pdftotext` de Xpdf écrit en Latin1 par défaut (sa documentation : « This defaults to "Latin1" »). Celui de Poppler, courant sous Linux et macOS, écrit en UTF-8. Le Python de l'étape 06 attend de l'UTF-8 : sans précaution, il casse sur les accents. Ajouter `-enc UTF-8` :

```powershell
pdftotext -layout -enc UTF-8 corpus\pdf\un-document.pdf - | Select-Object -First 15
```

Les accents doivent s'afficher correctement.

## 5. Relancer OpenCode

Depuis la même fenêtre, en lui disant : « pdftotext est installé (Xpdf 4.06) et dans le PATH : n'installe rien. Appelle-le avec `-layout -enc UTF-8` ; sans `-enc`, Xpdf écrit en Latin1. » La consigne 06 le dit aussi depuis le 19 novembre 2026.

Procédure écrite à partir de l'archive officielle et de sa documentation ; `pdftotext.exe` n'a pas été lancé par l'auteur de cette page (pas de Windows sous la main).
