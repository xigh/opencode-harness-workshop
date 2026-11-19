Écris `ingestion.py` : l'ingestion des documents de l'assistant documentaire. Les PDF sont dans `../corpus/pdf/` et leurs titres dans `../corpus/manifeste.json` (champ `fichier` → `titre`).

Les fichiers se traitent dans l'ordre du manifeste ; `--limite N` garde les N premiers du manifeste. Un fichier du manifeste absent de `../corpus/pdf/` est signalé et sauté.

Pour chaque PDF :
1. Extraire le texte page par page avec la commande `pdftotext -layout` : les pages sont séparées par le caractère `\f`, numérotées à partir de 1 ; la page vide qui suit le dernier `\f` ne compte pas. Si `pdftotext` est celui de Xpdf (`pdftotext -v` affiche « www.xpdfreader.com » ; celui de Poppler affiche « poppler »), ajouter `-enc UTF-8` : il écrit en Latin1 par défaut. Si `pdftotext` est absent, le dire et s'arrêter : ne pas l'installer soi-même (procédure : `journal/procedures/pdftotext-windows.md`).
2. Découper exactement ainsi, pour que tout le monde obtienne les mêmes morceaux :
   - chaque page à part : un morceau ne chevauche jamais deux pages ;
   - dans le texte de la page, remplacer toute suite de blancs (espaces, tabulations, retours à la ligne) par une seule espace, puis retirer les espaces du début et de la fin ; une page vide après ce nettoyage ne donne aucun morceau ;
   - `debut = 0` ; tant que `debut` est inférieur à la longueur `n` du texte : `fin = debut + 1500` ; si `fin < n`, ramener `fin` sur la dernière espace qui se trouve après `debut` et au plus à `fin` (s'il n'y en a pas, garder `fin`) ; le morceau est `texte[debut:fin]` sans espaces autour, gardé s'il n'est pas vide ; si `fin >= n`, c'est le dernier morceau de la page ; sinon, le nouveau début vaut `fin - 200`, avancé juste après la première espace qui se trouve entre `fin - 200` et `fin` (s'il n'y en a pas, il reste `fin - 200`) ; si ce nouveau début n'est pas plus grand que l'ancien, prendre `debut = fin` ;
   - les morceaux sont numérotés à partir de 1 dans chaque fichier ; le nombre de caractères affiché pour un fichier est la somme des longueurs de ses pages après nettoyage.
   Un morceau garde : fichier, titre, page, numéro du morceau, texte.
3. Calculer les embeddings par lots de 32 avec le serveur d'embedding (`EMBED_URL`, défaut `http://127.0.0.1:8801/v1`, route `/embeddings`, format OpenAI ; le modèle dans `EMBED_MODELE`, défaut `qwen3-embedding-0.6b` ; la clé d'API dans `EMBED_CLE`, facultative, envoyée en `Authorization: Bearer`, jamais affichée). Les documents s'envoient tels quels, sans préfixe.
4. Envoyer les morceaux dans Qdrant (`QDRANT_URL`, défaut `http://127.0.0.1:8803`, API REST, pas de bibliothèque cliente ; clé d'API facultative dans `QDRANT_CLE`, envoyée dans l'en-tête `api-key`, jamais affichée ; sans Qdrant installé, `services-simules/pseudo-qdrant.py` répond sur la même adresse) dans la collection nommée par `QDRANT_COLLECTION` (défaut `documents` ; sur un Qdrant partagé, chacun prend la sienne) : la créer si elle n'existe pas (taille lue sur le premier vecteur, distance `Cosine`), puis `PUT /collections/<nom>/points` avec les vecteurs et le reste en `payload`. Identifiants : des entiers qui se suivent, à partir de 1, dans l'ordre des fichiers puis des morceaux.

Le programme affiche ce qui se passe à chaque étape, pour qu'on le montre en formation :
- pour chaque fichier : nombre de pages, nombre de caractères, nombre de morceaux, durée de l'extraction et de l'embedding ;
- une seule fois, pour le premier morceau du premier fichier : le texte complet du morceau, la requête JSON envoyée au serveur d'embedding (sans la liste complète des textes), les 8 premières valeurs du vecteur et sa taille, puis le JSON d'un point tel qu'envoyé à Qdrant (vecteur abrégé) ;
- à la fin : le total de morceaux, le temps total et le nombre de points dans la collection, relu depuis Qdrant.

Option `--limite N` pour ne traiter que les N premiers fichiers ; `--recreer` pour vider la collection avant de commencer : supprimer tous ses points (`POST /collections/<nom>/points/delete` avec `{"filter": {}}`), pas la collection elle-même. Sur le Qdrant partagé, la clé de la salle peut écrire et supprimer des points dans sa collection, mais ni la créer ni la supprimer : si elle n'existe pas et que la création est refusée (403), le programme le dit et s'arrête.

Lance `python3 ingestion.py --recreer --limite 2` et montre la sortie. Avec le même corpus et le même découpage, tout le monde doit obtenir les mêmes nombres de pages, de caractères et de morceaux : le formateur donne ceux de référence. Ne lance pas tout le corpus : le formateur le fera.

Les variables d'environnement (`EMBED_URL`, `EMBED_MODELE`, `EMBED_CLE`, `QDRANT_URL`, `QDRANT_CLE`, `QDRANT_COLLECTION`, `RERANK_URL`) sont déjà définies dans le terminal où tu travailles : le programme les lit avec `os.environ`, avec les valeurs par défaut ci-dessus si elles manquent. Si un serveur ne répond pas, montre l'erreur et arrête-toi ; ne le cherche pas ailleurs sur la machine.
