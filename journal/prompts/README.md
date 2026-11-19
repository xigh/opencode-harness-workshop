# Les consignes du harnais et de l'assistant documentaire (étapes 00 à 12 et 19)

Chaque fichier est une consigne donnée telle quelle à OpenCode, dans `projet/`, par `./etape.sh NN slug` (shell Unix ; sous Windows, prendre la série `../prompts-etat/` et `etape-etat.ps1`). Le code qu'OpenCode en a tiré est dans `projet/`. Les règles communes à toutes les étapes sont dans `projet/AGENTS.md`, qu'OpenCode lit à chaque session.

| Étape | Fichier | Ce qu'OpenCode écrit |
|---|---|---|
| 00 | `00-essai.md` | `bonjour.py` : vérifier qu'OpenCode tourne et parle au modèle |
| 01 | `01-appel-simple.md` | `etape1_appel.py` : le plus petit client du modèle, configuration et clé par variables d'environnement, JSON envoyé et reçu affiché |
| 02 | `02-prompt-systeme.md` | `etape2_systeme.py` : la même question avec et sans prompt système |
| 03 | `03-definir-outil.md` | `etape3_outil.py` : un outil décrit en JSON Schema ; le harnais répond « état inconnu » au lieu de laisser le modèle inventer |
| 04 | `04-boucle.md` | `etape4_boucle.py` : la boucle d'un harnais (question, appel d'outil, résultat, réponse) |
| 05 | `05-journal.md` | `harnais.py` : la boucle réutilisable, avec sa trace |
| 06 | `06-ingestion.md` | `ingestion.py` : PDF, morceaux, embeddings, Qdrant |
| 07 | `07-recherche.md` | `recherche.py` : embedding de la question, recherche vectorielle, reranking (facultatif) |
| 08 | `08-assistant-docs.md` | `assistant_docs.py` : la recherche branchée comme outil dans le harnais |
| 09 | `09-langgraph.md` | `assistant_docs_langgraph.py` : le même assistant avec LangGraph |
| 10 | `10-llamaindex.md` | `assistant_docs_llamaindex.py` : le même assistant avec LlamaIndex |
| 11 | `11-outils-supervision.md` | `outils_supervision.py` : les outils d'astreinte (supervision, journaux, tickets, messagerie), sur les services simulés |
| 12 | `12-assistant-incident.md` | `assistant_incident.py` : de l'alerte au ticket |
| 12 | `12-assistant-incident-reprise.md` | la même consigne, mot pour mot, relancée après une interruption |
| 19 | `19-ingestion-confluence.md` | `ingestion_confluence.py` : les pages d'un Confluence Cloud dans la même collection, pages restreintes écartées |

## Ce qu'il faut avoir pour chaque étape

- Toutes : un serveur de modèle compatible OpenAI (`LLM_URL`, `LLM_MODELE`, `LLM_CLE`).
- 06 à 10 et 19 : un serveur d'embedding (`EMBED_URL`, `EMBED_MODELE`, `EMBED_CLE`), Qdrant ou le pseudo-Qdrant (`QDRANT_URL`, `QDRANT_CLE`, `QDRANT_COLLECTION`), un reranker ou rien (`RERANK_URL`, `RERANK_CLE`), des PDF dans `../corpus/pdf/`.
- 09 et 10 : un environnement `.venv` avec LangGraph et LlamaIndex (les seules étapes hors bibliothèque standard).
- 11 et 12 : `python3 services-simules/serveur.py` (`SERVICES_URL`).
- 19 : un Confluence Cloud (`CONFLUENCE_URL`, `CONFLUENCE_COMPTE`, `CONFLUENCE_JETON`, `CONFLUENCE_ESPACES`), ou `services-simules/serveur-docs.py` qui imite son API.

## Consignes précisées après l'atelier

Le code publié dans `projet/` vient de la version précédente de ces consignes ; relancer l'étape le régénère.

- 01 : la clé d'API passe par `LLM_CLE`, jamais affichée.
- 03 : le harnais renvoie au modèle un résultat « état inconnu » au lieu de s'arrêter sur la demande d'appel.
- 06 et 07 : clés de chaque service (`EMBED_CLE`, `QDRANT_CLE`, `RERANK_CLE`), collection réglable (`QDRANT_COLLECTION`), reranking facultatif, `--recreer` qui vide la collection au lieu de la supprimer ; ne pas chercher un service ailleurs sur la machine.
- 19 : nouvelle étape.

Une version de ces consignes où chaque étape est une session neuve, avec un fichier d'état et les secrets dans `.env`, est dans `../prompts-etat/`.
