Écris `assistant_docs_llamaindex.py` : le même assistant que `assistant_docs.py`, mais construite avec **LlamaIndex** au lieu de notre `harnais.py`.

- Lance-le avec `.venv/bin/python` : LlamaIndex (`llama-index-core`, `llama-index-llms-openai-like`) y est déjà installé. N'installe rien d'autre.
- Le modèle : `OpenAILike` branché sur notre serveur (`LLM_URL`, `LLM_MODELE`, clé factice), avec `is_chat_model=True` et `is_function_calling_model=True`, température 0.2.
- L'outil : `FunctionTool` autour d'une fonction `rechercher_documents(question)` qui appelle **la même** fonction `rechercher` de `recherche.py` et renvoie les mêmes extraits. Même description que dans `assistant_docs.py`.
- L'agent : `FunctionAgent` (module `llama_index.core.agent.workflow`), avec le même prompt système que `assistant_docs.py`. Il est asynchrone : utilise `asyncio.run`.
- Après chaque réponse, affiche les appels d'outils faits par l'agent (nom, arguments), pour comparer avec la trace de notre harnais.

Essaie avec les trois mêmes questions que l'étape 8, montre les réponses, puis compte les lignes de `assistant_docs_llamaindex.py` et de `assistant_docs.py` + `harnais.py`.
