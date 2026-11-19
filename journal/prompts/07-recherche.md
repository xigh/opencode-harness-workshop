Écris `recherche.py` : la récupération des morceaux pour une question, en trois étages, sur la collection remplie par `ingestion.py` (`QDRANT_COLLECTION`, défaut `documents`).

1. Embedding de la question avec le même serveur (`EMBED_URL`, `EMBED_MODELE`, `EMBED_CLE`, comme dans `ingestion.py`). Le modèle d'embedding est Qwen3-Embedding : une question s'envoie précédée de l'instruction `Instruct: Étant donné une question, retrouver les passages de documents qui y répondent\nQuery: ` (les documents, eux, n'ont pas de préfixe).
2. Recherche des 20 plus proches dans Qdrant (`POST /collections/<nom>/points/query`, avec `with_payload` ; `QDRANT_URL` et `QDRANT_CLE` comme dans `ingestion.py`). Les points de la réponse sont dans `result.points`, pas directement dans `result` (c'était la forme de l'ancienne route `/points/search`).
3. Reranking de ces 20 morceaux avec le serveur de reranking (`RERANK_URL`, défaut `http://127.0.0.1:8802/v1`, route `/rerank`, corps `{"query": ..., "documents": [...]}`, réponse `results` avec `index` et `relevance_score` ; clé d'API facultative dans `RERANK_CLE`). On envoie le texte entier des 20 morceaux, dans l'ordre rendu par Qdrant, sans le couper. On trie les résultats par `relevance_score` décroissant (le serveur ne les rend pas toujours triés), à égalité dans l'ordre de Qdrant ; on garde les 5 meilleurs. Cet étage est facultatif : si `RERANK_URL` vaut la chaîne vide, le programme le saute, le dit dans sa sortie et garde les 5 premiers de Qdrant (score de reranking absent).

Une fonction `rechercher(question, k_vecteur=20, k_final=5)` renvoie les 5 morceaux avec leurs deux scores. Elle affiche :
- le tableau des 20 résultats de Qdrant (rang, score cosinus à 4 décimales, fichier, page, les 60 premiers caractères du texte) ;
- le tableau après reranking (nouveau rang, ancien rang, score du reranker à 4 décimales, fichier, page) ;
- la durée de chaque étage.

Le programme principal prend la question en argument. Essaie avec ces deux questions et montre les sorties :
- « Quelle part de l'empreinte carbone du numérique en France vient des terminaux ? »
- « Que recommandent les publications pour réutiliser la chaleur des data centers ? »

Les variables d'environnement (`EMBED_URL`, `EMBED_MODELE`, `EMBED_CLE`, `QDRANT_URL`, `QDRANT_CLE`, `QDRANT_COLLECTION`, `RERANK_URL`, `RERANK_CLE`) sont déjà définies dans le terminal où tu travailles : le programme les lit avec `os.environ`, avec les valeurs par défaut ci-dessus si elles manquent. Si un serveur ne répond pas, montre l'erreur et arrête-toi ; ne le cherche pas ailleurs sur la machine.
