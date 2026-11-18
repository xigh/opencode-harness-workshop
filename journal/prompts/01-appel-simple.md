Écris `etape1_appel.py` : le plus petit client possible pour le serveur du modèle (voir AGENTS.md).

- La configuration du moteur d'inférence et les identifiants se lisent dans des variables d'environnement, jamais en dur dans le code : `LLM_URL` (adresse de base d'un serveur compatible OpenAI), `LLM_MODELE` (nom du modèle), `LLM_CLE` (clé d'API, facultative : si elle est définie, l'envoyer dans l'en-tête `Authorization: Bearer`). Ainsi, le même programme parle à un serveur local ou à un fournisseur en ligne sans changer une ligne.
- La clé n'apparaît jamais à l'écran : ni dans la requête affichée, ni dans un message d'erreur.
- Une fonction `appeler(messages, outils=None)` qui fait un POST sur `/chat/completions` et renvoie la réponse JSON.
- Avant l'envoi, elle affiche le JSON exact de la requête, indenté, sous un titre « >>> REQUÊTE ». Après, le JSON exact reçu sous « <<< RÉPONSE ».
- Le programme principal envoie un seul message utilisateur : « En une phrase, qu'est-ce qu'un reverse proxy ? », puis affiche seulement le texte de la réponse et le nombre de tokens consommés (champ `usage`).
- Pas de streaming.

Lance-le et montre la sortie.
