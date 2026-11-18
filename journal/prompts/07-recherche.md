Écris `recherche.py` : la récupération des morceaux pour une question, en trois étages, sur la collection `documents` remplie par `ingestion.py`.

1. Embedding de la question avec le même serveur (`EMBED_URL`). Le modèle d'embedding est Qwen3-Embedding : une question s'envoie précédée de l'instruction `Instruct: Étant donné une question, retrouver les passages de documents qui y répondent\nQuery: ` (les documents, eux, n'ont pas de préfixe).
2. Recherche des 20 plus proches dans Qdrant (`POST /collections/documents/points/query`, avec `with_payload`).
3. Reranking de ces 20 morceaux avec le serveur de reranking (`RERANK_URL`, défaut `http://127.0.0.1:8802/v1`, route `/rerank`, corps `{"query": ..., "documents": [...]}`, réponse `results` avec `index` et `relevance_score`). On garde les 5 meilleurs.

Une fonction `rechercher(question, k_vecteur=20, k_final=5)` renvoie les 5 morceaux avec leurs deux scores, et affiche :
- le tableau des 20 résultats de Qdrant (rang, score cosinus, fichier, page, début du texte) ;
- le tableau après reranking (nouveau rang, ancien rang, score du reranker, fichier, page) ;
- la durée de chaque étage.

Le programme principal prend la question en argument. Essaie avec ces deux questions et montre les sorties :
- « Quelle part de l'empreinte carbone du numérique en France vient des terminaux ? »
- « Que recommandent les publications pour réutiliser la chaleur des data centers ? »
