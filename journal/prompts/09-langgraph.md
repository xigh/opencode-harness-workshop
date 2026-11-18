Écris `assistant_docs_langgraph.py` : le même assistant que `assistant_docs.py`, mais construite avec **LangGraph** au lieu de notre `harnais.py`.

- Lance-le avec `.venv/bin/python` : LangGraph, langchain-openai et LlamaIndex y sont déjà installés. N'installe rien d'autre.
- Le modèle : `ChatOpenAI` de langchain-openai, branché sur notre serveur (`LLM_URL`, `LLM_MODELE`, clé factice), température 0.2.
- L'outil : `rechercher_documents(question)`, décoré avec `@tool` de langchain, qui appelle **la même** fonction `rechercher` de `recherche.py` et renvoie les mêmes extraits (source et texte). Même description que dans `assistant_docs.py`.
- Le même prompt système que `assistant_docs.py`.
- L'agent : un graphe LangGraph explicite (un nœud modèle, un nœud outils `ToolNode`, une arête conditionnelle `tools_condition`), pas la fonction toute faite `create_react_agent`, pour qu'on voie les étapes. Limite de 5 tours (`recursion_limit`).
- Après chaque réponse, affiche les messages du fil (type, appels d'outils, longueur du contenu), pour comparer avec la trace de notre harnais.

Essaie avec les trois mêmes questions que l'étape 8, montre les réponses, puis compte les lignes de `assistant_docs_langgraph.py` et de `assistant_docs.py` + `harnais.py`.
