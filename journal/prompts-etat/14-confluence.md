Étape 14, dans une session neuve. Commence par lire `ETAT.md` (où en est le projet, laissé par l'étape précédente) et `AGENTS.md` (la définition du projet). Les adresses, les clés et les jetons ne s'écrivent jamais dans le code : ils sont dans `.env` ou dans les variables d'environnement, chargés par `config.charger()` au début de chaque programme. Ne lis jamais `.env` avec tes outils.

Écris `source_confluence.py` : le connecteur Confluence (Data Center, API REST v1). Adresse dans `CONFLUENCE_URL`, jeton personnel dans `CONFLUENCE_JETON`, envoyé en `Authorization: Bearer`.

- Liste les espaces (`/rest/api/space`), puis les pages de chaque espace (`/rest/api/content?spaceKey=...&expand=body.storage,version,space`).
- Les réponses sont paginées : suis `_links.next` jusqu'au bout.
- Convertis le corps au format « storage » en texte lisible : titres, paragraphes, listes, et tableaux ligne par ligne (« Paramètre : Valeur »). Le contenu des macros d'information est gardé.
- Pour chaque page, lis ses restrictions de lecture (`/rest/api/content/<id>/restriction/byOperation/read`) : les groupes trouvés deviennent le champ `droits`, sinon `["tous"]`.
- Format commun : `{"id", "source": "confluence", "url", "titre", "texte", "maj", "droits", "espace"}`, `maj` vient de `version.when`.
- Écris dans `donnees/documents-confluence.jsonl`, affiche le nombre de pages par espace et le texte complet d'une page qui contient un tableau.

Pour clore l'étape :
1. Mets à jour `ETAT.md` (sections de l'étape 00) : ce qui a été fait, les fichiers créés ou modifiés, les commandes lancées et leur résultat, l'état des services utilisés, les variables utilisées (leurs noms, jamais leurs valeurs), ce qui ne marche pas encore, la prochaine étape.
2. Si l'étape utilise une variable nouvelle, ajoute-la à `.env.example` avec une valeur d'exemple, jamais la vraie.
3. Si l'étape change le projet (fichier nouveau, règle nouvelle), mets à jour `AGENTS.md`.
4. Vérifie qu'aucune clé n'apparaît dans `ETAT.md`, `AGENTS.md`, `.env.example`, le code ni la sortie.
