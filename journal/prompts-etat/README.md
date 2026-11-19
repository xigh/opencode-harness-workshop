# La série « état » : les mêmes étapes, une session neuve à chaque fois

Les consignes de `journal/prompts/` et `journal/prompts-maquette/`, réécrites avec trois règles de plus :

- **Le projet se définit d'abord.** L'étape `00-projet.md` fait ce que fait la commande `/init` d'OpenCode, mais en français et avec les règles de l'atelier : `AGENTS.md`, `config.py`, `.env.example`, `.gitignore`, `ETAT.md`.
- **Les secrets vont dans `.env`, pour le code généré.** Les adresses, clés et jetons dont les programmes ont besoin vivent dans `.env` (jamais versionné) ou dans les variables d'environnement, qui l'emportent. Chaque programme appelle `config.charger()`. OpenCode ne lit jamais `.env` avec ses outils. La configuration d'OpenCode lui-même reste dans `opencode.json` ; sa clé d'accès au modèle passe par `OPENCODE_CLE`, distincte de `LLM_CLE` du `.env`.
- **Chaque étape est une session neuve.** Elle commence par lire `ETAT.md` et `AGENTS.md`. Elle finit en mettant `ETAT.md` à jour : ce qui a été fait, les fichiers, les commandes et leur résultat, l'état des services, les noms des variables (jamais leurs valeurs), ce qui ne marche pas, la prochaine étape. On peut donc reprendre n'importe quand, dans une autre session, sur un autre poste.

## Lancer

```
cp journal/prompts-etat/opencode-minimal.json projet/opencode.json   # puis régler baseURL
export OPENCODE_CLE=…            # la clé d'OpenCode vers le modèle
./etape-etat.sh projet 00 projet
cp projet/.env.example projet/.env   # le formateur remplit .env
./etape-etat.sh projet 01 appel-simple
./etape-etat.sh projet 02 prompt-systeme
…
./etape-etat.sh maquette 00 projet    # même étape 00 pour la maquette, puis 13 à 18
```

`etape-etat.sh` garde la sortie complète d'OpenCode et une copie de `ETAT.md` après chaque étape (`journal/etat-<dossier>/`). `OPENCODE=` choisit le binaire, `OPENCODE_HOME=` donne à OpenCode un dossier personnel vide.

## Sous Windows (PowerShell)

`etape-etat.ps1` fait la même chose que `etape-etat.sh`, pour Windows PowerShell 5.1 et PowerShell 7 :

```powershell
Copy-Item journal\prompts-etat\opencode-minimal.json projet\opencode.json   # puis régler baseURL
$env:OPENCODE_CLE = "…"                      # la clé d'OpenCode vers le modèle
powershell -ExecutionPolicy Bypass -File .\etape-etat.ps1 projet 00 projet
Copy-Item projet\.env.example projet\.env    # le formateur remplit .env
powershell -ExecutionPolicy Bypass -File .\etape-etat.ps1 projet 01 appel-simple
```

- Windows bloque par défaut les scripts téléchargés : `-ExecutionPolicy Bypass` lève le blocage pour ce seul lancement, sans changer la configuration du poste.
- La consigne passe à OpenCode par l'entrée standard, pas en argument : Windows PowerShell 5.1 abîme les guillemets d'un argument passé à un programme. Le script force aussi l'UTF-8, sinon les accents arrivent abîmés.
- `$env:OPENCODE = "C:\chemin\opencode.exe"` choisit le binaire ; `$env:OPENCODE_HOME = "C:\opencode-vide"` donne à OpenCode un dossier personnel vide.
- Si `python3` n'existe pas, les programmes se lancent avec `py -3` ou `python`.
- Le script est enregistré en UTF-8 avec BOM : sans cette marque, Windows PowerShell 5.1 lirait ses accents dans l'encodage local. Le garder ainsi en le modifiant.

Essayé le 19 novembre 2026 avec PowerShell 7.7 sur macOS et OpenCode 2.3.2 (étape 00 : fichiers produits, accents intacts, journal en JSON valide). Pas encore essayé sous Windows ni avec Windows PowerShell 5.1.

## OpenCode au plus simple

Essayé avec OpenCode 2.3.2 le 18 novembre 2026 : avec `OPENCODE_HOME` vide, les variables du script et `opencode-minimal.json` (aucun plugin, aucun serveur MCP, aucune instruction ajoutée, `webfetch` et `websearch` refusés, rien hors du dossier), la requête envoyée au modèle, lue au proxy de journalisation, ne contient que les dix outils d'OpenCode (`edit`, `glob`, `grep`, `question`, `read`, `shell`, `skill`, `subagent`, `write`, `execute`) et ses deux skills intégrés (`opencode`, `report`). Rien de Claude Code, rien du poste.

## Essai du 18 novembre 2026

OpenCode 2.3.2, Qwen3.8 27B chez Scaleway, projet vide (seul `AGENTS.md`), étapes 00, 01 et 02, chacune dans une session neuve. L'étape 00 a écrit `AGENTS.md`, `config.py`, `.env.example` (16 variables commentées), `.gitignore`, `bonjour.py` et `ETAT.md`, en français. Le formateur a rempli `.env`. Les étapes 01 et 02 ont lu `ETAT.md` en premier ; la 02 a réutilisé `appeler()` de la 01 sans la réécrire. OpenCode n'a jamais ouvert `.env` (il a lu `.env.example`). Aucune clé dans `ETAT.md`, `AGENTS.md`, le code ni les journaux. Un détail faux dans `ETAT.md` : `SERVICES_URL` décrit comme un « catalogue des services » (ce sont les services simulés) : relire `ETAT.md` entre deux étapes.

## Pièges rencontrés

- `opencode run "/init"` : en 1.18.10, la commande n'est pas reconnue, le modèle a écrit un `CLAUDE.md` en anglais ; en 2.3.2, elle écrit un `AGENTS.md`, en anglais aussi. D'où l'étape 00 écrite en clair.
- La 2.3.2 refuse l'option `--pure` (elle affiche son aide et s'arrête) : `etape-etat.sh` ne la passe qu'en 1.x.
- `OPENCODE_DISABLE_EXTERNAL_SKILLS` n'existe plus en 2.3.2 ; les noms sont `OPENCODE_DISABLE_CLAUDE_CODE`, `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT` et `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS`. Le script positionne les deux jeux.
- Avec un dossier personnel vide, OpenCode n'a plus son catalogue de modèles : un fournisseur déclaré dans `opencode.json` (comme `formation` ici) n'en a pas besoin.
