# opencode-harness-workshop

*English summary.* A hands-on workshop, in French: an agent harness built step by step by [OpenCode](https://opencode.ai) driven by a local model (Qwen3.8 27B on `llama-server`), with every exchange recorded by a logging proxy. The 20 prompts given to OpenCode, the code it wrote, the proxy and the simulated services are all here. Standard library Python only, unless a step says otherwise.

---

Un atelier pas à pas : on demande à OpenCode, branché sur un modèle local, de construire un harnais d'agent, puis un assistant documentaire, puis une maquette de RAG sur des sources d'entreprise. Chaque consigne est un fichier ; chaque échange avec le modèle passe par un proxy qui l'enregistre en entier. On voit donc ce que l'outil envoie vraiment au modèle, puis ce que le modèle répond.

## Ce que contient le dépôt

| Dossier | Contenu | Écrit par |
|---|---|---|
| `journal/prompts/` | les consignes des étapes 00 à 12 : du premier appel au modèle jusqu'à l'assistant d'astreinte | Claude, pour l'atelier |
| `journal/prompts-maquette/` | les consignes des étapes 13 à 18 : la maquette de RAG documentaire | Claude |
| `projet/` | le code produit par les étapes 00 à 12 : client, prompt système, outil, boucle, journal, ingestion, recherche, assistant documentaire (aussi en LangGraph et en LlamaIndex), outils de supervision, assistant d'incident | OpenCode |
| `maquette/` | le code produit par les étapes 13 à 18 : connecteurs site, Confluence et Teams, index, assistant, évaluation | OpenCode |
| `proxy/` | le proxy qui enregistre chaque requête et chaque réponse, avec deux outils pour en faire une page lisible | Claude |
| `services-simules/` | des imitations des API utilisées : supervision, journaux, tickets, messagerie (`serveur.py`) ; Confluence, Microsoft Graph et un site de base de connaissance (`serveur-docs.py`). Toutes les données sont fictives | Claude |
| `essais/` | deux essais écrits à côté du code d'OpenCode, sans le modifier | Claude |
| `etape.sh`, `etape-maquette.sh` | lancent une étape : la consigne, OpenCode, la sortie complète, l'instantané et le diff | Claude |

Deux consignes ont été précisées après l'atelier ; le code publié vient de leur version précédente ; relancer l'étape le régénère :

- étape 01 (et `projet/AGENTS.md`) : la configuration du moteur d'inférence et la clé d'API passent par des variables d'environnement (`LLM_URL`, `LLM_MODELE`, `LLM_CLE`). Le `projet/etape1_appel.py` publié lit déjà l'adresse et le modèle dans l'environnement, pas encore la clé ;
- étape 03 : après la demande d'appel d'outil (dont le `content` est vide), le harnais renvoie au modèle un résultat « outil non branché : état inconnu ». L'échange se boucle : on voit si le modèle avoue ne pas savoir au lieu d'inventer. Le `projet/etape3_outil.py` publié s'arrête encore à la demande d'appel.

Le code de `projet/` et de `maquette/` est tel qu'OpenCode l'a écrit, à une exception près : les noms propres du contexte d'origine ont été remplacés par des noms neutres (« l'assistant documentaire », « l'équipe infrastructure », l'application « docs »).

## Prérequis

- Un serveur de modèle compatible OpenAI. Dans l'atelier : `llama-server` (llama.cpp) avec Qwen3.8 27B, lancé avec `--jinja`.
- Pour les étapes 06 à 10 : un serveur d'embedding et un serveur de reranking (`llama-server --embedding --pooling last` et `--reranking`), plus Qdrant.
- OpenCode ; Python 3.11 ou plus récent.

## Lancer

1. Le proxy devant le modèle (port 8800, ce que lisent `projet/opencode.json` et `maquette/opencode.json`) :
   `python3 proxy/proxy-journal.py --amont http://127.0.0.1:8080 --port 8800 --journal journal/appels.jsonl`
2. Une étape : `./etape.sh 01 appel-simple` lit `journal/prompts/01-appel-simple.md`, lance OpenCode dans `projet/`, garde sa sortie JSON, un instantané et le diff de ce qui a changé.
3. Pour la maquette : `python3 services-simules/serveur-docs.py 8914`, puis `./etape-maquette.sh 13 site`, puis les étapes suivantes jusqu'à 18.
4. Pour lire ce qui s'est passé pendant une étape : `python3 proxy/rendre-html.py journal/appels.jsonl 04-boucle journal/04-boucle.html` (le journal, le nom de l'étape, la page à écrire).

Les adresses se règlent par variables d'environnement (`LLM_URL`, `EMBED_URL`, `QDRANT_URL`, `RERANK_URL`, `SERVICES_URL`…), avec des valeurs locales par défaut : voir `projet/AGENTS.md` et `maquette/AGENTS.md`.

## Le corpus des étapes 06 à 10

Les PDF ne sont pas fournis. Mettez vos propres documents publics dans `corpus/pdf/` et décrivez-les dans `corpus/manifeste.json` : voir `corpus/README.md`. Les questions des consignes 07 et 08 portaient sur des rapports publics consacrés au numérique responsable ; adaptez-les à votre corpus.

## Pièges rencontrés pendant l'atelier

- `opencode run` attend l'entrée standard : la fermer (`< /dev/null`), sinon il ne démarre jamais.
- Déclarer `small_model`, sinon les titres de session partent vers le modèle par défaut du poste.
- OpenCode injecte dans son prompt les compétences d'autres outils installés sur le poste : `OPENCODE_DISABLE_CLAUDE_CODE=1 OPENCODE_DISABLE_EXTERNAL_SKILLS=1` (déjà dans les scripts).
- En mode `--auto`, l'agent a inspecté les processus de la machine pendant une étape : pour une démonstration, le lancer dans un conteneur ou une machine virtuelle.
- Pendant la maquette, OpenCode a modifié le test d'évaluation jusqu'à le faire passer, sans toucher à l'assistant : relire aussi le code de l'évaluation.
- La lecture des droits de Confluence traite une erreur 404 comme « page publique » : un défaut ouvert, à corriger avant tout usage réel.

## Licence

MIT, voir `LICENSE`.
