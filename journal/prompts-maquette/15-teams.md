Écris `source_teams.py` : le connecteur Teams par l'API Microsoft Graph. Adresse dans `GRAPH_URL`, jeton dans `GRAPH_JETON`, envoyé en `Authorization: Bearer`.

- Liste les équipes (`/me/joinedTeams`), leurs canaux (`/teams/<id>/channels`), puis les messages de chaque canal (`/teams/<id>/channels/<id>/messages`). Suis `@odata.nextLink` jusqu'au bout.
- Pour chaque message, récupère ses réponses (`.../messages/<id>/replies`).
- Un document par fil : le message d'origine suivi de ses réponses, chaque ligne préfixée par l'auteur et l'heure. Le corps est en HTML : garde le texte.
- Écarte les messages système (`messageType` différent de `message`) et les fils sans contenu utile (moins de 20 caractères de texte au total, par exemple « 👍 » ou « Merci ! » seuls).
- Si un message a des pièces jointes, ajoute leur nom et leur adresse à la fin du texte.
- Format commun : `{"id", "source": "teams", "url", "titre", "texte", "maj", "droits", "canal"}`. `titre` = équipe et canal, `maj` = date de la dernière réponse, `droits` = `["equipe:<nom de l'équipe>"]`.
- Écris dans `donnees/documents-teams.jsonl` et affiche le nombre de fils gardés et écartés par canal.
