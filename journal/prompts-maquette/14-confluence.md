Écris `source_confluence.py` : le connecteur Confluence (Data Center, API REST v1). Adresse dans `CONFLUENCE_URL`, jeton personnel dans `CONFLUENCE_JETON`, envoyé en `Authorization: Bearer`.

- Liste les espaces (`/rest/api/space`), puis les pages de chaque espace (`/rest/api/content?spaceKey=...&expand=body.storage,version,space`).
- Les réponses sont paginées : suis `_links.next` jusqu'au bout.
- Convertis le corps au format « storage » en texte lisible : titres, paragraphes, listes, et tableaux ligne par ligne (« Paramètre : Valeur »). Le contenu des macros d'information est gardé.
- Pour chaque page, lis ses restrictions de lecture (`/rest/api/content/<id>/restriction/byOperation/read`) : les groupes trouvés deviennent le champ `droits`, sinon `["tous"]`.
- Format commun : `{"id", "source": "confluence", "url", "titre", "texte", "maj", "droits", "espace"}`, `maj` vient de `version.when`.
- Écris dans `donnees/documents-confluence.jsonl`, affiche le nombre de pages par espace et le texte complet d'une page qui contient un tableau.
