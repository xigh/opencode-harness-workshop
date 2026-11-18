Écris `ingestion_confluence.py` : l'ingestion des pages d'un Confluence Cloud dans la même collection que `ingestion.py` (`QDRANT_COLLECTION`, défaut `documents`), pour que `recherche.py` les retrouve sans changer une ligne.

Accès : l'API REST v2 de Confluence Cloud, par la passerelle d'Atlassian (jeton d'API à portées).
- `CONFLUENCE_URL` : la base, de la forme `https://api.atlassian.com/ex/confluence/<cloudId>` (sans `/wiki` à la fin) ;
- `CONFLUENCE_COMPTE` (l'adresse mail du compte) et `CONFLUENCE_JETON` (le jeton) : authentification Basic, le jeton n'est jamais affiché ;
- `CONFLUENCE_ESPACES` : les clés des espaces à ingérer, séparées par des virgules ; vide : tous les espaces visibles.

1. Les espaces : `GET {CONFLUENCE_URL}/wiki/api/v2/spaces`, puis les pages de chaque espace : `GET {CONFLUENCE_URL}/wiki/api/v2/spaces/<id>/pages?body-format=storage&limit=250`. Les réponses sont paginées : suis `_links.next` jusqu'au bout. Attention : ce chemin est relatif au site (il commence par `/wiki/api/v2/`) ; recolle-le à `CONFLUENCE_URL`, jamais à `_links.base`, qui désigne le site lui-même, où le jeton à portées ne passe pas.
2. Les droits : une page n'est indexée que si ni elle ni aucun de ses ancêtres n'a de permission de lecture directe. Pour chaque page, lis `GET .../wiki/api/v2/pages/<id>/permissions?operation=read` (permissions posées sur la page elle-même) et `GET .../wiki/api/v2/pages/<id>/ancestors`, puis les permissions de chaque ancêtre (une fois par ancêtre, garde-les en mémoire). Une page restreinte, par elle-même ou par un ancêtre, est écartée, et le programme dit laquelle et pourquoi (« restriction propre » ou « héritée de la page <titre> »). Une erreur sur ces lectures arrête le programme : on ne range jamais une page dont on n'a pas pu lire les droits.
3. Le corps au format « storage » devient du texte lisible : titres, paragraphes, listes, tableaux ligne par ligne (« Paramètre : Valeur »), contenu des macros d'information gardé. Tu peux reprendre la conversion de `../maquette/source_confluence.py`.
4. Découpage, embeddings et rangement comme dans `ingestion.py` (morceaux de 1 500 caractères, 200 de recouvrement, lots de 32, mêmes variables `EMBED_*`, `QDRANT_URL`, `QDRANT_CLE` et `QDRANT_COLLECTION`). Le payload garde les clés que lit `recherche.py` : `fichier` vaut `confluence:<clé de l'espace>`, `titre` le titre de la page, `page` l'identifiant de la page (un entier), plus `morceau`, `texte`, et en plus `source` (`confluence`), `url` (l'adresse de la page à ouvrir dans le navigateur) et `maj` (`version.createdAt`). Identifiants des points : `<identifiant de la page> × 1000 + <numéro du morceau>`, pour qu'une nouvelle ingestion remplace les morceaux d'une page au lieu de les doubler. Ne supprime jamais la collection : elle contient aussi les PDF.

Le programme affiche :
- pour chaque espace : pages lues, pages écartées (avec la raison), morceaux rangés ;
- une seule fois : la requête envoyée pour lister les pages (sans le jeton), le texte complet d'une page qui contient un tableau, puis un point tel qu'envoyé à Qdrant (vecteur abrégé) ;
- à la fin : le nombre de points de la collection, relu depuis Qdrant.

Les variables d'environnement sont déjà définies dans le terminal où tu travailles : le programme les lit avec `os.environ`. Si un serveur ne répond pas, montre l'erreur et arrête-toi ; ne le cherche pas ailleurs sur la machine.

Lance `python3 ingestion_confluence.py` et montre la sortie, puis `python3 recherche.py "Quel port pour le VPN ?"` et `python3 recherche.py "Quand tourne le secret de svc-docs-ingest ?"` : la seconde réponse ne doit pas venir de Confluence, puisque la page qui en parle est restreinte par héritage.
