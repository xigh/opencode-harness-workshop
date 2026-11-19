Étape 10, dans une session neuve. Commence par lire `ETAT.md` (où en est le projet, laissé par l'étape précédente) et `AGENTS.md` (la définition du projet). Les adresses, les clés et les jetons ne s'écrivent jamais dans le code : ils sont dans `.env` ou dans les variables d'environnement, chargés par `config.charger()` au début de chaque programme. Ne lis jamais `.env` avec tes outils.

Écris `assistant_docs_llamaindex.py` : le même assistant que `assistant_docs.py`, mais construite avec **LlamaIndex** au lieu de notre `harnais.py`.

- Lance-le avec `.venv/bin/python` : LlamaIndex (`llama-index-core`, `llama-index-llms-openai-like`) y est déjà installé. N'installe rien d'autre.
- Le modèle : `OpenAILike` branché sur notre serveur (`LLM_URL`, `LLM_MODELE`, clé factice), avec `is_chat_model=True` et `is_function_calling_model=True`, température 0.2.
- L'outil : `FunctionTool` autour d'une fonction `rechercher_documents(question)` qui appelle **la même** fonction `rechercher` de `recherche.py` et renvoie les mêmes extraits. Même description que dans `assistant_docs.py`.
- L'agent : `FunctionAgent` (module `llama_index.core.agent.workflow`), avec le même prompt système que `assistant_docs.py`. Il est asynchrone : utilise `asyncio.run`.
- Après chaque réponse, affiche les appels d'outils faits par l'agent (nom, arguments), pour comparer avec la trace de notre harnais.

Essaie avec les trois mêmes questions que l'étape 8, montre les réponses, puis compte les lignes de `assistant_docs_llamaindex.py` et de `assistant_docs.py` + `harnais.py`.

Pour clore l'étape :
1. Mets à jour `ETAT.md` (sections de l'étape 00) : ce qui a été fait, les fichiers créés ou modifiés, les commandes lancées et leur résultat, l'état des services utilisés, les variables utilisées (leurs noms, jamais leurs valeurs), ce qui ne marche pas encore, la prochaine étape.
2. Si l'étape utilise une variable nouvelle, ajoute-la à `.env.example` avec une valeur d'exemple, jamais la vraie.
3. Si l'étape change le projet (fichier nouveau, règle nouvelle), mets à jour `AGENTS.md`.
4. Vérifie qu'aucune clé n'apparaît dans `ETAT.md`, `AGENTS.md`, `.env.example`, le code ni la sortie.
