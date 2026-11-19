# opencode-harness-workshop

*English summary.* A hands-on workshop, in French: an agent harness built step by step by [OpenCode](https://opencode.ai) driven by a local model (Qwen3.8 27B on `llama-server`) or a hosted one, with every exchange recorded by a logging proxy. The prompts given to OpenCode (two series: the original one, and a « state » series where each step is a fresh session that reads and updates `ETAT.md`, with secrets in `.env`), the code it wrote, the proxy and the simulated services are all here. Standard library Python only, unless a step says otherwise.

---

Un atelier pas à pas : on demande à OpenCode, branché sur un modèle local, de construire un harnais d'agent, puis un assistant documentaire, puis une maquette de RAG sur des sources d'entreprise. Chaque consigne est un fichier ; chaque échange avec le modèle passe par un proxy qui l'enregistre en entier. On voit donc ce que l'outil envoie vraiment au modèle, puis ce que le modèle répond.

## Ce que contient le dépôt

| Dossier | Contenu | Écrit par |
|---|---|---|
| `journal/prompts/` | les consignes des étapes 00 à 12 (du premier appel au modèle jusqu'à l'assistant d'astreinte) et 19 (Confluence Cloud) ; un README par dossier | Claude, pour l'atelier |
| `journal/prompts-maquette/` | les consignes des étapes 13 à 18 : la maquette de RAG documentaire | Claude |
| `journal/prompts-etat/` | les mêmes consignes en série « état » : une étape 00 qui définit le projet, puis une session neuve par étape qui lit et met à jour `ETAT.md`, les secrets dans `.env` | Claude |
| `projet/` | le code produit par les étapes 00 à 12 : client, prompt système, outil, boucle, journal, ingestion, recherche, assistant documentaire (aussi en LangGraph et en LlamaIndex), outils de supervision, assistant d'incident | OpenCode |
| `maquette/` | le code produit par les étapes 13 à 18 : connecteurs site, Confluence et Teams, index, assistant, évaluation | OpenCode |
| `proxy/` | le proxy qui enregistre chaque requête et chaque réponse, avec deux outils pour en faire une page lisible | Claude |
| `services-simules/` | des imitations des API utilisées : supervision, journaux, tickets, messagerie (`serveur.py`) ; Confluence, Microsoft Graph et un site de base de connaissance (`serveur-docs.py`). Toutes les données sont fictives. Pour les postes sans Qdrant ni reranker : `pseudo-qdrant.py` et `pseudo-reranker.py` (voir plus bas) | Claude |
| `essais/` | deux essais écrits à côté du code d'OpenCode, sans le modifier | Claude |
| `etape.sh`, `etape-maquette.sh` | lancent une étape : la consigne, OpenCode, la sortie complète, l'instantané et le diff | Claude |
| `etape-etat.sh` | lance une étape de la série « état », OpenCode réduit à ses propres outils ; garde une copie de `ETAT.md` | Claude |

Plusieurs consignes ont été précisées après l'atelier (01, 03, 06, 07) et une ajoutée (19) : le détail est dans `journal/prompts/README.md`. Le code publié vient des versions précédentes ; relancer une étape le régénère.

Le code de `projet/` et de `maquette/` est tel qu'OpenCode l'a écrit, à une exception près : les noms propres du contexte d'origine ont été remplacés par des noms neutres (« l'assistant documentaire », « l'équipe infrastructure », l'application « docs »).

## Prérequis

- Un serveur de modèle compatible OpenAI. Dans l'atelier : `llama-server` (llama.cpp) avec Qwen3.8 27B, lancé avec `--jinja`.
- Pour les étapes 06 à 10 : un serveur d'embedding et un serveur de reranking (`llama-server --embedding --pooling last` et `--reranking`), plus Qdrant.
- OpenCode, en 1.x ou en 2.x (essayé avec 1.18.10 et 2.3.2) ; Python 3.11 ou plus récent. La 2.x refuse l'option `--pure` de `etape.sh` et `etape-maquette.sh` : utiliser `etape-etat.sh`, qui ne la passe qu'en 1.x.

## Lancer

1. Le proxy devant le modèle (port 8800, ce que lisent `projet/opencode.json` et `maquette/opencode.json`) :
   `python3 proxy/proxy-journal.py --amont http://127.0.0.1:8080 --port 8800 --journal journal/appels.jsonl`
2. Une étape : `./etape.sh 01 appel-simple` lit `journal/prompts/01-appel-simple.md`, lance OpenCode dans `projet/`, garde sa sortie JSON, un instantané et le diff de ce qui a changé.
3. Pour la maquette : `python3 services-simules/serveur-docs.py 8914`, puis `./etape-maquette.sh 13 site`, puis les étapes suivantes jusqu'à 18.
4. Pour lire ce qui s'est passé pendant une étape : `python3 proxy/rendre-html.py journal/appels.jsonl 04-boucle journal/04-boucle.html` (le journal, le nom de l'étape, la page à écrire).

5. La série « état » : `./etape-etat.sh projet 00 projet`, remplir `projet/.env` à partir de `.env.example`, puis `./etape-etat.sh projet 01 appel-simple` et la suite : voir `journal/prompts-etat/README.md`.

### Sous Windows (PowerShell)

Les scripts `etape.sh` et `etape-maquette.sh` demandent un shell Unix. Sous Windows, prendre la série « état » et son script PowerShell :

```powershell
git clone https://github.com/xigh/opencode-harness-workshop
cd opencode-harness-workshop
$env:OPENCODE_CLE = "…"
powershell -ExecutionPolicy Bypass -File .\etape-etat.ps1 projet 00 projet
```

Les autres commandes du dépôt sont les mêmes, avec `py -3` (ou `python`) à la place de `python3` et `$env:NOM = "valeur"` à la place de `export NOM=valeur` :

```powershell
py -3 proxy\proxy-journal.py --amont https://api.scaleway.ai --port 8800 --journal journal\appels.jsonl
py -3 services-simules\pseudo-qdrant.py --port 8803
py -3 services-simules\serveur-docs.py 8914
py -3 services-simules\serveur.py
$env:QDRANT_URL = "http://127.0.0.1:8803"
```

Détails et précautions (politique d'exécution, encodage) : `journal/prompts-etat/README.md`.

Les adresses se règlent par variables d'environnement (`LLM_URL`, `EMBED_URL`, `QDRANT_URL`, `RERANK_URL`, `SERVICES_URL`…), avec des valeurs locales par défaut : voir `projet/AGENTS.md` et `maquette/AGENTS.md`.

## Sans Qdrant, sans reranker

Les étapes 06 et 07 parlent à Qdrant par son API REST et à un serveur de reranking par la route `/v1/rerank`. Sur un poste où l'on ne peut rien installer, quatre solutions, essayées le 18 novembre 2026 sur un MacBook M5 avec les embeddings `qwen3-embedding-8b` de Scaleway :

- **Le pseudo-Qdrant** : `python3 services-simules/pseudo-qdrant.py --port 8803`. Python standard, le sous-ensemble de l'API REST dont l'atelier se sert (collections, ajout de points, `/points/query`, filtre simple sur le payload), gardé sur disque. Pas d'index : chaque question est comparée à tous les vecteurs. Mesuré en 4 096 dimensions : 0,1 s par question à 1 000 morceaux, 0,9 s à 10 000. Les `ingestion.py` et `recherche.py` publiés s'en servent sans changer une ligne.
- **Un vrai reranker local, sans rien compiler** : le binaire précompilé de llama.cpp (page des versions de `ggml-org/llama.cpp`) et un modèle GGUF, `llama-server -m bge-reranker-v2-m3-Q8_0.gguf --reranking --port 8802 -c 8192 -ub 8192 -b 8192`. Pour 20 morceaux de 1 500 caractères : bge-reranker-v2-m3 0,8 s sur le GPU, 4,2 à 4,5 s sur le CPU seul (`--device none -ngl 0`) ; Qwen3-Reranker-0.6B 1,3 s sur le GPU, 9 s sur le CPU. Les deux modèles font environ 600 Mo en Q8_0. bge rend un score brut (un logit, négatif possible), Qwen3-Reranker une probabilité entre 0 et 1.
- **Le pseudo-reranker** : `python3 services-simules/pseudo-reranker.py --port 8802` fait noter chaque morceau de 0 à 10 par un modèle de chat (`RERANK_LLM_URL`, `RERANK_LLM_MODELE`, `RERANK_LLM_CLE`). Environ 2 s pour 20 morceaux avec Qwen3.8 27B chez Scaleway, mais les notes sont grossières (beaucoup d'ex aequo) : de quoi comparer, pas un reranker.
- **Un vrai Qdrant partagé** : pendant l'atelier, Qdrant 1.20 tourne sur un serveur du formateur (adresse et clé données en séance, `QDRANT_CLE`, en-tête `api-key`). La clé de la salle est courte : un portier la vérifie puis ajoute un jeton JWT (Qdrant en mode `jwt_rbac`) qui ouvre `stagiaire01` à `stagiaire10` en écriture et `demo_droits` en lecture. Chacun prend son numéro (`QDRANT_COLLECTION`). Le jeton ne permet ni de créer ni de supprimer une collection : le formateur les crée ; `--recreer` vide la collection au lieu de la supprimer. La collection `demo_droits` montre le filtre de droits.
- **Sans reranking** : la consigne 07 rend l'étage 3 facultatif (`RERANK_URL=`) ; on garde les cinq premiers de la recherche vectorielle.

## Confluence Cloud (étape 19)

La consigne `journal/prompts/19-ingestion-confluence.md` fait écrire `ingestion_confluence.py` : les pages d'un Confluence Cloud, lues par l'API REST v2 à travers la passerelle d'Atlassian (`https://api.atlassian.com/ex/confluence/<cloudId>`, adresse mail et jeton d'API à portées en Basic, portées `read:space:confluence` et `read:page:confluence`), rangées dans la collection `documents` à côté des PDF. Le `cloudId` se lit sur `https://<site>.atlassian.net/_edge/tenant_info`. `services-simules/serveur-docs.py` imite cette API (`/ex/confluence/<cloudId>/wiki/api/v2/...`) pour essayer sans compte. Essai du 18 novembre 2026 : OpenCode (Qwen3.8 27B chez Scaleway) l'a écrit et lancé ; 8 pages lues, 2 écartées (une restriction propre, une héritée), « Quel port pour le VPN ? » trouve la bonne page en premier ; une seconde ingestion remplace les morceaux au lieu de les doubler.

Trois pièges de cette API :
- la pagination (`_links.next`, en-tête `Link`) donne un chemin relatif au site ; il faut le recoller à l'adresse de la passerelle, pas à `_links.base`, où le jeton à portées ne passe pas ;
- `/pages/<id>/permissions` et `/restriction-state` ne rendent que les restrictions posées sur la page elle-même ; une page « ouverte » rangée sous une page restreinte hérite de sa restriction : il faut lire aussi `/pages/<id>/ancestors` ;
- les pages entrent dans le prompt du modèle : une page du Confluence simulé contient une consigne glissée pour l'assistant (« ignore les consignes de ton prompt système… »), à garder pour montrer l'injection.

## Le corpus des étapes 06 à 10

Les PDF ne sont pas fournis. Mettez vos propres documents publics dans `corpus/pdf/` et décrivez-les dans `corpus/manifeste.json` : voir `corpus/README.md`. Les questions des consignes 07 et 08 portaient sur des rapports publics consacrés au numérique responsable ; adaptez-les à votre corpus.

## Pièges rencontrés pendant l'atelier

- `opencode run "/init"` : en 1.18.10, la commande n'est pas reconnue (le modèle a écrit un `CLAUDE.md` en anglais) ; en 2.3.2, elle écrit un `AGENTS.md` en anglais. L'étape 00 de la série « état » fait ce travail en clair.
- `opencode run` attend l'entrée standard : la fermer (`< /dev/null`), sinon il ne démarre jamais.
- Déclarer `small_model`, sinon les titres de session partent vers le modèle par défaut du poste.
- OpenCode injecte dans son prompt les compétences d'autres outils installés sur le poste : `OPENCODE_DISABLE_CLAUDE_CODE=1 OPENCODE_DISABLE_EXTERNAL_SKILLS=1` en 1.x ; en 2.x, `OPENCODE_DISABLE_CLAUDE_CODE`, `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT` et `OPENCODE_DISABLE_CLAUDE_CODE_SKILLS` (déjà dans les scripts). Avec en plus un dossier personnel vide et `journal/prompts-etat/opencode-minimal.json`, la requête envoyée au modèle ne contient que les outils et les deux skills intégrés d'OpenCode : vérifié au proxy.
- En mode `--auto`, l'agent a inspecté les processus de la machine pendant une étape : pour une démonstration, le lancer dans un conteneur ou une machine virtuelle.
- Pendant la maquette, OpenCode a modifié le test d'évaluation jusqu'à le faire passer, sans toucher à l'assistant : relire aussi le code de l'évaluation.
- La lecture des droits de Confluence traite une erreur 404 comme « page publique » : un défaut ouvert, à corriger avant tout usage réel.
- Étape 06 relancée chez Scaleway : le modèle a appelé l'adresse d'embedding par défaut sans lire `EMBED_URL`, puis, faute de réponse, il est allé chercher le service ailleurs : il a lu le script de lancement et listé le dossier de configuration qui contient la clé d'API. La consigne et `AGENTS.md` disent maintenant que les variables sont déjà définies et qu'il ne faut rien lire hors du dépôt. Mieux encore : lancer OpenCode avec un `HOME` à part, ou dans un conteneur.
- Un `HOME` vide prive OpenCode de son catalogue de modèles en cache (`~/.cache/opencode/models.json`) : il retombe sur celui livré avec le binaire, plus ancien, qui ne connaît pas un modèle récent (« Model not found »). Recopier ce seul fichier.
- Même avec la consigne, OpenCode a écrit un faux serveur de reranking dans le dossier temporaire du système pour tester l'étage 3 : la règle « ne pas écrire hors du dossier » ne tient pas toute seule.
- Chez Scaleway, `chat_template_kwargs` ne coupe pas la réflexion de Qwen3.8 ; `reasoning_effort: "none"` la coupe. Sans cela, une réponse courte (`max_tokens` 8) arrive vide : tout part dans le raisonnement.
- La réponse de `/points/query` range les points dans `result.points` ; l'ancienne route `/points/search` les mettait directement dans `result`. Le modèle a d'abord écrit l'ancienne forme.

## Licence

MIT, voir `LICENSE`.
