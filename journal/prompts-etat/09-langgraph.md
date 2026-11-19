Étape 09, dans une session neuve. Commence par lire `ETAT.md` (où en est le projet, laissé par l'étape précédente) et `AGENTS.md` (la définition du projet). Les adresses, les clés et les jetons ne s'écrivent jamais dans le code : ils sont dans `.env` ou dans les variables d'environnement, chargés par `config.charger()` au début de chaque programme. Ne lis jamais `.env` avec tes outils.

Écris `assistant_docs_langgraph.py` : le même assistant que `assistant_docs.py`, mais construite avec **LangGraph** au lieu de notre `harnais.py`.

- Lance-le avec `.venv/bin/python` : LangGraph, langchain-openai et LlamaIndex y sont déjà installés. N'installe rien d'autre.
- Le modèle : `ChatOpenAI` de langchain-openai, branché sur notre serveur (`LLM_URL`, `LLM_MODELE`, clé factice), température 0.2.
- L'outil : `rechercher_documents(question)`, décoré avec `@tool` de langchain, qui appelle **la même** fonction `rechercher` de `recherche.py` et renvoie les mêmes extraits (source et texte). Même description que dans `assistant_docs.py`.
- Le même prompt système que `assistant_docs.py`.
- L'agent : un graphe LangGraph explicite (un nœud modèle, un nœud outils `ToolNode`, une arête conditionnelle `tools_condition`), pas la fonction toute faite `create_react_agent`, pour qu'on voie les étapes. Limite de 5 tours (`recursion_limit`).
- Après chaque réponse, affiche les messages du fil (type, appels d'outils, longueur du contenu), pour comparer avec la trace de notre harnais.

Essaie avec les trois mêmes questions que l'étape 8, montre les réponses, puis compte les lignes de `assistant_docs_langgraph.py` et de `assistant_docs.py` + `harnais.py`.

Pour clore l'étape :
1. Mets à jour `ETAT.md` (sections de l'étape 00) : ce qui a été fait, les fichiers créés ou modifiés, les commandes lancées et leur résultat, l'état des services utilisés, les variables utilisées (leurs noms, jamais leurs valeurs), ce qui ne marche pas encore, la prochaine étape.
2. Si l'étape utilise une variable nouvelle, ajoute-la à `.env.example` avec une valeur d'exemple, jamais la vraie.
3. Si l'étape change le projet (fichier nouveau, règle nouvelle), mets à jour `AGENTS.md`.
4. Vérifie qu'aucune clé n'apparaît dans `ETAT.md`, `AGENTS.md`, `.env.example`, le code ni la sortie.
