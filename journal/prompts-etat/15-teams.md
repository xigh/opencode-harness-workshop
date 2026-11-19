Étape 15, dans une session neuve. Commence par lire `ETAT.md` (où en est le projet, laissé par l'étape précédente) et `AGENTS.md` (la définition du projet). Les adresses, les clés et les jetons ne s'écrivent jamais dans le code : ils sont dans `.env` ou dans les variables d'environnement, chargés par `config.charger()` au début de chaque programme. Ne lis jamais `.env` avec tes outils.

Écris `source_teams.py` : le connecteur Teams par l'API Microsoft Graph. Adresse dans `GRAPH_URL`, jeton dans `GRAPH_JETON`, envoyé en `Authorization: Bearer`.

- Liste les équipes (`/me/joinedTeams`), leurs canaux (`/teams/<id>/channels`), puis les messages de chaque canal (`/teams/<id>/channels/<id>/messages`). Suis `@odata.nextLink` jusqu'au bout.
- Pour chaque message, récupère ses réponses (`.../messages/<id>/replies`).
- Un document par fil : le message d'origine suivi de ses réponses, chaque ligne préfixée par l'auteur et l'heure. Le corps est en HTML : garde le texte.
- Écarte les messages système (`messageType` différent de `message`) et les fils sans contenu utile (moins de 20 caractères de texte au total, par exemple « 👍 » ou « Merci ! » seuls).
- Si un message a des pièces jointes, ajoute leur nom et leur adresse à la fin du texte.
- Format commun : `{"id", "source": "teams", "url", "titre", "texte", "maj", "droits", "canal"}`. `titre` = équipe et canal, `maj` = date de la dernière réponse, `droits` = `["equipe:<nom de l'équipe>"]`.
- Écris dans `donnees/documents-teams.jsonl` et affiche le nombre de fils gardés et écartés par canal.

Pour clore l'étape :
1. Mets à jour `ETAT.md` (sections de l'étape 00) : ce qui a été fait, les fichiers créés ou modifiés, les commandes lancées et leur résultat, l'état des services utilisés, les variables utilisées (leurs noms, jamais leurs valeurs), ce qui ne marche pas encore, la prochaine étape.
2. Si l'étape utilise une variable nouvelle, ajoute-la à `.env.example` avec une valeur d'exemple, jamais la vraie.
3. Si l'étape change le projet (fichier nouveau, règle nouvelle), mets à jour `AGENTS.md`.
4. Vérifie qu'aucune clé n'apparaît dans `ETAT.md`, `AGENTS.md`, `.env.example`, le code ni la sortie.
