Étape 16, dans une session neuve. Commence par lire `ETAT.md` (où en est le projet, laissé par l'étape précédente) et `AGENTS.md` (la définition du projet). Les adresses, les clés et les jetons ne s'écrivent jamais dans le code : ils sont dans `.env` ou dans les variables d'environnement, chargés par `config.charger()` au début de chaque programme. Ne lis jamais `.env` avec tes outils.

Écris `index.py` : découpe les documents des trois fichiers `donnees/documents-*.jsonl`, calcule leurs embeddings et range le tout dans un index local.

- Découpage : morceaux d'environ 1 000 caractères avec un recouvrement de 150, coupés de préférence en fin de paragraphe ou de phrase. Chaque morceau commence par le titre du document.
- Embeddings : API compatible OpenAI `/embeddings` à l'adresse `EMB_URL`, modèle `EMB_MODELE`, clé facultative `EMB_CLE`. Envoie les morceaux par paquets de 16.
- Index : un simple fichier `donnees/index.json` (vecteurs normalisés et métadonnées : source, url, titre, maj, droits). La recherche est un produit scalaire en Python pur. Isole le stockage dans deux fonctions `ranger(morceaux)` et `chercher(vecteur, k, droits_utilisateur)` pour pouvoir passer plus tard à Qdrant sans toucher au reste.
- `chercher` ne renvoie que les morceaux dont un des `droits` est `tous` ou appartient aux droits de l'utilisateur.
- Affiche le nombre de morceaux par source, la taille de l'index et le temps d'indexation, puis une recherche d'essai : « Quel port pour le VPN ? ».

Pour clore l'étape :
1. Mets à jour `ETAT.md` (sections de l'étape 00) : ce qui a été fait, les fichiers créés ou modifiés, les commandes lancées et leur résultat, l'état des services utilisés, les variables utilisées (leurs noms, jamais leurs valeurs), ce qui ne marche pas encore, la prochaine étape.
2. Si l'étape utilise une variable nouvelle, ajoute-la à `.env.example` avec une valeur d'exemple, jamais la vraie.
3. Si l'étape change le projet (fichier nouveau, règle nouvelle), mets à jour `AGENTS.md`.
4. Vérifie qu'aucune clé n'apparaît dans `ETAT.md`, `AGENTS.md`, `.env.example`, le code ni la sortie.
