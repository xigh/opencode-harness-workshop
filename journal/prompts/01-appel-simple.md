Écris `etape1_appel.py` : le plus petit client possible pour le serveur du modèle (voir AGENTS.md pour l'adresse).

- Une fonction `appeler(messages, outils=None)` qui fait un POST sur `/chat/completions` et renvoie la réponse JSON.
- Avant l'envoi, elle affiche le JSON exact de la requête, indenté, sous un titre « >>> REQUÊTE ». Après, le JSON exact reçu sous « <<< RÉPONSE ».
- Le programme principal envoie un seul message utilisateur : « En une phrase, qu'est-ce qu'un reverse proxy ? », puis affiche seulement le texte de la réponse et le nombre de tokens consommés (champ `usage`).
- Pas de streaming.

Lance-le et montre la sortie.
