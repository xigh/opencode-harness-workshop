Écris `ingestion.py` : l'ingestion des documents de l'assistant documentaire. Les PDF sont dans `../corpus/pdf/` et leurs titres dans `../corpus/manifeste.json` (champ `fichier` → `titre`).

Pour chaque PDF :
1. Extraire le texte page par page avec la commande `pdftotext -layout` (les pages sont séparées par le caractère `\f`). Garder le numéro de page.
2. Découper en morceaux d'environ 1 500 caractères avec 200 caractères de recouvrement, sans couper au milieu d'un mot. Un morceau garde : fichier, titre, page, numéro du morceau, texte.
3. Calculer les embeddings par lots de 32 avec le serveur d'embedding (`EMBED_URL`, défaut `http://127.0.0.1:8801/v1`, route `/embeddings`, format OpenAI). Les documents s'envoient tels quels, sans préfixe.
4. Envoyer les morceaux dans Qdrant (`QDRANT_URL`, défaut `http://127.0.0.1:8803`, API REST, pas de bibliothèque cliente) dans la collection `documents` : la créer si elle n'existe pas (taille lue sur le premier vecteur, distance `Cosine`), puis `PUT /collections/documents/points` avec les vecteurs et le reste en `payload`. Identifiants : des entiers qui se suivent.

Le programme affiche ce qui se passe à chaque étape, pour qu'on le montre en formation :
- pour chaque fichier : nombre de pages, nombre de caractères, nombre de morceaux, durée de l'extraction et de l'embedding ;
- une seule fois, pour le premier morceau du premier fichier : le texte complet du morceau, la requête JSON envoyée au serveur d'embedding (sans la liste complète des textes), les 8 premières valeurs du vecteur et sa taille, puis le JSON d'un point tel qu'envoyé à Qdrant (vecteur abrégé) ;
- à la fin : le total de morceaux, le temps total et le nombre de points dans la collection, relu depuis Qdrant.

Option `--limite N` pour ne traiter que les N premiers fichiers, et `--recreer` pour supprimer la collection avant de commencer.

Lance `python3 ingestion.py --recreer --limite 2` et montre la sortie. Ne lance pas tout le corpus : le formateur le fera.
