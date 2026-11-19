Étape 05, dans une session neuve. Commence par lire `ETAT.md` (où en est le projet, laissé par l'étape précédente) et `AGENTS.md` (la définition du projet). Les adresses, les clés et les jetons ne s'écrivent jamais dans le code : ils sont dans `.env` ou dans les variables d'environnement, chargés par `config.charger()` au début de chaque programme. Ne lis jamais `.env` avec tes outils.

Écris `harnais.py`, version propre et réutilisable de la boucle de `etape4_boucle.py` :

- `executer(question, outils, fonctions, systeme=None, max_tours=5)` : `outils` est la liste des définitions JSON, `fonctions` un dictionnaire nom → fonction Python.
- Chaque échange est écrit dans un fichier `traces/AAAAMMJJ-HHMMSS.md` lisible par un humain : pour chaque tour, la requête JSON complète, la réponse JSON complète, l'outil exécuté avec ses arguments et son résultat, la durée de l'appel et les tokens (`usage`). Rien n'est tronqué.
- Si un outil demandé n'existe pas, ou si ses arguments ne sont pas un JSON valide, le harnais renvoie au modèle un message `tool` qui décrit l'erreur, au lieu de planter.
- Un `if __name__ == "__main__"` rejoue la question de l'étape 4 et affiche le chemin de la trace.

Lance-le, montre la sortie et les 40 premières lignes de la trace.

Pour clore l'étape :
1. Mets à jour `ETAT.md` (sections de l'étape 00) : ce qui a été fait, les fichiers créés ou modifiés, les commandes lancées et leur résultat, l'état des services utilisés, les variables utilisées (leurs noms, jamais leurs valeurs), ce qui ne marche pas encore, la prochaine étape.
2. Si l'étape utilise une variable nouvelle, ajoute-la à `.env.example` avec une valeur d'exemple, jamais la vraie.
3. Si l'étape change le projet (fichier nouveau, règle nouvelle), mets à jour `AGENTS.md`.
4. Vérifie qu'aucune clé n'apparaît dans `ETAT.md`, `AGENTS.md`, `.env.example`, le code ni la sortie.
