Étape 01, dans une session neuve. Commence par lire `ETAT.md` (où en est le projet, laissé par l'étape précédente) et `AGENTS.md` (la définition du projet). Les adresses, les clés et les jetons ne s'écrivent jamais dans le code : ils sont dans `.env` ou dans les variables d'environnement, chargés par `config.charger()` au début de chaque programme. Ne lis jamais `.env` avec tes outils.

Écris `etape1_appel.py` : le plus petit client possible pour le serveur du modèle (voir AGENTS.md).

- La configuration du moteur d'inférence et les identifiants se lisent dans des variables d'environnement, jamais en dur dans le code : `LLM_URL` (adresse de base d'un serveur compatible OpenAI), `LLM_MODELE` (nom du modèle), `LLM_CLE` (clé d'API, facultative : si elle est définie, l'envoyer dans l'en-tête `Authorization: Bearer`). Ainsi, le même programme parle à un serveur local ou à un fournisseur en ligne sans changer une ligne.
- La clé n'apparaît jamais à l'écran : ni dans la requête affichée, ni dans un message d'erreur.
- Une fonction `appeler(messages, outils=None)` qui fait un POST sur `/chat/completions` et renvoie la réponse JSON.
- Avant l'envoi, elle affiche le JSON exact de la requête, indenté, sous un titre « >>> REQUÊTE ». Après, le JSON exact reçu sous « <<< RÉPONSE ».
- Le programme principal envoie un seul message utilisateur : « En une phrase, qu'est-ce qu'un reverse proxy ? », puis affiche seulement le texte de la réponse et le nombre de tokens consommés (champ `usage`).
- Pas de streaming.

Lance-le et montre la sortie.

Pour clore l'étape :
1. Mets à jour `ETAT.md` (sections de l'étape 00) : ce qui a été fait, les fichiers créés ou modifiés, les commandes lancées et leur résultat, l'état des services utilisés, les variables utilisées (leurs noms, jamais leurs valeurs), ce qui ne marche pas encore, la prochaine étape.
2. Si l'étape utilise une variable nouvelle, ajoute-la à `.env.example` avec une valeur d'exemple, jamais la vraie.
3. Si l'étape change le projet (fichier nouveau, règle nouvelle), mets à jour `AGENTS.md`.
4. Vérifie qu'aucune clé n'apparaît dans `ETAT.md`, `AGENTS.md`, `.env.example`, le code ni la sortie.
