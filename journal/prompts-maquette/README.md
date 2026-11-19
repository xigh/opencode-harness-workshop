# Les consignes de la maquette de RAG documentaire (étapes 13 à 18)

Chaque fichier est une consigne donnée telle quelle à OpenCode, dans `maquette/`, par `./etape-maquette.sh NN slug` (shell Unix ; sous Windows, prendre la série `../prompts-etat/` et `.\etape-etat.ps1 maquette NN slug`). Le code qu'OpenCode en a tiré est dans `maquette/`. Les règles communes, dont la liste des adresses et des jetons, sont dans `maquette/AGENTS.md`. Le code doit tourner tel quel sous Windows Server 2025 comme sous Linux.

| Étape | Fichier | Ce qu'OpenCode écrit |
|---|---|---|
| 13 | `13-site.md` | `source_site.py` : le site « base de connaissance » (`robots.txt`, `sitemap.xml`, pages) |
| 14 | `14-confluence.md` | `source_confluence.py` : Confluence Data Center (API REST v1), avec les restrictions de lecture de chaque page |
| 15 | `15-teams.md` | `source_teams.py` : les messages des canaux Teams par l'API Microsoft Graph |
| 16 | `16-index.md` | `index.py` : découpage, embeddings, index local avec les droits de chaque morceau |
| 17 | `17-assistant.md` | `assistant.py` : l'assistant documentaire, qui ne cite que ce que l'utilisateur a le droit de lire |
| 18 | `18-questions.md` | `questions.json` et `evaluer.py` : un petit jeu de test de l'assistant |

## Ce qu'il faut avoir

- `python3 services-simules/serveur-docs.py 8914` : il imite le site, Confluence (Data Center et Cloud) et Microsoft Graph, avec des données fictives.
- Un serveur de modèle et un serveur d'embedding compatibles OpenAI (`LLM_*`, `EMB_*`, voir `maquette/AGENTS.md`).

## À savoir

- Le connecteur Confluence publié traite une erreur 404 sur la lecture des restrictions comme une page publique : un défaut ouvert, à corriger avant tout usage réel.
- Pendant l'étape 18, OpenCode a modifié le test d'évaluation jusqu'à le faire passer, sans toucher à l'assistant : relire aussi le code de l'évaluation.
- Pour un Confluence Cloud (passerelle `api.atlassian.com`, API v2, restrictions héritées), voir l'étape 19 dans `../prompts/`.

Une version de ces consignes où chaque étape est une session neuve, avec un fichier d'état et les secrets dans `.env`, est dans `../prompts-etat/` (lancer d'abord `./etape-etat.sh maquette 00 projet`).
