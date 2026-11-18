Écris `harnais.py`, version propre et réutilisable de la boucle de `etape4_boucle.py` :

- `executer(question, outils, fonctions, systeme=None, max_tours=5)` : `outils` est la liste des définitions JSON, `fonctions` un dictionnaire nom → fonction Python.
- Chaque échange est écrit dans un fichier `traces/AAAAMMJJ-HHMMSS.md` lisible par un humain : pour chaque tour, la requête JSON complète, la réponse JSON complète, l'outil exécuté avec ses arguments et son résultat, la durée de l'appel et les tokens (`usage`). Rien n'est tronqué.
- Si un outil demandé n'existe pas, ou si ses arguments ne sont pas un JSON valide, le harnais renvoie au modèle un message `tool` qui décrit l'erreur, au lieu de planter.
- Un `if __name__ == "__main__"` rejoue la question de l'étape 4 et affiche le chemin de la trace.

Lance-le, montre la sortie et les 40 premières lignes de la trace.
