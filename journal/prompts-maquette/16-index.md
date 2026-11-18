Écris `index.py` : découpe les documents des trois fichiers `donnees/documents-*.jsonl`, calcule leurs embeddings et range le tout dans un index local.

- Découpage : morceaux d'environ 1 000 caractères avec un recouvrement de 150, coupés de préférence en fin de paragraphe ou de phrase. Chaque morceau commence par le titre du document.
- Embeddings : API compatible OpenAI `/embeddings` à l'adresse `EMB_URL`, modèle `EMB_MODELE`, clé facultative `EMB_CLE`. Envoie les morceaux par paquets de 16.
- Index : un simple fichier `donnees/index.json` (vecteurs normalisés et métadonnées : source, url, titre, maj, droits). La recherche est un produit scalaire en Python pur. Isole le stockage dans deux fonctions `ranger(morceaux)` et `chercher(vecteur, k, droits_utilisateur)` pour pouvoir passer plus tard à Qdrant sans toucher au reste.
- `chercher` ne renvoie que les morceaux dont un des `droits` est `tous` ou appartient aux droits de l'utilisateur.
- Affiche le nombre de morceaux par source, la taille de l'index et le temps d'indexation, puis une recherche d'essai : « Quel port pour le VPN ? ».
